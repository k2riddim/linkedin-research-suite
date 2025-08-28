#!/usr/bin/env python3
"""
Database Migration Script for LinkedIn Research Suite
Adds missing columns to the accounts table to match the new Account model
"""

import os
import sys
import logging
from datetime import datetime

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from sqlalchemy import text, inspect
from src.models import db, Account, Session, Activity, Persona, PersonaUsage, Job, Target, User
from src.config import config
from flask import Flask

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_app():
    """Create Flask app with database configuration"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = config.security.session_secret
    app.config['SQLALCHEMY_DATABASE_URI'] = config.database.url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def check_column_exists(connection, table_name, column_name):
    """Check if a column exists in a table"""
    try:
        inspector = inspect(connection)
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        return column_name in columns
    except Exception as e:
        logger.warning(f"Could not inspect table {table_name}: {e}")
        return False

def migrate_accounts_table(connection):
    """Migrate the accounts table to add missing columns"""
    logger.info("Migrating accounts table...")
    
    # List of columns to add with their SQL definitions
    new_columns = [
        ('linkedin_creation_started', 'TIMESTAMP NULL'),
        ('linkedin_url', 'VARCHAR(500) NULL'),
        ('persona_id', 'VARCHAR(36) NULL'),
        ('email_verified', 'BOOLEAN DEFAULT FALSE'),
        ('sms_verified', 'BOOLEAN DEFAULT FALSE'),
        ('verification_phone', 'VARCHAR(20) NULL'),
        ('verification_email', 'VARCHAR(200) NULL'),
        ('proxy_used', 'VARCHAR(500) NULL'),
        ('user_agent', 'TEXT NULL'),
        ('creation_logs', 'TEXT NULL')
    ]
    
    for column_name, column_def in new_columns:
        if not check_column_exists(connection, 'accounts', column_name):
            try:
                sql = f"ALTER TABLE accounts ADD COLUMN {column_name} {column_def};"
                connection.execute(text(sql))
                logger.info(f"✅ Added column: accounts.{column_name}")
            except Exception as e:
                logger.error(f"❌ Failed to add column accounts.{column_name}: {e}")
        else:
            logger.info(f"✓ Column already exists: accounts.{column_name}")

def create_missing_tables(app):
    """Create any missing tables"""
    logger.info("Creating missing tables...")
    try:
        with app.app_context():
            # This will create tables that don't exist but won't modify existing ones
            db.create_all()
        logger.info("✅ All tables ensured to exist")
    except Exception as e:
        logger.error(f"❌ Failed to create tables: {e}")

def run_migration():
    """Run the complete database migration"""
    logger.info("🚀 Starting LinkedIn Research Suite Database Migration")
    logger.info(f"Database URL: {config.database.url}")
    
    app = create_app()
    
    try:
        with app.app_context():
            # Get database connection
            connection = db.engine.connect()
            
            # Start transaction
            trans = connection.begin()
            
            try:
                # Migrate accounts table
                migrate_accounts_table(connection)
                
                # Commit the migration
                trans.commit()
                logger.info("✅ Migration committed successfully")
                
            except Exception as e:
                trans.rollback()
                logger.error(f"❌ Migration failed, rolled back: {e}")
                return False
            finally:
                connection.close()
        
        # Create any missing tables
        create_missing_tables(app)
        
        logger.info("🎉 Database migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
