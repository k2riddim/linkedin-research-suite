from flask import Blueprint, jsonify, request
import asyncio
import logging
from src.services.service_manager import get_service_manager

logger = logging.getLogger(__name__)
service_bp = Blueprint('service', __name__)

@service_bp.route('/services/health', methods=['GET'])
def get_services_health():
    """Get health status of all external services"""
    try:
        async def _check_health():
            manager = await get_service_manager()
            return await manager.check_all_services_health()
        
        health_status = asyncio.run(_check_health())
        
        # Convert to JSON-serializable format
        result = {}
        for service_name, health in health_status.items():
            result[service_name] = {
                'service_name': health.service_name,
                'is_healthy': health.is_healthy,
                'last_check': health.last_check.isoformat(),
                'error_message': health.error_message,
                'response_time': health.response_time
            }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error checking services health: {e}")
        return jsonify({'error': 'Failed to check services health'}), 500

@service_bp.route('/services/status', methods=['GET'])
def get_services_status():
    """Get overall service status and resource usage"""
    try:
        async def _get_status():
            manager = await get_service_manager()
            return manager.get_service_status()
        
        status = asyncio.run(_get_status())
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error getting services status: {e}")
        return jsonify({'error': 'Failed to get services status'}), 500

@service_bp.route('/services/sms/balance', methods=['GET'])
def get_sms_balance():
    """Get SMS service balance"""
    try:
        async def _get_balance():
            manager = await get_service_manager()
            if manager.sms_manager:
                return await manager.sms_manager.check_balance()
            else:
                return 0.0
        
        balance = asyncio.run(_get_balance())
        return jsonify({'balance': balance, 'currency': 'USD'})
        
    except Exception as e:
        logger.error(f"Error getting SMS balance: {e}")
        return jsonify({'error': 'Failed to get SMS balance'}), 500

@service_bp.route('/services/sms/countries', methods=['GET'])
def get_sms_countries():
    """Get available countries for SMS service"""
    try:
        async def _get_countries():
            manager = await get_service_manager()
            if manager.sms_manager:
                return await manager.sms_manager.get_available_countries()
            else:
                return []
        
        countries = asyncio.run(_get_countries())
        return jsonify(countries)
        
    except Exception as e:
        logger.error(f"Error getting SMS countries: {e}")
        return jsonify({'error': 'Failed to get SMS countries'}), 500

@service_bp.route('/services/sms/prices', methods=['GET'])
def get_sms_prices():
    """Get SMS service prices"""
    try:
        country = request.args.get('country', 'france')
        
        async def _get_prices():
            manager = await get_service_manager()
            if manager.sms_manager:
                return await manager.sms_manager.get_service_prices(country)
            else:
                return {}
        
        prices = asyncio.run(_get_prices())
        return jsonify(prices)
        
    except Exception as e:
        logger.error(f"Error getting SMS prices: {e}")
        return jsonify({'error': 'Failed to get SMS prices'}), 500

@service_bp.route('/services/email/domains', methods=['GET'])
def get_email_domains():
    """Get available email domains"""
    try:
        async def _get_domains():
            manager = await get_service_manager()
            if manager.email_manager:
                return await manager.email_manager.get_available_domains()
            else:
                return []
        
        domains = asyncio.run(_get_domains())
        return jsonify(domains)
        
    except Exception as e:
        logger.error(f"Error getting email domains: {e}")
        return jsonify({'error': 'Failed to get email domains'}), 500

@service_bp.route('/services/proxy/status', methods=['GET'])
def get_proxy_status():
    """Get proxy pool status"""
    try:
        async def _get_proxy_status():
            manager = await get_service_manager()
            if manager.proxy_manager:
                return await manager.proxy_manager.get_proxy_pool_status()
            else:
                return {}
        
        status = asyncio.run(_get_proxy_status())
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error getting proxy status: {e}")
        return jsonify({'error': 'Failed to get proxy status'}), 500

@service_bp.route('/services/test', methods=['POST'])
def test_services():
    """Test all external services"""
    try:
        data = request.json or {}
        test_account_id = data.get('test_account_id', 'test_account')
        
        async def _test_services():
            manager = await get_service_manager()
            
            # Test resource creation
            resources = await manager.create_account_resources(
                test_account_id, 
                "Test", 
                "User"
            )
            
            # Cleanup test resources
            if 'email' in resources and resources['email'].success:
                await manager.cleanup_account_resources(
                    test_account_id, 
                    resources['email'].email_address
                )
            else:
                await manager.cleanup_account_resources(test_account_id)
            
            return resources
        
        test_results = asyncio.run(_test_services())
        
        # Format results for response
        result = {
            'test_completed': True,
            'timestamp': asyncio.run(asyncio.coroutine(lambda: __import__('datetime').datetime.now().isoformat())()),
            'results': {}
        }
        
        if 'email' in test_results:
            result['results']['email'] = {
                'success': test_results['email'].success,
                'error': test_results['email'].error_message
            }
        
        if 'sms' in test_results:
            result['results']['sms'] = {
                'success': test_results['sms'].success,
                'error': test_results['sms'].error_message
            }
        
        if 'proxy' in test_results:
            result['results']['proxy'] = {
                'success': test_results['proxy'].success,
                'error': test_results['proxy'].error_message
            }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error testing services: {e}")
        return jsonify({'error': 'Failed to test services'}), 500

@service_bp.route('/services/resources/create', methods=['POST'])
def create_account_resources():
    """Create resources for account creation"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['account_id', 'first_name', 'last_name']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        async def _create_resources():
            manager = await get_service_manager()
            return await manager.create_account_resources(
                data['account_id'],
                data['first_name'],
                data['last_name']
            )
        
        resources = asyncio.run(_create_resources())
        
        # Format response
        result = {
            'account_id': data['account_id'],
            'success': 'error' not in resources,
            'resources': {}
        }
        
        if 'email' in resources:
            result['resources']['email'] = {
                'success': resources['email'].success,
                'email_address': resources['email'].email_address if resources['email'].success else None,
                'error': resources['email'].error_message
            }
        
        if 'sms' in resources:
            result['resources']['sms'] = {
                'success': resources['sms'].success,
                'phone_number': resources['sms'].phone_number if resources['sms'].success else None,
                'activation_id': resources['sms'].activation_id if resources['sms'].success else None,
                'error': resources['sms'].error_message
            }
        
        if 'proxy' in resources:
            result['resources']['proxy'] = {
                'success': resources['proxy'].success,
                'session_id': resources['proxy'].session_id if resources['proxy'].success else None,
                'error': resources['proxy'].error_message
            }
        
        if 'error' in resources:
            result['error'] = resources['error']
            return jsonify(result), 500
        
        return jsonify(result), 201
        
    except Exception as e:
        logger.error(f"Error creating account resources: {e}")
        return jsonify({'error': 'Failed to create account resources'}), 500

@service_bp.route('/services/resources/cleanup', methods=['POST'])
def cleanup_account_resources():
    """Cleanup resources for an account"""
    try:
        data = request.json
        
        if 'account_id' not in data:
            return jsonify({'error': 'Missing required field: account_id'}), 400
        
        async def _cleanup_resources():
            manager = await get_service_manager()
            return await manager.cleanup_account_resources(
                data['account_id'],
                data.get('email')
            )
        
        success = asyncio.run(_cleanup_resources())
        
        return jsonify({
            'account_id': data['account_id'],
            'cleanup_successful': success
        })
        
    except Exception as e:
        logger.error(f"Error cleaning up account resources: {e}")
        return jsonify({'error': 'Failed to cleanup account resources'}), 500

