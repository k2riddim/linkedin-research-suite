from src.models import db
from datetime import datetime
import uuid
import json

class Account(db.Model):
    """
    Account model for storing LinkedIn account information
    """
    __tablename__ = 'accounts'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Basic account information
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    
    # Account status tracking
    status = db.Column(db.String(50), default='new')  # new, creating_linkedin, verifying_email, verifying_sms, completed, failed
    
    # LinkedIn specific fields
    linkedin_created = db.Column(db.Boolean, default=False)
    linkedin_creation_started = db.Column(db.DateTime, nullable=True)
    linkedin_url = db.Column(db.String(500), nullable=True)
    
    # Persona relationship
    persona_id = db.Column(db.String(36), db.ForeignKey('personas.id'), nullable=True)
    
    # Verification details
    email_verified = db.Column(db.Boolean, default=False)
    sms_verified = db.Column(db.Boolean, default=False)
    verification_phone = db.Column(db.String(20), nullable=True)
    verification_email = db.Column(db.String(200), nullable=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Additional fields for automation
    proxy_used = db.Column(db.String(500), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    creation_logs = db.Column(db.Text, nullable=True)  # JSON string for logs
    
    def __repr__(self):
        return f'<Account {self.email}>'
    
    def set_profile_data(self, profile_data):
        """Set profile data for the account"""
        if isinstance(profile_data, dict):
            # Store profile data as JSON in creation_logs field
            if self.creation_logs:
                try:
                    existing_logs = json.loads(self.creation_logs)
                    if isinstance(existing_logs, dict):
                        existing_logs['profile_data'] = profile_data
                    else:
                        existing_logs = {'profile_data': profile_data, 'logs': existing_logs}
                    self.creation_logs = json.dumps(existing_logs)
                except (json.JSONDecodeError, TypeError):
                    self.creation_logs = json.dumps({'profile_data': profile_data})
        else:
                self.creation_logs = json.dumps({'profile_data': profile_data})
    
    def get_profile_data(self):
        """Get profile data for the account"""
        if self.creation_logs:
            try:
                logs = json.loads(self.creation_logs)
                if isinstance(logs, dict):
                    return logs.get('profile_data', {})
            except (json.JSONDecodeError, TypeError):
                pass
        return {}

    def to_dict(self):
        profile_data = self.get_profile_data()
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'status': self.status,
            'linkedin_created': self.linkedin_created,
            'linkedin_creation_started': self.linkedin_creation_started.isoformat() if self.linkedin_creation_started else None,
            'linkedin_url': self.linkedin_url,
            'persona_id': self.persona_id,
            'email_verified': self.email_verified,
            'sms_verified': self.sms_verified,
            'verification_phone': self.verification_phone,
            'verification_email': self.verification_email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'proxy_used': self.proxy_used,
            'user_agent': self.user_agent,
            'profile_data': profile_data
        }

# Placeholder models for Session and Activity - will be implemented properly later
class Session(db.Model):
    """Placeholder Session model"""
    __tablename__ = 'sessions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    account_id = db.Column(db.String(36), db.ForeignKey('accounts.id'), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(50), default='active')
    
    def to_dict(self):
        return {
            'id': self.id,
            'account_id': self.account_id,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'status': self.status
        }

class Activity(db.Model):
    """Placeholder Activity model"""
    __tablename__ = 'activities'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    account_id = db.Column(db.String(36), db.ForeignKey('accounts.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    activity_type = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'account_id': self.account_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'activity_type': self.activity_type,
            'description': self.description
        }