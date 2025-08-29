"""
Comprehensive AI Error Handler for GPT-5 Integration
Provides error classification, recovery strategies, and monitoring for AI operations.
"""

import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import re
import json

logger = logging.getLogger(__name__)


class AIErrorType(Enum):
    """Classification of AI-related errors."""
    API_KEY_INVALID = "api_key_invalid"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    MODEL_UNAVAILABLE = "model_unavailable"
    NETWORK_TIMEOUT = "network_timeout"
    SESSION_EXPIRED = "session_expired"
    BROWSER_DISCONNECTED = "browser_disconnected"
    PARSING_ERROR = "parsing_error"
    VALIDATION_ERROR = "validation_error"
    SERVER_ERROR = "server_error"


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorPattern:
    """Pattern for error detection and classification."""
    pattern: str
    error_type: AIErrorType
    severity: ErrorSeverity
    is_transient: bool = False
    retry_recommended: bool = False
    max_retries: int = 3
    retry_delay: float = 5.0


@dataclass
class ErrorInstance:
    """Individual error occurrence record."""
    timestamp: datetime
    error_type: AIErrorType
    severity: ErrorSeverity
    message: str
    context: Dict[str, Any]
    stack_trace: Optional[str] = None
    session_id: Optional[str] = None
    account_id: Optional[str] = None
    operation_type: Optional[str] = None
    retry_count: int = 0
    resolved: bool = False
    resolution_time: Optional[datetime] = None


@dataclass
class RecoveryStrategy:
    """Recovery strategy for specific error types."""
    error_type: AIErrorType
    actions: List[str]
    estimated_time: int  # seconds
    success_rate: float  # 0.0 to 1.0
    requires_user_intervention: bool = False


class AIErrorHandler:
    """Comprehensive error handler for AI operations."""
    
    def __init__(self):
        self._error_patterns = self._initialize_error_patterns()
        self._recovery_strategies = self._initialize_recovery_strategies()
        self._error_history: List[ErrorInstance] = []
        self._error_stats: Dict[AIErrorType, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        
        # Initialize statistics
        for error_type in AIErrorType:
            self._error_stats[error_type] = {
                'count': 0,
                'last_occurrence': None,
                'total_retries': 0,
                'resolution_rate': 0.0,
                'avg_resolution_time': 0.0
            }
        
        logger.info("AIErrorHandler initialized with comprehensive error patterns")
    
    def _initialize_error_patterns(self) -> List[ErrorPattern]:
        """Initialize error detection patterns."""
        return [
            # API Key Issues
            ErrorPattern(
                pattern=r"(?i)(invalid.*api.*key|incorrect.*api.*key|authentication.*failed|401.*unauthorized)",
                error_type=AIErrorType.API_KEY_INVALID,
                severity=ErrorSeverity.CRITICAL,
                is_transient=False,
                retry_recommended=False
            ),
            
            # Rate Limiting
            ErrorPattern(
                pattern=r"(?i)(rate.*limit|429|too.*many.*requests|quota.*exceeded|throttled)",
                error_type=AIErrorType.RATE_LIMIT_EXCEEDED,
                severity=ErrorSeverity.HIGH,
                is_transient=True,
                retry_recommended=True,
                max_retries=5,
                retry_delay=30.0
            ),
            
            # Model Issues
            ErrorPattern(
                pattern=r"(?i)(model.*unavailable|model.*not.*found|service.*unavailable|503.*service)",
                error_type=AIErrorType.MODEL_UNAVAILABLE,
                severity=ErrorSeverity.HIGH,
                is_transient=True,
                retry_recommended=True,
                max_retries=3,
                retry_delay=10.0
            ),
            
            # Network/Timeout Issues
            ErrorPattern(
                pattern=r"(?i)(timeout|connection.*timeout|read.*timeout|network.*error|connection.*reset)",
                error_type=AIErrorType.NETWORK_TIMEOUT,
                severity=ErrorSeverity.MEDIUM,
                is_transient=True,
                retry_recommended=True,
                max_retries=3,
                retry_delay=5.0
            ),
            
            # Session Issues
            ErrorPattern(
                pattern=r"(?i)(session.*expired|session.*closed|session.*terminated|no.*active.*session)",
                error_type=AIErrorType.SESSION_EXPIRED,
                severity=ErrorSeverity.MEDIUM,
                is_transient=False,
                retry_recommended=True,
                max_retries=1,
                retry_delay=2.0
            ),
            
            # Browser Issues
            ErrorPattern(
                pattern=r"(?i)(browser.*closed|browser.*disconnected|page.*closed|target.*closed)",
                error_type=AIErrorType.BROWSER_DISCONNECTED,
                severity=ErrorSeverity.MEDIUM,
                is_transient=False,
                retry_recommended=True,
                max_retries=2,
                retry_delay=3.0
            ),
            
            # Parsing Issues
            ErrorPattern(
                pattern=r"(?i)(json.*decode|parse.*error|invalid.*format|malformed.*response)",
                error_type=AIErrorType.PARSING_ERROR,
                severity=ErrorSeverity.LOW,
                is_transient=True,
                retry_recommended=True,
                max_retries=2,
                retry_delay=1.0
            ),
            
            # Validation Issues
            ErrorPattern(
                pattern=r"(?i)(validation.*failed|invalid.*input|bad.*request|400.*bad)",
                error_type=AIErrorType.VALIDATION_ERROR,
                severity=ErrorSeverity.MEDIUM,
                is_transient=False,
                retry_recommended=False
            ),
            
            # Server Errors
            ErrorPattern(
                pattern=r"(?i)(500.*internal.*server|502.*bad.*gateway|503.*service|504.*gateway)",
                error_type=AIErrorType.SERVER_ERROR,
                severity=ErrorSeverity.HIGH,
                is_transient=True,
                retry_recommended=True,
                max_retries=3,
                retry_delay=10.0
            )
        ]
    
    def _initialize_recovery_strategies(self) -> Dict[AIErrorType, RecoveryStrategy]:
        """Initialize recovery strategies for each error type."""
        return {
            AIErrorType.API_KEY_INVALID: RecoveryStrategy(
                error_type=AIErrorType.API_KEY_INVALID,
                actions=[
                    "Validate OpenAI API key format",
                    "Check environment variable OPENAI_API_KEY",
                    "Verify API key permissions and quota",
                    "Update API key if expired"
                ],
                estimated_time=300,  # 5 minutes
                success_rate=0.9,
                requires_user_intervention=True
            ),
            
            AIErrorType.RATE_LIMIT_EXCEEDED: RecoveryStrategy(
                error_type=AIErrorType.RATE_LIMIT_EXCEEDED,
                actions=[
                    "Implement exponential backoff",
                    "Reduce request frequency",
                    "Check rate limit headers",
                    "Consider request batching"
                ],
                estimated_time=60,  # 1 minute
                success_rate=0.95
            ),
            
            AIErrorType.MODEL_UNAVAILABLE: RecoveryStrategy(
                error_type=AIErrorType.MODEL_UNAVAILABLE,
                actions=[
                    "Retry with exponential backoff",
                    "Check OpenAI status page",
                    "Fallback to alternative model if configured",
                    "Monitor service status"
                ],
                estimated_time=30,  # 30 seconds
                success_rate=0.8
            ),
            
            AIErrorType.NETWORK_TIMEOUT: RecoveryStrategy(
                error_type=AIErrorType.NETWORK_TIMEOUT,
                actions=[
                    "Increase timeout duration",
                    "Retry with exponential backoff",
                    "Check network connectivity",
                    "Verify Stagehand server status"
                ],
                estimated_time=15,  # 15 seconds
                success_rate=0.85
            ),
            
            AIErrorType.SESSION_EXPIRED: RecoveryStrategy(
                error_type=AIErrorType.SESSION_EXPIRED,
                actions=[
                    "Create new browser session",
                    "Update session tracking",
                    "Validate session lifecycle",
                    "Implement session keep-alive"
                ],
                estimated_time=20,  # 20 seconds
                success_rate=0.9
            ),
            
            AIErrorType.BROWSER_DISCONNECTED: RecoveryStrategy(
                error_type=AIErrorType.BROWSER_DISCONNECTED,
                actions=[
                    "Reconnect to browser session",
                    "Create new session if needed",
                    "Validate Browserbase connection",
                    "Check proxy configuration"
                ],
                estimated_time=25,  # 25 seconds
                success_rate=0.8
            ),
            
            AIErrorType.PARSING_ERROR: RecoveryStrategy(
                error_type=AIErrorType.PARSING_ERROR,
                actions=[
                    "Retry with structured format",
                    "Validate response format",
                    "Adjust prompt for clarity",
                    "Enable JSON mode if available"
                ],
                estimated_time=10,  # 10 seconds
                success_rate=0.9
            ),
            
            AIErrorType.VALIDATION_ERROR: RecoveryStrategy(
                error_type=AIErrorType.VALIDATION_ERROR,
                actions=[
                    "Validate input parameters",
                    "Check data format requirements",
                    "Review API documentation",
                    "Adjust request structure"
                ],
                estimated_time=30,  # 30 seconds
                success_rate=0.7,
                requires_user_intervention=True
            ),
            
            AIErrorType.SERVER_ERROR: RecoveryStrategy(
                error_type=AIErrorType.SERVER_ERROR,
                actions=[
                    "Retry with exponential backoff",
                    "Check server status",
                    "Monitor error frequency",
                    "Contact support if persistent"
                ],
                estimated_time=45,  # 45 seconds
                success_rate=0.7
            )
        }
    
    def classify_error(self, error_message: str, context: Dict[str, Any] = None) -> Tuple[AIErrorType, ErrorSeverity]:
        """Classify error based on message and context."""
        error_message_lower = error_message.lower()
        
        for pattern in self._error_patterns:
            if re.search(pattern.pattern, error_message, re.IGNORECASE):
                return pattern.error_type, pattern.severity
        
        # Default classification for unmatched errors
        return AIErrorType.SERVER_ERROR, ErrorSeverity.MEDIUM
    
    def handle_error(self, 
                    error_message: str, 
                    context: Dict[str, Any] = None,
                    session_id: str = None,
                    account_id: str = None,
                    operation_type: str = None,
                    stack_trace: str = None) -> Dict[str, Any]:
        """Comprehensive error handling with classification and recovery suggestions."""
        
        with self._lock:
            # Classify error
            error_type, severity = self.classify_error(error_message, context)
            
            # Create error instance
            error_instance = ErrorInstance(
                timestamp=datetime.utcnow(),
                error_type=error_type,
                severity=severity,
                message=error_message,
                context=context or {},
                stack_trace=stack_trace,
                session_id=session_id,
                account_id=account_id,
                operation_type=operation_type
            )
            
            # Store in history
            self._error_history.append(error_instance)
            
            # Update statistics
            stats = self._error_stats[error_type]
            stats['count'] += 1
            stats['last_occurrence'] = datetime.utcnow()
            
            # Get recovery strategy
            recovery_strategy = self._recovery_strategies.get(error_type)
            
            # Get retry recommendation
            retry_info = self._get_retry_recommendation(error_type, error_message)
            
            # Prepare response
            response = {
                'error_id': len(self._error_history),  # Simple ID
                'error_type': error_type.value,
                'severity': severity.value,
                'classification': {
                    'is_transient': self._is_transient_error(error_type),
                    'retry_recommended': retry_info['recommended'],
                    'max_retries': retry_info['max_retries'],
                    'retry_delay': retry_info['delay']
                },
                'recovery_strategy': {
                    'actions': recovery_strategy.actions if recovery_strategy else [],
                    'estimated_time': recovery_strategy.estimated_time if recovery_strategy else 60,
                    'success_rate': recovery_strategy.success_rate if recovery_strategy else 0.5,
                    'requires_intervention': recovery_strategy.requires_user_intervention if recovery_strategy else False
                },
                'context': {
                    'session_id': session_id,
                    'account_id': account_id,
                    'operation_type': operation_type,
                    'timestamp': error_instance.timestamp.isoformat()
                },
                'statistics': {
                    'error_count': stats['count'],
                    'last_occurrence': stats['last_occurrence'].isoformat() if stats['last_occurrence'] else None
                }
            }
            
            # Log error with appropriate level
            log_level = {
                ErrorSeverity.LOW: logging.INFO,
                ErrorSeverity.MEDIUM: logging.WARNING,
                ErrorSeverity.HIGH: logging.ERROR,
                ErrorSeverity.CRITICAL: logging.CRITICAL
            }.get(severity, logging.ERROR)
            
            logger.log(log_level, f"AI Error [{error_type.value}]: {error_message}")
            
            return response
    
    def _is_transient_error(self, error_type: AIErrorType) -> bool:
        """Check if error type is typically transient."""
        transient_errors = {
            AIErrorType.RATE_LIMIT_EXCEEDED,
            AIErrorType.MODEL_UNAVAILABLE,
            AIErrorType.NETWORK_TIMEOUT,
            AIErrorType.PARSING_ERROR,
            AIErrorType.SERVER_ERROR
        }
        return error_type in transient_errors
    
    def _get_retry_recommendation(self, error_type: AIErrorType, error_message: str) -> Dict[str, Any]:
        """Get retry recommendation for error type."""
        pattern = next((p for p in self._error_patterns if p.error_type == error_type), None)
        
        if not pattern:
            return {'recommended': False, 'max_retries': 0, 'delay': 0}
        
        return {
            'recommended': pattern.retry_recommended,
            'max_retries': pattern.max_retries,
            'delay': pattern.retry_delay
        }
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get comprehensive error statistics."""
        with self._lock:
            total_errors = len(self._error_history)
            recent_errors = [e for e in self._error_history if e.timestamp > datetime.utcnow() - timedelta(hours=24)]
            
            severity_counts = {}
            type_counts = {}
            
            for error in self._error_history:
                severity_counts[error.severity.value] = severity_counts.get(error.severity.value, 0) + 1
                type_counts[error.error_type.value] = type_counts.get(error.error_type.value, 0) + 1
            
            return {
                'total_errors': total_errors,
                'recent_errors_24h': len(recent_errors),
                'error_rate_24h': len(recent_errors) / 24 if recent_errors else 0,
                'severity_breakdown': severity_counts,
                'type_breakdown': type_counts,
                'top_errors': sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:5],
                'error_trends': self._calculate_error_trends(),
                'statistics_by_type': self._error_stats.copy()
            }
    
    def _calculate_error_trends(self) -> Dict[str, Any]:
        """Calculate error trends over time."""
        now = datetime.utcnow()
        periods = {
            'last_hour': now - timedelta(hours=1),
            'last_6_hours': now - timedelta(hours=6),
            'last_24_hours': now - timedelta(hours=24)
        }
        
        trends = {}
        for period_name, start_time in periods.items():
            period_errors = [e for e in self._error_history if e.timestamp > start_time]
            trends[period_name] = {
                'count': len(period_errors),
                'by_type': {},
                'by_severity': {}
            }
            
            for error in period_errors:
                error_type = error.error_type.value
                severity = error.severity.value
                
                trends[period_name]['by_type'][error_type] = trends[period_name]['by_type'].get(error_type, 0) + 1
                trends[period_name]['by_severity'][severity] = trends[period_name]['by_severity'].get(severity, 0) + 1
        
        return trends
    
    def get_recent_errors(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent error instances."""
        with self._lock:
            recent_errors = sorted(self._error_history, key=lambda x: x.timestamp, reverse=True)[:limit]
            
            return [
                {
                    'timestamp': error.timestamp.isoformat(),
                    'error_type': error.error_type.value,
                    'severity': error.severity.value,
                    'message': error.message,
                    'session_id': error.session_id,
                    'account_id': error.account_id,
                    'operation_type': error.operation_type,
                    'retry_count': error.retry_count,
                    'resolved': error.resolved
                }
                for error in recent_errors
            ]
    
    def mark_error_resolved(self, error_id: int) -> bool:
        """Mark an error as resolved."""
        with self._lock:
            if 0 <= error_id < len(self._error_history):
                error_instance = self._error_history[error_id]
                error_instance.resolved = True
                error_instance.resolution_time = datetime.utcnow()
                
                # Update resolution statistics
                stats = self._error_stats[error_instance.error_type]
                resolution_time = (error_instance.resolution_time - error_instance.timestamp).total_seconds()
                
                # Calculate running average
                current_avg = stats.get('avg_resolution_time', 0.0)
                current_count = stats.get('resolved_count', 0)
                stats['avg_resolution_time'] = (current_avg * current_count + resolution_time) / (current_count + 1)
                stats['resolved_count'] = current_count + 1
                
                logger.info(f"Error {error_id} marked as resolved after {resolution_time:.2f} seconds")
                return True
            
            return False
    
    def cleanup_old_errors(self, days: int = 7) -> int:
        """Clean up error history older than specified days."""
        with self._lock:
            cutoff_time = datetime.utcnow() - timedelta(days=days)
            initial_count = len(self._error_history)
            
            self._error_history = [e for e in self._error_history if e.timestamp > cutoff_time]
            
            cleaned_count = initial_count - len(self._error_history)
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} error records older than {days} days")
            
            return cleaned_count


# Global error handler instance
_error_handler: Optional[AIErrorHandler] = None
_error_handler_lock = threading.Lock()


def get_error_handler() -> AIErrorHandler:
    """Get the global error handler instance (thread-safe singleton)."""
    global _error_handler
    
    if _error_handler is None:
        with _error_handler_lock:
            if _error_handler is None:
                _error_handler = AIErrorHandler()
    
    return _error_handler


def handle_ai_error(error_message: str, **context) -> Dict[str, Any]:
    """Convenience function for error handling."""
    return get_error_handler().handle_error(error_message, **context)
