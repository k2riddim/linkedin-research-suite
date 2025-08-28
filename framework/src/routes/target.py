from flask import Blueprint, jsonify, request
from src.models import db
from src.models.target import Target
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
target_bp = Blueprint('target', __name__)

@target_bp.route('/targets', methods=['GET'])
def get_targets():
    """Get all targets"""
    try:
        targets = Target.query.all()
        return jsonify([target.to_dict() for target in targets])
    except Exception as e:
        logger.error(f"Error getting targets: {e}")
        return jsonify({'error': 'Failed to retrieve targets'}), 500

@target_bp.route('/targets', methods=['POST'])
def create_target():
    """Add target profile"""
    try:
        data = request.json
        
        # Validate required fields
        if 'linkedin_url' not in data:
            return jsonify({'error': 'Missing required field: linkedin_url'}), 400
        
        # Check if target already exists
        existing_target = Target.query.filter_by(linkedin_url=data['linkedin_url']).first()
        if existing_target:
            return jsonify({'error': 'Target with this LinkedIn URL already exists'}), 409
        
        # Create new target
        target = Target(
            linkedin_url=data['linkedin_url'],
            name=data.get('name'),
            company=data.get('company'),
            industry=data.get('industry'),
            notes=data.get('notes')
        )
        
        db.session.add(target)
        db.session.commit()
        
        logger.info(f"Created new target: {target.linkedin_url}")
        return jsonify(target.to_dict()), 201
        
    except Exception as e:
        logger.error(f"Error creating target: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to create target'}), 500

@target_bp.route('/targets/<target_id>', methods=['GET'])
def get_target(target_id):
    """Get specific target"""
    try:
        target = Target.query.get_or_404(target_id)
        return jsonify(target.to_dict())
    except Exception as e:
        logger.error(f"Error getting target {target_id}: {e}")
        return jsonify({'error': 'Target not found'}), 404

@target_bp.route('/targets/<target_id>', methods=['PUT'])
def update_target(target_id):
    """Update target"""
    try:
        target = Target.query.get_or_404(target_id)
        data = request.json
        
        # Update fields if provided
        if 'linkedin_url' in data:
            # Check if new URL already exists
            existing = Target.query.filter_by(linkedin_url=data['linkedin_url']).filter(Target.id != target_id).first()
            if existing:
                return jsonify({'error': 'LinkedIn URL already exists'}), 409
            target.linkedin_url = data['linkedin_url']
        if 'name' in data:
            target.name = data['name']
        if 'company' in data:
            target.company = data['company']
        if 'industry' in data:
            target.industry = data['industry']
        if 'notes' in data:
            target.notes = data['notes']
        
        db.session.commit()
        
        logger.info(f"Updated target: {target.linkedin_url}")
        return jsonify(target.to_dict())
        
    except Exception as e:
        logger.error(f"Error updating target {target_id}: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update target'}), 500

@target_bp.route('/targets/<target_id>', methods=['DELETE'])
def delete_target(target_id):
    """Delete target"""
    try:
        target = Target.query.get_or_404(target_id)
        db.session.delete(target)
        db.session.commit()
        
        logger.info(f"Deleted target: {target.linkedin_url}")
        return '', 204
        
    except Exception as e:
        logger.error(f"Error deleting target {target_id}: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to delete target'}), 500

@target_bp.route('/targets/<target_id>/insights', methods=['GET'])
def get_target_insights(target_id):
    """Get target insights"""
    try:
        target = Target.query.get_or_404(target_id)
        insights = target.get_insights()
        return jsonify(insights)
    except Exception as e:
        logger.error(f"Error getting insights for target {target_id}: {e}")
        return jsonify({'error': 'Target not found'}), 404

@target_bp.route('/targets/<target_id>/analytics', methods=['POST'])
def update_target_analytics(target_id):
    """Update target analytics"""
    try:
        target = Target.query.get_or_404(target_id)
        data = request.json
        
        # Update analytics
        target.update_analytics(
            visit_count=data.get('visit_count', 0),
            new_account=data.get('new_account', False),
            connection_request=data.get('connection_request', False),
            message_sent=data.get('message_sent', False)
        )
        
        db.session.commit()
        
        logger.info(f"Updated analytics for target: {target.linkedin_url}")
        return jsonify(target.to_dict())
        
    except Exception as e:
        logger.error(f"Error updating analytics for target {target_id}: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update analytics'}), 500

@target_bp.route('/targets/search', methods=['GET'])
def search_targets():
    """Search targets by name, company, or industry"""
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify([])
        
        # Search in name, company, and industry fields
        targets = Target.query.filter(
            db.or_(
                Target.name.ilike(f'%{query}%'),
                Target.company.ilike(f'%{query}%'),
                Target.industry.ilike(f'%{query}%')
            )
        ).limit(50).all()
        
        return jsonify([target.to_dict() for target in targets])
        
    except Exception as e:
        logger.error(f"Error searching targets: {e}")
        return jsonify({'error': 'Search failed'}), 500

@target_bp.route('/targets/stats', methods=['GET'])
def get_targets_stats():
    """Get overall target statistics"""
    try:
        total_targets = Target.query.count()
        total_visits = db.session.query(db.func.sum(Target.total_visits)).scalar() or 0
        total_connections = db.session.query(db.func.sum(Target.connection_requests)).scalar() or 0
        total_messages = db.session.query(db.func.sum(Target.messages_sent)).scalar() or 0
        
        # Calculate average success rate
        avg_success_rate = db.session.query(db.func.avg(Target.success_rate)).scalar() or 0.0
        
        return jsonify({
            'total_targets': total_targets,
            'total_visits': total_visits,
            'total_connections': total_connections,
            'total_messages': total_messages,
            'average_success_rate': round(avg_success_rate, 3)
        })
        
    except Exception as e:
        logger.error(f"Error getting target stats: {e}")
        return jsonify({'error': 'Failed to retrieve statistics'}), 500

