import aiohttp
import asyncio
import logging
import random
import string
import socket
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class EmailResult:
    """Result of email creation process"""
    email_address: str
    password: str
    success: bool
    error_message: Optional[str] = None

@dataclass
class EmailMessage:
    """Email message structure"""
    sender: str
    subject: str
    body: str
    received_at: datetime
    verification_link: Optional[str] = None
    verification_code: Optional[str] = None

class EmailCreationError(Exception):
    """Raised when email creation fails"""
    pass

class EmailVerificationManager:
    """
    Manages temporary email lifecycle for LinkedIn registration

    Algorithm Flow:
    1. Generate realistic email pattern
    2. Create email address on available domain
    3. Monitor inbox for LinkedIn verification
    4. Extract verification link or code
    5. Handle multiple verification attempts
    """

    def __init__(self, api_key: str):
        # EmailOnDeck PRO API uses 'token' and 'act' parameters, returns text responses for most actions
        self.api_key = api_key
        self.base_url = "https://api.emailondeck.com/api.php"
        self.session = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        connector = aiohttp.TCPConnector(family=socket.AF_INET, ttl_dns_cache=300, limit=20)
        timeout = aiohttp.ClientTimeout(total=15, connect=5, sock_connect=5, sock_read=10)
        self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def get_available_domains(self, order: str = "alpha_asc") -> List[str]:
        """Get list of available email domains using PRO API (text response)."""
        last_error = None
        for attempt in range(1, 4):
            try:
                params = {
                    'token': self.api_key,
                    'act': 'list_email_domains',
                    'order': order
                }
                async with self.session.get(self.base_url, params=params) as response:
                    text = await response.text()
                    if text.startswith('success:'):
                        csv_part = text[len('success:'):].strip()
                        domains = [d.strip() for d in csv_part.split(',') if d.strip()]
                        logger.info(f"Available domains: {len(domains)}")
                        return domains
                    elif text.startswith('error:'):
                        logger.error(f"list_email_domains error (status={response.status}): {text}")
                        return []
                    else:
                        logger.error(f"Unexpected response for list_email_domains (status={response.status}): {text[:200]}")
                        return []
            except Exception as e:
                last_error = e
                logger.error(f"Error getting domains (attempt {attempt}/3): {e}")
                await asyncio.sleep(min(2 ** attempt, 5))
        logger.error(f"Giving up fetching domains after retries: {last_error}")
        return []

    def generate_secure_password(self, length: int = 12) -> str:
        """Generate secure password"""
        characters = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(random.choice(characters) for _ in range(length))
        return password

    async def create_linkedin_email(self, first_name: str, last_name: str) -> EmailResult:
        """Create a realistic email via PRO API (create_email)."""
        try:
            def sanitize_handle(s: str) -> str:
                import re
                s = s.lower()
                s = re.sub(r"[^a-z0-9]", "", s)  # alphanumeric only
                return s

            # Step 1: Generate handles
            base_first = sanitize_handle(first_name)
            base_last = sanitize_handle(last_name)
            handles = [
                f"{base_first}{base_last}",
                f"{base_first}{base_last}{random.randint(10,99)}",
                f"{base_first[0]}{base_last}{random.randint(100,999)}"
            ]

            # Step 2: Available domains
            domains = await self.get_available_domains()
            if not domains:
                domains = ['emailondeck.com', 'guerrillamail.com', 'tempmail.org']

            # Step 3: Try combinations
            for handle in handles:
                for domain in domains[:5]:
                    created_email = await self.create_email_address(handle, domain)
                    if created_email:
                        return EmailResult(
                            email_address=created_email,
                            password=self.generate_secure_password(),
                            success=True
                        )

            # Final fallback: let API auto-generate handle and domain
            created_email = await self.create_email_address("", "")
            if created_email:
                return EmailResult(
                    email_address=created_email,
                    password=self.generate_secure_password(),
                    success=True
                )
                

            raise EmailCreationError("Could not create email address")
        except Exception as e:
            logger.error(f"Error creating LinkedIn email: {e}")
            return EmailResult(
                email_address="",
                password="",
                success=False,
                error_message=str(e)
            )

    async def create_email_address(self, handle: str, domain: str) -> Optional[str]:
        """Create email address using PRO API (text response).

        Returns the created email address on success, otherwise None.
        """
        last_error = None
        for attempt in range(1, 3):
            try:
                params = {
                    'token': self.api_key,
                    'act': 'create_email'
                }
                # Omit empty values to allow provider auto-selection
                if handle:
                    params['handle'] = handle
                if domain:
                    params['domain'] = domain
                async with self.session.get(self.base_url, params=params) as response:
                    text = await response.text()
                    if text.startswith('success:'):
                        created_email = text[len('success:'):].strip()
                        logger.info(f"Created email address: {created_email}")
                        return created_email or None
                    # Fallback: some providers prefer POST, try once on server error or empty response
                    if response.status >= 500 or not text.strip():
                        try:
                            async with self.session.post(self.base_url, data=params) as post_resp:
                                post_text = await post_resp.text()
                                if post_text.startswith('success:'):
                                    created_email = post_text[len('success:'):].strip()
                                    logger.info(f"Created email address (POST): {created_email}")
                                    return created_email or None
                                logger.warning(f"create_email POST failed (status={post_resp.status}) for {handle or '<auto>'}@{domain or '<auto>'}: {post_text}")
                        except Exception as pe:
                            logger.error(f"Error during create_email POST fallback: {pe}")
                    logger.warning(f"create_email failed (status={response.status}) for {handle or '<auto>'}@{domain or '<auto>'}: {text}")
                    return None
            except Exception as e:
                last_error = e
                logger.error(f"Error creating email {handle}@{domain} (attempt {attempt}/2): {e}")
                await asyncio.sleep(min(2 ** attempt, 5))
        logger.error(f"Giving up creating email after retries: {last_error}")
        return None

    async def check_inbox(self, email: str) -> List[EmailMessage]:
        """Check inbox via view_email_headers (JSON on success)."""
        try:
            params = {
                'token': self.api_key,
                'act': 'view_email_headers',
                'email_address': email
            }
            async with self.session.get(self.base_url, params=params) as response:
                # Read once and try JSON parse, then fallback to text markers
                content = await response.text()
                try:
                    import json as _json
                    data = _json.loads(content)
                    messages = []
                    # Expect a list of headers with msg_id
                    for msg in data if isinstance(data, list) else data.get('messages', []):
                        message = EmailMessage(
                            sender=msg.get('from', ''),
                            subject=msg.get('subject', ''),
                            body='',
                            received_at=datetime.fromisoformat(msg.get('received')) if msg.get('received') else datetime.now(),
                            )
                        # Fetch raw email to parse body
                        msg_id = msg.get('msg_id') or msg.get('id')
                        if msg_id:
                            raw = await self.view_raw_email(msg_id)
                            if raw:
                                message.body = raw
                                message.verification_link = self.extract_verification_link(raw)
                                message.verification_code = self.extract_verification_code(raw)
                        messages.append(message)
                    return messages
                except Exception:
                    # Fallback: check text markers
                    if content.startswith('success:') and 'no messages found' in content.lower():
                        return []
                    logger.error(f"Unexpected inbox response: {content[:200]}")
                    return []
        except Exception as e:
            logger.error(f"Error checking inbox for {email}: {e}")
            return []

    def extract_verification_link(self, email_body: str) -> Optional[str]:
        """Extract verification link from email body"""
        import re
        
        # Common LinkedIn verification link patterns
        patterns = [
            r'https://www\.linkedin\.com/checkpoint/challenge/[^\s<>"]+',
            r'https://www\.linkedin\.com/e/[^\s<>"]+',
            r'https://www\.linkedin\.com/comm/[^\s<>"]+',
            r'href=["\']([^"\']*linkedin[^"\']*verify[^"\']*)["\']',
            r'href=["\']([^"\']*verify[^"\']*linkedin[^"\']*)["\']'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, email_body, re.IGNORECASE)
            if match:
                link = match.group(1) if 'href' in pattern else match.group(0)
                logger.info(f"Extracted verification link: {link}")
                return link
        
        return None

    def extract_verification_code(self, email_body: str) -> Optional[str]:
        """Extract verification code from email body"""
        import re
        
        # Common verification code patterns
        patterns = [
            r'verification code[:\s]*(\d{4,8})',
            r'confirm[:\s]*(\d{4,8})',
            r'code[:\s]*(\d{4,8})',
            r'pin[:\s]*(\d{4,8})',
            r'\b(\d{6})\b',  # 6-digit standalone code
            r'\b(\d{4})\b'   # 4-digit standalone code
        ]
        
        for pattern in patterns:
            match = re.search(pattern, email_body, re.IGNORECASE)
            if match:
                code = match.group(1)
                logger.info(f"Extracted verification code: {code}")
                return code
        
        return None

    async def wait_for_linkedin_verification(self, email: str, timeout: int = 300) -> Optional[EmailMessage]:
        """Wait for LinkedIn verification email using view_email_headers + view_raw_email."""
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=timeout)
        logger.info(f"Waiting for LinkedIn verification email on {email} (timeout: {timeout}s)")
        while datetime.now() < end_time:
            try:
                messages = await self.check_inbox(email)
                for message in messages:
                    if self.is_linkedin_verification_email(message):
                        logger.info(f"LinkedIn verification email received: {message.subject}")
                        return message
                await asyncio.sleep(10)
            except Exception as e:
                logger.error(f"Error while waiting for verification email: {e}")
                await asyncio.sleep(15)
        logger.warning(f"LinkedIn verification email not received within {timeout} seconds")
        return None

    def is_linkedin_verification_email(self, message: EmailMessage) -> bool:
        """Check if message is a LinkedIn verification email"""
        linkedin_indicators = [
            'linkedin' in message.sender.lower(),
            'linkedin' in message.subject.lower(),
            'verify' in message.subject.lower(),
            'confirm' in message.subject.lower(),
            'activation' in message.subject.lower(),
            message.verification_link is not None,
            message.verification_code is not None
        ]
        
        return any(linkedin_indicators)

    async def delete_email(self, email: str) -> bool:
        """Delete email address via PRO API (text response)."""
        try:
            params = {
                'token': self.api_key,
                'act': 'delete_email',
                'email_address': email
            }
            async with self.session.get(self.base_url, params=params) as response:
                text = await response.text()
                if text.startswith('success'):
                    logger.info(f"Deleted email address: {email}")
                    return True
                logger.error(f"Failed to delete email: {text}")
                return False
        except Exception as e:
            logger.error(f"Error deleting email {email}: {e}")
            return False

    async def view_raw_email(self, msg_id: str) -> Optional[str]:
        """Fetch raw email contents for a message id."""
        try:
            params = {
                'token': self.api_key,
                'act': 'view_raw_email',
                'msg_id': msg_id
            }
            async with self.session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    return await response.text()
                return None
        except Exception as e:
            logger.error(f"Error fetching raw email {msg_id}: {e}")
            return None

# Synchronous wrapper for easier integration
class EmailVerificationManagerSync:
    """Synchronous wrapper for EmailVerificationManager"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def create_linkedin_email(self, first_name: str, last_name: str) -> EmailResult:
        """Create LinkedIn email synchronously"""
        async def _create_email():
            async with EmailVerificationManager(self.api_key) as manager:
                return await manager.create_linkedin_email(first_name, last_name)
        
        return asyncio.run(_create_email())
    
    def wait_for_verification(self, email: str, timeout: int = 300) -> Optional[EmailMessage]:
        """Wait for verification email synchronously"""
        async def _wait_for_verification():
            async with EmailVerificationManager(self.api_key) as manager:
                return await manager.wait_for_linkedin_verification(email, timeout)
        
        return asyncio.run(_wait_for_verification())

