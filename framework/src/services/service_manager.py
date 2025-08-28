import asyncio
import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from src.config import config
from src.services.fivesim import SMSVerificationManager, SMSResult
from src.services.emailondeck import EmailVerificationManager, EmailResult, EmailMessage
from src.services.geonode import ProxyRotationManager, ProxyAssignment
from src.socketio_bus import progress_queue

logger = logging.getLogger(__name__)

@dataclass
class ServiceHealth:
    """Service health status"""
    service_name: str
    is_healthy: bool
    last_check: datetime
    error_message: Optional[str] = None
    response_time: Optional[float] = None

@dataclass
class ResourceUsage:
    """Resource usage statistics"""
    sms_balance: float
    emails_created: int
    proxies_active: int
    total_cost: float
    last_updated: datetime

class ServiceManager:
    """
    Manages external service resources efficiently

    Algorithm Flow:
    1. Monitor service usage and costs
    2. Optimize resource allocation
    3. Handle rate limiting and quotas
    4. Implement resource pooling
    5. Manage failover strategies
    """

    def __init__(self):
        self.sms_manager = None
        self.email_manager = None
        self.proxy_manager = None
        self.service_health: Dict[str, ServiceHealth] = {}
        self.resource_usage = ResourceUsage(
            sms_balance=0.0,
            emails_created=0,
            proxies_active=0,
            total_cost=0.0,
            last_updated=datetime.now()
        )
        
    def _emit_enhanced(self, account_id: str, logs: list, current_step: Optional[str] = None, overall_progress: Optional[float] = None):
        """Emit enhanced progress update to the account-specific WebSocket room."""
        try:
            room = f"account_{account_id}"
            payload = {
                'recent_logs': logs,
            }
            if current_step:
                payload['current_step'] = { 'name': current_step, 'status': 'running' }
            if overall_progress is not None:
                payload['overall_progress'] = int(overall_progress)
            # Enqueue to Socket.IO drainer with room info
            data = dict(payload)
            data['_room'] = room
            try:
                progress_queue.put_nowait(data)
            except Exception:
                pass
        except Exception:
            # Do not raise errors from telemetry path
            pass

    async def __aenter__(self):
        """Initialize all service managers"""
        try:
            # Initialize SMS manager
            if config.external_services.fivesim_api_key:
                self.sms_manager = SMSVerificationManager(config.external_services.fivesim_api_key)
                await self.sms_manager.__aenter__()
                logger.info("5SIM service initialized")
            else:
                logger.warning("5SIM API key not configured")

            # Initialize email manager
            if config.external_services.emailondeck_api_key:
                self.email_manager = EmailVerificationManager(config.external_services.emailondeck_api_key)
                await self.email_manager.__aenter__()
                logger.info("EmailOnDeck service initialized")
            else:
                logger.warning("EmailOnDeck API key not configured")

            # Initialize proxy manager
            if config.external_services.geonode_username and config.external_services.geonode_password:
                self.proxy_manager = ProxyRotationManager(
                    config.external_services.geonode_username,
                    config.external_services.geonode_password
                )
                await self.proxy_manager.__aenter__()
                logger.info("Geonode proxy service initialized")
            else:
                logger.warning("Geonode credentials not configured")

            # Initial health check
            await self.check_all_services_health()
            
            return self
            
        except Exception as e:
            logger.error(f"Error initializing service manager: {e}")
            await self.__aexit__(None, None, None)
            raise

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup all service managers"""
        try:
            if self.sms_manager:
                await self.sms_manager.__aexit__(exc_type, exc_val, exc_tb)
            if self.email_manager:
                await self.email_manager.__aexit__(exc_type, exc_val, exc_tb)
            if self.proxy_manager:
                await self.proxy_manager.__aexit__(exc_type, exc_val, exc_tb)
        except Exception as e:
            logger.error(f"Error during service manager cleanup: {e}")

    async def check_all_services_health(self) -> Dict[str, ServiceHealth]:
        """Check health of all external services"""
        health_checks = []
        
        if self.sms_manager:
            health_checks.append(self.check_sms_service_health())
        if self.email_manager:
            health_checks.append(self.check_email_service_health())
        if self.proxy_manager:
            health_checks.append(self.check_proxy_service_health())
        
        if health_checks:
            await asyncio.gather(*health_checks, return_exceptions=True)
        
        return self.service_health

    async def check_sms_service_health(self) -> ServiceHealth:
        """Check 5SIM service health"""
        start_time = datetime.now()
        
        try:
            balance = await self.sms_manager.check_balance()
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            health = ServiceHealth(
                service_name="5SIM",
                is_healthy=(balance is not None and balance >= 0),
                last_check=datetime.now(),
                response_time=response_time
            )
            
            self.service_health["5SIM"] = health
            if balance is not None:
                self.resource_usage.sms_balance = balance
            
            logger.info(f"5SIM health check: {'OK' if health.is_healthy else 'FAIL'} (balance: {balance})")
            return health
            
        except Exception as e:
            health = ServiceHealth(
                service_name="5SIM",
                is_healthy=False,
                last_check=datetime.now(),
                error_message=str(e)
            )
            self.service_health["5SIM"] = health
            logger.error(f"5SIM health check failed: {e}")
            return health

    async def check_email_service_health(self) -> ServiceHealth:
        """Check EmailOnDeck service health"""
        start_time = datetime.now()
        
        try:
            domains = await self.email_manager.get_available_domains()
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            health = ServiceHealth(
                service_name="EmailOnDeck",
                is_healthy=len(domains) > 0,
                last_check=datetime.now(),
                response_time=response_time
            )
            
            self.service_health["EmailOnDeck"] = health
            logger.info(f"EmailOnDeck health check: {'OK' if health.is_healthy else 'FAIL'} ({len(domains)} domains)")
            return health
            
        except Exception as e:
            health = ServiceHealth(
                service_name="EmailOnDeck",
                is_healthy=False,
                last_check=datetime.now(),
                error_message=str(e)
            )
            self.service_health["EmailOnDeck"] = health
            logger.error(f"EmailOnDeck health check failed: {e}")
            return health

    async def check_proxy_service_health(self) -> ServiceHealth:
        """Check Geonode proxy service health"""
        start_time = datetime.now()
        
        try:
            # Test proxy assignment
            test_proxy = await self.proxy_manager.select_residential_proxy()
            performance = await self.proxy_manager.test_proxy_performance(test_proxy)
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            health = ServiceHealth(
                service_name="Geonode",
                is_healthy=performance.success_rate > 0,
                last_check=datetime.now(),
                response_time=response_time
            )
            
            self.service_health["Geonode"] = health
            logger.info(f"Geonode health check: {'OK' if health.is_healthy else 'FAIL'}")
            return health
            
        except Exception as e:
            health = ServiceHealth(
                service_name="Geonode",
                is_healthy=False,
                last_check=datetime.now(),
                error_message=str(e)
            )
            self.service_health["Geonode"] = health
            logger.error(f"Geonode health check failed: {e}")
            return health

    async def create_account_resources(self, account_id: str, first_name: str, last_name: str) -> Dict[str, Any]:
        """Create all resources needed for account creation"""
        logger.info(f"Creating resources for account {account_id}")
        self._emit_enhanced(account_id, [{'level': 'info', 'message': 'Initialisation des ressources externes'}], current_step='Préparation des services', overall_progress=5)
        
        results = {}
        
        try:
            # Preflight connectivity checks
            try:
                import aiohttp, socket
                timeout = aiohttp.ClientTimeout(total=8, connect=4, sock_connect=4, sock_read=4)
                connector = aiohttp.TCPConnector(family=socket.AF_INET, ttl_dns_cache=120)
                async with aiohttp.ClientSession(timeout=timeout, connector=connector) as sess:
                    ok_5sim = False
                    ok_eod = False
                    ok_probe = False
                    try:
                        async with sess.get('https://5sim.net/v1/guest/countries') as r:
                            ok_5sim = (r.status == 200)
                    except Exception as e:
                        self._emit_enhanced(account_id, [{'level': 'error', 'message': f"Préflight 5SIM échec: {e}"}])
                    try:
                        async with sess.get('https://api.emailondeck.com/api.php?act=ping') as r:
                            ok_eod = (r.status in (200, 400, 401))
                    except Exception as e:
                        self._emit_enhanced(account_id, [{'level': 'error', 'message': f"Préflight EmailOnDeck échec: {e}"}])
                    try:
                        async with sess.get('https://ifconfig.me/ip') as r:
                            ok_probe = (r.status == 200)
                    except Exception as e:
                        self._emit_enhanced(account_id, [{'level': 'error', 'message': f"Préflight réseau échec: {e}"}])
                    self._emit_enhanced(account_id, [{'level': 'info', 'message': f"Préflight: 5SIM={'OK' if ok_5sim else 'FAIL'}, EmailOnDeck={'OK' if ok_eod else 'FAIL'}, InternetProbe={'OK' if ok_probe else 'FAIL'}"}], overall_progress=8)
            except Exception:
                pass

            # Create resources in parallel for efficiency
            tasks = []
            
            # When account is configured for manual email, skip provisioning
            from src.models.account import Account as _Account
            acct = _Account.query.get(account_id)
            profile_data = acct.get_profile_data() if acct else {}
            creation_settings = profile_data.get('creation_settings', {})
            use_manual_email = creation_settings.get('email_service') == 'manual'

            if self.email_manager and not use_manual_email:
                self._emit_enhanced(account_id, [{'level': 'info', 'message': 'EmailOnDeck: préparation de l\'adresse'}], current_step='Email', overall_progress=10)
                tasks.append(self.email_manager.create_linkedin_email(first_name, last_name))
            if self.sms_manager:
                self._emit_enhanced(account_id, [{'level': 'info', 'message': '5SIM: vérification du solde et demande de numéro'}], current_step='SMS', overall_progress=12)
                tasks.append(self.sms_manager.get_french_number())
            if self.proxy_manager:
                self._emit_enhanced(account_id, [{'level': 'info', 'message': 'Geonode: attribution d\'un proxy'}], current_step='Proxy', overall_progress=15)
                tasks.append(self.proxy_manager.assign_proxy_to_account(account_id))
            
            if not tasks:
                raise Exception("No external services available")
            
            # Execute all tasks
            task_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            result_index = 0
            
            if self.email_manager and not use_manual_email:
                email_result = task_results[result_index]
                result_index += 1
                
                if isinstance(email_result, EmailResult):
                    results['email'] = email_result
                    if email_result.success:
                        self.resource_usage.emails_created += 1
                        self._emit_enhanced(account_id, [{'level': 'success', 'message': f"Email créé: {email_result.email_address}"}], current_step='Email', overall_progress=30)
                    else:
                        self._emit_enhanced(account_id, [{'level': 'error', 'message': f"EmailOnDeck échec: {email_result.error_message}"}])
                else:
                    results['email'] = EmailResult("", "", False, str(email_result))
                    self._emit_enhanced(account_id, [{'level': 'error', 'message': f"EmailOnDeck exception: {results['email'].error_message}"}])
            
            if self.sms_manager:
                sms_result = task_results[result_index]
                result_index += 1
                
                if isinstance(sms_result, SMSResult):
                    results['sms'] = sms_result
                    if sms_result.success:
                        self._emit_enhanced(account_id, [{'level': 'success', 'message': f"Numéro SMS obtenu: {sms_result.phone_number}"}], current_step='SMS', overall_progress=40)
                    else:
                        self._emit_enhanced(account_id, [{'level': 'error', 'message': f"5SIM échec: {sms_result.error_message or 'indisponible'}"}])
                else:
                    results['sms'] = SMSResult("", None, "", False, str(sms_result))
                    self._emit_enhanced(account_id, [{'level': 'error', 'message': f"5SIM exception: {results['sms'].error_message}"}])
            
            if self.proxy_manager:
                proxy_result = task_results[result_index]
                result_index += 1
                
                if isinstance(proxy_result, ProxyAssignment):
                    results['proxy'] = proxy_result
                    if proxy_result.success:
                        self.resource_usage.proxies_active += 1
                        self._emit_enhanced(account_id, [{'level': 'success', 'message': f"Proxy assigné: {proxy_result.session_id}"}], current_step='Proxy', overall_progress=50)
                    else:
                        self._emit_enhanced(account_id, [{'level': 'error', 'message': f"Geonode échec: {proxy_result.error_message}"}])
                else:
                    results['proxy'] = ProxyAssignment(account_id, "", "", datetime.now(), False, str(proxy_result))
                    self._emit_enhanced(account_id, [{'level': 'error', 'message': f"Geonode exception: {results['proxy'].error_message}"}])
            
            # Update resource usage
            self.resource_usage.last_updated = datetime.now()
            
            logger.info(f"Resource creation completed for account {account_id}")
            self._emit_enhanced(account_id, [{'level': 'info', 'message': 'Ressources créées'}], overall_progress=60)
            return results
            
        except Exception as e:
            logger.error(f"Error creating resources for account {account_id}: {e}")
            return {'error': str(e)}

    async def wait_for_verifications(self, email: str, sms_activation_id: str, timeout: int = 300) -> Dict[str, Any]:
        """Wait for email and SMS verifications"""
        logger.info(f"Waiting for verifications (email: {email}, SMS: {sms_activation_id})")
        
        verification_results = {}
        
        try:
            # Wait for both verifications in parallel
            tasks = []
            
            if self.email_manager and email:
                tasks.append(self.email_manager.wait_for_linkedin_verification(email, timeout))
            
            if self.sms_manager and sms_activation_id:
                tasks.append(self.sms_manager.poll_for_sms(sms_activation_id, timeout))
            
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                result_index = 0
                
                if self.email_manager and email:
                    email_verification = results[result_index]
                    result_index += 1
                    
                    if isinstance(email_verification, EmailMessage):
                        verification_results['email_verification'] = {
                            'success': True,
                            'verification_link': email_verification.verification_link,
                            'verification_code': email_verification.verification_code,
                            'message': email_verification
                        }
                    else:
                        verification_results['email_verification'] = {
                            'success': False,
                            'error': str(email_verification)
                        }
                
                if self.sms_manager and sms_activation_id:
                    sms_code = results[result_index]
                    result_index += 1
                    
                    if isinstance(sms_code, str) and sms_code:
                        verification_results['sms_verification'] = {
                            'success': True,
                            'code': sms_code
                        }
                    else:
                        verification_results['sms_verification'] = {
                            'success': False,
                            'error': str(sms_code) if sms_code else "No SMS code received"
                        }
            
            return verification_results
            
        except Exception as e:
            logger.error(f"Error waiting for verifications: {e}")
            return {'error': str(e)}

    async def cleanup_account_resources(self, account_id: str, email: str = None) -> bool:
        """Cleanup resources for an account"""
        logger.info(f"Cleaning up resources for account {account_id}")
        
        try:
            cleanup_tasks = []
            
            # Release proxy
            if self.proxy_manager:
                cleanup_tasks.append(self.proxy_manager.release_proxy_for_account(account_id))
            
            # Delete email
            if self.email_manager and email:
                cleanup_tasks.append(self.email_manager.delete_email(email))
            
            if cleanup_tasks:
                results = await asyncio.gather(*cleanup_tasks, return_exceptions=True)
                success = all(r is True or not isinstance(r, Exception) for r in results)
            else:
                success = True
            
            if success:
                self.resource_usage.proxies_active = max(0, self.resource_usage.proxies_active - 1)
                self.resource_usage.last_updated = datetime.now()
            
            logger.info(f"Resource cleanup {'successful' if success else 'failed'} for account {account_id}")
            return success
            
        except Exception as e:
            logger.error(f"Error cleaning up resources for account {account_id}: {e}")
            return False

    def get_service_status(self) -> Dict[str, Any]:
        """Get overall service status"""
        return {
            'services': {name: {
                'healthy': health.is_healthy,
                'last_check': health.last_check.isoformat(),
                'response_time': health.response_time,
                'error': health.error_message
            } for name, health in self.service_health.items()},
            'resource_usage': {
                'sms_balance': self.resource_usage.sms_balance,
                'emails_created': self.resource_usage.emails_created,
                'proxies_active': self.resource_usage.proxies_active,
                'total_cost': self.resource_usage.total_cost,
                'last_updated': self.resource_usage.last_updated.isoformat()
            }
        }

# Global service manager instance
service_manager = None

async def get_service_manager() -> ServiceManager:
    """Get or create global service manager instance"""
    global service_manager
    
    if service_manager is None:
        service_manager = ServiceManager()
        await service_manager.__aenter__()
    
    return service_manager

