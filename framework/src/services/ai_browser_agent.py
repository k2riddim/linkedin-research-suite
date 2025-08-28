import asyncio
import logging
import os
import random
from typing import Any, Dict, Optional


logger = logging.getLogger(__name__)


# Optional dependency; resolve Stagehand dynamically to support varying package names
Stagehand = None  # type: ignore
StagehandConfig = None  # type: ignore
_stagehand_import_error = None
try:
    from stagehand import Stagehand as _SH, StagehandConfig as _SHC  # type: ignore
    Stagehand, StagehandConfig = _SH, _SHC
except Exception as _e1:  # pragma: no cover
    _stagehand_import_error = _e1
    try:
        # Alternate package names (defensive)
        import importlib
        _mod = importlib.import_module('stagehand')
        Stagehand = getattr(_mod, 'Stagehand', None)
        StagehandConfig = getattr(_mod, 'StagehandConfig', None)
    except Exception as _e2:  # pragma: no cover
        if Stagehand is None or StagehandConfig is None:
            _stagehand_import_error = _e2


class AIBrowserAgent:
    """
    Thin wrapper around Stagehand+Browserbase for AI-native browser control.
    Exposes a minimal API used by higher-level services.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.session_id: Optional[str] = None
        self.live_url: Optional[str] = None

    async def initialize(self) -> bool:
        """Initialize Stagehand session via Node.js server with proper OpenAI API key configuration."""
        try:

            api_key = self.config.get('browserbase_api_key') or os.getenv('BROWSERBASE_API_KEY')
            project_id = self.config.get('browserbase_project_id') or os.getenv('BROWSERBASE_PROJECT_ID')
            env_name = self.config.get('stagehand_env') or os.getenv('STAGEHAND_ENV', 'BROWSERBASE')
            headless = str(self.config.get('stagehand_headless') or os.getenv('STAGEHAND_HEADLESS', 'true')).lower() == 'true'
            debug_dom = str(self.config.get('stagehand_debug_dom') or os.getenv('STAGEHAND_DEBUG_DOM', 'false')).lower() == 'true'
            # Model config (OpenAI by default)
            model_api_key = self.config.get('openai_api_key') or os.getenv('OPENAI_API_KEY')
            model_name = self.config.get('openai_model') or os.getenv('OPENAI_MODEL', 'gpt-4o')

            if not api_key or not project_id:
                logger.error("Browserbase credentials are missing.")
                return False
            if not model_api_key:
                logger.error("OpenAI model_api_key is missing (set OPENAI_API_KEY).")
                return False

            # Check if Stagehand server is available
            server_url = self.config.get('stagehand_server_url') or os.getenv('STAGEHAND_API_URL', 'http://localhost:8081')
            
            # Test if server is reachable
            import aiohttp
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{server_url}/health", timeout=5) as response:
                        if response.status != 200:
                            raise Exception(f"Server responded with status {response.status}")
            except Exception as server_error:
                logger.error(f"Stagehand server not available at {server_url}: {server_error}")
                logger.error("AIBrowserAgent initialization failed - Stagehand server is required")
                return False

            # Create session via Node.js server with OpenAI API key in headers
            session_data = {
                'env': env_name,
                'headless': headless,
                'debugDom': debug_dom,
                'modelName': model_name
            }
            
            headers = {
                'x-bb-api-key': api_key,
                'x-bb-project-id': project_id,
                'x-model-api-key': model_api_key,
                'Content-Type': 'application/json'
            }

            # Check existing sessions and cleanup if needed to prevent rate limiting
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{server_url}/sessions", timeout=5) as response:
                        if response.status == 200:
                            sessions_data = await response.json()
                            session_count = sessions_data.get('count', 0)
                            if session_count >= 2:  # Browserbase likely has session limits
                                logger.info(f"Found {session_count} existing sessions, cleaning up to prevent rate limits...")
                                async with session.post(f"{server_url}/sessions/cleanup", timeout=10) as cleanup_response:
                                    if cleanup_response.status == 200:
                                        cleanup_result = await cleanup_response.json()
                                        logger.info(f"Cleanup completed: {cleanup_result.get('message', 'Done')}")
            except Exception as cleanup_error:
                logger.warning(f"Session cleanup failed, proceeding anyway: {cleanup_error}")
            
            # Add initial delay to prevent rate limiting
            await asyncio.sleep(random.uniform(2.0, 5.0))
            
            # Initialize session via HTTP with retry logic for rate limiting
            max_retries = 3
            retry_delay = 10  # seconds
            
            for attempt in range(max_retries):
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            f"{server_url}/sessions/start", 
                            json=session_data,
                            headers=headers,
                            timeout=30
                        ) as response:
                            if response.status == 200:
                                result = await response.json()
                                if result.get('success'):
                                    self.session_id = result.get('sessionId')
                                    self.live_url = result.get('liveUrl')
                                    
                                    # Store configuration for later use
                                    self.config.update({
                                        'browserbase_api_key': api_key,
                                        'browserbase_project_id': project_id,
                                        'openai_api_key': model_api_key,
                                        'openai_model': model_name,
                                        'stagehand_server_url': server_url
                                    })
                                    
                                    logger.info("AI Browser Agent initialized via Node.js server. session_id=%s live=%s", self.session_id, self.live_url)
                                    return True
                                else:
                                    raise Exception(f"Session creation failed: {result.get('error', 'Unknown error')}")
                            else:
                                error_text = await response.text()
                                raise Exception(f"HTTP {response.status}: {error_text}")
                    
                except Exception as init_error:
                    error_msg = str(init_error)
                    
                    # Check for rate limiting (429) or server errors (5xx)
                    if ("429" in error_msg or "rate limit" in error_msg.lower() or 
                        "500" in error_msg or "502" in error_msg or "503" in error_msg or
                        "too many requests" in error_msg.lower()):
                        
                        if attempt < max_retries - 1:
                            # For 429 errors, use longer waits with exponential backoff
                            if "429" in error_msg:
                                base_wait = 30 + (attempt * 30)  # 30s, 60s, 90s for 429 errors
                            else:
                                base_wait = retry_delay * (2 ** attempt)
                            
                            jitter = random.uniform(0.8, 1.2)
                            wait_time = base_wait * jitter
                            logger.warning(f"Rate limited or server error (attempt {attempt + 1}/{max_retries}). Retrying in {wait_time:.1f}s: {error_msg}")
                            
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            logger.error(f"Failed to initialize after {max_retries} attempts due to rate limiting: {error_msg}")
                            return False
                    else:
                        # Non-retryable error
                        logger.error(f"AIBrowserAgent initialization failed: {error_msg}")
                        return False
            
            return False
            
        except Exception as exc:  # pragma: no cover - integration branch
            logger.error("Failed to initialize AIBrowserAgent: %s", exc)
            return False

    async def _make_stagehand_request(self, method: str, data: dict) -> dict:
        """Make HTTP request to Stagehand server."""
        import aiohttp
        
        if not self.session_id:
            raise Exception("No active session")
        
        server_url = self.config.get('stagehand_server_url') or os.getenv('STAGEHAND_API_URL', 'http://localhost:8081')
        url = f"{server_url}/sessions/{self.session_id}/{method}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, timeout=120) as response:
                    # Always try to parse as JSON first (server returns JSON for both success and error)
                    try:
                        response_data = await response.json()
                    except Exception as json_error:
                        # Fallback to text if JSON parsing fails
                        response_text = await response.text()
                        logger.error(f"Failed to parse JSON response: {json_error}. Raw response: {response_text}")
                        raise Exception(f"Failed to parse server response: {response_text}")
                    
                    if response.status == 200:
                        return response_data
                    else:
                        # Server returned an error but in JSON format
                        error_msg = response_data.get('error', 'Unknown error')
                        error_details = response_data.get('details', '')
                        full_error = f"{error_msg}" + (f" | Details: {error_details}" if error_details else "")
                        
                        # Check if it's a session closed error
                        if ('closed' in error_msg.lower() or 'terminated' in error_msg.lower() or 
                            'no longer available' in error_msg.lower()):
                            logger.warning(f"Session {self.session_id} appears to be closed/terminated: {error_msg}")
                            # Invalidate the session
                            self.session_id = None
                            self.live_url = None
                            raise Exception(f"Session closed: {error_msg}")
                        
                        # Log the detailed error for debugging
                        logger.error(f"Stagehand request failed: {method} -> {full_error}")
                        raise Exception(f"Stagehand request failed: {response.status} - {error_msg}")
                        
        except aiohttp.ClientError as client_error:
            logger.error(f"HTTP client error for {method}: {client_error}")
            raise Exception(f"HTTP request failed: {client_error}")

    async def navigate_to_linkedin(self) -> bool:
        """Navigate to LinkedIn with human-like dwell times and robust timeout handling."""
        try:
            if not self.session_id:
                logger.warning("No active session; skipping AI browser navigation")
                return False  # Return False to indicate failure
            
            logger.info("Navigating to LinkedIn homepage...")
            
            # Navigate with longer timeout and retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Use Stagehand's HTTP interface instead of direct page access
                    result = await self._make_stagehand_request('goto', {
                        'url': 'https://www.linkedin.com',
                        'options': {
                            'timeout': 90000,  # 90 seconds
                            'waitUntil': 'networkidle'
                        }
                    })
                    
                    if result and result.get('success'):
                        logger.info("Successfully navigated to LinkedIn")
                        await asyncio.sleep(random.uniform(2.0, 4.0))  # Human-like pause
                        return True
                    else:
                        raise Exception(f"Navigation failed: {result}")
                        
                except Exception as nav_error:
                    if attempt < max_retries - 1:
                        wait_time = 5 * (attempt + 1)  # 5s, 10s, 15s
                        logger.warning(f"Navigation attempt {attempt + 1} failed, retrying in {wait_time}s: {nav_error}")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        raise nav_error
            
            return False
                        
        except Exception as exc:  # pragma: no cover - integration branch
            logger.error("Failed to navigate to LinkedIn: %s", exc)
            return False

    async def get_live_stream_url(self) -> Optional[str]:
        return self.live_url

    async def cleanup(self) -> None:
        """Clean up Browserbase session via Stagehand server."""
        try:
            if self.session_id:
                logger.info(f"Cleaning up Browserbase session: {self.session_id}")
                
                # Send explicit close request to Stagehand server
                try:
                    import aiohttp
                    server_url = self.config.get('stagehand_server_url') or os.getenv('STAGEHAND_API_URL', 'http://localhost:8081')
                    async with aiohttp.ClientSession() as session:
                        async with session.delete(f"{server_url}/sessions/{self.session_id}", timeout=5) as response:
                            if response.status == 200:
                                logger.info(f"✅ Browserbase session {self.session_id} closed successfully")
                            else:
                                logger.warning(f"Server cleanup returned status {response.status}")
                except Exception as e:
                    logger.warning(f"Could not confirm server-side cleanup for session {self.session_id}: {e}")
                
                # Reset session state
                self.session_id = None
                self.live_url = None
                
        except Exception as e:
            logger.error(f"Error during AIBrowserAgent cleanup: {e}")
        
    def __del__(self):
        """Ensure cleanup is called when object is destroyed."""
        if self.session_id:
            logger.warning(f"AIBrowserAgent destroyed without explicit cleanup for session {self.session_id}")
            # Note: Can't call async cleanup from __del__, but log the issue


