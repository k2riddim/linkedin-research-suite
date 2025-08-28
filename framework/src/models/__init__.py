from flask_sqlalchemy import SQLAlchemy

# Shared database instance
db = SQLAlchemy()

# Import all models to ensure they're registered with SQLAlchemy
from src.models.account import Account, Session, Activity
from src.models.persona import Persona, PersonaUsage
from src.models.job import Job
from src.models.target import Target
from src.models.user import User

# Make models available for import
__all__ = ['db', 'Account', 'Session', 'Activity', 'Persona', 'PersonaUsage', 'Job', 'Target', 'User']
