import asyncio
import logging
import random
import time
import json
from dataclasses import dataclass
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from enum import Enum
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

logger = logging.getLogger(__name__)

class ActionType(Enum):
    CLICK = "click"
    TYPE = "type"
    SCROLL = "scroll"
    NAVIGATE = "navigate"
    WAIT = "wait"

@dataclass
class BrowserFingerprint:
    """Browser fingerprint for anti-detection"""
    user_agent: str
    viewport: Dict[str, int]
    timezone: str
    locale: str
    platform: str
    screen_resolution: Dict[str, int]

@dataclass
class BrowserSession:
    """Browser session container"""
    browser: Browser
    context: BrowserContext
    page: Page
    fingerprint: BrowserFingerprint
    account_id: str
    session_id: str
    created_at: datetime

@dataclass
class ActionResult:
    """Result of browser action execution"""
    success: bool
    action_type: ActionType
    target_data: Dict[str, Any]
    detection_risk: float
    error_message: Optional[str] = None
    execution_time: Optional[float] = None

class StealthBrowserManager:
    """
    Manages browser sessions with anti-detection measures

    Algorithm Flow:
    1. Initialize Playwright with stealth plugins
    2. Generate realistic browser fingerprint
    3. Configure proxy and user agent rotation
    4. Implement human-like behavior patterns
    5. Execute actions with randomized timing
    6. Monitor for detection indicators
    7. Rotate session on risk detection
    """

    def __init__(self):
        self.active_sessions: Dict[str, BrowserSession] = {}
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        ]
        
        self.viewports = [
            {"width": 1920, "height": 1080},
            {"width": 1366, "height": 768},
            {"width": 1440, "height": 900},
            {"width": 1536, "height": 864},
            {"width": 1280, "height": 720}
        ]
        
        self.timezones = [
            "Europe/Paris", "Europe/London", "Europe/Berlin", 
            "Europe/Madrid", "Europe/Rome", "Europe/Amsterdam"
        ]

    def generate_browser_fingerprint(self) -> BrowserFingerprint:
        """Generate realistic browser fingerprint"""
        user_agent = random.choice(self.user_agents)
        viewport = random.choice(self.viewports)
        timezone = random.choice(self.timezones)
        
        # Extract platform from user agent
        if "Windows" in user_agent:
            platform = "Win32"
        elif "Macintosh" in user_agent:
            platform = "MacIntel"
        else:
            platform = "Linux x86_64"
        
        # Generate screen resolution (usually larger than viewport)
        screen_width = viewport["width"] + random.randint(0, 200)
        screen_height = viewport["height"] + random.randint(0, 200)
        
        return BrowserFingerprint(
            user_agent=user_agent,
            viewport=viewport,
            timezone=timezone,
            locale="fr-FR",
            platform=platform,
            screen_resolution={"width": screen_width, "height": screen_height}
        )

    async def create_stealth_session(self, account_id: str, proxy_url: Optional[str] = None) -> BrowserSession:
        """Algorithm: Stealth Session Creation"""
        session_id = f"session_{account_id}_{int(time.time())}"
        
        try:
            # Step 1: Generate browser fingerprint
            fingerprint = self.generate_browser_fingerprint()

            # Step 2: Launch browser with stealth configuration
            playwright = await async_playwright().start()
            
            browser_args = [
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-software-rasterizer',
                '--disable-background-timer-throttling',
                '--disable-renderer-backgrounding',
                '--disable-backgrounding-occluded-windows',
                '--disable-features=TranslateUI',
                '--disable-ipc-flooding-protection',
                '--disable-blink-features=AutomationControlled',
                '--no-first-run',
                '--no-default-browser-check',
                '--disable-default-apps',
                '--disable-popup-blocking',
                '--disable-prompt-on-repost',
                '--disable-hang-monitor',
                '--disable-sync',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--disable-extensions-except',
                '--disable-extensions',
                '--disable-plugins-discovery',
                '--disable-preconnect',
                '--disable-print-preview'
            ]
            
            browser = await playwright.chromium.launch(
                headless=True,  # Set to False for debugging
                args=browser_args
            )

            # Step 3: Create context with fingerprint
            context_options = {
                'user_agent': fingerprint.user_agent,
                'viewport': fingerprint.viewport,
                'timezone_id': fingerprint.timezone,
                'locale': fingerprint.locale,
                'permissions': ['geolocation'],
                'geolocation': {'latitude': 48.8566, 'longitude': 2.3522},  # Paris coordinates
                'extra_http_headers': {
                    'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Upgrade-Insecure-Requests': '1'
                }
            }
            
            # Add proxy if provided
            if proxy_url:
                context_options['proxy'] = {'server': proxy_url}
            
            context = await browser.new_context(**context_options)

            # Step 4: Apply stealth measures
            await self.apply_stealth_measures(context, fingerprint)

            # Step 5: Create page and apply additional stealth
            page = await context.new_page()
            try:
                await page.set_default_navigation_timeout(90000)
                await page.set_default_timeout(45000)
            except Exception:
                pass
            await self.apply_page_stealth(page)

            session = BrowserSession(
                browser=browser,
                context=context,
                page=page,
                fingerprint=fingerprint,
                account_id=account_id,
                session_id=session_id,
                created_at=datetime.now()
            )
            
            self.active_sessions[session_id] = session
            logger.info(f"Created stealth browser session: {session_id}")
            
            return session
            
        except Exception as e:
            logger.error(f"Error creating stealth session: {e}")
            raise e

    async def apply_stealth_measures(self, context: BrowserContext, fingerprint: BrowserFingerprint):
        """Apply stealth measures to browser context"""
        
        # Override navigator properties
        stealth_script = f"""
        Object.defineProperty(navigator, 'webdriver', {{
            get: () => undefined,
        }});
        
        Object.defineProperty(navigator, 'platform', {{
            get: () => '{fingerprint.platform}',
        }});
        
        Object.defineProperty(navigator, 'languages', {{
            get: () => ['fr-FR', 'fr', 'en-US', 'en'],
        }});
        
        Object.defineProperty(navigator, 'plugins', {{
            get: () => [{{
                0: {{
                    type: "application/x-google-chrome-pdf",
                    suffixes: "pdf",
                    description: "Portable Document Format",
                    enabledPlugin: null
                }},
                description: "Portable Document Format",
                filename: "internal-pdf-viewer",
                length: 1,
                name: "Chrome PDF Plugin"
            }}],
        }});
        
        Object.defineProperty(screen, 'width', {{
            get: () => {fingerprint.screen_resolution['width']},
        }});
        
        Object.defineProperty(screen, 'height', {{
            get: () => {fingerprint.screen_resolution['height']},
        }});
        
        // Remove automation indicators
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
        
        // Override chrome runtime
        window.chrome = {{
            runtime: {{}}
        }};
        
        // Mock permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({{ state: Notification.permission }}) :
                originalQuery(parameters)
        );
        """
        
        await context.add_init_script(stealth_script)

    async def apply_page_stealth(self, page: Page):
        """Apply additional stealth measures to page"""
        
        # Set realistic headers
        await page.set_extra_http_headers({
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1'
        })
        
        # Do not block images or SVG on initial load to avoid breaking LinkedIn flows
        
        # Add random mouse movements
        await self.add_random_mouse_movements(page)

    async def add_random_mouse_movements(self, page: Page):
        """Add random mouse movements to simulate human behavior"""
        try:
            # Move mouse to random positions
            for _ in range(random.randint(2, 5)):
                x = random.randint(100, 800)
                y = random.randint(100, 600)
                await page.mouse.move(x, y)
                await asyncio.sleep(random.uniform(0.1, 0.3))
        except Exception as e:
            logger.warning(f"Error adding mouse movements: {e}")

    async def human_delay(self, min_ms: int = 100, max_ms: int = 500):
        """Add human-like delay"""
        delay = random.uniform(min_ms, max_ms) / 1000
        await asyncio.sleep(delay)

    async def human_type(self, page: Page, selector: str, text: str):
        """Type text with human-like timing"""
        element = await page.wait_for_selector(selector, timeout=10000)
        
        # Clear existing text
        await element.click()
        await page.keyboard.press('Control+a')
        await self.human_delay(50, 150)
        
        # Type character by character with random delays
        for char in text:
            await page.keyboard.type(char)
            await asyncio.sleep(random.uniform(0.05, 0.15))
        
        await self.human_delay(200, 500)

    async def human_click(self, page: Page, selector: str):
        """Click with human-like behavior"""
        element = await page.wait_for_selector(selector, timeout=10000)
        
        # Get element position
        box = await element.bounding_box()
        if box:
            # Click at random position within element
            x = box['x'] + random.uniform(0.2, 0.8) * box['width']
            y = box['y'] + random.uniform(0.2, 0.8) * box['height']
            
            # Move mouse to position first
            await page.mouse.move(x, y)
            await self.human_delay(100, 300)
            
            # Click
            await page.mouse.click(x, y)
            await self.human_delay(200, 500)
        else:
            # Fallback to element click
            await element.click()
            await self.human_delay(200, 500)

    async def human_scroll(self, page: Page, distance: int = 300):
        """Scroll with human-like behavior"""
        # Random scroll distance
        actual_distance = distance + random.randint(-50, 50)
        
        # Scroll in chunks
        chunks = random.randint(3, 6)
        chunk_size = actual_distance // chunks
        
        for _ in range(chunks):
            await page.mouse.wheel(0, chunk_size)
            await asyncio.sleep(random.uniform(0.1, 0.3))
        
        await self.human_delay(500, 1000)

    async def navigate_with_human_timing(self, page: Page, url: str):
        """Navigate to URL with human-like timing"""
        try:
            # Add random delay before navigation
            await self.human_delay(1000, 3000)
            
            # Navigate
            response = await page.goto(url, wait_until='domcontentloaded', timeout=60000)
            
            # Wait for page to stabilize
            await self.human_delay(2000, 4000)
            
            # Add some random mouse movements
            await self.add_random_mouse_movements(page)
            
            return response
            
        except Exception as e:
            logger.error(f"Error navigating to {url}: {e}")
            raise e

    async def wait_for_page_ready(self, page: Page):
        """Wait for page to be ready with human-like patience"""
        try:
            # Wait for network to be idle
            await page.wait_for_load_state('networkidle', timeout=15000)
            
            # Additional wait for dynamic content
            await self.human_delay(1000, 2000)
            
            # Check if page is interactive
            ready_state = await page.evaluate('document.readyState')
            if ready_state != 'complete':
                await page.wait_for_load_state('load', timeout=10000)
            
        except Exception as e:
            logger.warning(f"Page ready check failed: {e}")

    def calculate_detection_risk(self, session: BrowserSession, recent_actions: List[ActionResult]) -> float:
        """Calculate detection risk based on session and actions"""
        risk_score = 0.0
        
        # Session age factor (newer sessions are riskier)
        session_age = (datetime.now() - session.created_at).total_seconds() / 3600  # hours
        if session_age < 0.5:  # Less than 30 minutes
            risk_score += 0.3
        elif session_age < 2:  # Less than 2 hours
            risk_score += 0.1
        
        # Action frequency factor
        if len(recent_actions) > 10:  # More than 10 actions recently
            risk_score += 0.2
        
        # Failed actions factor
        failed_actions = sum(1 for action in recent_actions if not action.success)
        if failed_actions > 2:
            risk_score += 0.3
        
        # Time pattern analysis (too regular = suspicious)
        if len(recent_actions) >= 3:
            time_intervals = []
            for i in range(1, len(recent_actions)):
                if hasattr(recent_actions[i], 'timestamp') and hasattr(recent_actions[i-1], 'timestamp'):
                    interval = recent_actions[i].timestamp - recent_actions[i-1].timestamp
                    time_intervals.append(interval)
            
            if time_intervals:
                avg_interval = sum(time_intervals) / len(time_intervals)
                # If intervals are too regular (low variance), increase risk
                variance = sum((x - avg_interval) ** 2 for x in time_intervals) / len(time_intervals)
                if variance < 1:  # Very regular timing
                    risk_score += 0.2
        
        return min(1.0, risk_score)

    async def close_session(self, session_id: str):
        """Close browser session"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            try:
                await session.page.close()
                await session.context.close()
                await session.browser.close()
                del self.active_sessions[session_id]
                logger.info(f"Closed browser session: {session_id}")
            except Exception as e:
                logger.error(f"Error closing session {session_id}: {e}")

    async def get_session(self, session_id: str) -> Optional[BrowserSession]:
        """Get active browser session"""
        return self.active_sessions.get(session_id)

    async def cleanup_old_sessions(self, max_age_hours: int = 4):
        """Cleanup old browser sessions"""
        current_time = datetime.now()
        sessions_to_close = []
        
        for session_id, session in self.active_sessions.items():
            age = (current_time - session.created_at).total_seconds() / 3600
            if age > max_age_hours:
                sessions_to_close.append(session_id)
        
        for session_id in sessions_to_close:
            await self.close_session(session_id)
        
        logger.info(f"Cleaned up {len(sessions_to_close)} old browser sessions")

# Global browser manager instance
browser_manager = StealthBrowserManager()

async def get_browser_manager() -> StealthBrowserManager:
    """Get the global browser manager instance"""
    return browser_manager

