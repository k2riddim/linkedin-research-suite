import aiohttp
import asyncio
import logging
from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timedelta
import socket

logger = logging.getLogger(__name__)

@dataclass
class SMSResult:
    """Result of SMS verification process"""
    phone_number: str
    sms_code: Optional[str]
    activation_id: str
    success: bool
    error_message: Optional[str] = None

class InsufficientBalanceError(Exception):
    """Raised when account balance is insufficient"""
    pass

class SMSTimeoutError(Exception):
    """Raised when SMS verification times out"""
    pass

class SMSVerificationManager:
    """
    Manages SMS verification lifecycle using 5SIM API

    Algorithm Flow:
    1. Request French phone number
    2. Poll for SMS reception
    3. Extract verification code
    4. Complete activation or handle timeout
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://5sim.net/v1"
        self.session = None
        # Reasonable defaults to avoid long hangs on DNS/connect
        self._timeout = aiohttp.ClientTimeout(total=15, connect=5, sock_connect=5, sock_read=10)
        
    async def __aenter__(self):
        """Async context manager entry"""
        # Prefer IPv4 to avoid IPv6 resolution issues on constrained networks
        connector = aiohttp.TCPConnector(family=socket.AF_INET, ttl_dns_cache=300, limit=20)
        self.session = aiohttp.ClientSession(
            headers={'Authorization': f'Bearer {self.api_key}'},
            timeout=self._timeout,
            connector=connector
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def check_balance(self) -> Optional[float]:
        """Check account balance. Returns None on network error."""
        last_error = None
        for attempt in range(1, 4):
            try:
                async with self.session.get(f"{self.base_url}/user/profile") as response:
                    if response.status == 200:
                        data = await response.json()
                        balance = float(data.get('balance', 0))
                        logger.info(f"5SIM balance: {balance}")
                        return balance
                    else:
                        logger.error(f"Failed to check balance: {response.status}")
                        return None
            except Exception as e:
                last_error = e
                logger.error(f"Error checking balance (attempt {attempt}/3): {e}")
                await asyncio.sleep(min(2 ** attempt, 5))
        logger.error(f"Giving up fetching 5SIM balance after retries: {last_error}")
        return None

    async def get_french_number(self) -> SMSResult:
        """Algorithm: French Number Acquisition (non-blocking)

        Returns activation_id and phone_number immediately without polling for SMS.
        The caller should invoke poll_for_sms(activation_id) later when verification is needed.
        """
        try:
            # Step 1: Check balance
            balance = await self.check_balance()
            if balance is None:
                raise InsufficientBalanceError("5SIM balance unavailable (network error)")
            if balance < 0.12:  # Cost per French number
                raise InsufficientBalanceError(f"Insufficient balance: {balance}")

            # Step 2: Request French number for LinkedIn
            payload = {
                "country": "france",
                "product": "linkedin",
                "operator": "any"
            }

            async with self.session.get(
                f"{self.base_url}/user/buy/activation/{payload['country']}/{payload['operator']}/{payload['product']}"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    activation_id = data.get('id')
                    phone_number = data.get('phone')
                    
                    logger.info(f"Acquired French number: {phone_number} (ID: {activation_id})")

                    # Do NOT poll here. Defer SMS polling until verification stage.
                    return SMSResult(
                        phone_number=phone_number,
                        sms_code=None,
                        activation_id=activation_id,
                        success=True
                    )
                else:
                    error_msg = f"Failed to acquire number: {response.status}"
                    logger.error(error_msg)
                    return SMSResult(
                        phone_number="",
                        sms_code=None,
                        activation_id="",
                        success=False,
                        error_message=error_msg
                    )
                    
        except Exception as e:
            logger.error(f"Error acquiring French number: {e}")
            return SMSResult(
                phone_number="",
                sms_code=None,
                activation_id="",
                success=False,
                error_message=str(e)
            )

    async def poll_for_sms(self, activation_id: str, timeout: int = 300) -> Optional[str]:
        """Poll for SMS reception with timeout"""
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=timeout)
        
        logger.info(f"Polling for SMS on activation {activation_id} (timeout: {timeout}s)")
        
        while datetime.now() < end_time:
            try:
                async with self.session.get(f"{self.base_url}/user/check/{activation_id}") as response:
                    if response.status == 200:
                        data = await response.json()
                        status = data.get('status')
                        sms_code = data.get('sms')
                        
                        if status == 'RECEIVED' and sms_code:
                            logger.info(f"SMS received for activation {activation_id}: {sms_code}")
                            return self.extract_verification_code(sms_code)
                        elif status == 'FINISHED':
                            logger.warning(f"Activation {activation_id} finished without SMS")
                            return None
                        elif status == 'CANCELED':
                            logger.warning(f"Activation {activation_id} was canceled")
                            return None
                        
                        # Continue polling
                        await asyncio.sleep(5)  # Wait 5 seconds before next poll
                        
                    else:
                        logger.error(f"Error polling SMS: {response.status}")
                        await asyncio.sleep(10)  # Wait longer on error
                        
            except Exception as e:
                logger.error(f"Exception while polling SMS: {e}")
                await asyncio.sleep(10)
        
        logger.warning(f"SMS polling timeout for activation {activation_id}")
        raise SMSTimeoutError(f"SMS not received within {timeout} seconds")

    def extract_verification_code(self, sms_text: str) -> Optional[str]:
        """Extract verification code from SMS text"""
        import re
        
        # Common patterns for verification codes
        patterns = [
            r'\b(\d{6})\b',  # 6-digit code
            r'\b(\d{4})\b',  # 4-digit code
            r'code[:\s]*(\d+)',  # "code: 123456"
            r'verification[:\s]*(\d+)',  # "verification: 123456"
            r'confirm[:\s]*(\d+)',  # "confirm: 123456"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, sms_text, re.IGNORECASE)
            if match:
                code = match.group(1)
                logger.info(f"Extracted verification code: {code}")
                return code
        
        logger.warning(f"Could not extract verification code from SMS: {sms_text}")
        return None

    async def finish_activation(self, activation_id: str) -> bool:
        """Mark activation as finished"""
        try:
            async with self.session.get(f"{self.base_url}/user/finish/{activation_id}") as response:
                if response.status == 200:
                    logger.info(f"Finished activation {activation_id}")
                    return True
                else:
                    logger.error(f"Failed to finish activation {activation_id}: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Error finishing activation {activation_id}: {e}")
            return False

    async def cancel_activation(self, activation_id: str) -> bool:
        """Cancel activation"""
        try:
            async with self.session.get(f"{self.base_url}/user/cancel/{activation_id}") as response:
                if response.status == 200:
                    logger.info(f"Canceled activation {activation_id}")
                    return True
                else:
                    logger.error(f"Failed to cancel activation {activation_id}: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Error canceling activation {activation_id}: {e}")
            return False

    async def get_available_countries(self) -> list:
        """Get list of available countries"""
        try:
            async with self.session.get(f"{self.base_url}/guest/countries") as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    logger.error(f"Failed to get countries: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error getting countries: {e}")
            return []

    async def get_service_prices(self, country: str = "france") -> dict:
        """Get service prices for a country"""
        try:
            async with self.session.get(f"{self.base_url}/guest/prices") as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get(country, {})
                else:
                    logger.error(f"Failed to get prices: {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"Error getting prices: {e}")
            return {}

# Synchronous wrapper for easier integration
class SMSVerificationManagerSync:
    """Synchronous wrapper for SMSVerificationManager"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def get_french_number(self) -> SMSResult:
        """Get French number synchronously"""
        async def _get_number():
            async with SMSVerificationManager(self.api_key) as manager:
                return await manager.get_french_number()
        
        return asyncio.run(_get_number())
    
    def check_balance(self) -> float:
        """Check balance synchronously"""
        async def _check_balance():
            async with SMSVerificationManager(self.api_key) as manager:
                return await manager.check_balance()
        
        return asyncio.run(_check_balance())

