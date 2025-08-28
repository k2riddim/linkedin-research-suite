import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from src.services.browser_automation import StealthBrowserManager

logger = logging.getLogger(__name__)


class AccountCreationAgent:
    """
    Goal-driven agent that performs LinkedIn account creation using Playwright.

    Responsibility:
    - Drive the LinkedIn signup flow with resilient selectors and human-like delays
    - Handle branching layouts gracefully (new/legacy signup)
    - Bridge to verification (email/SMS) when requested
    - Report rich progress through the provided tracker
    """

    def __init__(self, browser_manager: StealthBrowserManager):
        self.browser_manager = browser_manager
        self._shot_idx = 0

        # Core selectors (multiple fallbacks for resilience)
        self.sel = {
            'join_now_button': 'a[href*="/signup"][data-tracking-control-name*="join-now"], a[href*="/start/join"]',
            'join_email': 'input[name="email"], input[name="session_key"], input#email-or-phone',
            'join_password': 'input[name="password"], input[name="session_password"], input#password',
            'join_first': 'input[name="firstName"], input#first-name',
            'join_last': 'input[name="lastName"], input#last-name',
            'join_submit': 'button[type="submit"], button[data-tracking-control-name*="registration-form_submit"], button[data-id="sign-in-form__submit-btn"]',
            'agree_terms': 'input[name="agreementCheckbox"], input#agreement-checkbox',
            'phone_input': 'input[name="phoneNumber"], input[name="phone_number"], input[type="tel"], input#phone, input#phoneNumber',
            'verification_code': 'input[name="pin"], input#input__verification_pin',
            'verify_submit': 'button[data-tracking-control-name*="verification"], button[type="submit"]',
        }

    async def _type(self, page, selector: str, text: str, tracker, step: str, sub: str) -> None:
        await page.wait_for_selector(selector, timeout=10000)
        await self.browser_manager.human_type(page, selector, text)
        tracker.log_info(step, sub, f"Typed into {selector}")

    async def _click_if_present(self, page, selector: str) -> bool:
        try:
            await page.wait_for_selector(selector, timeout=2500)
            await self.browser_manager.human_click(page, selector)
            return True
        except PlaywrightTimeoutError:
            return False

    def _prepare_run_dir(self, account_data: Dict[str, Any]) -> Path:
        try:
            root_dir = Path(__file__).resolve().parents[3]
        except Exception:
            root_dir = Path.cwd()
        logs_dir = root_dir / "logs"
        # Build label from name or email
        name_parts = []
        if account_data.get('first_name'):
            name_parts.append(str(account_data['first_name']))
        if account_data.get('last_name'):
            name_parts.append(str(account_data['last_name']))
        label = "-".join(name_parts) if name_parts else (str(account_data.get('email', 'account')).split('@')[0])
        label = "".join(ch if ch.isalnum() or ch in ('-', '_') else '_' for ch in label) or "account"
        ts = datetime.now().strftime("%H%M%S")
        run_dir = logs_dir / f"run-{label}-{ts}"
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir

    async def _screenshot(self, page, run_dir: Path, name: str) -> None:
        try:
            self._shot_idx += 1
            filename = f"{self._shot_idx:02d}-{name}.png"
            path = run_dir / filename
            await page.screenshot(path=str(path), full_page=True)
        except Exception:
            # Screenshot attempts must never break the run
            pass

    async def run(self,
                  account_id: str,
                  session_id: str,
                  account_data: Dict[str, Any],
                  tracker,
                  manual_verification: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute the signup flow. Returns a dict with keys:
          { 'success': bool, 'verification_required': bool, 'current_url': str }
        """

        step = "account_creation"
        run_dir = self._prepare_run_dir(account_data)
        tracker.start_sub_step(step, "navigate_signup")
        try:
            session = await self.browser_manager.get_session(session_id)
            if not session:
                raise RuntimeError(f"No browser session {session_id}")
            page = session.page

            try:
                await self.browser_manager.navigate_with_human_timing(page, "https://www.linkedin.com/")
            except Exception as nav_err:
                # Retry once without proxy if navigation timed out
                try:
                    session = await self.browser_manager.get_session(session_id)
                    if session and getattr(session.context, 'tracing', None) is not None:
                        pass
                except Exception:
                    pass
                # Close and recreate a session without proxy to de-risk proxy failures
                try:
                    from src.services.browser_automation import get_browser_manager
                    bm = await get_browser_manager()
                    await bm.close_session(session_id)
                    new_session = await bm.create_stealth_session(account_id=account_id, proxy_url=None)
                    page = new_session.page
                    await self.browser_manager.navigate_with_human_timing(page, "https://www.linkedin.com/")
                except Exception:
                    raise nav_err
            await self._click_if_present(page, self.sel['join_now_button'])
            await self.browser_manager.human_delay(1000, 2000)
            tracker.complete_sub_step(step, "navigate_signup", True, {}, 0)
            await self._screenshot(page, run_dir, "navigate_signup")
        except Exception as e:
            tracker.complete_sub_step(step, "navigate_signup", False, { 'error': str(e) }, 0)
            try:
                await self._screenshot(page, run_dir, "navigate_signup_error")
            except Exception:
                pass
            raise

        # Fill email + password first (some flows ask for these first)
        tracker.start_sub_step(step, "fill_credentials")
        try:
            await self._type(page, self.sel['join_email'], account_data['email'], tracker, step, "fill_credentials")
            await self._type(page, self.sel['join_password'], account_data['password'], tracker, step, "fill_credentials")
            await self._click_if_present(page, self.sel['agree_terms'])
            await self._click_if_present(page, self.sel['join_submit'])
            tracker.complete_sub_step(step, "fill_credentials", True, {}, 0)
            await self._screenshot(page, run_dir, "fill_credentials")
        except Exception as e:
            tracker.complete_sub_step(step, "fill_credentials", False, { 'error': str(e) }, 0)
            try:
                await self._screenshot(page, run_dir, "fill_credentials_error")
            except Exception:
                pass
            raise

        # Some variants then ask for first/last name
        tracker.start_sub_step(step, "fill_names")
        try:
            filled_name = False
            try:
                await page.wait_for_selector(self.sel['join_first'], timeout=4000)
                await self._type(page, self.sel['join_first'], account_data['first_name'], tracker, step, "fill_names")
                await self._type(page, self.sel['join_last'], account_data['last_name'], tracker, step, "fill_names")
                await self._click_if_present(page, self.sel['join_submit'])
                filled_name = True
            except PlaywrightTimeoutError:
                filled_name = False
            tracker.complete_sub_step(step, "fill_names", True, { 'filled': filled_name }, 0)
            await self._screenshot(page, run_dir, "fill_names")
        except Exception as e:
            tracker.complete_sub_step(step, "fill_names", False, { 'error': str(e) }, 0)
            try:
                await self._screenshot(page, run_dir, "fill_names_error")
            except Exception:
                pass
            raise

        # Some flows request a phone number before verification
        if account_data.get('phone_number'):
            tracker.start_sub_step(step, "fill_phone")
            try:
                entered_phone = False
                try:
                    await page.wait_for_selector(self.sel['phone_input'], timeout=4000)
                    await self._type(page, self.sel['phone_input'], account_data['phone_number'], tracker, step, "fill_phone")
                    await self._click_if_present(page, self.sel['join_submit'])
                    entered_phone = True
                except PlaywrightTimeoutError:
                    entered_phone = False
                tracker.complete_sub_step(step, "fill_phone", True, { 'entered': entered_phone }, 0)
                await self._screenshot(page, run_dir, "fill_phone")
            except Exception as e:
                tracker.complete_sub_step(step, "fill_phone", False, { 'error': str(e) }, 0)
                try:
                    await self._screenshot(page, run_dir, "fill_phone_error")
                except Exception:
                    pass
                raise

        # Determine whether verification is required
        tracker.start_sub_step(step, "detect_verification")
        await self.browser_manager.human_delay(2000, 4000)
        current_url = page.url
        verification_required = False
        try:
            # Either URL contains challenge/verification or code input is present
            if any(k in current_url for k in ("challenge", "verification")):
                verification_required = True
            else:
                try:
                    await page.wait_for_selector(self.sel['verification_code'], timeout=2500)
                    verification_required = True
                except PlaywrightTimeoutError:
                    verification_required = False
            tracker.complete_sub_step(step, "detect_verification", True, { 'verification_required': verification_required, 'current_url': current_url }, 0)
            await self._screenshot(page, run_dir, "detect_verification")
        except Exception as e:
            tracker.complete_sub_step(step, "detect_verification", False, { 'error': str(e) }, 0)
            try:
                await self._screenshot(page, run_dir, "detect_verification_error")
            except Exception:
                pass
            raise

        # If verification form is already visible and user supplied code manually, submit it immediately
        if verification_required and manual_verification:
            code = manual_verification.get('email_code')
            link = manual_verification.get('verification_link')
            if code:
                tracker.start_sub_step(step, "manual_email_code")
                try:
                    await self._type(page, self.sel['verification_code'], code, tracker, step, "manual_email_code")
                    await self._click_if_present(page, self.sel['verify_submit'])
                    await self.browser_manager.human_delay(2000, 4000)
                    tracker.complete_sub_step(step, "manual_email_code", True, { 'used_code': True }, 0)
                    # Recompute URL after submit
                    current_url = page.url
                    await self._screenshot(page, run_dir, "manual_email_code")
                except Exception as e:
                    tracker.complete_sub_step(step, "manual_email_code", False, { 'error': str(e) }, 0)
                    try:
                        await self._screenshot(page, run_dir, "manual_email_code_error")
                    except Exception:
                        pass
                    raise
            elif link:
                tracker.start_sub_step(step, "manual_email_link")
                try:
                    await self.browser_manager.navigate_with_human_timing(page, link)
                    await self.browser_manager.human_delay(2000, 3000)
                    tracker.complete_sub_step(step, "manual_email_link", True, { 'used_link': True }, 0)
                    current_url = page.url
                    await self._screenshot(page, run_dir, "manual_email_link")
                except Exception as e:
                    tracker.complete_sub_step(step, "manual_email_link", False, { 'error': str(e) }, 0)
                    try:
                        await self._screenshot(page, run_dir, "manual_email_link_error")
                    except Exception:
                        pass
                    raise

        return {
            'success': True,
            'verification_required': verification_required,
            'current_url': current_url
        }

    async def submit_code(self, session_id: str, code: str, tracker) -> bool:
        """Submit a verification code on the current page if the input is present."""
        step = "verification"
        tracker.start_sub_step(step, "submit_code")
        try:
            session = await self.browser_manager.get_session(session_id)
            if not session:
                raise RuntimeError(f"No browser session {session_id}")
            page = session.page
            await page.wait_for_selector(self.sel['verification_code'], timeout=8000)
            await self.browser_manager.human_type(page, self.sel['verification_code'], code)
            await self._click_if_present(page, self.sel['verify_submit'])
            await self.browser_manager.human_delay(1500, 2500)
            tracker.complete_sub_step(step, "submit_code", True, { 'used_code': True }, 0)
            # Save screenshot near submission
            try:
                # Derive run dir from a stable place: logs/last_run or use account id if available
                # For simplicity here, we skip resolving run dir and focus on submission path
                pass
            except Exception:
                pass
            return True
        except Exception as e:
            tracker.complete_sub_step(step, "submit_code", False, { 'error': str(e) }, 0)
            return False


