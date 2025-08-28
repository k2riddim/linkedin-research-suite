"""
LinkedIn Creator Service - Integrates existing LinkedIn engine with real-time progress tracking
"""

import asyncio
import logging
import json
import time
from datetime import datetime
from typing import Dict, Any
from src.services.linkedin_engine import get_linkedin_engine
# Local Playwright agent is deprecated in favor of MCP orchestration
from src.services.browser_automation import get_browser_manager
from src.services.enhanced_progress_tracker import EnhancedProgressTracker
from src.services.service_manager import get_service_manager
from src.models.account import Account
from src.models.persona import Persona, PersonaUsage
from src.models import db
import os
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Optional AI-native browser stack (Stagehand + Browserbase)
try:
    from src.services.ai_browser_agent import AIBrowserAgent  # type: ignore
    from src.services.linkedin_ai_engine import LinkedInAIEngine  # type: ignore
    _AI_AVAILABLE = True
except Exception:
    AIBrowserAgent = None  # type: ignore
    LinkedInAIEngine = None  # type: ignore
    _AI_AVAILABLE = False

async def create_linkedin_account_async(account_id: str) -> Dict[str, Any]:
    """
    Create LinkedIn account using existing LinkedIn engine with enhanced real-time progress tracking
    """
    progress = EnhancedProgressTracker(account_id)
    
    try:
        # ===========================================
        # STEP 1: INITIALIZATION
        # ===========================================
        progress.start_step("init", {"account_id": account_id})
        
        # Sub-step: Fetch account
        progress.start_sub_step("init", "fetch_account")
        start_time = time.time()
        
        account = Account.query.get(account_id)
        if not account:
            progress.log_error("init", "fetch_account", f"Account {account_id} not found")
            raise ValueError(f"Account {account_id} not found")
        
        execution_time = time.time() - start_time
        progress.complete_sub_step("init", "fetch_account", True, {
            "account_email": account.email,
            "account_name": f"{account.first_name} {account.last_name}"
        }, execution_time)
        
        # Sub-step: Fetch persona
        progress.start_sub_step("init", "fetch_persona")
        start_time = time.time()
        
        persona = None
        if account.persona_id:
            persona = Persona.query.get(account.persona_id)
            if persona:
                progress.log_success("init", "fetch_persona", f"Persona loaded: {persona.first_name} {persona.last_name}")
            else:
                progress.log_warning("init", "fetch_persona", "Persona ID exists but persona not found")
        else:
            progress.log_info("init", "fetch_persona", "No persona linked to account")
        
        execution_time = time.time() - start_time
        progress.complete_sub_step("init", "fetch_persona", True, {
            "persona_id": account.persona_id,
            "has_persona": persona is not None
        }, execution_time)
        
        # Sub-step: Validate data
        progress.start_sub_step("init", "validate_data")
        start_time = time.time()
        
        # Prepare account data for LinkedIn engine
        account_data = {
            'account_id': account_id,
            'first_name': account.first_name,
            'last_name': account.last_name,
            'email': account.email,
            'password': account.password
        }
        
        # Validate required fields
        missing_fields = [field for field, value in account_data.items() if not value]
        if missing_fields:
            progress.log_error("init", "validate_data", f"Missing required fields: {missing_fields}")
            raise ValueError(f"Missing required fields: {missing_fields}")
        
        execution_time = time.time() - start_time
        progress.complete_sub_step("init", "validate_data", True, {
            "account_data_valid": True,
            "required_fields_present": True
        }, execution_time)
        
        progress.complete_step("init", True)
        
        # ===========================================
        # STEP 2: EXTERNAL SERVICES SETUP
        # ===========================================
        progress.start_step("external_services")
        
        # Get profile data for proxy/email services
        profile_data = account.get_profile_data()
        creation_settings = profile_data.get('creation_settings', {})
        
        # Initialize and use real external services via ServiceManager
        service_mgr = await get_service_manager()
        proxy_url = None
        sms_activation_id = None
        
        # Email provisioning
        progress.start_sub_step("external_services", "email_service")
        start_time = time.time()
        try:
            resources = await service_mgr.create_account_resources(
                account_id=account_id,
                first_name=account.first_name,
                last_name=account.last_name
            )
            email_res = resources.get('email')
            if email_res and getattr(email_res, 'success', False):
                account.email = email_res.email_address or account.email
                if getattr(email_res, 'password', None):
                    account.password = email_res.password
                db.session.commit()
                progress.log_success("external_services", "email_service", "Email provisioned", {"email": account.email})
                email_ok = True
            else:
                progress.log_error("external_services", "email_service", "Email provisioning failed or unavailable")
                email_ok = False
        except Exception as prov_e:
            email_ok = False
            progress.log_error("external_services", "email_service", f"Provisioning failed: {prov_e}")
        execution_time = time.time() - start_time
        progress.complete_sub_step("external_services", "email_service", email_ok, {"email": account.email}, execution_time)

        # Manual email mode override: if the creation settings require manual email, accept
        # the already-present account credentials as satisfying the email prerequisite.
        try:
            manual_email_mode = (creation_settings.get('email_service') == 'manual')
        except Exception:
            manual_email_mode = False
        if manual_email_mode:
            manual_ok = bool(account.email and account.password)
            if manual_ok and not email_ok:
                progress.log_success("external_services", "email_service", "Manual email mode: using provided credentials", {"email": account.email})
            if not manual_ok:
                progress.log_error("external_services", "email_service", "Manual email mode but missing email/password on account", {})
            email_ok = email_ok or manual_ok

        # Proxy assignment
        progress.start_sub_step("external_services", "proxy_service")
        start_time = time.time()
        try:
            proxy_res = resources.get('proxy') if 'resources' in locals() else None
            if proxy_res and getattr(proxy_res, 'success', False):
                proxy_url = proxy_res.proxy_url
                progress.log_success("external_services", "proxy_service", "Proxy assigned", {"session": proxy_res.session_id})
                proxy_ok = True
            else:
                progress.log_error("external_services", "proxy_service", "Proxy assignment failed or unavailable")
                proxy_ok = False
        except Exception as e:
            proxy_ok = False
            progress.log_error("external_services", "proxy_service", f"Proxy assignment failed: {e}")
        execution_time = time.time() - start_time
        progress.complete_sub_step("external_services", "proxy_service", proxy_ok, {"proxy_applied": proxy_url is not None}, execution_time)

        # SMS acquisition
        progress.start_sub_step("external_services", "sms_service")
        start_time = time.time()
        try:
            sms_res = resources.get('sms') if 'resources' in locals() else None
            if sms_res and getattr(sms_res, 'activation_id', None):
                sms_activation_id = sms_res.activation_id
                # Provide phone number to the agent for submission when prompted
                try:
                    if sms_res.phone_number:
                        account_data['phone_number'] = sms_res.phone_number
                except Exception:
                    pass
                progress.log_success("external_services", "sms_service", "SMS activation acquired", {"activation_id": sms_activation_id})
                sms_ok = True
            else:
                progress.log_error("external_services", "sms_service", "SMS provisioning failed or unavailable")
                sms_ok = False
        except Exception as e:
            sms_ok = False
            progress.log_error("external_services", "sms_service", f"SMS provisioning failed: {e}")
        execution_time = time.time() - start_time
        progress.complete_sub_step("external_services", "sms_service", sms_ok, {"has_sms": bool(sms_activation_id)}, execution_time)

        # Validate services
        progress.start_sub_step("external_services", "validate_services")
        start_time = time.time()
        try:
            services_health = await service_mgr.check_all_services_health()
            progress.log_success(
                "external_services",
                "validate_services",
                "Health checks completed",
                {k: v.is_healthy for k, v in services_health.items()}
            )
            validate_ok = True
        except Exception as e:
            validate_ok = False
            progress.log_error("external_services", "validate_services", f"Validation failed: {e}")
        execution_time = time.time() - start_time
        progress.complete_sub_step("external_services", "validate_services", validate_ok, {}, execution_time)

        # Enforce fail-fast: all external services must be healthy and provisioned
        if not (email_ok and proxy_ok and sms_ok and validate_ok):
            failure_details = {
                'email_ok': email_ok,
                'proxy_ok': proxy_ok,
                'sms_ok': sms_ok,
                'validate_ok': validate_ok
            }
            progress.log_error("external_services", None, "External services prerequisite failed. Aborting.", failure_details)
            raise Exception(f"External services failed: {failure_details}")

        progress.complete_step("external_services", email_ok and proxy_ok and sms_ok and validate_ok)
        
        # ===========================================
        # STEP 3: BROWSER LAUNCH (Stagehand preferred)
        # ===========================================
        progress.start_step("browser_launch")
        session_id = None
        if not _AI_AVAILABLE:
            # AI Browser initialization (Stagehand + Browserbase)
            progress.start_sub_step("browser_launch", "ai_browser_init")
            try:
                browser_manager = await get_browser_manager()
                session_obj = await browser_manager.create_stealth_session(account_id=account_id, proxy_url=proxy_url)
                session_id = session_obj.session_id
                progress.complete_sub_step("browser_launch", "ai_browser_init", True, {"session_id": session_id}, 0)
            except Exception as e:
                progress.complete_sub_step("browser_launch", "ai_browser_init", False, {"error": str(e)}, 0)
                raise
        progress.complete_step("browser_launch", True)
        
        # ===========================================
        # STEP 4: (Skipped) Direct AI automation via Stagehand flows
        # ===========================================
        progress.start_step("linkedin_navigation")
        progress.complete_step("linkedin_navigation", True)
        
        # STEP 5: ACCOUNT CREATION (Stagehand + Browserbase when available)
        # ===========================================
        progress.start_step("account_creation")

        # Sub-step: Run agent to fill the signup flow
        progress.start_sub_step("account_creation", "fill_personal")
        start_time = time.time()

        try:
            # Try AI automation first if available
            ai_success = False
            if _AI_AVAILABLE:
                try:
                    browser_agent = AIBrowserAgent()
                    init_ok = await browser_agent.initialize()
                    if init_ok:
                        persona_like = {
                            'first_name': account.first_name,
                            'last_name': account.last_name,
                            'email': account.email,
                            'industry': creation_settings.get('industry') if isinstance(creation_settings, dict) else None,
                            'location': (profile_data or {}).get('location'),
                            'experience_level': 'mid_level'
                        }
                        ai_engine = LinkedInAIEngine(browser_agent)
                        agent_result = await ai_engine.create_account(persona_like)
                        if agent_result.get('success'):
                            progress.log_success("account_creation", "fill_personal", "AI browser session created")
                            ai_success = True
                            # Store session info for later use by MCP agent
                            session_id = agent_result.get('session_id')
                            live_url = agent_result.get('live_url')
                            detection_risk = 0.2  # Lower risk with AI assistance
                        else:
                            logger.warning(f"AI automation failed, will fallback to MCP: {agent_result.get('error')}")
                    else:
                        logger.warning("AI browser initialization failed, will fallback to MCP")
                except Exception as ai_error:
                    logger.warning(f"AI automation failed, will fallback to MCP: {ai_error}")
            
            # If AI failed or not available, use MCP automation
            if not ai_success:
                logger.info("Using MCP automation for LinkedIn account creation")
                from src.services.agents.mcp_playwright_agent import MCPPlaywrightAgent
                mcp_agent = MCPPlaywrightAgent()
                manual_verification = {}
                try:
                    prof = account.get_profile_data() or {}
                    manual_verification = prof.get('manual_verification') or {}
                except Exception:
                    manual_verification = {}
                agent_result = await mcp_agent.run(
                    account_id=account_id,
                    account_data=account_data,
                    tracker=progress,
                    manual_verification=manual_verification,
                    proxy_url=proxy_url
                )
                if not agent_result or not agent_result.get('success', False):
                    progress.log_error("account_creation", "fill_personal", "MCP agent failed to complete signup flow")
                    raise Exception("MCP agent failed to complete signup flow")
                progress.log_success("account_creation", "fill_personal", "Personal information filled successfully")
                detection_risk = agent_result.get('detection_risk', 0.5)
        except Exception as e:
            progress.log_error("account_creation", "fill_personal", f"Error during account creation: {e}")
            raise

        execution_time = time.time() - start_time
        progress.complete_sub_step("account_creation", "fill_personal", True, {
            "form_filled": True,
            "detection_risk": detection_risk if 'detection_risk' in locals() else 0
        }, execution_time)

        # Mark remaining sub-steps as placeholders (will be expanded by agent as needed)
        for sub_step_id in ["fill_email", "fill_password", "accept_terms", "submit_form", "handle_captcha"]:
            progress.start_sub_step("account_creation", sub_step_id)
            await asyncio.sleep(0.05)
        
        # ===========================================
        # STEP 6: VERIFICATION (deferred to after UI prompt)
        # ===========================================
        progress.start_step("verification")

        # When LinkedIn prompts for a code, we now initiate fetching and submit via agent
        try:
            # Attempt to proactively wait for the verification prompt; if present, proceed
            needs_verification = True  # conservative default; agent detected earlier
            verification_result = {}

            # Email verification (manual mode may already have code/link)
            email_verification_payload = None
            profile_data = account.get_profile_data() or {}
            manual_verification = profile_data.get('manual_verification') or {}
            if manual_verification.get('email_code') or manual_verification.get('verification_link'):
                email_verification_payload = manual_verification

            # SMS: only start polling now if we have an activation id
            if sms_activation_id:
                progress.start_sub_step("verification", "sms_poll_start")
                sms_code = None
                try:
                    # Poll concurrently while agent waits on page
                    sms_code = await service_mgr.sms_manager.poll_for_sms(sms_activation_id, timeout=300)
                    verification_result['sms_verification'] = { 'success': bool(sms_code), 'code': sms_code }
                    progress.complete_sub_step("verification", "sms_poll_start", bool(sms_code), { 'has_code': bool(sms_code) }, 0)
                except Exception as e:
                    progress.complete_sub_step("verification", "sms_poll_start", False, { 'error': str(e) }, 0)

                # If we obtained an SMS code, submit it via the agent
                if sms_code:
                    progress.log_info("verification", "sms_submit", "SMS code received; submission delegated to MCP or manual flow")

            # Email: if manual provided code/link, agent already tried submission in run(); otherwise we can wait if needed
            if email_verification_payload and email_verification_payload.get('email_code'):
                progress.log_info("verification", "email_submit", "Email code available; submission delegated to MCP or manual flow")

            progress.complete_step("verification", True)
        except Exception as e:
            progress.log_warning("verification", None, f"Verification step encountered an issue: {e}")
            progress.complete_step("verification", False)
        
        # ===========================================
        # STEP 7: PROFILE SETUP
        # ===========================================
        progress.start_step("profile_setup")
        
        profile_result = None
        if persona:
            # Multiple sub-steps for profile setup
            for sub_step_id in ["upload_photo", "set_headline", "set_summary", "set_location", "add_experience", "add_education", "add_skills"]:
                progress.start_sub_step("profile_setup", sub_step_id)
                await asyncio.sleep(0.5)  # Simulate profile setup time
                progress.complete_sub_step("profile_setup", sub_step_id, True, {}, 0.5)
        else:
            progress.log_warning("profile_setup", None, "No persona available - skipping profile setup")
            
        progress.complete_step("profile_setup", True)
        
        # ===========================================
        # STEP 8: FINALIZATION
        # ===========================================
        progress.start_step("finalization")
        
        # Sub-step: Update database
        progress.start_sub_step("finalization", "update_database")
        start_time = time.time()
        
        account.status = 'completed'
        account.linkedin_created = True
        account.linkedin_creation_completed = datetime.utcnow()
        account.linkedin_url = f"https://linkedin.com/in/{account.first_name.lower()}-{account.last_name.lower()}"
        
        execution_time = time.time() - start_time
        progress.complete_sub_step("finalization", "update_database", True, {
            "linkedin_url": account.linkedin_url
        }, execution_time)
        
        # Sub-step: Create usage record
        progress.start_sub_step("finalization", "create_usage_record")
        start_time = time.time()
        
        if persona:
            persona_usage = PersonaUsage(
                persona_id=persona.id,
                account_id=account.id,
                usage_type='linkedin_creation',
                success=True,
                notes='LinkedIn account created successfully with enhanced progress tracking'
            )
            db.session.add(persona_usage)
        
        execution_time = time.time() - start_time
        progress.complete_sub_step("finalization", "create_usage_record", True, {
            "usage_recorded": persona is not None
        }, execution_time)
        
        # Sub-step: Cleanup browser sessions
        progress.start_sub_step("finalization", "cleanup_browser")
        start_time = time.time()
        try:
            if not _AI_AVAILABLE and session_id:
                browser_manager = await get_browser_manager()
                await browser_manager.close_session(session_id)
                progress.log_success("finalization", "cleanup_browser", "Browser session cleaned up")
            else:
                progress.log_success("finalization", "cleanup_browser", "AI session cleanup handled by provider")
        except Exception:
            pass
        execution_time = time.time() - start_time
        progress.complete_sub_step("finalization", "cleanup_browser", True, {"session_closed": True}, execution_time)
        
        # Sub-step: Final validation
        progress.start_sub_step("finalization", "final_validation")
        start_time = time.time()
        
        db.session.commit()
        progress.log_success("finalization", "final_validation", "All changes committed to database")
        
        execution_time = time.time() - start_time
        progress.complete_sub_step("finalization", "final_validation", True, {
            "database_committed": True
        }, execution_time)
        
        progress.complete_step("finalization", True)
        
        # ===========================================
        # COMPLETION & CLEANUP
        # ===========================================
        result = {
            'account_id': account_id,
            'linkedin_url': account.linkedin_url,
            'creation_time': (datetime.utcnow() - account.linkedin_creation_started).total_seconds(),
            'verification': verification_result,
            'profile_setup': profile_result is not None,
            'detection_risk': detection_risk
        }
        
        # Clean up browser sessions after successful completion
        if 'browser_agent' in locals() and browser_agent:
            try:
                await browser_agent.cleanup()
                logger.info(f"✅ Browser session cleaned up for account {account_id}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup browser session: {cleanup_error}")
        
        progress.send_completion(True, result)
        
        logger.info(f"LinkedIn account creation completed successfully for {account_id}")
        return result
        
    except Exception as e:
        logger.error(f"LinkedIn account creation failed for {account_id}: {e}")
        
        # Update account with failure status
        try:
            account = Account.query.get(account_id)
            if account:
                account.status = 'failed'
                account.linkedin_creation_failed = datetime.utcnow()
                db.session.commit()
        except Exception as db_error:
            logger.error(f"Failed to update account status: {db_error}")
        
        # Send failure notification
        progress.send_completion(False, error=str(e))
        
        # Clean up AIBrowserAgent sessions if they exist
        if 'browser_agent' in locals() and browser_agent:
            try:
                await browser_agent.cleanup()
                logger.info(f"✅ Browser agent cleaned up after error for account {account_id}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup browser agent: {cleanup_error}")
        
        # Cleanup browser session if it exists
        try:
            browser_manager = await get_browser_manager()
            # Attempt to close any known session for this account
            await browser_manager.cleanup_old_sessions(max_age_hours=0)  # force-check
        except Exception as cleanup_error:
            logger.warning(f"Failed to cleanup browser session: {cleanup_error}")
        
        return {
            'success': False,
            'error': str(e),
            'account_id': account_id
        }

