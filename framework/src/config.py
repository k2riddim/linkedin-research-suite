import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class ExternalServiceConfig:
    """Configuration for external services"""
    fivesim_api_key: Optional[str] = None
    emailondeck_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    skyvern_api_key: Optional[str] = None
    skyvern_workspace_id: Optional[str] = None

@dataclass
class DatabaseConfig:
    """Database configuration"""
    url: str = "sqlite:///./data/app.db"
    postgres_host: Optional[str] = None
    postgres_port: int = 5432
    postgres_db: Optional[str] = None
    postgres_user: Optional[str] = None
    postgres_password: Optional[str] = None

@dataclass
class SecurityConfig:
    """Security configuration"""
    encryption_key: str = "default_32_char_encryption_key_123"
    session_secret: str = "default_session_secret_key"
    jwt_secret: str = "default_jwt_secret_key"

@dataclass
class ApplicationConfig:
    """Application configuration"""
    debug: bool = False
    log_level: str = "INFO"
    workers: int = 2
    host: str = "0.0.0.0"
    port: int = 5001

class Config:
    """Main configuration class"""
    
    def __init__(self):
        self.external_services = ExternalServiceConfig(
            fivesim_api_key=os.getenv('FIVESIM_API_KEY'),
            emailondeck_api_key=os.getenv('EMAILONDECK_API_KEY'),
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            skyvern_api_key=os.getenv('SKYVERN_API_KEY'),
            skyvern_workspace_id=os.getenv('SKYVERN_WORKSPACE_ID')
        )
        
        # Database configuration with PostgreSQL support
        postgres_host = os.getenv('POSTGRES_HOST') or os.getenv('POSTGRES_IP')
        postgres_port = int(os.getenv('POSTGRES_PORT', '5432'))
        postgres_db = os.getenv('POSTGRES_DB')
        postgres_user = os.getenv('POSTGRES_USER')
        postgres_password = os.getenv('POSTGRES_PASSWORD')
        
        # Construct PostgreSQL URL if all required parameters are provided
        if postgres_host and postgres_db and postgres_user and postgres_password:
            database_url = f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"
            print(f"Using PostgreSQL: {postgres_user}@{postgres_host}:{postgres_port}/{postgres_db}")
        else:
            database_url = os.getenv('DATABASE_URL', 'sqlite:///./data/app.db')
            print(f"Using SQLite: {database_url}")
            # Ensure the data directory exists for SQLite
            os.makedirs('./data', exist_ok=True)
        
        self.database = DatabaseConfig(
            url=database_url,
            postgres_host=postgres_host,
            postgres_port=postgres_port,
            postgres_db=postgres_db,
            postgres_user=postgres_user,
            postgres_password=postgres_password
        )
        
        self.security = SecurityConfig(
            encryption_key=os.getenv('ENCRYPTION_KEY', 'default_32_char_encryption_key_123'),
            session_secret=os.getenv('SESSION_SECRET', 'default_session_secret_key'),
            jwt_secret=os.getenv('JWT_SECRET', 'default_jwt_secret_key')
        )
        
        self.application = ApplicationConfig(
            debug=os.getenv('DEBUG', 'false').lower() == 'true',
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            workers=int(os.getenv('WORKERS', '2')),
            host=os.getenv('HOST', '0.0.0.0'),
            port=int(os.getenv('PORT', '5001'))
        )
    
    def validate(self):
        """Validate configuration"""
        errors = []
        
        # Check required external service keys
        if not self.external_services.openai_api_key:
            errors.append("OPENAI_API_KEY is required")
        
        # Add other validation as needed
        
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
        
        return True
    
    def to_dict(self):
        """Convert config to dictionary (excluding sensitive data)"""
        return {
            'database': {
                'url': self.database.url.replace(os.path.expanduser('~'), '~'),  # Hide full path
                'type': 'postgresql' if 'postgresql://' in self.database.url else 'sqlite',
                'postgres_configured': bool(self.database.postgres_host and self.database.postgres_db)
            },
            'application': {
                'debug': self.application.debug,
                'log_level': self.application.log_level,
                'workers': self.application.workers,
                'host': self.application.host,
                'port': self.application.port
            },
            'external_services': {
                'fivesim_configured': bool(self.external_services.fivesim_api_key),
                'emailondeck_configured': bool(self.external_services.emailondeck_api_key),
                'openai_configured': bool(self.external_services.openai_api_key),
                'skyvern_configured': bool(self.external_services.skyvern_api_key and self.external_services.skyvern_workspace_id)
            }
        }

# Global config instance
config = Config()