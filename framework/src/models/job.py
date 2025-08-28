from src.models import db
from datetime import datetime
import json
import uuid

class Job(db.Model):
    """
    Job model for managing automation jobs
    """
    __tablename__ = 'jobs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    type = db.Column(db.String(50), nullable=False)  # browse, connect, message, monitor
    account_id = db.Column(db.String(36), db.ForeignKey('accounts.id'), nullable=False)
    target_id = db.Column(db.String(36), db.ForeignKey('targets.id'), nullable=True)
    status = db.Column(db.String(50), default='pending')  # pending, running, completed, failed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    parameters = db.Column(db.Text, nullable=True)  # JSON string
    result = db.Column(db.Text, nullable=True)  # JSON string
    error_message = db.Column(db.Text, nullable=True)
    progress = db.Column(db.Float, default=0.0)
    
    def __repr__(self):
        return f'<Job {self.type} for Account {self.account_id}>'
    
    def to_dict(self):
        parameters = {}
        if self.parameters:
            try:
                parameters = json.loads(self.parameters)
            except json.JSONDecodeError:
                parameters = {}
        
        result = {}
        if self.result:
            try:
                result = json.loads(self.result)
            except json.JSONDecodeError:
                result = {}
                
        return {
            'id': self.id,
            'type': self.type,
            'account_id': self.account_id,
            'target_id': self.target_id,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'parameters': parameters,
            'result': result,
            'error_message': self.error_message,
            'progress': self.progress
        }
    
    def set_parameters(self, data):
        """Set job parameters as JSON string"""
        self.parameters = json.dumps(data) if data else None
    
    def get_parameters(self):
        """Get job parameters as dictionary"""
        if self.parameters:
            try:
                return json.loads(self.parameters)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_result(self, data):
        """Set job result as JSON string"""
        self.result = json.dumps(data) if data else None
    
    def get_result(self):
        """Get job result as dictionary"""
        if self.result:
            try:
                return json.loads(self.result)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def start(self):
        """Mark job as started"""
        self.status = 'running'
        self.started_at = datetime.utcnow()
    
    def complete(self, result_data=None):
        """Mark job as completed"""
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
        self.progress = 1.0
        if result_data:
            self.set_result(result_data)
    
    def fail(self, error_message):
        """Mark job as failed"""
        self.status = 'failed'
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
    
    def update_progress(self, progress):
        """Update job progress (0.0 to 1.0)"""
        self.progress = max(0.0, min(1.0, progress))

