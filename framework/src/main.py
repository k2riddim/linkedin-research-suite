import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
from src.socketio_bus import backend_log_queue, progress_queue

# Import all models and shared db
from src.models import db
from src.models.user import User
from src.models.account import Account, Session, Activity
from src.models.target import Target
from src.models.job import Job
from src.models.persona import Persona, PersonaUsage

# Import configuration
from src.config import config

# Import routes
from src.routes.user import user_bp
from src.routes.account import account_bp
from src.routes.target import target_bp
from src.routes.job import job_bp
from src.routes.service import service_bp
from src.routes.ai import ai_bp
from src.routes.automation import automation_bp
from src.routes.analytics import analytics_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Configuration
app.config['SECRET_KEY'] = config.security.session_secret
app.config['SQLALCHEMY_DATABASE_URI'] = config.database.url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Enable CORS for all routes
CORS(app, origins="*")

# Initialize SocketIO for real-time features
# Enable cross-worker event delivery via Redis if available
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='threading',
    message_queue=None
)

# Socket.IO queue drainers (started lazily to avoid blocking server bind)
_drainers_started = False

def _drain_backend_log_queue():
    while True:
        try:
            payload = backend_log_queue.get()
            socketio.emit('backend_log', payload, namespace='/')
        except Exception:
            pass
        finally:
            try:
                socketio.sleep(0)
            except Exception:
                pass

def _drain_progress_queue():
    while True:
        try:
            payload = progress_queue.get()
            room = payload.pop('_room', None)
            socketio.emit('enhanced_progress_update', payload, room=room)
        except Exception:
            pass
        finally:
            try:
                socketio.sleep(0)
            except Exception:
                pass

def _ensure_drainers_started():
    global _drainers_started
    if not _drainers_started:
        try:
            socketio.start_background_task(_drain_backend_log_queue)
            socketio.start_background_task(_drain_progress_queue)
            _drainers_started = True
            logger.info('Socket.IO drainers started')
        except Exception as _e:
            logger.error(f'Failed to start drainers: {_e}')

# Register blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(account_bp, url_prefix='/api')
app.register_blueprint(target_bp, url_prefix='/api')
app.register_blueprint(job_bp, url_prefix='/api')
app.register_blueprint(service_bp, url_prefix='/api')
app.register_blueprint(ai_bp, url_prefix='/api')
app.register_blueprint(automation_bp, url_prefix='/api')
app.register_blueprint(analytics_bp, url_prefix='/api')

# Initialize database
db.init_app(app)

# Create database tables
with app.app_context():
    db.create_all()
    # Lightweight migration for manual email mode (safe if columns already exist)
    try:
        from sqlalchemy import text
        engine = db.get_engine()
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE personas ADD COLUMN IF NOT EXISTS manual_email VARCHAR(255)"))
            conn.execute(text("ALTER TABLE personas ADD COLUMN IF NOT EXISTS manual_email_password VARCHAR(255)"))
            conn.commit()
    except Exception as _migrate_e:
        # Non-fatal; table may already exist without support for IF NOT EXISTS on some backends
        try:
            import logging as _logging
            _logging.getLogger(__name__).warning(f"Migration attempt failed or not supported: {_migrate_e}")
        except Exception:
            pass

# Setup logging
logging.basicConfig(
    level=getattr(logging, config.application.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Forward WARNING/ERROR logs to frontend via SocketIO
class SocketIOLogHandler(logging.Handler):
    """Custom logging handler to emit logs to frontend in real-time."""
    def emit(self, record: logging.LogRecord):
        try:
            from datetime import datetime as _dt
            payload = {
                'timestamp': _dt.utcnow().isoformat(),
                'level': record.levelname,
                'logger': record.name,
                'message': self.format(record)
            }
            # Enqueue for the greenlet drainer (safe from any thread)
            from src.socketio_bus import enqueue_backend_log
            enqueue_backend_log(payload)
        except Exception:
            # Avoid recursive logging on handler failure
            pass

socketio_log_handler = SocketIOLogHandler(level=logging.INFO)
socketio_log_handler.setFormatter(logging.Formatter('%(message)s'))
root_logger = logging.getLogger()
# Avoid installing the SocketIO log handler multiple times (prevents duplicate frontend logs)
_already_installed = any(isinstance(h, SocketIOLogHandler) for h in root_logger.handlers)
if not _already_installed:
    root_logger.addHandler(socketio_log_handler)

# Health check endpoint
@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0',
        'config': config.to_dict()
    })

# WebSocket event handlers for LinkedIn account creation progress
from flask_socketio import emit, join_room, leave_room

# Track active connections per account
active_connections = {}

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    from flask import request
    logger.info(f'Client connected: {request.sid}')
    emit('connected', {'status': 'connected', 'session_id': request.sid})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    from flask import request
    logger.info(f'Client disconnected: {request.sid}')
    
    # Remove from all account rooms
    for account_id in list(active_connections.keys()):
        if request.sid in active_connections[account_id]:
            active_connections[account_id].discard(request.sid)
            if not active_connections[account_id]:
                del active_connections[account_id]

@socketio.on('join_account_room')
def handle_join_account_room(data):
    """Join room for specific account creation tracking"""
    from flask import request
    try:
        account_id = data.get('account_id')
        if not account_id:
            emit('error', {'message': 'Account ID required'})
            return
        
        room_name = f"account_{account_id}"
        # Guard: avoid duplicate joins/logs
        if account_id not in active_connections:
            active_connections[account_id] = set()
        if request.sid not in active_connections[account_id]:
            join_room(room_name)
            active_connections[account_id].add(request.sid)
            logger.info(f"Client {request.sid} joined room for account {account_id}")
            emit('joined_room', {
                'account_id': account_id,
                'room': room_name,
                'message': f'Monitoring account creation for {account_id}'
            })
        else:
            # Already in room; do not re-emit to prevent duplicate frontend lines
            pass
        
    except Exception as e:
        logger.error(f"Error joining room: {e}")
        emit('error', {'message': 'Failed to join room'})

@socketio.on('leave_account_room')
def handle_leave_account_room(data):
    """Leave account creation room"""
    from flask import request
    try:
        account_id = data.get('account_id')
        if not account_id:
            return
        
        room_name = f"account_{account_id}"
        leave_room(room_name)
        
        # Remove from tracking
        if account_id in active_connections:
            active_connections[account_id].discard(request.sid)
            if not active_connections[account_id]:
                del active_connections[account_id]
        
        logger.info(f"Client {request.sid} left room for account {account_id}")
        emit('left_room', {'account_id': account_id})
        
    except Exception as e:
        logger.error(f"Error leaving room: {e}")

@socketio.on('get_account_status')
def handle_get_account_status(data):
    """Get current status of account creation"""
    try:
        account_id = data.get('account_id')
        if not account_id:
            emit('error', {'message': 'Account ID required'})
            return
        
        # Get account status from database
        account = Account.query.get(account_id)
        
        if not account:
            emit('error', {'message': 'Account not found'})
            return
        
        status_data = {
            'account_id': account_id,
            'status': account.status,
            'linkedin_created': account.linkedin_created,
            'creation_started': account.linkedin_creation_started.isoformat() if account.linkedin_creation_started else None,
            'creation_completed': account.linkedin_creation_completed.isoformat() if account.linkedin_creation_completed else None,
            'linkedin_url': account.linkedin_url
        }
        
        emit('account_status', status_data)
        
    except Exception as e:
        logger.error(f"Error getting account status: {e}")
        emit('error', {'message': 'Failed to get account status'})

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# Frontend serving
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

if __name__ == '__main__':
    try:
        config.validate()
        logger.info(f"Starting LinkedIn Research Framework on {config.application.host}:{config.application.port}")
        # Start Socket.IO server and then start drainers lazily in a background task
        def _post_start():
            try:
                _ensure_drainers_started()
            finally:
                try:
                    socketio.sleep(0)
                except Exception:
                    pass

        socketio.start_background_task(_post_start)
        socketio.run(
            app, 
            host=config.application.host, 
            port=config.application.port, 
            debug=config.application.debug,
            allow_unsafe_werkzeug=True
        )
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)