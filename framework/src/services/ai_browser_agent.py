import asyncio
import logging
import os
import random
from typing import Any, Dict, Optional

from .ai_config import get_ai_config, get_stagehand_client, AIOperationType
from .session_manager import get_session_manager, SessionStatus
from .ai_error_handler import get_error_handler


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

    def __init__(self, config: Optional[Dict[str, Any]] = None, account_id: Optional[str] = None):
        self.config = config or {}
        self.account_id = account_id
        self.session_id: Optional[str] = None
        self.live_url: Optional[str] = None
        
        # Initialize managers
        self.session_manager = get_session_manager()
        self.error_handler = get_error_handler()

    async def initialize(self) -> bool:
        """Initialize Stagehand session via Node.js server with comprehensive API key validation."""
        try:
            # Use centralized AI configuration
            ai_config = get_ai_config()
            stagehand_client = get_stagehand_client()
            
            # Get validated session configuration
            session_config = stagehand_client.get_session_config(AIOperationType.BROWSER_AUTOMATION)
            headers = stagehand_client.get_session_headers()
            
            logger.info("Initializing AI browser session with validated credentials")
            logger.info(f"Using model: {session_config['modelName']} with optimized settings")

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

            # Use validated session configuration

            # AGGRESSIVE cleanup to prevent Browserbase session limit issues
            try:
                # First, clean up any sessions in our Stagehand server
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{server_url}/sessions", timeout=5) as response:
                        if response.status == 200:
                            sessions_data = await response.json()
                            session_count = sessions_data.get('count', 0)
                            if session_count >= 1:  # Clean up ANY existing sessions for single-session Browserbase accounts
                                logger.info(f"Found {session_count} existing sessions, cleaning up to prevent rate limits...")
                                async with session.post(f"{server_url}/sessions/cleanup", timeout=10) as cleanup_response:
                                    if cleanup_response.status == 200:
                                        cleanup_result = await cleanup_response.json()
                                        logger.info(f"Stagehand cleanup completed: {cleanup_result.get('message', 'Done')}")
                
                # Also check for orphaned sessions directly in Browserbase
                bb_api_key = os.getenv('BROWSERBASE_API_KEY')
                if bb_api_key:
                    async with aiohttp.ClientSession() as session:
                        headers = {'x-bb-api-key': bb_api_key}
                        async with session.get('https://api.browserbase.com/v1/sessions', headers=headers, timeout=10) as response:
                            if response.status == 200:
                                bb_sessions = await response.json()
                                if isinstance(bb_sessions, dict) and 'data' in bb_sessions:
                                    active_sessions = [s for s in bb_sessions['data'] if s.get('status') in ['RUNNING', 'STARTING']]
                                    if active_sessions:
                                        logger.info(f"Found {len(active_sessions)} active Browserbase sessions, terminating them...")
                                        for bb_session in active_sessions:
                                            try:
                                                session_id = bb_session.get('id')
                                                async with session.delete(f'https://api.browserbase.com/v1/sessions/{session_id}', headers=headers, timeout=5) as del_response:
                                                    if del_response.status == 200:
                                                        logger.info(f"Terminated Browserbase session: {session_id}")
                                            except Exception as del_error:
                                                logger.warning(f"Failed to terminate Browserbase session: {del_error}")
                
                # Wait a moment for cleanup to complete
                await asyncio.sleep(2.0)
                
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
                            json=session_config,
                            headers=headers,
                            timeout=session_config.get('timeout', 30000) // 1000  # Convert from ms to seconds
                        ) as response:
                            if response.status == 200:
                                result = await response.json()
                                if result.get('success'):
                                    # Extract from data object (stagehand-server format)
                                    data = result.get('data', {})
                                    browserbase_session_id = data.get('sessionId')
                                    live_url = data.get('liveUrl')
                                    
                                    if browserbase_session_id and live_url:
                                        # Create session in session manager
                                        managed_session_id = self.session_manager.create_session(
                                            account_id=self.account_id,
                                            operation_type=AIOperationType.BROWSER_AUTOMATION,
                                            browserbase_session_id=browserbase_session_id,
                                            live_url=live_url,
                                            stagehand_server_url=server_url
                                        )
                                        
                                        # Set session as active
                                        self.session_manager.set_session_status(managed_session_id, SessionStatus.ACTIVE)
                                        
                                        # Store session details
                                        self.session_id = managed_session_id
                                        self.live_url = live_url
                                        
                                        # Store configuration for later use
                                        self.config.update({
                                            'ai_config_manager': ai_config,
                                            'stagehand_client': stagehand_client,
                                            'stagehand_server_url': server_url,
                                            'operation_type': AIOperationType.BROWSER_AUTOMATION,
                                            'browserbase_session_id': browserbase_session_id
                                        })
                                        
                                        logger.info("AI Browser Agent initialized. session_id=%s live=%s", self.session_id, self.live_url)
                                        return True
                                    else:
                                        raise Exception("Invalid session response - missing session ID or live URL")
                                else:
                                    raise Exception(f"Session creation failed: {result.get('error', 'Unknown error')}")
                            else:
                                error_text = await response.text()
                                raise Exception(f"HTTP {response.status}: {error_text}")
                    
                except Exception as init_error:
                    error_msg = str(init_error)
                    
                    # Use error handler for classification and recovery strategy
                    error_info = self.error_handler.handle_error(
                        error_msg,
                        context={
                            'attempt': attempt + 1,
                            'max_retries': max_retries,
                            'operation': 'session_initialization',
                            'server_url': server_url
                        },
                        account_id=self.account_id,
                        operation_type='browser_automation'
                    )
                    
                    # Check if retry is recommended
                    if (error_info['classification']['retry_recommended'] and 
                        attempt < max_retries - 1):
                        
                        # Use recommended retry delay
                        wait_time = error_info['classification']['retry_delay']
                        if error_info['error_type'] == 'rate_limit_exceeded':
                            # Special handling for rate limits
                            wait_time = 30 + (attempt * 30)  # 30s, 60s, 90s
                        
                        # Add jitter
                        jitter = random.uniform(0.8, 1.2)
                        final_wait = wait_time * jitter
                        
                        logger.warning(f"Retrying session initialization (attempt {attempt + 1}/{max_retries}) "
                                     f"in {final_wait:.1f}s. Error: {error_info['error_type']}")
                        
                        await asyncio.sleep(final_wait)
                        continue
                    else:
                        # Non-retryable error or max retries reached
                        logger.error(f"Failed to initialize after {max_retries} attempts: {error_info['error_type']}")
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
        """Clean up Browserbase session via Stagehand server and session manager."""
        try:
            if self.session_id:
                logger.info(f"Cleaning up AI browser session: {self.session_id}")
                
                # Get session details before cleanup
                session_meta = self.session_manager.get_session(self.session_id)
                browserbase_session_id = None
                
                if session_meta:
                    browserbase_session_id = session_meta.browserbase_session_id
                    
                    # Mark session for cleanup in session manager
                    self.session_manager.close_session(self.session_id)
                
                # Send explicit close request to Stagehand server if we have browserbase session ID
                if browserbase_session_id:
                    try:
                        import aiohttp
                        server_url = self.config.get('stagehand_server_url') or os.getenv('STAGEHAND_API_URL', 'http://localhost:8081')
                        async with aiohttp.ClientSession() as session:
                            async with session.delete(f"{server_url}/sessions/{browserbase_session_id}", timeout=5) as response:
                                if response.status == 200:
                                    logger.info(f"✅ Browserbase session {browserbase_session_id} closed successfully")
                                else:
                                    logger.warning(f"Server cleanup returned status {response.status}")
                    except Exception as e:
                        logger.warning(f"Could not confirm server-side cleanup for session {browserbase_session_id}: {e}")
                
                # Reset session state
                self.session_id = None
                self.live_url = None
                
        except Exception as e:
            logger.error(f"Error during AIBrowserAgent cleanup: {e}")
            # Use error handler
            self.error_handler.handle_error(
                str(e),
                context={'operation': 'session_cleanup'},
                account_id=self.account_id,
                operation_type='browser_automation'
            )
        
    def __del__(self):
        """Ensure cleanup is called when object is destroyed."""
        if self.session_id:
            logger.warning(f"AIBrowserAgent destroyed without explicit cleanup for session {self.session_id}")
            # Note: Can't call async cleanup from __del__, but log the issue


