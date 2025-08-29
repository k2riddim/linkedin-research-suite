"""
AI Health Monitoring System for GPT-5 Integration
Provides real-time monitoring, service status tracking, and health verification.
"""

import asyncio
import threading
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import aiohttp
import json

from .ai_config import get_ai_config, AIOperationType
from .session_manager import get_session_manager
from .ai_error_handler import get_error_handler

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """Service health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class HealthCheckType(Enum):
    """Types of health checks."""
    API_CONNECTIVITY = "api_connectivity"
    MODEL_AVAILABILITY = "model_availability"
    SESSION_HEALTH = "session_health"
    STAGEHAND_SERVER = "stagehand_server"
    BROWSERBASE_CONNECTIVITY = "browserbase_connectivity"
    ERROR_RATE = "error_rate"


@dataclass
class HealthMetric:
    """Individual health metric."""
    name: str
    value: Any
    status: ServiceStatus
    timestamp: datetime
    threshold: Optional[float] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ServiceHealth:
    """Complete service health status."""
    service_name: str
    status: ServiceStatus
    last_check: datetime
    metrics: Dict[str, HealthMetric]
    uptime_percentage: float = 100.0
    response_time_ms: Optional[float] = None
    error_count_24h: int = 0
    last_error: Optional[str] = None


class AIHealthMonitor:
    """Comprehensive AI service health monitoring."""
    
    def __init__(self):
        self.ai_config = get_ai_config()
        self.session_manager = get_session_manager()
        self.error_handler = get_error_handler()
        
        self._services: Dict[str, ServiceHealth] = {}
        self._monitoring_tasks: Dict[str, asyncio.Task] = {}
        self._health_history: List[Dict[str, Any]] = []
        self._lock = threading.RLock()
        
        # Configuration
        self._check_intervals = {
            HealthCheckType.API_CONNECTIVITY: 60,      # 1 minute
            HealthCheckType.MODEL_AVAILABILITY: 120,   # 2 minutes
            HealthCheckType.SESSION_HEALTH: 30,        # 30 seconds
            HealthCheckType.STAGEHAND_SERVER: 30,      # 30 seconds
            HealthCheckType.BROWSERBASE_CONNECTIVITY: 180,  # 3 minutes
            HealthCheckType.ERROR_RATE: 60             # 1 minute
        }
        
        self._thresholds = {
            'response_time_ms': 5000,      # 5 seconds
            'error_rate_24h': 0.1,         # 10% error rate
            'session_success_rate': 0.95,   # 95% success rate
            'uptime_percentage': 99.0       # 99% uptime
        }
        
        self._initialize_services()
        logger.info("AIHealthMonitor initialized with comprehensive service tracking")
    
    def _initialize_services(self):
        """Initialize service health tracking."""
        services = [
            "openai_api",
            "stagehand_server", 
            "browserbase",
            "session_manager",
            "error_handler"
        ]
        
        for service_name in services:
            self._services[service_name] = ServiceHealth(
                service_name=service_name,
                status=ServiceStatus.UNKNOWN,
                last_check=datetime.utcnow(),
                metrics={}
            )
    
    async def start_monitoring(self):
        """Start health monitoring tasks."""
        try:
            # Start individual monitoring tasks
            self._monitoring_tasks['api_connectivity'] = asyncio.create_task(
                self._monitor_api_connectivity()
            )
            self._monitoring_tasks['model_availability'] = asyncio.create_task(
                self._monitor_model_availability()
            )
            self._monitoring_tasks['session_health'] = asyncio.create_task(
                self._monitor_session_health()
            )
            self._monitoring_tasks['stagehand_server'] = asyncio.create_task(
                self._monitor_stagehand_server()
            )
            self._monitoring_tasks['browserbase'] = asyncio.create_task(
                self._monitor_browserbase()
            )
            self._monitoring_tasks['error_rate'] = asyncio.create_task(
                self._monitor_error_rates()
            )
            
            logger.info("AI health monitoring started for all services")
            
        except Exception as e:
            logger.error(f"Failed to start health monitoring: {e}")
    
    async def stop_monitoring(self):
        """Stop all monitoring tasks."""
        for task_name, task in self._monitoring_tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                logger.info(f"Stopped monitoring task: {task_name}")
        
        self._monitoring_tasks.clear()
    
    async def _monitor_api_connectivity(self):
        """Monitor OpenAI API connectivity."""
        interval = self._check_intervals[HealthCheckType.API_CONNECTIVITY]
        
        while True:
            try:
                start_time = time.time()
                
                # Test API connectivity with a simple request
                async with aiohttp.ClientSession() as session:
                    headers = {'Authorization': f'Bearer {self.ai_config.api_key}'}
                    async with session.get(
                        'https://api.openai.com/v1/models',
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        response_time = (time.time() - start_time) * 1000
                        
                        if response.status == 200:
                            status = ServiceStatus.HEALTHY
                            details = {'models_available': True}
                        else:
                            status = ServiceStatus.DEGRADED
                            details = {'http_status': response.status}
                
                self._update_service_health(
                    'openai_api',
                    status,
                    response_time_ms=response_time,
                    details=details
                )
                
            except Exception as e:
                self._update_service_health(
                    'openai_api',
                    ServiceStatus.UNHEALTHY,
                    error=str(e)
                )
            
            await asyncio.sleep(interval)
    
    async def _monitor_model_availability(self):
        """Monitor GPT-5 model availability."""
        interval = self._check_intervals[HealthCheckType.MODEL_AVAILABILITY]
        
        while True:
            try:
                start_time = time.time()
                
                # Test model with a minimal request
                config = self.ai_config.get_config(AIOperationType.DEBUG_ANALYSIS)
                
                async with aiohttp.ClientSession() as session:
                    headers = {
                        'Authorization': f'Bearer {self.ai_config.api_key}',
                        'Content-Type': 'application/json'
                    }
                    
                    test_payload = {
                        'model': config.model,
                        'messages': [{'role': 'user', 'content': 'Test'}],
                        'max_tokens': 5,
                        'temperature': 0
                    }
                    
                    async with session.post(
                        'https://api.openai.com/v1/chat/completions',
                        headers=headers,
                        json=test_payload,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        response_time = (time.time() - start_time) * 1000
                        
                        if response.status == 200:
                            status = ServiceStatus.HEALTHY
                            details = {'model_responsive': True, 'model': config.model}
                        else:
                            status = ServiceStatus.DEGRADED
                            error_text = await response.text()
                            details = {'http_status': response.status, 'error': error_text}
                
                self._update_service_health(
                    'openai_api',
                    status,
                    response_time_ms=response_time,
                    details=details,
                    metric_name='model_availability'
                )
                
            except Exception as e:
                self._update_service_health(
                    'openai_api',
                    ServiceStatus.UNHEALTHY,
                    error=str(e),
                    metric_name='model_availability'
                )
            
            await asyncio.sleep(interval)
    
    async def _monitor_session_health(self):
        """Monitor session manager health."""
        interval = self._check_intervals[HealthCheckType.SESSION_HEALTH]
        
        while True:
            try:
                stats = self.session_manager.get_session_stats()
                active_sessions = stats['active_sessions']
                total_sessions = stats['total_sessions']
                
                # Calculate session success rate
                success_rate = 1.0
                if total_sessions > 0:
                    error_sessions = stats['status_breakdown'].get('error', 0)
                    success_rate = 1.0 - (error_sessions / total_sessions)
                
                # Determine status
                if success_rate >= self._thresholds['session_success_rate']:
                    status = ServiceStatus.HEALTHY
                elif success_rate >= 0.8:
                    status = ServiceStatus.DEGRADED
                else:
                    status = ServiceStatus.UNHEALTHY
                
                details = {
                    'active_sessions': active_sessions,
                    'total_sessions': total_sessions,
                    'success_rate': success_rate,
                    'status_breakdown': stats['status_breakdown']
                }
                
                self._update_service_health(
                    'session_manager',
                    status,
                    details=details
                )
                
            except Exception as e:
                self._update_service_health(
                    'session_manager',
                    ServiceStatus.UNHEALTHY,
                    error=str(e)
                )
            
            await asyncio.sleep(interval)
    
    async def _monitor_stagehand_server(self):
        """Monitor Stagehand server health."""
        interval = self._check_intervals[HealthCheckType.STAGEHAND_SERVER]
        
        while True:
            try:
                start_time = time.time()
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        'http://localhost:8081/health',
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        response_time = (time.time() - start_time) * 1000
                        
                        if response.status == 200:
                            data = await response.json()
                            status = ServiceStatus.HEALTHY
                            details = {'server_response': data}
                        else:
                            status = ServiceStatus.DEGRADED
                            details = {'http_status': response.status}
                
                self._update_service_health(
                    'stagehand_server',
                    status,
                    response_time_ms=response_time,
                    details=details
                )
                
            except Exception as e:
                self._update_service_health(
                    'stagehand_server',
                    ServiceStatus.UNHEALTHY,
                    error=str(e)
                )
            
            await asyncio.sleep(interval)
    
    async def _monitor_browserbase(self):
        """Monitor Browserbase connectivity."""
        interval = self._check_intervals[HealthCheckType.BROWSERBASE_CONNECTIVITY]
        
        while True:
            try:
                start_time = time.time()
                
                # Test Browserbase API connectivity
                import os
                api_key = os.getenv('BROWSERBASE_API_KEY')
                if not api_key:
                    raise ValueError("BROWSERBASE_API_KEY not configured")
                
                async with aiohttp.ClientSession() as session:
                    headers = {'x-bb-api-key': api_key}
                    async with session.get(
                        'https://api.browserbase.com/v1/sessions',
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        response_time = (time.time() - start_time) * 1000
                        
                        if response.status == 200:
                            status = ServiceStatus.HEALTHY
                            details = {'api_accessible': True}
                        else:
                            status = ServiceStatus.DEGRADED
                            details = {'http_status': response.status}
                
                self._update_service_health(
                    'browserbase',
                    status,
                    response_time_ms=response_time,
                    details=details
                )
                
            except Exception as e:
                self._update_service_health(
                    'browserbase',
                    ServiceStatus.UNHEALTHY,
                    error=str(e)
                )
            
            await asyncio.sleep(interval)
    
    async def _monitor_error_rates(self):
        """Monitor system error rates."""
        interval = self._check_intervals[HealthCheckType.ERROR_RATE]
        
        while True:
            try:
                error_stats = self.error_handler.get_error_statistics()
                
                # Calculate 24h error rate
                recent_errors = error_stats['recent_errors_24h']
                error_rate = error_stats.get('error_rate_24h', 0)
                
                # Determine status based on error rate
                if error_rate <= self._thresholds['error_rate_24h']:
                    status = ServiceStatus.HEALTHY
                elif error_rate <= 0.2:  # 20%
                    status = ServiceStatus.DEGRADED
                else:
                    status = ServiceStatus.UNHEALTHY
                
                details = {
                    'error_rate_24h': error_rate,
                    'recent_errors': recent_errors,
                    'error_trends': error_stats['error_trends'],
                    'top_errors': error_stats['top_errors']
                }
                
                self._update_service_health(
                    'error_handler',
                    status,
                    details=details
                )
                
            except Exception as e:
                self._update_service_health(
                    'error_handler',
                    ServiceStatus.UNHEALTHY,
                    error=str(e)
                )
            
            await asyncio.sleep(interval)
    
    def _update_service_health(self, 
                             service_name: str, 
                             status: ServiceStatus, 
                             response_time_ms: Optional[float] = None,
                             error: Optional[str] = None,
                             details: Dict[str, Any] = None,
                             metric_name: str = 'general'):
        """Update service health status."""
        with self._lock:
            service = self._services.get(service_name)
            if not service:
                return
            
            # Update basic status
            service.status = status
            service.last_check = datetime.utcnow()
            service.response_time_ms = response_time_ms
            
            if error:
                service.last_error = error
                service.error_count_24h += 1
            
            # Update metrics
            metric = HealthMetric(
                name=metric_name,
                value=status.value,
                status=status,
                timestamp=datetime.utcnow(),
                details=details or {}
            )
            
            service.metrics[metric_name] = metric
            
            # Calculate uptime (simplified)
            healthy_checks = sum(1 for m in service.metrics.values() if m.status == ServiceStatus.HEALTHY)
            total_checks = len(service.metrics)
            if total_checks > 0:
                service.uptime_percentage = (healthy_checks / total_checks) * 100
            
            # Log status changes
            logger.info(f"Service {service_name} health: {status.value} "
                       f"(response: {response_time_ms}ms)" if response_time_ms else "")
    
    def get_overall_health(self) -> Dict[str, Any]:
        """Get overall system health status."""
        with self._lock:
            # Calculate overall status
            service_statuses = [s.status for s in self._services.values()]
            
            if all(s == ServiceStatus.HEALTHY for s in service_statuses):
                overall_status = ServiceStatus.HEALTHY
            elif any(s == ServiceStatus.UNHEALTHY for s in service_statuses):
                overall_status = ServiceStatus.UNHEALTHY
            elif any(s == ServiceStatus.DEGRADED for s in service_statuses):
                overall_status = ServiceStatus.DEGRADED
            else:
                overall_status = ServiceStatus.UNKNOWN
            
            # Get service summary
            service_summary = {}
            for name, service in self._services.items():
                service_summary[name] = {
                    'status': service.status.value,
                    'last_check': service.last_check.isoformat(),
                    'uptime_percentage': service.uptime_percentage,
                    'response_time_ms': service.response_time_ms,
                    'error_count_24h': service.error_count_24h,
                    'last_error': service.last_error
                }
            
            return {
                'overall_status': overall_status.value,
                'timestamp': datetime.utcnow().isoformat(),
                'services': service_summary,
                'system_metrics': {
                    'active_sessions': len(self.session_manager.get_active_sessions()),
                    'total_errors_24h': sum(s.error_count_24h for s in self._services.values()),
                    'average_uptime': sum(s.uptime_percentage for s in self._services.values()) / len(self._services)
                }
            }
    
    def get_service_health(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed health information for specific service."""
        with self._lock:
            service = self._services.get(service_name)
            if not service:
                return None
            
            metrics_data = {}
            for metric_name, metric in service.metrics.items():
                metrics_data[metric_name] = {
                    'value': metric.value,
                    'status': metric.status.value,
                    'timestamp': metric.timestamp.isoformat(),
                    'details': metric.details
                }
            
            return {
                'service_name': service.service_name,
                'status': service.status.value,
                'last_check': service.last_check.isoformat(),
                'uptime_percentage': service.uptime_percentage,
                'response_time_ms': service.response_time_ms,
                'error_count_24h': service.error_count_24h,
                'last_error': service.last_error,
                'metrics': metrics_data
            }
    
    def get_health_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get health status history."""
        with self._lock:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            history = []
            for service_name, service in self._services.items():
                for metric_name, metric in service.metrics.items():
                    if metric.timestamp > cutoff_time:
                        history.append({
                            'timestamp': metric.timestamp.isoformat(),
                            'service': service_name,
                            'metric': metric_name,
                            'status': metric.status.value,
                            'value': metric.value,
                            'details': metric.details
                        })
            
            return sorted(history, key=lambda x: x['timestamp'], reverse=True)
    
    async def run_health_check(self, service_name: Optional[str] = None) -> Dict[str, Any]:
        """Run immediate health check for service(s)."""
        if service_name:
            if service_name == 'openai_api':
                await self._check_openai_health()
            elif service_name == 'stagehand_server':
                await self._check_stagehand_health()
            elif service_name == 'browserbase':
                await self._check_browserbase_health()
            
            return self.get_service_health(service_name) or {}
        else:
            # Run all health checks
            await asyncio.gather(
                self._check_openai_health(),
                self._check_stagehand_health(),
                self._check_browserbase_health(),
                return_exceptions=True
            )
            return self.get_overall_health()
    
    async def _check_openai_health(self):
        """Immediate OpenAI health check."""
        try:
            start_time = time.time()
            async with aiohttp.ClientSession() as session:
                headers = {'Authorization': f'Bearer {self.ai_config.api_key}'}
                async with session.get(
                    'https://api.openai.com/v1/models',
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        status = ServiceStatus.HEALTHY
                    else:
                        status = ServiceStatus.DEGRADED
            
            self._update_service_health('openai_api', status, response_time_ms=response_time)
            
        except Exception as e:
            self._update_service_health('openai_api', ServiceStatus.UNHEALTHY, error=str(e))
    
    async def _check_stagehand_health(self):
        """Immediate Stagehand health check."""
        try:
            start_time = time.time()
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    'http://localhost:8081/health',
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        status = ServiceStatus.HEALTHY
                    else:
                        status = ServiceStatus.DEGRADED
            
            self._update_service_health('stagehand_server', status, response_time_ms=response_time)
            
        except Exception as e:
            self._update_service_health('stagehand_server', ServiceStatus.UNHEALTHY, error=str(e))
    
    async def _check_browserbase_health(self):
        """Immediate Browserbase health check."""
        try:
            start_time = time.time()
            import os
            api_key = os.getenv('BROWSERBASE_API_KEY')
            
            async with aiohttp.ClientSession() as session:
                headers = {'x-bb-api-key': api_key}
                async with session.get(
                    'https://api.browserbase.com/v1/sessions',
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        status = ServiceStatus.HEALTHY
                    else:
                        status = ServiceStatus.DEGRADED
            
            self._update_service_health('browserbase', status, response_time_ms=response_time)
            
        except Exception as e:
            self._update_service_health('browserbase', ServiceStatus.UNHEALTHY, error=str(e))


# Global health monitor instance
_health_monitor: Optional[AIHealthMonitor] = None
_health_monitor_lock = threading.Lock()


def get_health_monitor() -> AIHealthMonitor:
    """Get the global health monitor instance (thread-safe singleton)."""
    global _health_monitor
    
    if _health_monitor is None:
        with _health_monitor_lock:
            if _health_monitor is None:
                _health_monitor = AIHealthMonitor()
    
    return _health_monitor
