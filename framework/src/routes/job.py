from flask import Blueprint, jsonify, request
from src.models import db
from src.models.job import Job
from src.models.account import Account
from src.models.target import Target
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
job_bp = Blueprint('job', __name__)

@job_bp.route('/jobs', methods=['GET'])
def get_jobs():
    """Get all jobs"""
    try:
        # Get query parameters
        status = request.args.get('status')
        account_id = request.args.get('account_id')
        job_type = request.args.get('type')
        limit = request.args.get('limit', 100, type=int)
        
        # Build query
        query = Job.query
        
        if status:
            query = query.filter(Job.status == status)
        if account_id:
            query = query.filter(Job.account_id == account_id)
        if job_type:
            query = query.filter(Job.type == job_type)
        
        jobs = query.order_by(Job.created_at.desc()).limit(limit).all()
        return jsonify([job.to_dict() for job in jobs])
        
    except Exception as e:
        logger.error(f"Error getting jobs: {e}")
        return jsonify({'error': 'Failed to retrieve jobs'}), 500

@job_bp.route('/jobs/start', methods=['POST'])
def start_job():
    """Start automation job"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['job_type', 'account_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate job type
        valid_types = ['browse', 'connect', 'message', 'monitor']
        if data['job_type'] not in valid_types:
            return jsonify({'error': f'Invalid job type. Must be one of: {valid_types}'}), 400
        
        # Validate account exists
        account = Account.query.get(data['account_id'])
        if not account:
            return jsonify({'error': 'Account not found'}), 404
        
        # Validate target if provided
        target_id = data.get('target_id')
        if target_id:
            target = Target.query.get(target_id)
            if not target:
                return jsonify({'error': 'Target not found'}), 404
        
        # Create new job
        job = Job(
            type=data['job_type'],
            account_id=data['account_id'],
            target_id=target_id,
            status='pending'
        )
        
        # Set job parameters
        parameters = data.get('parameters', {})
        job.set_parameters(parameters)
        
        db.session.add(job)
        db.session.commit()
        
        # In a real implementation, this would trigger the automation engine
        # For now, we'll just mark it as started
        job.start()
        db.session.commit()
        
        logger.info(f"Started job {job.id}: {job.type} for account {job.account_id}")
        return jsonify(job.to_dict()), 201
        
    except Exception as e:
        logger.error(f"Error starting job: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to start job'}), 500

@job_bp.route('/jobs/<job_id>', methods=['GET'])
def get_job(job_id):
    """Get specific job"""
    try:
        job = Job.query.get_or_404(job_id)
        return jsonify(job.to_dict())
    except Exception as e:
        logger.error(f"Error getting job {job_id}: {e}")
        return jsonify({'error': 'Job not found'}), 404

@job_bp.route('/jobs/<job_id>', methods=['PUT'])
def update_job(job_id):
    """Update job"""
    try:
        job = Job.query.get_or_404(job_id)
        data = request.json
        
        # Update fields if provided
        if 'status' in data:
            job.status = data['status']
        if 'progress' in data:
            job.update_progress(data['progress'])
        if 'parameters' in data:
            job.set_parameters(data['parameters'])
        if 'result' in data:
            job.set_result(data['result'])
        if 'error_message' in data:
            job.error_message = data['error_message']
        
        # Update timestamps based on status
        if job.status == 'running' and not job.started_at:
            job.started_at = datetime.utcnow()
        elif job.status in ['completed', 'failed', 'cancelled'] and not job.completed_at:
            job.completed_at = datetime.utcnow()
        
        db.session.commit()
        
        logger.info(f"Updated job {job.id}: status={job.status}, progress={job.progress}")
        return jsonify(job.to_dict())
        
    except Exception as e:
        logger.error(f"Error updating job {job_id}: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update job'}), 500

@job_bp.route('/jobs/<job_id>', methods=['DELETE'])
def delete_job(job_id):
    """Delete job"""
    try:
        job = Job.query.get_or_404(job_id)
        
        # Only allow deletion of completed, failed, or cancelled jobs
        if job.status in ['running', 'pending']:
            return jsonify({'error': 'Cannot delete running or pending jobs'}), 400
        
        db.session.delete(job)
        db.session.commit()
        
        logger.info(f"Deleted job {job.id}")
        return '', 204
        
    except Exception as e:
        logger.error(f"Error deleting job {job_id}: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to delete job'}), 500

@job_bp.route('/jobs/<job_id>/cancel', methods=['POST'])
def cancel_job(job_id):
    """Cancel running job"""
    try:
        job = Job.query.get_or_404(job_id)
        
        if job.status not in ['pending', 'running']:
            return jsonify({'error': 'Job cannot be cancelled'}), 400
        
        job.status = 'cancelled'
        job.completed_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Cancelled job {job.id}")
        return jsonify(job.to_dict())
        
    except Exception as e:
        logger.error(f"Error cancelling job {job_id}: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to cancel job'}), 500

@job_bp.route('/jobs/active', methods=['GET'])
def get_active_jobs():
    """Get active jobs"""
    try:
        jobs = Job.query.filter(Job.status.in_(['pending', 'running'])).order_by(Job.created_at.desc()).all()
        return jsonify([job.to_dict() for job in jobs])
    except Exception as e:
        logger.error(f"Error getting active jobs: {e}")
        return jsonify({'error': 'Failed to retrieve active jobs'}), 500

@job_bp.route('/jobs/stats', methods=['GET'])
def get_job_stats():
    """Get job statistics"""
    try:
        total_jobs = Job.query.count()
        pending_jobs = Job.query.filter_by(status='pending').count()
        running_jobs = Job.query.filter_by(status='running').count()
        completed_jobs = Job.query.filter_by(status='completed').count()
        failed_jobs = Job.query.filter_by(status='failed').count()
        cancelled_jobs = Job.query.filter_by(status='cancelled').count()
        
        # Calculate success rate
        success_rate = 0.0
        if total_jobs > 0:
            success_rate = completed_jobs / total_jobs
        
        return jsonify({
            'total_jobs': total_jobs,
            'pending_jobs': pending_jobs,
            'running_jobs': running_jobs,
            'completed_jobs': completed_jobs,
            'failed_jobs': failed_jobs,
            'cancelled_jobs': cancelled_jobs,
            'success_rate': round(success_rate, 3)
        })
        
    except Exception as e:
        logger.error(f"Error getting job stats: {e}")
        return jsonify({'error': 'Failed to retrieve statistics'}), 500

@job_bp.route('/jobs/types', methods=['GET'])
def get_job_types():
    """Get available job types and their descriptions"""
    return jsonify({
        'browse': {
            'name': 'Browse',
            'description': 'Browse LinkedIn profiles and collect information',
            'parameters': ['duration_minutes', 'engagement_strategy']
        },
        'connect': {
            'name': 'Connect',
            'description': 'Send connection requests to target profiles',
            'parameters': ['message_template', 'max_connections']
        },
        'message': {
            'name': 'Message',
            'description': 'Send messages to connected profiles',
            'parameters': ['message_template', 'delay_between_messages']
        },
        'monitor': {
            'name': 'Monitor',
            'description': 'Monitor target profiles for activity and updates',
            'parameters': ['check_interval', 'notification_settings']
        }
    })

