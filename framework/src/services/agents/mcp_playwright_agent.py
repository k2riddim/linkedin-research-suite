import os
import logging
from typing import Any, Dict, Optional
import json
import base64
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class MCPPlaywrightAgent:
    """
    Orchestrates LinkedIn signup via OpenAI using browser automation.
    
    This agent uses OpenAI's chat completion API to generate step-by-step
    instructions for LinkedIn account creation and executes them using
    the existing browser automation infrastructure.

    Environment:
      - OPENAI_API_KEY: API key for the OpenAI API
    """

    def __init__(self, model: str = None):
        self.model = model or os.getenv("OPENAI_MCP_MODEL", "gpt-5")
        self._client = None
        try:
            # Import OpenAI client
            from openai import OpenAI
            self._client = OpenAI()
        except Exception as e:
            logger.warning(f"OpenAI client not available: {e}")

    async def run(self,
                  account_id: str,
                  account_data: Dict[str, Any],
                  tracker,
                  manual_verification: Optional[Dict[str, Any]] = None,
                  proxy_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Create LinkedIn account using AI-guided browser automation.
        Returns a dict: { success, verification_required, current_url }
        """

        step = "account_creation"
        tracker.start_sub_step(step, "mcp_orchestration")

        if self._client is None:
            tracker.complete_sub_step(step, "mcp_orchestration", False, { 'error': 'OpenAI client unavailable' }, 0)
            return { 'success': False, 'error': 'OpenAI client unavailable' }

        try:
            # Use existing browser automation instead of MCP
            from src.services.browser_automation import get_browser_manager
            from src.services.linkedin_engine import get_linkedin_engine
            
            browser_manager = await get_browser_manager()
            linkedin_engine = await get_linkedin_engine()
            
            # Create browser session with proxy if provided
            session_config = {
                'proxy': proxy_url,
                'locale': 'fr-FR',
                'timezone': 'Europe/Paris'
            }
            
            session = await browser_manager.create_stealth_session(account_id=account_id, proxy_url=proxy_url)
            session_id = session.session_id
            
            if not session:
                raise Exception("Failed to create browser session")
            
            # Use the existing LinkedIn engine for account creation
            result = await linkedin_engine.create_linkedin_account(account_data, session_id)
            
            # Take screenshot for debugging
            screenshot_saved = False
            try:
                page = session.page
                screenshot_bytes = await page.screenshot(full_page=True)
                
                # Save screenshot
                label = f"{account_data.get('first_name', '')}-{account_data.get('last_name', '')}".strip().replace(' ', '-') or account_data.get('email', 'account').split('@')[0]
                label = "".join(ch if ch.isalnum() or ch in ('-', '_') else '_' for ch in label) or 'account'
                ts = datetime.now().strftime("%H%M%S")
                
                try:
                    root_dir = Path(__file__).resolve().parents[3]
                except Exception:
                    root_dir = Path.cwd()
                
                run_dir = root_dir / "logs" / f"run-{label}-{ts}"
                run_dir.mkdir(parents=True, exist_ok=True)
                shot_path = run_dir / "00-signup_screenshot.png"
                shot_path.write_bytes(screenshot_bytes)
                screenshot_saved = True
                
            except Exception as e:
                logger.warning(f"Failed to save screenshot: {e}")
            
            # Clean up session
            await browser_manager.close_session(session_id)
            
            outcome = {
                'success': result.success,
                'verification_required': result.data.get('verification_required', True),
                'current_url': result.data.get('current_url', ''),
                'screenshot_saved': screenshot_saved,
                'detection_risk': result.detection_risk
            }
            
            if not result.success:
                outcome['error'] = getattr(result, 'error_message', 'Account creation failed')
            
            tracker.complete_sub_step(step, "mcp_orchestration", result.success, outcome, getattr(result, 'execution_time', 0))
            return outcome

        except Exception as e:
            logger.error(f"MCP orchestration failed: {e}")
            tracker.complete_sub_step(step, "mcp_orchestration", False, { 'error': str(e) }, 0)
            return { 'success': False, 'error': str(e) }

    async def generate_account_strategy(self, account_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use AI to generate a strategy for LinkedIn account creation.
        This can help with dynamic form handling and verification challenges.
        """
        if self._client is None:
            return {'strategy': 'default', 'steps': []}
        
        try:
            system_prompt = """You are an expert at LinkedIn account creation automation. 
            Analyze the provided account data and generate a strategy for successful account creation.
            Consider potential challenges like verification requirements, form variations, and detection avoidance.
            
            Return a JSON object with:
            - strategy: brief description of the approach
            - steps: array of step objects with {action, selector, value, delay_ms}
            - verification_handling: approach for handling email/SMS verification
            - risk_mitigation: techniques to avoid detection
            """
            
            user_prompt = f"""Account data:
            First name: {account_data.get('first_name')}
            Last name: {account_data.get('last_name')}
            Email: {account_data.get('email')}
            Has phone: {bool(account_data.get('phone_number'))}
            
            Generate an optimal strategy for creating this LinkedIn account."""
            
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
            
            strategy_text = response.choices[0].message.content
            
            # Try to parse JSON from response
            try:
                strategy = json.loads(strategy_text)
                return strategy
            except json.JSONDecodeError:
                # Fallback to default strategy
                return {
                    'strategy': 'default',
                    'steps': [],
                    'verification_handling': 'manual',
                    'risk_mitigation': 'standard_delays'
                }
                
        except Exception as e:
            logger.error(f"Failed to generate account strategy: {e}")
            return {
                'strategy': 'default',
                'steps': [],
                'error': str(e)
            }