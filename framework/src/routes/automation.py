from flask import Blueprint, jsonify, request
import asyncio
import logging
from src.services.browser_automation import browser_manager
from src.services.linkedin_engine import get_linkedin_engine
from src.services.ai_content import PersonaProfile, DemographicData, ProfessionalData, SkillsData, ContentData, VisualAssets
from datetime import datetime

# AI-native automation (optional, enabled when deps present)
try:
  from src.services.ai_browser_agent import AIBrowserAgent  # type: ignore
  from src.services.linkedin_ai_engine import LinkedInAIEngine  # type: ignore
  from src.services.account_warmup_service import AccountWarmupService  # type: ignore
  from src.services.session_manager import AISessionRegistry, AISession  # type: ignore
  AI_AVAILABLE = True
except Exception:
  AIBrowserAgent = None  # type: ignore
  LinkedInAIEngine = None  # type: ignore
  AccountWarmupService = None  # type: ignore
  AISessionRegistry = None  # type: ignore
  AISession = None  # type: ignore
  AI_AVAILABLE = False

logger = logging.getLogger(__name__)
automation_bp = Blueprint('automation', __name__)

# Registry for live AI sessions
_ai_sessions = AISessionRegistry() if AI_AVAILABLE else None

@automation_bp.route('/automation/browser/session/create', methods=['POST'])
def create_browser_session():
    """Create a new browser session"""
    try:
        data = request.json or {}
        account_id = data.get('account_id')
        proxy_url = data.get('proxy_url')
        
        if not account_id:
            return jsonify({'error': 'account_id is required'}), 400
        
        async def _create_session():
            session = await browser_manager.create_stealth_session(account_id, proxy_url)
            return {
                'session_id': session.session_id,
                'account_id': session.account_id,
                'created_at': session.created_at.isoformat(),
                'fingerprint': {
                    'user_agent': session.fingerprint.user_agent,
                    'viewport': session.fingerprint.viewport,
                    'timezone': session.fingerprint.timezone,
                    'locale': session.fingerprint.locale
                }
            }
        
        result = asyncio.run(_create_session())
        logger.info(f"Created browser session {result['session_id']} for account {account_id}")
        
        return jsonify(result), 201
        
    except Exception as e:
        logger.error(f"Error creating browser session: {e}")
        return jsonify({'error': 'Failed to create browser session'}), 500

@automation_bp.route('/automation/browser/session/<session_id>', methods=['DELETE'])
def close_browser_session(session_id):
    """Close a browser session"""
    try:
        async def _close_session():
            await browser_manager.close_session(session_id)
            return True
        
        success = asyncio.run(_close_session())
        
        if success:
            logger.info(f"Closed browser session {session_id}")
            return jsonify({'message': 'Session closed successfully'})
        else:
            return jsonify({'error': 'Session not found'}), 404
        
    except Exception as e:
        logger.error(f"Error closing browser session: {e}")
        return jsonify({'error': 'Failed to close browser session'}), 500

@automation_bp.route('/automation/browser/sessions', methods=['GET'])
def list_browser_sessions():
    """List active browser sessions"""
    try:
        sessions = []
        for session_id, session in browser_manager.active_sessions.items():
            sessions.append({
                'session_id': session_id,
                'account_id': session.account_id,
                'created_at': session.created_at.isoformat(),
                'user_agent': session.fingerprint.user_agent,
                'viewport': session.fingerprint.viewport
            })
        
        return jsonify({
            'active_sessions': len(sessions),
            'sessions': sessions
        })
        
    except Exception as e:
        logger.error(f"Error listing browser sessions: {e}")
        return jsonify({'error': 'Failed to list browser sessions'}), 500

@automation_bp.route('/automation/browser/cleanup', methods=['POST'])
def cleanup_browser_sessions():
    """Cleanup old browser sessions"""
    try:
        data = request.json or {}
        max_age_hours = data.get('max_age_hours', 4)
        
        async def _cleanup():
            await browser_manager.cleanup_old_sessions(max_age_hours)
            return len(browser_manager.active_sessions)
        
        remaining_sessions = asyncio.run(_cleanup())
        
        return jsonify({
            'message': 'Cleanup completed',
            'remaining_sessions': remaining_sessions
        })
        
    except Exception as e:
        logger.error(f"Error cleaning up browser sessions: {e}")
        return jsonify({'error': 'Failed to cleanup browser sessions'}), 500

@automation_bp.route('/automation/linkedin/account/create', methods=['POST'])
def create_linkedin_account():
    """Create a LinkedIn account"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['account_data', 'session_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        account_data = data['account_data']
        session_id = data['session_id']
        
        # Validate account data
        required_account_fields = ['first_name', 'last_name', 'email', 'password']
        for field in required_account_fields:
            if field not in account_data:
                return jsonify({'error': f'Missing required account field: {field}'}), 400
        
        async def _create_account():
            engine = await get_linkedin_engine()
            return await engine.create_linkedin_account(account_data, session_id)
        
        result = asyncio.run(_create_account())
        
        # Convert result to JSON-serializable format
        response = {
            'action_type': result.action_type.value,
            'success': result.success,
            'account_id': result.account_id,
            'data': result.data,
            'detection_risk': result.detection_risk,
            'error_message': result.error_message,
            'execution_time': result.execution_time,
            'timestamp': result.timestamp.isoformat()
        }
        
        if result.success:
            logger.info(f"LinkedIn account created successfully for {account_data['email']}")
            return jsonify(response), 201
        else:
            logger.error(f"LinkedIn account creation failed: {result.error_message}")
            return jsonify(response), 500
        
    except Exception as e:
        logger.error(f"Error creating LinkedIn account: {e}")
        return jsonify({'error': 'Failed to create LinkedIn account'}), 500

@automation_bp.route('/automation/linkedin/verify/email', methods=['POST'])
def verify_linkedin_email():
    """Verify LinkedIn email"""
    try:
        data = request.json
        
        required_fields = ['verification_link', 'session_id', 'account_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        async def _verify_email():
            engine = await get_linkedin_engine()
            return await engine.verify_email(
                data['verification_link'],
                data['session_id'],
                data['account_id']
            )
        
        result = asyncio.run(_verify_email())
        
        response = {
            'action_type': result.action_type.value,
            'success': result.success,
            'account_id': result.account_id,
            'data': result.data,
            'detection_risk': result.detection_risk,
            'error_message': result.error_message,
            'execution_time': result.execution_time,
            'timestamp': result.timestamp.isoformat()
        }
        
        return jsonify(response), 200 if result.success else 500
        
    except Exception as e:
        logger.error(f"Error verifying LinkedIn email: {e}")
        return jsonify({'error': 'Failed to verify LinkedIn email'}), 500

@automation_bp.route('/automation/linkedin/verify/sms', methods=['POST'])
def verify_linkedin_sms():
    """Verify LinkedIn SMS"""
    try:
        data = request.json
        
        required_fields = ['verification_code', 'session_id', 'account_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        async def _verify_sms():
            engine = await get_linkedin_engine()
            return await engine.verify_sms(
                data['verification_code'],
                data['session_id'],
                data['account_id']
            )
        
        result = asyncio.run(_verify_sms())
        
        response = {
            'action_type': result.action_type.value,
            'success': result.success,
            'account_id': result.account_id,
            'data': result.data,
            'detection_risk': result.detection_risk,
            'error_message': result.error_message,
            'execution_time': result.execution_time,
            'timestamp': result.timestamp.isoformat()
        }
        
        return jsonify(response), 200 if result.success else 500
        
    except Exception as e:
        logger.error(f"Error verifying LinkedIn SMS: {e}")
        return jsonify({'error': 'Failed to verify LinkedIn SMS'}), 500

@automation_bp.route('/automation/linkedin/profile/setup', methods=['POST'])
def setup_linkedin_profile():
    """Setup LinkedIn profile using persona data"""
    try:
        data = request.json
        
        required_fields = ['persona_data', 'session_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        persona_data = data['persona_data']
        session_id = data['session_id']
        
        # Reconstruct persona object
        persona = PersonaProfile(
            demographic_data=DemographicData(**persona_data['demographic_data']),
            professional_data=ProfessionalData(**persona_data['professional_data']),
            skills_data=SkillsData(**persona_data['skills_data']),
            content_data=ContentData(**persona_data['content_data']),
            visual_assets=VisualAssets(**persona_data['visual_assets']),
            persona_id=persona_data.get('persona_id', 'temp'),
            created_at=datetime.now()
        )
        
        async def _setup_profile():
            engine = await get_linkedin_engine()
            return await engine.setup_profile(persona, session_id)
        
        result = asyncio.run(_setup_profile())
        
        response = {
            'action_type': result.action_type.value,
            'success': result.success,
            'account_id': result.account_id,
            'data': result.data,
            'detection_risk': result.detection_risk,
            'error_message': result.error_message,
            'execution_time': result.execution_time,
            'timestamp': result.timestamp.isoformat()
        }
        
        return jsonify(response), 200 if result.success else 500
        
    except Exception as e:
        logger.error(f"Error setting up LinkedIn profile: {e}")
        return jsonify({'error': 'Failed to setup LinkedIn profile'}), 500

@automation_bp.route('/automation/linkedin/experience/add', methods=['POST'])
def add_linkedin_experience():
    """Add experience to LinkedIn profile"""
    try:
        data = request.json
        
        required_fields = ['experience_data', 'session_id', 'account_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        async def _add_experience():
            engine = await get_linkedin_engine()
            return await engine.add_experience(
                data['experience_data'],
                data['session_id'],
                data['account_id']
            )
        
        result = asyncio.run(_add_experience())
        
        response = {
            'action_type': result.action_type.value,
            'success': result.success,
            'account_id': result.account_id,
            'data': result.data,
            'detection_risk': result.detection_risk,
            'error_message': result.error_message,
            'execution_time': result.execution_time,
            'timestamp': result.timestamp.isoformat()
        }
        
        return jsonify(response), 200 if result.success else 500
        
    except Exception as e:
        logger.error(f"Error adding LinkedIn experience: {e}")
        return jsonify({'error': 'Failed to add LinkedIn experience'}), 500

@automation_bp.route('/automation/linkedin/search', methods=['POST'])
def search_linkedin_profiles():
    """Search LinkedIn profiles"""
    try:
        data = request.json
        
        required_fields = ['search_query', 'session_id', 'account_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        search_query = data['search_query']
        session_id = data['session_id']
        account_id = data['account_id']
        max_results = data.get('max_results', 10)
        
        async def _search_profiles():
            engine = await get_linkedin_engine()
            return await engine.search_profiles(search_query, session_id, account_id, max_results)
        
        result = asyncio.run(_search_profiles())
        
        response = {
            'action_type': result.action_type.value,
            'success': result.success,
            'account_id': result.account_id,
            'data': result.data,
            'detection_risk': result.detection_risk,
            'error_message': result.error_message,
            'execution_time': result.execution_time,
            'timestamp': result.timestamp.isoformat()
        }
        
        return jsonify(response), 200 if result.success else 500
        
    except Exception as e:
        logger.error(f"Error searching LinkedIn profiles: {e}")
        return jsonify({'error': 'Failed to search LinkedIn profiles'}), 500

@automation_bp.route('/automation/linkedin/account/<account_id>/statistics', methods=['GET'])
def get_account_statistics(account_id):
    """Get statistics for a LinkedIn account"""
    try:
        async def _get_statistics():
            engine = await get_linkedin_engine()
            return engine.get_account_statistics(account_id)
        
        stats = asyncio.run(_get_statistics())
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error getting account statistics: {e}")
        return jsonify({'error': 'Failed to get account statistics'}), 500

@automation_bp.route('/automation/linkedin/account/<account_id>/actions', methods=['GET'])
def get_account_actions(account_id):
    """Get recent actions for a LinkedIn account"""
    try:
        hours = request.args.get('hours', 24, type=int)
        
        async def _get_actions():
            engine = await get_linkedin_engine()
            actions = engine.get_recent_actions(account_id, hours)
            
            # Convert to JSON-serializable format
            return [
                {
                    'action_type': action.action_type.value,
                    'success': action.success,
                    'data': action.data,
                    'detection_risk': action.detection_risk,
                    'error_message': action.error_message,
                    'execution_time': action.execution_time,
                    'timestamp': action.timestamp.isoformat()
                }
                for action in actions
            ]
        
        actions = asyncio.run(_get_actions())
        
        return jsonify({
            'account_id': account_id,
            'hours': hours,
            'actions_count': len(actions),
            'actions': actions
        })
        
    except Exception as e:
        logger.error(f"Error getting account actions: {e}")
        return jsonify({'error': 'Failed to get account actions'}), 500

@automation_bp.route('/automation/test', methods=['POST'])
def test_automation():
    """Test automation services"""
    try:
        data = request.json or {}
        test_account_id = data.get('test_account_id', 'test_automation')
        
        async def _test_automation():
            # Test browser session creation
            session = await browser_manager.create_stealth_session(test_account_id)
            
            # Test navigation
            page = session.page
            await browser_manager.navigate_with_human_timing(page, "https://www.linkedin.com")
            await browser_manager.wait_for_page_ready(page)
            
            # Get page title
            title = await page.title()
            
            # Cleanup
            await browser_manager.close_session(session.session_id)
            
            return {
                'browser_session_created': True,
                'navigation_successful': True,
                'page_title': title,
                'session_id': session.session_id
            }
        
        result = asyncio.run(_test_automation())
        
        return jsonify({
            'automation_services_available': True,
            'test_results': result
        })
        
    except Exception as e:
        logger.error(f"Error testing automation: {e}")
        return jsonify({
            'automation_services_available': False,
            'error_message': str(e)
        }), 500


# ==========================
# AI-NATIVE AUTOMATION ROUTES
# ==========================

@automation_bp.route('/automation/ai/account/<account_id>/create', methods=['POST'])
def ai_create_account(account_id):
    """Start AI-driven account creation using Stagehand+Browserbase if available."""
    if not AI_AVAILABLE:
        return jsonify({'error': 'AI automation not available on this deployment'}), 501

    try:
        data = request.json or {}
        persona = data.get('persona') or {}

        async def _run():
            browser = AIBrowserAgent()
            engine = LinkedInAIEngine(browser)
            result = await engine.create_account(persona)

            # Register session for live monitoring even if account creation fails
            if _ai_sessions is not None:
                sess_id = result.get('session_id')
                live = result.get('live_url')
                if sess_id:
                    _ai_sessions.register(AISession(account_id=account_id, session_id=sess_id, created_at=datetime.utcnow(), live_url=live))
                    logger.info(f"Registered AI session {sess_id} for account {account_id} with live URL: {live}")
            return result

        result = asyncio.run(_run())
        status = 200 if result.get('success') else 500
        return jsonify(result), status
    except Exception as e:
        logger.error(f"AI create account failed: {e}")
        return jsonify({'error': 'AI account creation failed'}), 500


@automation_bp.route('/automation/ai/account/<account_id>/warmup', methods=['POST'])
def ai_warmup_account(account_id):
    """Execute AI-generated warmup plan for an account."""
    if not AI_AVAILABLE:
        return jsonify({'error': 'AI automation not available on this deployment'}), 501
    try:
        data = request.json or {}
        persona = data.get('persona') or {}

        async def _run():
            browser = AIBrowserAgent()
            warmup = AccountWarmupService(browser)
            result = await warmup.execute_warmup_plan(persona, account_id)
            
            # Register session for live monitoring even if warmup fails
            if _ai_sessions is not None:
                sess_id = result.get('session_id')
                live = result.get('live_url')
                if sess_id:
                    _ai_sessions.register(AISession(account_id=account_id, session_id=sess_id, created_at=datetime.utcnow(), live_url=live))
                    logger.info(f"Registered AI session {sess_id} for account {account_id} with live URL: {live}")
            return result

        result = asyncio.run(_run())
        status = 200 if result.get('success') else 500
        return jsonify(result), status
    except Exception as e:
        logger.error(f"AI warmup failed: {e}")
        return jsonify({'error': 'AI warmup failed'}), 500


@automation_bp.route('/automation/ai/account/<account_id>/live', methods=['GET'])
def ai_account_live(account_id):
    """Return the live monitoring URL for the current AI browser session if present."""
    if not AI_AVAILABLE or _ai_sessions is None:
        return jsonify({'live_url': None, 'available': False})
    sess = _ai_sessions.by_account(account_id)
    return jsonify({'live_url': getattr(sess, 'live_url', None), 'available': True})

