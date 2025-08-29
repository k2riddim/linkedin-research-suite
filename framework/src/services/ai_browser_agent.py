import asyncio
import logging
import os
import random
from typing import Any, Dict, Optional

from .ai_config import get_skyvern_client, AIOperationType
from .session_manager import get_session_manager, SessionStatus
from .ai_error_handler import get_error_handler


logger = logging.getLogger(__name__)


class AIBrowserAgent:
    """
    Wrapper around Skyvern for AI-native browser control.
    Exposes a minimal API used by higher-level services.
    """

    def __init__(self, account_id: Optional[str] = None):
        self.account_id = account_id
        self.session_id: Optional[str] = None
        self.live_url: Optional[str] = None
        
        # Initialize managers
        self.session_manager = get_session_manager()
        self.error_handler = get_error_handler()
        self.skyvern_client = get_skyvern_client()

    async def initialize(self) -> bool:
        """Initialize a new browser session using the session manager."""
        try:
            logger.info(f"Initializing AI browser session for account {self.account_id}")
            
            # Create a new session via the session manager
            managed_session_id = await self.session_manager.create_session(
                account_id=self.account_id,
                operation_type=AIOperationType.BROWSER_AUTOMATION
            )
            
            session_meta = self.session_manager.get_session(managed_session_id)
            if not session_meta:
                raise Exception("Failed to retrieve session metadata after creation")
                
            self.session_id = managed_session_id
            self.live_url = session_meta.live_url
            
            self.session_manager.set_session_status(self.session_id, SessionStatus.ACTIVE)
            
            logger.info(f"AI Browser Agent initialized. session_id={self.session_id} live={self.live_url}")
            return True
            
        except Exception as exc:
            logger.error(f"Failed to initialize AIBrowserAgent: {exc}")
            self.error_handler.handle_error(
                str(exc),
                context={'operation': 'session_initialization'},
                account_id=self.account_id,
                operation_type='browser_automation'
            )
            return False

    async def run_task(self, prompt: str) -> Dict[str, Any]:
        """Run a task in the current browser session."""
        if not self.session_id:
            raise Exception("No active session")

        session_meta = self.session_manager.get_session(self.session_id)
        if not session_meta or not session_meta.skyvern_session_id:
            raise Exception("Session not found or skyvern_session_id is missing")

        try:
            task_result = await self.skyvern_client.run_task(
                browser_session_id=session_meta.skyvern_session_id,
                prompt=prompt
            )
            return task_result
        except Exception as e:
            logger.error(f"Error running task: {e}")
            self.error_handler.handle_error(
                str(e),
                context={'operation': 'run_task', 'prompt': prompt},
                account_id=self.account_id,
                operation_type='browser_automation'
            )
            raise

    async def navigate_to_linkedin(self) -> bool:
        """Navigate to LinkedIn using a Skyvern task."""
        try:
            if not self.session_id:
                logger.warning("No active session; skipping AI browser navigation")
                return False

            logger.info("Navigating to LinkedIn homepage...")
            
            result = await self.run_task(prompt="Navigate to https://www.linkedin.com")
            
            if result and result.get('success'):
                logger.info("Successfully navigated to LinkedIn")
                return True
            else:
                logger.error(f"Navigation to LinkedIn failed: {result}")
                return False

        except Exception as exc:
            logger.error(f"Failed to navigate to LinkedIn: {exc}")
            return False

    async def get_live_stream_url(self) -> Optional[str]:
        return self.live_url

    async def cleanup(self) -> None:
        """Clean up the browser session."""
        try:
            if self.session_id:
                logger.info(f"Cleaning up AI browser session: {self.session_id}")
                self.session_manager.close_session(self.session_id)
                self.session_id = None
                self.live_url = None
        except Exception as e:
            logger.error(f"Error during AIBrowserAgent cleanup: {e}")
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


