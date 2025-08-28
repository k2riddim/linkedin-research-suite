from flask import Blueprint, jsonify, request
from src.models import db
from src.models.account import Account, Session, Activity
from src.models.persona import Persona, PersonaUsage
from src.services.linkedin_engine import get_linkedin_engine
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)
account_bp = Blueprint('account', __name__)

# In-process guard to avoid launching multiple creation threads for the same account
_active_creation_accounts = set()

@account_bp.route('/accounts', methods=['GET'])
def get_accounts():
    """Get all accounts"""
    try:
        accounts = Account.query.all()
        return jsonify([account.to_dict() for account in accounts])
    except Exception as e:
        logger.error(f"Error getting accounts: {e}")
        return jsonify({'error': 'Failed to retrieve accounts'}), 500

@account_bp.route('/accounts', methods=['POST'])
def create_account():
    """Create new account"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['first_name', 'last_name', 'email', 'password']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Check if email already exists
        existing_account = Account.query.filter_by(email=data['email']).first()
        if existing_account:
            return jsonify({'error': 'Account with this email already exists'}), 409
        
        # Create new account
        account = Account(
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            password=data['password'],
            status='new'
        )
        
        # Set profile data if provided
        if 'profile_data' in data:
            account.set_profile_data(data['profile_data'])
        
        db.session.add(account)
        db.session.commit()
        
        logger.info(f"Created new account: {account.email}")
        return jsonify(account.to_dict()), 201
        
    except Exception as e:
        logger.error(f"Error creating account: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to create account'}), 500

@account_bp.route('/accounts/<account_id>', methods=['GET'])
def get_account(account_id):
    """Get specific account"""
    try:
        account = Account.query.get_or_404(account_id)
        return jsonify(account.to_dict())
    except Exception as e:
        logger.error(f"Error getting account {account_id}: {e}")
        return jsonify({'error': 'Account not found'}), 404

@account_bp.route('/accounts/<account_id>', methods=['PUT'])
def update_account(account_id):
    """Update account"""
    try:
        account = Account.query.get_or_404(account_id)
        data = request.json
        
        # Update fields if provided
        if 'first_name' in data:
            account.first_name = data['first_name']
        if 'last_name' in data:
            account.last_name = data['last_name']
        if 'email' in data:
            # Check if new email already exists
            existing = Account.query.filter_by(email=data['email']).filter(Account.id != account_id).first()
            if existing:
                return jsonify({'error': 'Email already exists'}), 409
            account.email = data['email']
        if 'password' in data:
            account.password = data['password']
        if 'status' in data:
            account.status = data['status']
        if 'linkedin_url' in data:
            account.linkedin_url = data['linkedin_url']
        if 'linkedin_created' in data:
            account.linkedin_created = data['linkedin_created']
        if 'profile_data' in data:
            account.set_profile_data(data['profile_data'])
        
        db.session.commit()
        
        logger.info(f"Updated account: {account.email}")
        return jsonify(account.to_dict())
        
    except Exception as e:
        logger.error(f"Error updating account {account_id}: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update account'}), 500

@account_bp.route('/accounts/<account_id>', methods=['DELETE'])
def delete_account(account_id):
    """Delete account"""
    try:
        account = Account.query.get_or_404(account_id)
        db.session.delete(account)
        db.session.commit()
        
        logger.info(f"Deleted account: {account.email}")
        return '', 204
        
    except Exception as e:
        logger.error(f"Error deleting account {account_id}: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to delete account'}), 500

@account_bp.route('/accounts/<account_id>/status', methods=['GET'])
def get_account_status(account_id):
    """Get account creation status"""
    try:
        account = Account.query.get_or_404(account_id)
        
        # Calculate progress based on status
        progress_map = {
            'new': 0.0,
            'creating_linkedin': 0.25,
            'verifying_email': 0.5,
            'verifying_sms': 0.75,
            'completed': 1.0,
            'failed': 0.0
        }
        
        progress = progress_map.get(account.status, 0.0)
        
        return jsonify({
            'account_id': account.id,
            'status': account.status,
            'progress': progress,
            'current_step': account.status,
            'linkedin_created': account.linkedin_created,
            'linkedin_url': account.linkedin_url,
            'error_message': None  # This would come from job status in real implementation
        })
        
    except Exception as e:
        logger.error(f"Error getting account status {account_id}: {e}")
        return jsonify({'error': 'Account not found'}), 404

# DISABLED: Mock LinkedIn creation endpoint - replaced with real implementation below
# @account_bp.route('/accounts/<account_id>/create-linkedin', methods=['POST'])
# def create_linkedin_account(account_id):
#     """Create LinkedIn account for existing profile"""
#     try:
#         account = Account.query.get_or_404(account_id)
#         data = request.json or {}
#         
#         # Update account status
#         account.status = 'creating_linkedin'
#         db.session.commit()
#         
#         # In a real implementation, this would trigger the automation job
#         # For now, we'll just return a success response
#         
#         logger.info(f"Started LinkedIn account creation for: {account.email}")
#         return jsonify({
#             'message': 'LinkedIn account creation started',
#             'account_id': account.id,
#             'use_real_credentials': data.get('use_real_credentials', True),
#             'warmup_after_creation': data.get('warmup_after_creation', True)
#         }), 202
#         
#     except Exception as e:
#         logger.error(f"Error starting LinkedIn creation for {account_id}: {e}")
#         db.session.rollback()
#         return jsonify({'error': 'Failed to start LinkedIn account creation'}), 500

@account_bp.route('/accounts/<account_id>/sessions', methods=['GET'])
def get_account_sessions(account_id):
    """Get sessions for account"""
    try:
        account = Account.query.get_or_404(account_id)
        sessions = Session.query.filter_by(account_id=account_id).order_by(Session.started_at.desc()).all()
        return jsonify([session.to_dict() for session in sessions])
    except Exception as e:
        logger.error(f"Error getting sessions for account {account_id}: {e}")
        return jsonify({'error': 'Failed to retrieve sessions'}), 500

@account_bp.route('/accounts/<account_id>/activities', methods=['GET'])
def get_account_activities(account_id):
    """Get activities for account"""
    try:
        account = Account.query.get_or_404(account_id)
        activities = Activity.query.filter_by(account_id=account_id).order_by(Activity.timestamp.desc()).limit(100).all()
        return jsonify([activity.to_dict() for activity in activities])
    except Exception as e:
        logger.error(f"Error getting activities for account {account_id}: {e}")
        return jsonify({'error': 'Failed to retrieve activities'}), 500

@account_bp.route('/accounts/create-from-persona', methods=['POST'])
def create_account_from_persona():
    """Create LinkedIn account from AI-generated persona"""
    try:
        data = request.json
        
        # Validate required fields
        if 'persona_id' not in data:
            return jsonify({'error': 'Missing required field: persona_id'}), 400
        
        # Get persona from database
        persona = Persona.query.filter_by(persona_id=data['persona_id'], is_active=True).first()
        if not persona:
            return jsonify({'error': 'Persona not found'}), 404
        
        # Check if account already exists for this persona
        existing_account = Account.query.filter_by(persona_id=persona.id).first()
        if existing_account:
            return jsonify({
                'error': 'Account already exists for this persona',
                'existing_account_id': existing_account.id
            }), 409
        
        # Generate or use manual email based on service preference
        email_service = data.get('email_service', 'emailondeck')
        if email_service == 'manual' and (persona.manual_email and persona.manual_email_password):
            email = persona.manual_email
            password = persona.manual_email_password
        else:
            email = generate_email_for_persona(persona, email_service)
            # Generate password
            password = generate_secure_password()
        
        # Create account with persona data
        account = Account(
            first_name=persona.first_name,
            last_name=persona.last_name,
            email=email,
            password=password,
            status='new',
            persona_id=persona.id
        )
        
        # Set profile data from persona
        profile_data = {
            'headline': persona.headline,
            'summary': persona.summary,
            'about_section': persona.about_section,
            'location': persona.location,
            'industry': persona.industry,
            'current_position': persona.current_position,
            'current_company': persona.current_company,
            'education': json.loads(persona.education) if persona.education else [],
            'previous_positions': json.loads(persona.previous_positions) if persona.previous_positions else [],
            'technical_skills': json.loads(persona.technical_skills) if persona.technical_skills else [],
            'soft_skills': json.loads(persona.soft_skills) if persona.soft_skills else [],
            'certifications': json.loads(persona.certifications) if persona.certifications else [],
            'visual_assets': {
                'profile_photo_description': persona.profile_photo_description,
                'background_image_description': persona.background_image_description,
                'company_logo_description': persona.company_logo_description
            },
            'creation_settings': {
                'email_service': email_service,
                'proxy_service': data.get('proxy_service', 'geonode'),
                'verification_method': data.get('verification_method', 'email'),
                'profile_completion_level': data.get('profile_completion_level', 'full')
            }
        }
        
        account.set_profile_data(profile_data)
        
        db.session.add(account)
        
        # Create persona usage record
        persona_usage = PersonaUsage(
            persona_id=persona.id,
            account_id=account.id,
            usage_type='account_creation',
            success=True,
            notes=f'Account created using {email_service} and {data.get("proxy_service", "geonode")}'
        )
        db.session.add(persona_usage)
        
        db.session.commit()
        
        logger.info(f"Created account from persona: {persona.persona_id} -> {account.email}")
        
        # Return account details with creation status
        result = account.to_dict()
        result['persona_data'] = persona.to_dict()
        result['creation_settings'] = profile_data['creation_settings']
        
        return jsonify(result), 201
        
    except Exception as e:
        logger.error(f"Error creating account from persona: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to create account from persona'}), 500

@account_bp.route('/accounts/<account_id>/link-persona', methods=['PATCH'])
def link_persona_to_account(account_id):
    """Link an existing account to a persona"""
    try:
        account = Account.query.get_or_404(account_id)
        data = request.json
        
        if 'persona_id' not in data:
            return jsonify({'error': 'Missing required field: persona_id'}), 400
        
        # Get persona from database
        persona = Persona.query.filter_by(persona_id=data['persona_id'], is_active=True).first()
        if not persona:
            return jsonify({'error': 'Persona not found'}), 404
        
        # Link persona to account
        account.persona_id = persona.id
        
        # Create persona usage record
        persona_usage = PersonaUsage(
            persona_id=persona.id,
            account_id=account.id,
            usage_type='account_linking',
            success=True,
            notes='Persona linked to existing account'
        )
        db.session.add(persona_usage)
        
        db.session.commit()
        
        logger.info(f"Linked persona {persona.persona_id} to account {account.email}")
        return jsonify(account.to_dict())
        
    except Exception as e:
        logger.error(f"Error linking persona to account {account_id}: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to link persona to account'}), 500

@account_bp.route('/accounts/stats', methods=['GET'])
def get_account_stats():
    """Get account statistics for dashboard"""
    try:
        from sqlalchemy import func, extract
        from datetime import datetime, timedelta
        
        # Total accounts by status
        status_counts = db.session.query(
            Account.status,
            func.count(Account.id).label('count')
        ).group_by(Account.status).all()
        
        # Accounts created in last 7 days
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        daily_creation_counts = db.session.query(
            func.date(Account.created_at).label('date'),
            func.count(Account.id).label('count')
        ).filter(
            Account.created_at >= seven_days_ago
        ).group_by(
            func.date(Account.created_at)
        ).order_by('date').all()
        
        # Total counts
        total_accounts = Account.query.count()
        active_accounts = Account.query.filter_by(status='completed').count()
        pending_accounts = Account.query.filter(Account.status.in_(['new', 'creating_linkedin', 'verifying_email', 'verifying_sms'])).count()
        failed_accounts = Account.query.filter_by(status='failed').count()
        
        # Success rate calculation
        completed_accounts = Account.query.filter_by(status='completed').count()
        total_attempted = Account.query.filter(Account.status != 'new').count()
        success_rate = (completed_accounts / total_attempted * 100) if total_attempted > 0 else 0
        
        # Accounts with personas
        accounts_with_personas = Account.query.filter(Account.persona_id.isnot(None)).count()
        
        result = {
            'total_accounts': total_accounts,
            'active_accounts': active_accounts,
            'pending_accounts': pending_accounts,
            'failed_accounts': failed_accounts,
            'success_rate': round(success_rate, 1),
            'accounts_with_personas': accounts_with_personas,
            'status_distribution': [
                {'status': status, 'count': count} for status, count in status_counts
            ],
            'daily_creation_counts': [
                {'date': str(date), 'count': count} for date, count in daily_creation_counts
            ]
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting account stats: {e}")
        return jsonify({'error': 'Failed to get account statistics'}), 500

@account_bp.route('/accounts/<account_id>/create-linkedin', methods=['POST'])
def start_linkedin_account_creation(account_id):
    """Start LinkedIn account creation process with real-time progress"""
    logger.info(f"DEBUG: Account creation endpoint called for account {account_id}")
    try:
        from src.services.linkedin_creator_service import create_linkedin_account_async
        import asyncio
        
        # Get account from database
        logger.info(f"DEBUG: Looking for account {account_id} in database")
        account = Account.query.get(account_id)
        if not account:
            logger.error(f"DEBUG: Account {account_id} not found in database")
            return jsonify({'error': 'Account not found'}), 404
        
        logger.info(f"DEBUG: Account found: {account.email}")
        
        if account.linkedin_created:
            logger.info(f"DEBUG: LinkedIn account already exists for {account_id}")
            return jsonify({'error': 'LinkedIn account already created for this account'}), 409
        
        # Guard: if a creation is already running or was recently started, do not start another
        try:
            if account_id in _active_creation_accounts:
                logger.info(f"DEBUG: Creation already running for {account_id}")
                return jsonify({'message': 'Creation already running', 'account_id': account_id, 'status': 'creating_linkedin', 'websocket_room': f'account_{account_id}'}), 202
            if account.status in ('creating_linkedin', 'verifying_email', 'verifying_sms') and account.linkedin_creation_started:
                from datetime import timedelta as _td
                if (datetime.utcnow() - account.linkedin_creation_started) < _td(minutes=10):
                    logger.info(f"DEBUG: Recent creation already started for {account_id}, skipping duplicate start")
                    return jsonify({'message': 'Creation already started', 'account_id': account_id, 'status': account.status, 'websocket_room': f'account_{account_id}'}), 202
        except Exception:
            pass

        # Update account status
        logger.info(f"DEBUG: Updating account status to 'creating_linkedin'")
        account.status = 'creating_linkedin'
        account.linkedin_creation_started = datetime.utcnow()
        db.session.commit()
        logger.info(f"DEBUG: Account status updated and committed")
        
        # Start async LinkedIn creation process using AI automation
        logger.info(f"DEBUG: Starting AI-powered LinkedIn creation process")

        # Try AI automation first, fall back to legacy if not available
        try:
            # Check if AI automation is available
            from src.routes.automation import AI_AVAILABLE, AIBrowserAgent, LinkedInAIEngine, _ai_sessions, AISession
            if AI_AVAILABLE:
                logger.info(f"DEBUG: Using AI automation for account {account_id}")
                
                # Run the creation process in a dedicated OS thread with its own event loop
                import threading
                from src.main import app as flask_app

                def run_ai_context():
                    try:
                        with flask_app.app_context():
                            logger.info(f"DEBUG: AI thread started for account {account_id}")
                            _active_creation_accounts.add(account_id)
                            loop = asyncio.new_event_loop()
                            try:
                                asyncio.set_event_loop(loop)
                                
                                async def _run_ai():
                                    # Re-fetch account in this thread context
                                    current_account = Account.query.get(account_id)
                                    if not current_account:
                                        logger.error(f"Account {account_id} not found in AI thread")
                                        return {"success": False, "error": "Account not found"}
                                    
                                    # Use the full linkedin creator service workflow with AI automation
                                    from src.services.linkedin_creator_service import create_linkedin_account_async
                                    
                                    result = await create_linkedin_account_async(account_id)
                                    
                                    # Register session for live monitoring
                                    if _ai_sessions is not None:
                                        sess_id = result.get('session_id')
                                        live = result.get('live_url')
                                        if sess_id:
                                            _ai_sessions.register(AISession(account_id=account_id, session_id=sess_id, created_at=datetime.utcnow(), live_url=live))
                                            logger.info(f"Registered AI session {sess_id} for account {account_id} with live URL: {live}")
                                    
                                    # Update account status based on result
                                    if result.get('success'):
                                        current_account.status = 'linkedin_created'
                                        current_account.linkedin_created = True
                                        current_account.linkedin_profile_url = result.get('profile_data', {}).get('profile_url')
                                        logger.info(f"AI LinkedIn account creation succeeded for {account_id}")
                                    else:
                                        current_account.status = 'creation_failed'
                                        logger.error(f"AI LinkedIn account creation failed for {account_id}: {result.get('error')}")
                                    
                                    db.session.commit()
                                    return result
                                
                                loop.run_until_complete(_run_ai())
                            finally:
                                try:
                                    loop.close()
                                except Exception:
                                    pass
                    except Exception as thread_error:
                        logger.exception(f"AI creation thread failed for {account_id}: {thread_error}")
                        # Update account status to failed
                        try:
                            with flask_app.app_context():
                                account = Account.query.get(account_id)
                                if account:
                                    account.status = 'creation_failed'
                                    db.session.commit()
                        except Exception:
                            pass
                    finally:
                        try:
                            _active_creation_accounts.discard(account_id)
                        except Exception:
                            pass

                thread = threading.Thread(target=run_ai_context, daemon=True)
                thread.start()
                logger.info(f"DEBUG: AI thread started successfully")
            else:
                logger.error(f"AI automation is required but not available for account {account_id}")
                return jsonify({'error': 'AI automation service is not available'}), 503
                
        except ImportError as import_error:
            logger.error(f"AI automation dependencies missing for account {account_id}: {import_error}")
            return jsonify({'error': 'AI automation dependencies not installed'}), 503
        
        logger.info(f"LinkedIn creation started for account {account_id}")
        
        return jsonify({
            'message': 'LinkedIn account creation started',
            'account_id': account_id,
            'status': 'creating_linkedin',
            'websocket_room': f'account_{account_id}'
        }), 202
        
    except Exception as e:
        logger.exception(f"Error starting LinkedIn creation for account {account_id}: {e}")
        return jsonify({'error': 'Failed to start LinkedIn creation'}), 500

@account_bp.route('/accounts/<account_id>/submit-email-code', methods=['POST'])
def submit_email_code(account_id):
    """Submit a manual email verification code/link for the running creation session.
    Accepts either { code: '123456' } or { verification_link: 'https://...' }.
    """
    try:
        account = Account.query.get(account_id)
        if not account:
            return jsonify({'error': 'Account not found'}), 404

        data = request.json or {}
        verification_code = data.get('code')
        verification_link = data.get('verification_link')

        # Persist into account profile_data so the async creator can pick it up
        profile = account.get_profile_data()
        manual = profile.get('manual_verification', {})
        if verification_code:
            manual['email_code'] = verification_code
        if verification_link:
            manual['verification_link'] = verification_link
        manual['submitted_at'] = datetime.utcnow().isoformat()
        profile['manual_verification'] = manual
        account.set_profile_data(profile)
        db.session.commit()

        # Emit a progress log to console consumers
        from src.socketio_bus import enqueue_backend_log
        enqueue_backend_log({
            'timestamp': datetime.utcnow().isoformat(),
            'level': 'INFO',
            'logger': 'manual_verification',
            'message': f'Manual email verification received for {account.email}'
        })

        return jsonify({'ok': True})
    except Exception as e:
        logger.error(f"Failed to submit manual email code for {account_id}: {e}")
        return jsonify({'error': 'Failed to submit code'}), 500

def generate_email_for_persona(persona, email_service='emailondeck'):
    """Generate email address for persona based on service"""
    import random
    import string
    
    # Create email prefix from persona name
    first_name = persona.first_name.lower().replace(' ', '')
    last_name = persona.last_name.lower().replace(' ', '')
    
    # Add random numbers for uniqueness
    random_suffix = ''.join(random.choices(string.digits, k=3))
    
    # Different email services
    domains = {
        'emailondeck': ['emailondeck.com', 'tempmail.org', 'guerrillamail.com'],
        'fivesim': ['temp-mail.org', 'mailinator.com', '10minutemail.com'],
        'custom': ['gmail.com', 'outlook.com', 'yahoo.com']
    }
    
    domain = random.choice(domains.get(email_service, domains['emailondeck']))
    email = f"{first_name}.{last_name}{random_suffix}@{domain}"
    
    return email

def generate_secure_password():
    """Generate a secure password"""
    import random
    import string
    
    # Generate 12-character password with mix of characters
    chars = string.ascii_letters + string.digits + "!@#$%"
    password = ''.join(random.choice(chars) for _ in range(12))
    return password

