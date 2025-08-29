"""
AI Debug and Monitoring API Routes
Provides comprehensive debugging, monitoring, and management endpoints for AI services.
"""

import asyncio
import logging
from datetime import datetime
from flask import Blueprint, jsonify, request, current_app
from functools import wraps

from ..services.ai_config import get_ai_config, AIOperationType
from ..services.session_manager import get_session_manager, SessionStatus
from ..services.ai_error_handler import get_error_handler
from ..services.ai_health_monitor import get_health_monitor

logger = logging.getLogger(__name__)

# Create blueprint
ai_debug_bp = Blueprint('ai_debug', __name__, url_prefix='/api/ai/debug')


def async_route(f):
    """Decorator to handle async routes in Flask."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if asyncio.iscoroutinefunction(f):
            # Run async function in event loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is already running, use a thread
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        future = pool.submit(asyncio.run, f(*args, **kwargs))
                        return future.result()
                else:
                    return loop.run_until_complete(f(*args, **kwargs))
            except RuntimeError:
                # No event loop, create one
                return asyncio.run(f(*args, **kwargs))
        else:
            return f(*args, **kwargs)
    return wrapper


@ai_debug_bp.route('/status', methods=['GET'])
def get_debug_status():
    """Get overall AI system debug status."""
    try:
        ai_config = get_ai_config()
        session_manager = get_session_manager()
        error_handler = get_error_handler()
        health_monitor = get_health_monitor()
        
        # Get basic system info
        active_sessions = session_manager.get_active_sessions()
        session_stats = session_manager.get_session_stats()
        error_stats = error_handler.get_error_statistics()
        overall_health = health_monitor.get_overall_health()
        
        return jsonify({
            'status': 'operational',
            'timestamp': datetime.utcnow().isoformat(),
            'ai_config': {
                'default_model': ai_config.get_config(AIOperationType.BROWSER_AUTOMATION).model,
                'api_key_configured': bool(ai_config.api_key),
                'api_key_preview': f"***{ai_config.api_key[-8:]}" if ai_config.api_key else None,
                'capabilities': ai_config.get_model_capabilities()
            },
            'sessions': {
                'active_count': len(active_sessions),
                'total_count': session_stats['total_sessions'],
                'status_breakdown': session_stats['status_breakdown'],
                'uptime_stats': session_stats['lifetime_stats']
            },
            'errors': {
                'total_errors': error_stats['total_errors'],
                'recent_24h': error_stats['recent_errors_24h'],
                'error_rate': error_stats['error_rate_24h'],
                'top_error_types': error_stats['top_errors'][:3]
            },
            'health': {
                'overall_status': overall_health['overall_status'],
                'service_count': len(overall_health['services']),
                'healthy_services': len([s for s in overall_health['services'].values() if s['status'] == 'healthy']),
                'system_metrics': overall_health['system_metrics']
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting debug status: {e}")
        return jsonify({'error': str(e), 'status': 'error'}), 500


@ai_debug_bp.route('/health', methods=['GET'])
@async_route
async def get_health_status():
    """Get detailed health status for all AI services."""
    try:
        health_monitor = get_health_monitor()
        
        # Optional service filter
        service_name = request.args.get('service')
        
        if service_name:
            health_data = health_monitor.get_service_health(service_name)
            if not health_data:
                return jsonify({'error': f'Service {service_name} not found'}), 404
            return jsonify(health_data)
        else:
            # Get overall health
            overall_health = health_monitor.get_overall_health()
            
            # Add detailed service information
            detailed_services = {}
            for service_name in overall_health['services'].keys():
                detailed_services[service_name] = health_monitor.get_service_health(service_name)
            
            return jsonify({
                'overall': overall_health,
                'detailed_services': detailed_services,
                'timestamp': datetime.utcnow().isoformat()
            })
        
    except Exception as e:
        logger.error(f"Error getting health status: {e}")
        return jsonify({'error': str(e)}), 500


@ai_debug_bp.route('/health/check', methods=['POST'])
@async_route
async def run_health_check():
    """Run immediate health check for all or specific service."""
    try:
        health_monitor = get_health_monitor()
        service_name = request.json.get('service') if request.json else None
        
        result = await health_monitor.run_health_check(service_name)
        
        return jsonify({
            'check_completed': True,
            'timestamp': datetime.utcnow().isoformat(),
            'result': result
        })
        
    except Exception as e:
        logger.error(f"Error running health check: {e}")
        return jsonify({'error': str(e)}), 500


@ai_debug_bp.route('/sessions', methods=['GET'])
def get_session_debug():
    """Get detailed session information for debugging."""
    try:
        session_manager = get_session_manager()
        
        # Get query parameters
        status_filter = request.args.get('status')
        account_id = request.args.get('account_id')
        limit = int(request.args.get('limit', 50))
        
        # Get active sessions
        active_sessions = session_manager.get_active_sessions()
        
        # Apply filters
        filtered_sessions = active_sessions
        if status_filter:
            try:
                status_enum = SessionStatus(status_filter.lower())
                filtered_sessions = [s for s in filtered_sessions if s.status == status_enum]
            except ValueError:
                return jsonify({'error': f'Invalid status: {status_filter}'}), 400
        
        if account_id:
            filtered_sessions = [s for s in filtered_sessions if s.account_id == account_id]
        
        # Limit results
        filtered_sessions = filtered_sessions[:limit]
        
        # Format session data
        session_data = []
        for session in filtered_sessions:
            session_data.append({
                'session_id': session.session_id,
                'account_id': session.account_id,
                'status': session.status.value,
                'created_at': session.created_at.isoformat(),
                'last_activity': session.last_activity.isoformat(),
                'live_url': session.live_url,
                'operation_type': session.operation_type.value,
                'error_count': session.error_count,
                'last_error': session.last_error,
                'total_operations': session.total_operations,
                'browserbase_session_id': session.browserbase_session_id,
                'tags': list(session.tags),
                'is_expired': session.is_expired()
            })
        
        # Get session statistics
        stats = session_manager.get_session_stats()
        
        return jsonify({
            'sessions': session_data,
            'total_found': len(session_data),
            'filters_applied': {
                'status': status_filter,
                'account_id': account_id,
                'limit': limit
            },
            'statistics': stats,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting session debug info: {e}")
        return jsonify({'error': str(e)}), 500


@ai_debug_bp.route('/sessions/<session_id>', methods=['GET'])
def get_session_details(session_id):
    """Get detailed information for specific session."""
    try:
        session_manager = get_session_manager()
        
        session = session_manager.get_session(session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        # Validate session
        validation = session_manager.validate_session(session_id)
        
        return jsonify({
            'session': {
                'session_id': session.session_id,
                'account_id': session.account_id,
                'status': session.status.value,
                'created_at': session.created_at.isoformat(),
                'last_activity': session.last_activity.isoformat(),
                'live_url': session.live_url,
                'operation_type': session.operation_type.value,
                'error_count': session.error_count,
                'last_error': session.last_error,
                'total_operations': session.total_operations,
                'browserbase_session_id': session.browserbase_session_id,
                'stagehand_server_url': session.stagehand_server_url,
                'tags': list(session.tags),
                'is_expired': session.is_expired()
            },
            'validation': validation,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting session details: {e}")
        return jsonify({'error': str(e)}), 500


@ai_debug_bp.route('/sessions/<session_id>/close', methods=['POST'])
def close_session(session_id):
    """Close a specific session."""
    try:
        session_manager = get_session_manager()
        
        success = session_manager.close_session(session_id)
        if not success:
            return jsonify({'error': 'Session not found or already closed'}), 404
        
        return jsonify({
            'success': True,
            'message': f'Session {session_id} marked for closure',
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error closing session: {e}")
        return jsonify({'error': str(e)}), 500


@ai_debug_bp.route('/errors', methods=['GET'])
def get_error_debug():
    """Get detailed error information for debugging."""
    try:
        error_handler = get_error_handler()
        
        # Get query parameters
        limit = int(request.args.get('limit', 50))
        error_type = request.args.get('type')
        severity = request.args.get('severity')
        
        # Get error statistics
        stats = error_handler.get_error_statistics()
        
        # Get recent errors
        recent_errors = error_handler.get_recent_errors(limit)
        
        # Apply filters
        if error_type:
            recent_errors = [e for e in recent_errors if e['error_type'] == error_type]
        
        if severity:
            recent_errors = [e for e in recent_errors if e['severity'] == severity]
        
        return jsonify({
            'errors': recent_errors,
            'total_found': len(recent_errors),
            'statistics': stats,
            'filters_applied': {
                'limit': limit,
                'error_type': error_type,
                'severity': severity
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting error debug info: {e}")
        return jsonify({'error': str(e)}), 500


@ai_debug_bp.route('/errors/<int:error_id>/resolve', methods=['POST'])
def resolve_error(error_id):
    """Mark an error as resolved."""
    try:
        error_handler = get_error_handler()
        
        success = error_handler.mark_error_resolved(error_id)
        if not success:
            return jsonify({'error': 'Error not found'}), 404
        
        return jsonify({
            'success': True,
            'message': f'Error {error_id} marked as resolved',
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error resolving error: {e}")
        return jsonify({'error': str(e)}), 500


@ai_debug_bp.route('/config', methods=['GET'])
def get_ai_config_debug():
    """Get AI configuration for debugging."""
    try:
        ai_config = get_ai_config()
        
        # Get configuration for all operation types
        configs = {}
        for op_type in AIOperationType:
            config = ai_config.get_config(op_type)
            configs[op_type.value] = {
                'model': config.model,
                'temperature': config.temperature,
                'max_tokens': config.max_tokens,
                'timeout': config.timeout,
                'retry_attempts': config.retry_attempts,
                'response_format': config.response_format
            }
        
        return jsonify({
            'api_key_configured': bool(ai_config.api_key),
            'api_key_preview': f"***{ai_config.api_key[-8:]}" if ai_config.api_key else None,
            'model_capabilities': ai_config.get_model_capabilities(),
            'operation_configs': configs,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting AI config: {e}")
        return jsonify({'error': str(e)}), 500


@ai_debug_bp.route('/test/connectivity', methods=['POST'])
@async_route
async def test_connectivity():
    """Test connectivity to all AI services."""
    try:
        health_monitor = get_health_monitor()
        
        # Run health checks for all services
        results = await health_monitor.run_health_check()
        
        # Additional connectivity tests
        test_results = {
            'openai_api': {'status': 'testing'},
            'stagehand_server': {'status': 'testing'},
            'browserbase': {'status': 'testing'}
        }
        
        # Test each service
        try:
            await health_monitor._check_openai_health()
            test_results['openai_api'] = {'status': 'healthy', 'message': 'API accessible'}
        except Exception as e:
            test_results['openai_api'] = {'status': 'failed', 'error': str(e)}
        
        try:
            await health_monitor._check_stagehand_health()
            test_results['stagehand_server'] = {'status': 'healthy', 'message': 'Server responsive'}
        except Exception as e:
            test_results['stagehand_server'] = {'status': 'failed', 'error': str(e)}
        
        try:
            await health_monitor._check_browserbase_health()
            test_results['browserbase'] = {'status': 'healthy', 'message': 'API accessible'}
        except Exception as e:
            test_results['browserbase'] = {'status': 'failed', 'error': str(e)}
        
        return jsonify({
            'connectivity_test': test_results,
            'health_check_results': results,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error testing connectivity: {e}")
        return jsonify({'error': str(e)}), 500


@ai_debug_bp.route('/cleanup', methods=['POST'])
@async_route
async def cleanup_resources():
    """Clean up AI resources (sessions, errors, etc.)."""
    try:
        session_manager = get_session_manager()
        error_handler = get_error_handler()
        
        # Get cleanup parameters
        data = request.json or {}
        max_idle_minutes = data.get('max_idle_minutes', 30)
        error_cleanup_days = data.get('error_cleanup_days', 7)
        
        # Cleanup sessions
        session_cleanup = await session_manager.cleanup_expired_sessions(max_idle_minutes)
        
        # Cleanup errors
        error_cleanup = error_handler.cleanup_old_errors(error_cleanup_days)
        
        return jsonify({
            'cleanup_completed': True,
            'session_cleanup': session_cleanup,
            'error_cleanup': {
                'errors_removed': error_cleanup,
                'days_threshold': error_cleanup_days
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        return jsonify({'error': str(e)}), 500


@ai_debug_bp.route('/monitoring/start', methods=['POST'])
@async_route
async def start_monitoring():
    """Start AI health monitoring."""
    try:
        health_monitor = get_health_monitor()
        await health_monitor.start_monitoring()
        
        return jsonify({
            'success': True,
            'message': 'AI health monitoring started',
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error starting monitoring: {e}")
        return jsonify({'error': str(e)}), 500


@ai_debug_bp.route('/monitoring/stop', methods=['POST'])
@async_route
async def stop_monitoring():
    """Stop AI health monitoring."""
    try:
        health_monitor = get_health_monitor()
        await health_monitor.stop_monitoring()
        
        return jsonify({
            'success': True,
            'message': 'AI health monitoring stopped',
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error stopping monitoring: {e}")
        return jsonify({'error': str(e)}), 500


@ai_debug_bp.route('/logs', methods=['GET'])
def get_ai_logs():
    """Get recent AI-related log entries."""
    try:
        # This would require integration with logging system
        # For now, return a placeholder
        return jsonify({
            'message': 'AI logs endpoint - requires logging integration',
            'suggestion': 'Check unified-server.log for AI-related entries',
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting AI logs: {e}")
        return jsonify({'error': str(e)}), 500


# Error handlers for the blueprint
@ai_debug_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@ai_debug_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500
