import aiohttp
import asyncio
import logging
import random
import time
from dataclasses import dataclass
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

class ProxyType(Enum):
    RESIDENTIAL = "residential"
    DATACENTER = "datacenter"

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

@dataclass
class ProxyInfo:
    """Proxy information structure"""
    url: str
    session_id: str
    proxy_type: ProxyType
    country: str
    city: Optional[str]
    expires_at: datetime
    performance_score: float = 0.0

@dataclass
class ProxyAssignment:
    """Proxy assignment result"""
    account_id: str
    proxy_url: str
    session_id: str
    expires_at: datetime
    success: bool
    error_message: Optional[str] = None

@dataclass
class ProxyPerformance:
    """Proxy performance metrics"""
    response_time: float  # milliseconds
    success_rate: float
    uptime: float
    last_tested: datetime

class ProxyRotationManager:
    """
    Manages residential proxy lifecycle for anti-detection

    Algorithm Flow:
    1. Select optimal proxy based on account history
    2. Test proxy connectivity and performance
    3. Assign proxy to account with session affinity
    4. Monitor proxy performance and rotate on failure
    5. Maintain proxy pool health
    """

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.base_url = "proxy.geonode.io"
        self.port = 9000
        self.session = None
        self.proxy_pool: Dict[str, ProxyInfo] = {}
        self.account_assignments: Dict[str, ProxyInfo] = {}
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    def generate_session_id(self) -> str:
        """Generate unique session ID for proxy rotation"""
        timestamp = int(time.time())
        random_suffix = random.randint(1000, 9999)
        # GeoNode expects username suffix as '-session-<id>'; avoid embedding 'session_' again in the id
        return f"{timestamp}_{random_suffix}"

    def _build_auth_username(self, session_id: Optional[str] = None, country_code: Optional[str] = None, proxy_type: Optional[ProxyType] = None) -> str:
        """Construct GeoNode auth username with optional type/country/session.

        Examples:
        - baseuser + type + session -> baseuser-type-residential-session-<id>
        - baseuser + type + FR + session -> baseuser-type-residential-country-fr-session-<id>
        """
        base_username = self.username
        idx = base_username.find('-session')
        if idx != -1:
            base_username = base_username[:idx]
        segments = [base_username]
        if proxy_type == ProxyType.RESIDENTIAL:
            segments.append("type-residential")
        elif proxy_type == ProxyType.DATACENTER:
            segments.append("type-datacenter")
        # For now, do NOT append country or session to match provider format
        if country_code:
            pass
        if session_id:
            pass
        auth_username = "-".join(segments)
        return auth_username

    async def analyze_account_risk(self, account_id: str) -> RiskLevel:
        """Analyze account risk profile"""
        # In a real implementation, this would analyze:
        # - Account age and activity
        # - Previous detection incidents
        # - Current automation frequency
        # - LinkedIn response patterns
        
        # For now, return a random risk level for demonstration
        risk_levels = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH]
        weights = [0.6, 0.3, 0.1]  # Favor low risk
        
        risk = random.choices(risk_levels, weights=weights)[0]
        logger.info(f"Account {account_id} risk level: {risk.value}")
        return risk

    async def select_residential_proxy(self) -> ProxyInfo:
        """Select residential proxy for high-risk accounts"""
        session_id = self.generate_session_id()
        
        # Residential proxy configuration with de-duplicated '-session-'
        auth_username = self._build_auth_username(proxy_type=ProxyType.RESIDENTIAL)
        proxy_url = f"http://{auth_username}:{self.password}@{self.base_url}:{self.port}"
        logger.info(f"Selected residential proxy auth user: {auth_username}")
        
        proxy_info = ProxyInfo(
            url=proxy_url,
            session_id=session_id,
            proxy_type=ProxyType.RESIDENTIAL,
            country="FR",  # France for LinkedIn accounts
            city="Paris",
            expires_at=datetime.now() + timedelta(hours=1)  # 1 hour session
        )
        
        logger.info(f"Selected residential proxy: {session_id}")
        return proxy_info

    async def select_datacenter_proxy(self) -> ProxyInfo:
        """Select datacenter proxy for low-risk accounts"""
        session_id = self.generate_session_id()
        
        # Datacenter proxy configuration with de-duplicated '-session-'
        auth_username = self._build_auth_username(proxy_type=ProxyType.DATACENTER)
        proxy_url = f"http://{auth_username}:{self.password}@{self.base_url}:{self.port}"
        logger.info(f"Selected datacenter proxy auth user: {auth_username}")
        
        proxy_info = ProxyInfo(
            url=proxy_url,
            session_id=session_id,
            proxy_type=ProxyType.DATACENTER,
            country="FR",
            city="Paris",
            expires_at=datetime.now() + timedelta(hours=2)  # 2 hour session
        )
        
        logger.info(f"Selected datacenter proxy: {session_id}")
        return proxy_info

    async def select_backup_proxy(self) -> ProxyInfo:
        """Select backup proxy when primary fails"""
        # Always use residential for backup to ensure reliability
        return await self.select_residential_proxy()

    async def test_proxy_performance(self, proxy: ProxyInfo) -> ProxyPerformance:
        """Test proxy performance and connectivity"""
        start_time = time.time()
        
        try:
            # Test proxy by making a request to a test endpoint
            proxy_config = {
                'http': proxy.url,
                'https': proxy.url
            }
            
            import socket as _socket
            connector = aiohttp.TCPConnector(family=_socket.AF_INET, ttl_dns_cache=300, limit=20)
            timeout = aiohttp.ClientTimeout(total=12, connect=5, sock_connect=5, sock_read=7)
            
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            ) as test_session:
                
                # Use proxy for the request
                async with test_session.get(
                    'https://api.ipify.org',
                    params={'format': 'json'},
                    proxy=proxy.url
                ) as response:
                    
                    response_time = (time.time() - start_time) * 1000  # Convert to ms
                    
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Proxy test successful - IP: {data.get('ip')}, Response time: {response_time:.2f}ms")
                        
                        return ProxyPerformance(
                            response_time=response_time,
                            success_rate=1.0,
                            uptime=1.0,
                            last_tested=datetime.now()
                        )
                    else:
                        logger.warning(f"Proxy test failed with status: {response.status}")
                        return ProxyPerformance(
                            response_time=response_time,
                            success_rate=0.0,
                            uptime=0.0,
                            last_tested=datetime.now()
                        )
                        
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Proxy test error: {e}")
            
            return ProxyPerformance(
                response_time=response_time,
                success_rate=0.0,
                uptime=0.0,
                last_tested=datetime.now()
            )

    async def assign_proxy_to_account(self, account_id: str) -> ProxyAssignment:
        """Algorithm: Optimal Proxy Assignment"""
        try:
            # Step 1: Analyze account risk profile
            account_risk = await self.analyze_account_risk(account_id)

            # Step 2: Select proxy based on risk and geography
            if account_risk == RiskLevel.HIGH:
                proxy = await self.select_residential_proxy()
            else:
                proxy = await self.select_datacenter_proxy()

            # Step 3: Test proxy performance
            performance = await self.test_proxy_performance(proxy)

            if performance.response_time > 5000:  # 5 second timeout
                logger.warning(f"Proxy performance poor, selecting backup")
                proxy = await self.select_backup_proxy()
                performance = await self.test_proxy_performance(proxy)

            # Step 4: Store assignment
            self.account_assignments[account_id] = proxy
            self.proxy_pool[proxy.session_id] = proxy
            
            # Update proxy performance score
            proxy.performance_score = self.calculate_performance_score(performance)

            logger.info(f"Assigned proxy {proxy.session_id} to account {account_id}")
            
            return ProxyAssignment(
                account_id=account_id,
                proxy_url=proxy.url,
                session_id=proxy.session_id,
                expires_at=proxy.expires_at,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error assigning proxy to account {account_id}: {e}")
            return ProxyAssignment(
                account_id=account_id,
                proxy_url="",
                session_id="",
                expires_at=datetime.now(),
                success=False,
                error_message=str(e)
            )

    def calculate_performance_score(self, performance: ProxyPerformance) -> float:
        """Calculate overall performance score"""
        # Weight factors
        response_weight = 0.4
        success_weight = 0.4
        uptime_weight = 0.2
        
        # Normalize response time (lower is better)
        response_score = max(0, 1 - (performance.response_time / 5000))
        
        # Calculate weighted score
        score = (
            response_score * response_weight +
            performance.success_rate * success_weight +
            performance.uptime * uptime_weight
        )
        
        return min(1.0, max(0.0, score))

    async def rotate_proxy_for_account(self, account_id: str) -> ProxyAssignment:
        """Rotate proxy for an account"""
        logger.info(f"Rotating proxy for account {account_id}")
        
        # Remove old assignment
        if account_id in self.account_assignments:
            old_proxy = self.account_assignments[account_id]
            logger.info(f"Removing old proxy assignment: {old_proxy.session_id}")
            del self.account_assignments[account_id]
            
            if old_proxy.session_id in self.proxy_pool:
                del self.proxy_pool[old_proxy.session_id]
        
        # Assign new proxy
        return await self.assign_proxy_to_account(account_id)

    async def get_proxy_for_account(self, account_id: str) -> Optional[ProxyInfo]:
        """Get current proxy assignment for account"""
        proxy = self.account_assignments.get(account_id)
        
        if proxy:
            # Check if proxy is still valid
            if datetime.now() > proxy.expires_at:
                logger.info(f"Proxy expired for account {account_id}, rotating")
                assignment = await self.rotate_proxy_for_account(account_id)
                return self.account_assignments.get(account_id) if assignment.success else None
            
            return proxy
        
        return None

    async def release_proxy_for_account(self, account_id: str) -> bool:
        """Release proxy assignment for account"""
        try:
            if account_id in self.account_assignments:
                proxy = self.account_assignments[account_id]
                logger.info(f"Releasing proxy {proxy.session_id} for account {account_id}")
                
                del self.account_assignments[account_id]
                
                if proxy.session_id in self.proxy_pool:
                    del self.proxy_pool[proxy.session_id]
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error releasing proxy for account {account_id}: {e}")
            return False

    async def get_proxy_pool_status(self) -> Dict:
        """Get proxy pool status and health metrics"""
        total_proxies = len(self.proxy_pool)
        active_assignments = len(self.account_assignments)
        
        # Calculate average performance
        if self.proxy_pool:
            avg_performance = sum(p.performance_score for p in self.proxy_pool.values()) / total_proxies
        else:
            avg_performance = 0.0
        
        # Count by type
        residential_count = sum(1 for p in self.proxy_pool.values() if p.proxy_type == ProxyType.RESIDENTIAL)
        datacenter_count = sum(1 for p in self.proxy_pool.values() if p.proxy_type == ProxyType.DATACENTER)
        
        return {
            'total_proxies': total_proxies,
            'active_assignments': active_assignments,
            'average_performance': round(avg_performance, 3),
            'residential_proxies': residential_count,
            'datacenter_proxies': datacenter_count,
            'pool_utilization': round(active_assignments / max(1, total_proxies), 3)
        }

# Synchronous wrapper for easier integration
class ProxyRotationManagerSync:
    """Synchronous wrapper for ProxyRotationManager"""
    
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
    
    def assign_proxy_to_account(self, account_id: str) -> ProxyAssignment:
        """Assign proxy to account synchronously"""
        async def _assign_proxy():
            async with ProxyRotationManager(self.username, self.password) as manager:
                return await manager.assign_proxy_to_account(account_id)
        
        return asyncio.run(_assign_proxy())
    
    def get_proxy_pool_status(self) -> Dict:
        """Get proxy pool status synchronously"""
        async def _get_status():
            async with ProxyRotationManager(self.username, self.password) as manager:
                return await manager.get_proxy_pool_status()
        
        return asyncio.run(_get_status())

