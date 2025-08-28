from src.models import db
from datetime import datetime
import uuid

class Target(db.Model):
    """
    Target model for managing LinkedIn target profiles
    """
    __tablename__ = 'targets'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    linkedin_url = db.Column(db.String(500), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=True)
    company = db.Column(db.String(200), nullable=True)
    industry = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)
    
    # Analytics fields
    total_visits = db.Column(db.Integer, default=0)
    unique_accounts = db.Column(db.Integer, default=0)
    connection_requests = db.Column(db.Integer, default=0)
    messages_sent = db.Column(db.Integer, default=0)
    success_rate = db.Column(db.Float, default=0.0)
    
    # Relationships
    jobs = db.relationship('Job', backref='target', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Target {self.name} ({self.linkedin_url})>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'linkedin_url': self.linkedin_url,
            'name': self.name,
            'company': self.company,
            'industry': self.industry,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'notes': self.notes,
            'total_visits': self.total_visits,
            'unique_accounts': self.unique_accounts,
            'connection_requests': self.connection_requests,
            'messages_sent': self.messages_sent,
            'success_rate': self.success_rate
        }
    
    def update_analytics(self, visit_count=0, new_account=False, connection_request=False, message_sent=False):
        """Update target analytics"""
        self.total_visits += visit_count
        if new_account:
            self.unique_accounts += 1
        if connection_request:
            self.connection_requests += 1
        if message_sent:
            self.messages_sent += 1
        
        # Calculate success rate (connections + messages / total visits)
        if self.total_visits > 0:
            self.success_rate = (self.connection_requests + self.messages_sent) / self.total_visits
        else:
            self.success_rate = 0.0
    
    def get_insights(self):
        """Get target insights"""
        average_duration = 45.2  # This would be calculated from activities
        
        return {
            'target_id': self.id,
            'total_visits': self.total_visits,
            'unique_accounts': self.unique_accounts,
            'average_duration': average_duration,
            'connection_requests': self.connection_requests,
            'messages_sent': self.messages_sent,
            'success_rate': self.success_rate
        }

