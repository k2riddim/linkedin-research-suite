import asyncio
import logging
import random
import time
import json
from dataclasses import dataclass
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from src.services.browser_automation import StealthBrowserManager, BrowserSession, ActionResult, ActionType
from src.services.ai_content import PersonaProfile

logger = logging.getLogger(__name__)

class LinkedInActionType(Enum):
    ACCOUNT_CREATION = "account_creation"
    EMAIL_VERIFICATION = "email_verification"
    SMS_VERIFICATION = "sms_verification"
    PROFILE_SETUP = "profile_setup"
    PROFILE_PHOTO_UPLOAD = "profile_photo_upload"
    EXPERIENCE_ADD = "experience_add"
    EDUCATION_ADD = "education_add"
    SKILLS_ADD = "skills_add"
    CONNECTION_REQUEST = "connection_request"
    PROFILE_VIEW = "profile_view"
    SEARCH_PROFILES = "search_profiles"
    MESSAGE_SEND = "message_send"

@dataclass
class LinkedInAccount:
    """LinkedIn account information"""
    account_id: str
    email: str
    password: str
    phone_number: Optional[str]
    profile_url: Optional[str]
    status: str  # created, verified, setup_complete, active, suspended
    created_at: datetime
    last_activity: Optional[datetime] = None

@dataclass
class LinkedInActionResult:
    """Result of LinkedIn action execution"""
    action_type: LinkedInActionType
    success: bool
    account_id: str
    data: Dict[str, Any]
    detection_risk: float
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class ProfileSetupData:
    """Data for profile setup"""
    headline: str
    summary: str
    location: str
    industry: str
    current_position: str
    current_company: str
    education: List[Dict[str, str]]
    experience: List[Dict[str, str]]
    skills: List[str]

class LinkedInEngine:
    """
    LinkedIn automation engine for account management and research

    Algorithm Flow:
    1. Initialize browser session with stealth measures
    2. Navigate to LinkedIn with human-like behavior
    3. Execute LinkedIn-specific actions (signup, login, profile setup)
    4. Monitor for detection indicators
    5. Implement adaptive delays and behavior patterns
    6. Handle verification challenges
    7. Maintain session health and rotation
    """

    def __init__(self, browser_manager: StealthBrowserManager):
        self.browser_manager = browser_manager
        self.linkedin_base_url = "https://www.linkedin.com"
        self.action_history: Dict[str, List[LinkedInActionResult]] = {}
        
        # LinkedIn selectors (updated for current LinkedIn design)
        self.selectors = {
            # Registration page
            'signup_email': 'input[name="session_key"]',
            'signup_password': 'input[name="session_password"]',
            'signup_submit': 'button[type="submit"]',
            'join_now_button': 'a[data-tracking-control-name="guest_homepage-basic_join-now-link"]',
            'first_name_input': 'input[name="firstName"]',
            'last_name_input': 'input[name="lastName"]',
            'email_input': 'input[name="email"]',
            'password_input': 'input[name="password"]',
            'agree_terms': 'input[name="agreementCheckbox"]',
            'join_button': 'button[data-tracking-control-name="registration-form_submit-button"]',
            
            # Verification
            'verification_code_input': 'input[name="pin"]',
            'verify_button': 'button[data-tracking-control-name="verification-submit"]',
            'phone_input': 'input[name="phoneNumber"]',
            'phone_submit': 'button[data-tracking-control-name="phone-verification-submit"]',
            
            # Profile setup
            'profile_photo_upload': 'input[type="file"][accept="image/*"]',
            'headline_input': 'input[name="headline"]',
            'summary_textarea': 'textarea[name="summary"]',
            'location_input': 'input[name="geoLocation"]',
            'industry_select': 'select[name="industry"]',
            'save_button': 'button[data-tracking-control-name="save"]',
            
            # Experience
            'add_experience_button': 'button[data-tracking-control-name="add-experience"]',
            'position_title_input': 'input[name="title"]',
            'company_name_input': 'input[name="companyName"]',
            'start_date_month': 'select[name="startDateMonth"]',
            'start_date_year': 'select[name="startDateYear"]',
            'current_position_checkbox': 'input[name="currentlyWorking"]',
            
            # Skills
            'add_skills_button': 'button[data-tracking-control-name="add-skills"]',
            'skills_input': 'input[placeholder="Add a skill"]',
            'skills_suggestion': '.typeahead-result',
            
            # Search and connections
            'search_input': 'input[placeholder="Search"]',
            'search_button': 'button[data-tracking-control-name="nav-search-submit"]',
            'connect_button': 'button[data-tracking-control-name="people-connect"]',
            'send_invitation': 'button[data-tracking-control-name="send-invitation"]',
            
            # Navigation
            'profile_menu': 'button[data-tracking-control-name="nav-settings"]',
            'my_profile_link': 'a[data-tracking-control-name="nav-profile"]',
            'home_link': 'a[data-tracking-control-name="nav-home"]'
        }

    async def create_linkedin_account(self, account_data: Dict[str, str], session_id: str) -> LinkedInActionResult:
        """Algorithm: LinkedIn Account Creation"""
        start_time = time.time()
        
        try:
            session = await self.browser_manager.get_session(session_id)
            if not session:
                raise Exception(f"Browser session {session_id} not found")
            
            page = session.page
            
            # Step 1: Navigate to LinkedIn registration
            logger.info("Navigating to LinkedIn registration page")
            await self.browser_manager.navigate_with_human_timing(page, f"{self.linkedin_base_url}/signup")
            await self.browser_manager.wait_for_page_ready(page)
            
            # Step 2: Fill registration form
            logger.info("Filling registration form")
            
            # First name
            await self.browser_manager.human_type(page, self.selectors['first_name_input'], account_data['first_name'])
            await self.browser_manager.human_delay(500, 1000)
            
            # Last name
            await self.browser_manager.human_type(page, self.selectors['last_name_input'], account_data['last_name'])
            await self.browser_manager.human_delay(500, 1000)
            
            # Email
            await self.browser_manager.human_type(page, self.selectors['email_input'], account_data['email'])
            await self.browser_manager.human_delay(500, 1000)
            
            # Password
            await self.browser_manager.human_type(page, self.selectors['password_input'], account_data['password'])
            await self.browser_manager.human_delay(1000, 2000)
            
            # Agree to terms (if checkbox exists)
            try:
                await page.wait_for_selector(self.selectors['agree_terms'], timeout=3000)
                await self.browser_manager.human_click(page, self.selectors['agree_terms'])
                await self.browser_manager.human_delay(500, 1000)
            except PlaywrightTimeoutError:
                logger.info("Terms checkbox not found, continuing...")
            
            # Step 3: Submit registration
            await self.browser_manager.human_click(page, self.selectors['join_button'])
            await self.browser_manager.human_delay(3000, 5000)
            
            # Step 4: Check for verification requirements
            current_url = page.url
            verification_required = False
            
            if "challenge" in current_url or "verification" in current_url:
                verification_required = True
                logger.info("Account creation requires verification")
            
            execution_time = time.time() - start_time
            
            # Calculate detection risk
            recent_actions = self.get_recent_actions(account_data.get('account_id', 'unknown'))
            detection_risk = self.browser_manager.calculate_detection_risk(session, recent_actions)
            
            result = LinkedInActionResult(
                action_type=LinkedInActionType.ACCOUNT_CREATION,
                success=True,
                account_id=account_data.get('account_id', 'unknown'),
                data={
                    'email': account_data['email'],
                    'verification_required': verification_required,
                    'current_url': current_url
                },
                detection_risk=detection_risk,
                execution_time=execution_time
            )
            
            self.add_action_to_history(account_data.get('account_id', 'unknown'), result)
            logger.info(f"LinkedIn account creation completed for {account_data['email']}")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error creating LinkedIn account: {e}")
            
            result = LinkedInActionResult(
                action_type=LinkedInActionType.ACCOUNT_CREATION,
                success=False,
                account_id=account_data.get('account_id', 'unknown'),
                data={},
                detection_risk=0.8,  # High risk on failure
                error_message=str(e),
                execution_time=execution_time
            )
            
            self.add_action_to_history(account_data.get('account_id', 'unknown'), result)
            return result

    async def verify_email(self, verification_link: str, session_id: str, account_id: str) -> LinkedInActionResult:
        """Verify email using verification link"""
        start_time = time.time()
        
        try:
            session = await self.browser_manager.get_session(session_id)
            if not session:
                raise Exception(f"Browser session {session_id} not found")
            
            page = session.page
            
            # Navigate to verification link
            logger.info(f"Navigating to email verification link")
            await self.browser_manager.navigate_with_human_timing(page, verification_link)
            await self.browser_manager.wait_for_page_ready(page)
            
            # Check if verification was successful
            current_url = page.url
            success = "linkedin.com" in current_url and "challenge" not in current_url
            
            execution_time = time.time() - start_time
            
            result = LinkedInActionResult(
                action_type=LinkedInActionType.EMAIL_VERIFICATION,
                success=success,
                account_id=account_id,
                data={'verification_url': current_url},
                detection_risk=0.1,  # Low risk for email verification
                execution_time=execution_time
            )
            
            self.add_action_to_history(account_id, result)
            logger.info(f"Email verification {'successful' if success else 'failed'}")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error verifying email: {e}")
            
            result = LinkedInActionResult(
                action_type=LinkedInActionType.EMAIL_VERIFICATION,
                success=False,
                account_id=account_id,
                data={},
                detection_risk=0.5,
                error_message=str(e),
                execution_time=execution_time
            )
            
            self.add_action_to_history(account_id, result)
            return result

    async def verify_sms(self, verification_code: str, session_id: str, account_id: str) -> LinkedInActionResult:
        """Verify SMS using verification code"""
        start_time = time.time()
        
        try:
            session = await self.browser_manager.get_session(session_id)
            if not session:
                raise Exception(f"Browser session {session_id} not found")
            
            page = session.page
            
            # Wait for verification code input
            await page.wait_for_selector(self.selectors['verification_code_input'], timeout=10000)
            
            # Enter verification code
            await self.browser_manager.human_type(page, self.selectors['verification_code_input'], verification_code)
            await self.browser_manager.human_delay(1000, 2000)
            
            # Submit verification
            await self.browser_manager.human_click(page, self.selectors['verify_button'])
            await self.browser_manager.human_delay(3000, 5000)
            
            # Check if verification was successful
            current_url = page.url
            success = "challenge" not in current_url and "verification" not in current_url
            
            execution_time = time.time() - start_time
            
            result = LinkedInActionResult(
                action_type=LinkedInActionType.SMS_VERIFICATION,
                success=success,
                account_id=account_id,
                data={'verification_code': verification_code, 'current_url': current_url},
                detection_risk=0.2,  # Low risk for SMS verification
                execution_time=execution_time
            )
            
            self.add_action_to_history(account_id, result)
            logger.info(f"SMS verification {'successful' if success else 'failed'}")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error verifying SMS: {e}")
            
            result = LinkedInActionResult(
                action_type=LinkedInActionType.SMS_VERIFICATION,
                success=False,
                account_id=account_id,
                data={},
                detection_risk=0.5,
                error_message=str(e),
                execution_time=execution_time
            )
            
            self.add_action_to_history(account_id, result)
            return result

    async def setup_profile(self, persona: PersonaProfile, session_id: str) -> LinkedInActionResult:
        """Algorithm: LinkedIn Profile Setup"""
        start_time = time.time()
        
        try:
            session = await self.browser_manager.get_session(session_id)
            if not session:
                raise Exception(f"Browser session {session_id} not found")
            
            page = session.page
            
            # Navigate to profile edit page
            logger.info("Setting up LinkedIn profile")
            await self.browser_manager.navigate_with_human_timing(page, f"{self.linkedin_base_url}/in/me/edit/")
            await self.browser_manager.wait_for_page_ready(page)
            
            setup_steps = []
            
            # Step 1: Update headline
            try:
                await page.wait_for_selector(self.selectors['headline_input'], timeout=5000)
                await self.browser_manager.human_type(page, self.selectors['headline_input'], persona.content_data.headline)
                setup_steps.append("headline_updated")
                await self.browser_manager.human_delay(1000, 2000)
            except PlaywrightTimeoutError:
                logger.warning("Headline input not found")
            
            # Step 2: Update summary
            try:
                await page.wait_for_selector(self.selectors['summary_textarea'], timeout=5000)
                await self.browser_manager.human_type(page, self.selectors['summary_textarea'], persona.content_data.summary)
                setup_steps.append("summary_updated")
                await self.browser_manager.human_delay(1000, 2000)
            except PlaywrightTimeoutError:
                logger.warning("Summary textarea not found")
            
            # Step 3: Update location
            try:
                await page.wait_for_selector(self.selectors['location_input'], timeout=5000)
                await self.browser_manager.human_type(page, self.selectors['location_input'], persona.demographic_data.location)
                setup_steps.append("location_updated")
                await self.browser_manager.human_delay(1000, 2000)
            except PlaywrightTimeoutError:
                logger.warning("Location input not found")
            
            # Step 4: Save changes
            try:
                await self.browser_manager.human_click(page, self.selectors['save_button'])
                await self.browser_manager.human_delay(2000, 3000)
                setup_steps.append("changes_saved")
            except PlaywrightTimeoutError:
                logger.warning("Save button not found")
            
            execution_time = time.time() - start_time
            
            # Calculate detection risk
            recent_actions = self.get_recent_actions(persona.persona_id)
            detection_risk = self.browser_manager.calculate_detection_risk(session, recent_actions)
            
            result = LinkedInActionResult(
                action_type=LinkedInActionType.PROFILE_SETUP,
                success=len(setup_steps) > 0,
                account_id=persona.persona_id,
                data={
                    'setup_steps_completed': setup_steps,
                    'profile_data': {
                        'headline': persona.content_data.headline,
                        'location': persona.demographic_data.location
                    }
                },
                detection_risk=detection_risk,
                execution_time=execution_time
            )
            
            self.add_action_to_history(persona.persona_id, result)
            logger.info(f"Profile setup completed with {len(setup_steps)} steps")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error setting up profile: {e}")
            
            result = LinkedInActionResult(
                action_type=LinkedInActionType.PROFILE_SETUP,
                success=False,
                account_id=persona.persona_id,
                data={},
                detection_risk=0.6,
                error_message=str(e),
                execution_time=execution_time
            )
            
            self.add_action_to_history(persona.persona_id, result)
            return result

    async def add_experience(self, experience_data: Dict[str, str], session_id: str, account_id: str) -> LinkedInActionResult:
        """Add work experience to profile"""
        start_time = time.time()
        
        try:
            session = await self.browser_manager.get_session(session_id)
            if not session:
                raise Exception(f"Browser session {session_id} not found")
            
            page = session.page
            
            # Navigate to experience section
            await self.browser_manager.navigate_with_human_timing(page, f"{self.linkedin_base_url}/in/me/edit/experience/")
            await self.browser_manager.wait_for_page_ready(page)
            
            # Click add experience button
            await self.browser_manager.human_click(page, self.selectors['add_experience_button'])
            await self.browser_manager.human_delay(2000, 3000)
            
            # Fill experience form
            await self.browser_manager.human_type(page, self.selectors['position_title_input'], experience_data['title'])
            await self.browser_manager.human_delay(500, 1000)
            
            await self.browser_manager.human_type(page, self.selectors['company_name_input'], experience_data['company'])
            await self.browser_manager.human_delay(500, 1000)
            
            # Set dates (simplified)
            if 'start_month' in experience_data:
                await page.select_option(self.selectors['start_date_month'], experience_data['start_month'])
                await self.browser_manager.human_delay(300, 600)
            
            if 'start_year' in experience_data:
                await page.select_option(self.selectors['start_date_year'], experience_data['start_year'])
                await self.browser_manager.human_delay(300, 600)
            
            # Mark as current position if specified
            if experience_data.get('current', False):
                await self.browser_manager.human_click(page, self.selectors['current_position_checkbox'])
                await self.browser_manager.human_delay(500, 1000)
            
            # Save experience
            await self.browser_manager.human_click(page, self.selectors['save_button'])
            await self.browser_manager.human_delay(2000, 3000)
            
            execution_time = time.time() - start_time
            
            result = LinkedInActionResult(
                action_type=LinkedInActionType.EXPERIENCE_ADD,
                success=True,
                account_id=account_id,
                data={'experience': experience_data},
                detection_risk=0.3,
                execution_time=execution_time
            )
            
            self.add_action_to_history(account_id, result)
            logger.info(f"Added experience: {experience_data['title']} at {experience_data['company']}")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error adding experience: {e}")
            
            result = LinkedInActionResult(
                action_type=LinkedInActionType.EXPERIENCE_ADD,
                success=False,
                account_id=account_id,
                data={},
                detection_risk=0.5,
                error_message=str(e),
                execution_time=execution_time
            )
            
            self.add_action_to_history(account_id, result)
            return result

    async def search_profiles(self, search_query: str, session_id: str, account_id: str, max_results: int = 10) -> LinkedInActionResult:
        """Search for LinkedIn profiles"""
        start_time = time.time()
        
        try:
            session = await self.browser_manager.get_session(session_id)
            if not session:
                raise Exception(f"Browser session {session_id} not found")
            
            page = session.page
            
            # Navigate to LinkedIn home
            await self.browser_manager.navigate_with_human_timing(page, f"{self.linkedin_base_url}/feed/")
            await self.browser_manager.wait_for_page_ready(page)
            
            # Perform search
            await self.browser_manager.human_type(page, self.selectors['search_input'], search_query)
            await self.browser_manager.human_delay(1000, 2000)
            
            await self.browser_manager.human_click(page, self.selectors['search_button'])
            await self.browser_manager.human_delay(3000, 5000)
            
            # Extract search results
            profiles = []
            try:
                # Wait for search results to load
                await page.wait_for_selector('.search-result', timeout=10000)
                
                # Extract profile information
                profile_elements = await page.query_selector_all('.search-result')
                
                for i, element in enumerate(profile_elements[:max_results]):
                    try:
                        name_element = await element.query_selector('.actor-name')
                        headline_element = await element.query_selector('.subline')
                        link_element = await element.query_selector('a[href*="/in/"]')
                        
                        profile_data = {
                            'name': await name_element.inner_text() if name_element else 'Unknown',
                            'headline': await headline_element.inner_text() if headline_element else 'No headline',
                            'profile_url': await link_element.get_attribute('href') if link_element else None
                        }
                        
                        profiles.append(profile_data)
                        
                    except Exception as e:
                        logger.warning(f"Error extracting profile {i}: {e}")
                        continue
                
            except PlaywrightTimeoutError:
                logger.warning("Search results not found or took too long to load")
            
            execution_time = time.time() - start_time
            
            result = LinkedInActionResult(
                action_type=LinkedInActionType.SEARCH_PROFILES,
                success=len(profiles) > 0,
                account_id=account_id,
                data={
                    'search_query': search_query,
                    'profiles_found': len(profiles),
                    'profiles': profiles
                },
                detection_risk=0.2,
                execution_time=execution_time
            )
            
            self.add_action_to_history(account_id, result)
            logger.info(f"Search completed: found {len(profiles)} profiles for '{search_query}'")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error searching profiles: {e}")
            
            result = LinkedInActionResult(
                action_type=LinkedInActionType.SEARCH_PROFILES,
                success=False,
                account_id=account_id,
                data={},
                detection_risk=0.4,
                error_message=str(e),
                execution_time=execution_time
            )
            
            self.add_action_to_history(account_id, result)
            return result

    def add_action_to_history(self, account_id: str, action: LinkedInActionResult):
        """Add action to history for risk analysis"""
        if account_id not in self.action_history:
            self.action_history[account_id] = []
        
        self.action_history[account_id].append(action)
        
        # Keep only recent actions (last 50)
        if len(self.action_history[account_id]) > 50:
            self.action_history[account_id] = self.action_history[account_id][-50:]

    def get_recent_actions(self, account_id: str, hours: int = 2) -> List[LinkedInActionResult]:
        """Get recent actions for an account"""
        if account_id not in self.action_history:
            return []
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_actions = [
            action for action in self.action_history[account_id]
            if action.timestamp > cutoff_time
        ]
        
        return recent_actions

    def get_account_statistics(self, account_id: str) -> Dict[str, Any]:
        """Get statistics for an account"""
        if account_id not in self.action_history:
            return {'total_actions': 0, 'success_rate': 0.0, 'avg_detection_risk': 0.0}
        
        actions = self.action_history[account_id]
        total_actions = len(actions)
        successful_actions = sum(1 for action in actions if action.success)
        success_rate = successful_actions / total_actions if total_actions > 0 else 0.0
        
        avg_detection_risk = sum(action.detection_risk for action in actions) / total_actions if total_actions > 0 else 0.0
        
        return {
            'total_actions': total_actions,
            'successful_actions': successful_actions,
            'success_rate': success_rate,
            'avg_detection_risk': avg_detection_risk,
            'last_action': actions[-1].timestamp.isoformat() if actions else None
        }

# Global LinkedIn engine instance
linkedin_engine = None

async def get_linkedin_engine() -> LinkedInEngine:
    """Get or create global LinkedIn engine instance"""
    global linkedin_engine
    
    if linkedin_engine is None:
        from src.services.browser_automation import browser_manager
        linkedin_engine = LinkedInEngine(browser_manager)
    
    return linkedin_engine

