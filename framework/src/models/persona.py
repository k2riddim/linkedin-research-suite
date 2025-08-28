from src.models import db
from datetime import datetime
import json
import uuid

class Persona(db.Model):
    """
    Persona model for storing AI-generated professional personas
    """
    __tablename__ = 'personas'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    persona_id = db.Column(db.String(100), unique=True, nullable=False)
    
    # Demographic data
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    nationality = db.Column(db.String(100), nullable=False)
    languages = db.Column(db.Text, nullable=True)  # JSON array
    
    # Professional data
    current_position = db.Column(db.String(200), nullable=False)
    current_company = db.Column(db.String(200), nullable=False)
    industry = db.Column(db.String(100), nullable=False)
    experience_years = db.Column(db.Integer, nullable=False)
    education = db.Column(db.Text, nullable=True)  # JSON array
    previous_positions = db.Column(db.Text, nullable=True)  # JSON array
    
    # Skills data
    technical_skills = db.Column(db.Text, nullable=True)  # JSON array
    soft_skills = db.Column(db.Text, nullable=True)  # JSON array
    certifications = db.Column(db.Text, nullable=True)  # JSON array
    languages_spoken = db.Column(db.Text, nullable=True)  # JSON array
    
    # Content data
    headline = db.Column(db.Text, nullable=True)
    summary = db.Column(db.Text, nullable=True)
    about_section = db.Column(db.Text, nullable=True)
    sample_posts = db.Column(db.Text, nullable=True)  # JSON array
    
    # Visual assets
    profile_photo_description = db.Column(db.Text, nullable=True)
    background_image_description = db.Column(db.Text, nullable=True)
    company_logo_description = db.Column(db.Text, nullable=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # Manual email credentials (for manual email mode)
    manual_email = db.Column(db.String(255), nullable=True)
    manual_email_password = db.Column(db.String(255), nullable=True)
    
    # Relationships
    linkedin_accounts = db.relationship('Account', backref='persona', lazy=True, 
                                      foreign_keys='Account.persona_id')
    
    def __repr__(self):
        return f'<Persona {self.first_name} {self.last_name} ({self.persona_id})>'
    
    def to_dict(self):
        """Convert persona to dictionary format"""
        
        def safe_json_loads(data):
            if data:
                try:
                    return json.loads(data)
                except json.JSONDecodeError:
                    return []
            return []
        
        return {
            'id': self.id,
            'persona_id': self.persona_id,
            'manual_email': self.manual_email,
            'manual_email_password': self.manual_email_password,
            'demographic_data': {
                'first_name': self.first_name,
                'last_name': self.last_name,
                'age': self.age,
                'location': self.location,
                'nationality': self.nationality,
                'languages': safe_json_loads(self.languages)
            },
            'professional_data': {
                'current_position': self.current_position,
                'current_company': self.current_company,
                'industry': self.industry,
                'experience_years': self.experience_years,
                'education': safe_json_loads(self.education),
                'previous_positions': safe_json_loads(self.previous_positions)
            },
            'skills_data': {
                'technical_skills': safe_json_loads(self.technical_skills),
                'soft_skills': safe_json_loads(self.soft_skills),
                'certifications': safe_json_loads(self.certifications),
                'languages_spoken': safe_json_loads(self.languages_spoken)
            },
            'content_data': {
                'headline': self.headline,
                'summary': self.summary,
                'about_section': self.about_section,
                'sample_posts': safe_json_loads(self.sample_posts)
            },
            'visual_assets': {
                'profile_photo_description': self.profile_photo_description,
                'background_image_description': self.background_image_description,
                'company_logo_description': self.company_logo_description
            },
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active
        }
    
    @classmethod
    def from_persona_profile(cls, persona_profile):
        """Create Persona from PersonaProfile dataclass"""
        
        def safe_json_dumps(data):
            try:
                return json.dumps(data, ensure_ascii=False)
            except (TypeError, ValueError):
                return json.dumps([])
        
        return cls(
            persona_id=persona_profile.persona_id,
            first_name=persona_profile.demographic_data.first_name,
            last_name=persona_profile.demographic_data.last_name,
            age=persona_profile.demographic_data.age,
            location=persona_profile.demographic_data.location,
            nationality=persona_profile.demographic_data.nationality,
            languages=safe_json_dumps(persona_profile.demographic_data.languages),
            current_position=persona_profile.professional_data.current_position,
            current_company=persona_profile.professional_data.current_company,
            industry=persona_profile.professional_data.industry,
            experience_years=persona_profile.professional_data.experience_years,
            education=safe_json_dumps(persona_profile.professional_data.education),
            previous_positions=safe_json_dumps(persona_profile.professional_data.previous_positions),
            technical_skills=safe_json_dumps(persona_profile.skills_data.technical_skills),
            soft_skills=safe_json_dumps(persona_profile.skills_data.soft_skills),
            certifications=safe_json_dumps(persona_profile.skills_data.certifications),
            languages_spoken=safe_json_dumps(persona_profile.skills_data.languages_spoken),
            headline=persona_profile.content_data.headline,
            summary=persona_profile.content_data.summary,
            about_section=persona_profile.content_data.about_section,
            sample_posts=safe_json_dumps(persona_profile.content_data.sample_posts),
            profile_photo_description=persona_profile.visual_assets.profile_photo_description,
            background_image_description=persona_profile.visual_assets.background_image_description,
            company_logo_description=persona_profile.visual_assets.company_logo_description,
            created_at=persona_profile.created_at
        )


class PersonaUsage(db.Model):
    """
    Track persona usage in LinkedIn account creation
    """
    __tablename__ = 'persona_usage'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    persona_id = db.Column(db.String(36), db.ForeignKey('personas.id'), nullable=False)
    account_id = db.Column(db.String(36), db.ForeignKey('accounts.id'), nullable=True)
    usage_type = db.Column(db.String(50), nullable=False)  # 'account_creation', 'content_generation', etc.
    used_at = db.Column(db.DateTime, default=datetime.utcnow)
    success = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text, nullable=True)
    
    # Relationships
    persona = db.relationship('Persona', backref='usages')
    account = db.relationship('Account', backref='persona_usages')
    
    def __repr__(self):
        return f'<PersonaUsage {self.persona_id} -> {self.usage_type}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'persona_id': self.persona_id,
            'account_id': self.account_id,
            'usage_type': self.usage_type,
            'used_at': self.used_at.isoformat() if self.used_at else None,
            'success': self.success,
            'notes': self.notes
        }

