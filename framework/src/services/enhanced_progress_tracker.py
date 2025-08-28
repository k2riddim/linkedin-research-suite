"""
Enhanced Progress Tracker - Provides detailed real-time logging for LinkedIn account creation
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class LogLevel(Enum):
    DEBUG = "debug"
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"

class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    SKIPPED = "skipped"

@dataclass
class SubStep:
    """Represents a sub-step within a main step"""
    id: str
    name: str
    description: str
    status: StepStatus = StepStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}

@dataclass
class MainStep:
    """Represents a main step in the LinkedIn creation process"""
    id: str
    name: str
    description: str
    sub_steps: List[SubStep]
    status: StepStatus = StepStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress_percentage: int = 0

@dataclass
class ProgressLog:
    """Individual progress log entry"""
    timestamp: datetime
    level: LogLevel
    step_id: str
    sub_step_id: Optional[str]
    message: str
    details: Dict[str, Any]
    execution_time: Optional[float] = None

class EnhancedProgressTracker:
    """Enhanced progress tracker with detailed sub-step logging"""
    
    def __init__(self, account_id: str):
        self.account_id = account_id
        self.logs: List[ProgressLog] = []
        
        # Define all main steps and their sub-steps
        self.main_steps = [
            MainStep(
                id="init",
                name="Initialisation du processus",
                description="Préparation des données et validation",
                sub_steps=[
                    SubStep("fetch_account", "Récupération du compte", "Chargement des données du compte depuis la base"),
                    SubStep("fetch_persona", "Récupération de la persona", "Chargement des données de la persona"),
                    SubStep("validate_data", "Validation des données", "Vérification de la cohérence des données"),
                ]
            ),
            MainStep(
                id="external_services",
                name="Configuration des services externes",
                description="Configuration EmailOnDeck, proxy GeoNode",
                sub_steps=[
                    SubStep("email_service", "Service Email", "Configuration EmailOnDeck API"),
                    SubStep("proxy_service", "Service Proxy", "Configuration GeoNode proxy"),
                    SubStep("sms_service", "Service SMS", "Configuration 5SIM pour vérifications"),
                    SubStep("validate_services", "Validation services", "Test de connectivité des services"),
                ]
            ),
            MainStep(
                id="browser_launch",
                name="Lancement du navigateur sécurisé", 
                description="Création du navigateur avec mesures anti-détection",
                sub_steps=[
                    SubStep("generate_fingerprint", "Génération empreinte", "Création d'une empreinte browser réaliste"),
                    SubStep("launch_browser", "Démarrage navigateur", "Lancement de Playwright avec stealth"),
                    SubStep("configure_proxy", "Configuration proxy", "Application de la configuration proxy"),
                    SubStep("test_browser", "Test navigateur", "Vérification du fonctionnement"),
                ]
            ),
            MainStep(
                id="linkedin_navigation",
                name="Navigation vers LinkedIn",
                description="Accès au site LinkedIn avec comportement humain",
                sub_steps=[
                    SubStep("navigate_homepage", "Page d'accueil", "Navigation vers linkedin.com"),
                    SubStep("detect_layout", "Détection layout", "Analyse de la structure de la page"),
                    SubStep("find_signup", "Localisation inscription", "Recherche du bouton d'inscription"),
                    SubStep("human_behavior", "Simulation humaine", "Mouvements de souris et délais"),
                ]
            ),
            MainStep(
                id="account_creation",
                name="Création du compte LinkedIn",
                description="Remplissage et soumission du formulaire d'inscription",
                sub_steps=[
                    SubStep("mcp_orchestration", "Orchestration MCP", "Pilotage par agent LLM via MCP"),
                    SubStep("navigate_signup", "Navigation inscription", "Accès à la page d'inscription"),
                    SubStep("fill_credentials", "Identifiants", "Saisie email et mot de passe"),
                    SubStep("fill_names", "Noms", "Saisie prénom et nom"),
                    SubStep("fill_phone", "Téléphone", "Saisie du numéro de téléphone"),
                    SubStep("detect_verification", "Détection vérification", "Détection de la demande de code"),
                    SubStep("fill_personal", "Informations personnelles", "Saisie nom, prénom"),
                    SubStep("fill_email", "Adresse email", "Saisie de l'email généré"),
                    SubStep("fill_password", "Mot de passe", "Saisie du mot de passe sécurisé"),
                    SubStep("accept_terms", "Conditions d'utilisation", "Acceptation des CGU"),
                    SubStep("submit_form", "Soumission formulaire", "Envoi du formulaire d'inscription"),
                    SubStep("handle_captcha", "Gestion CAPTCHA", "Résolution des défis anti-robot"),
                ]
            ),
            MainStep(
                id="verification",
                name="Vérification email/SMS",
                description="Traitement des vérifications requises",
                sub_steps=[
                    SubStep("check_verification", "Vérification requise", "Détection du type de vérification"),
                    SubStep("email_verification", "Vérification email", "Traitement de la vérification email"),
                    SubStep("sms_verification", "Vérification SMS", "Traitement de la vérification SMS"),
                    SubStep("confirm_verification", "Confirmation", "Validation de la vérification"),
                ]
            ),
            MainStep(
                id="profile_setup",
                name="Configuration du profil",
                description="Configuration du profil avec les données de la persona",
                sub_steps=[
                    SubStep("upload_photo", "Photo de profil", "Upload de la photo générée"),
                    SubStep("set_headline", "Titre professionnel", "Configuration du headline"),
                    SubStep("set_summary", "Résumé", "Rédaction du résumé professionnel"),
                    SubStep("set_location", "Localisation", "Configuration de la localisation"),
                    SubStep("add_experience", "Expérience professionnelle", "Ajout des expériences"),
                    SubStep("add_education", "Formation", "Ajout des formations"),
                    SubStep("add_skills", "Compétences", "Ajout des compétences"),
                ]
            ),
            MainStep(
                id="finalization",
                name="Finalisation et validation",
                description="Finalisation du processus et nettoyage",
                sub_steps=[
                    SubStep("update_database", "Mise à jour BDD", "Sauvegarde des données en base"),
                    SubStep("create_usage_record", "Enregistrement usage", "Création du log d'utilisation"),
                    SubStep("cleanup_browser", "Nettoyage navigateur", "Fermeture de la session browser"),
                    SubStep("final_validation", "Validation finale", "Vérification de la création"),
                ]
            )
        ]
        
        # Create lookup dictionaries for easy access
        self.steps_by_id = {step.id: step for step in self.main_steps}
        self.sub_steps_by_id = {}
        for step in self.main_steps:
            for sub_step in step.sub_steps:
                self.sub_steps_by_id[f"{step.id}.{sub_step.id}"] = (step, sub_step)

    def start_step(self, step_id: str, details: Dict[str, Any] = None):
        """Start a main step"""
        if step_id not in self.steps_by_id:
            self.log_error("unknown", None, f"Unknown step: {step_id}")
            return
            
        step = self.steps_by_id[step_id]
        step.status = StepStatus.RUNNING
        step.started_at = datetime.now()
        
        self.log_info(step_id, None, f"Début: {step.name}", details or {})
        self._send_progress_update()

    def complete_step(self, step_id: str, success: bool = True, details: Dict[str, Any] = None):
        """Complete a main step"""
        if step_id not in self.steps_by_id:
            return
            
        step = self.steps_by_id[step_id]
        step.status = StepStatus.SUCCESS if success else StepStatus.ERROR
        step.completed_at = datetime.now()
        step.progress_percentage = 100
        
        level = LogLevel.SUCCESS if success else LogLevel.ERROR
        message = f"Terminé: {step.name}" if success else f"Échec: {step.name}"
        self._log(level, step_id, None, message, details or {})
        self._send_progress_update()

    def start_sub_step(self, step_id: str, sub_step_id: str, details: Dict[str, Any] = None):
        """Start a sub-step"""
        full_id = f"{step_id}.{sub_step_id}"
        if full_id not in self.sub_steps_by_id:
            self.log_error(step_id, None, f"Unknown sub-step: {full_id}")
            return
            
        step, sub_step = self.sub_steps_by_id[full_id]
        sub_step.status = StepStatus.RUNNING
        sub_step.started_at = datetime.now()
        
        self.log_info(step_id, sub_step_id, f"► {sub_step.name}: {sub_step.description}", details or {})
        self._send_progress_update()

    def complete_sub_step(self, step_id: str, sub_step_id: str, success: bool = True, 
                         details: Dict[str, Any] = None, execution_time: float = None):
        """Complete a sub-step"""
        full_id = f"{step_id}.{sub_step_id}"
        if full_id not in self.sub_steps_by_id:
            return
            
        step, sub_step = self.sub_steps_by_id[full_id]
        sub_step.status = StepStatus.SUCCESS if success else StepStatus.ERROR
        sub_step.completed_at = datetime.now()
        
        if execution_time:
            sub_step.details['execution_time'] = execution_time
            
        level = LogLevel.SUCCESS if success else LogLevel.ERROR
        status_icon = "✅" if success else "❌"
        message = f"{status_icon} {sub_step.name}"
        if execution_time:
            message += f" ({execution_time:.2f}s)"
            
        self._log(level, step_id, sub_step_id, message, details or {}, execution_time)
        
        # Update step progress
        completed_sub_steps = sum(1 for s in step.sub_steps if s.status == StepStatus.SUCCESS)
        step.progress_percentage = int((completed_sub_steps / len(step.sub_steps)) * 100)
        
        self._send_progress_update()

    def log_debug(self, step_id: str, sub_step_id: Optional[str], message: str, details: Dict[str, Any] = None):
        """Log debug message"""
        self._log(LogLevel.DEBUG, step_id, sub_step_id, message, details or {})

    def log_info(self, step_id: str, sub_step_id: Optional[str], message: str, details: Dict[str, Any] = None):
        """Log info message"""
        self._log(LogLevel.INFO, step_id, sub_step_id, message, details or {})

    def log_success(self, step_id: str, sub_step_id: Optional[str], message: str, details: Dict[str, Any] = None):
        """Log success message"""
        self._log(LogLevel.SUCCESS, step_id, sub_step_id, message, details or {})

    def log_warning(self, step_id: str, sub_step_id: Optional[str], message: str, details: Dict[str, Any] = None):
        """Log warning message"""
        self._log(LogLevel.WARNING, step_id, sub_step_id, message, details or {})

    def log_error(self, step_id: str, sub_step_id: Optional[str], message: str, details: Dict[str, Any] = None):
        """Log error message"""
        self._log(LogLevel.ERROR, step_id, sub_step_id, message, details or {})

    def _log(self, level: LogLevel, step_id: str, sub_step_id: Optional[str], 
            message: str, details: Dict[str, Any], execution_time: Optional[float] = None):
        """Internal logging method"""
        log_entry = ProgressLog(
            timestamp=datetime.now(),
            level=level,
            step_id=step_id,
            sub_step_id=sub_step_id,
            message=message,
            details=details,
            execution_time=execution_time
        )
        
        self.logs.append(log_entry)
        
        # Also log to Python logger
        python_logger_level = {
            LogLevel.DEBUG: logging.DEBUG,
            LogLevel.INFO: logging.INFO,
            LogLevel.SUCCESS: logging.INFO,
            LogLevel.WARNING: logging.WARNING,
            LogLevel.ERROR: logging.ERROR
        }[level]
        
        log_message = f"[{self.account_id}] {message}"
        if details:
            log_message += f" | Details: {json.dumps(details, default=str)}"
            
        logger.log(python_logger_level, log_message)

    def _send_progress_update(self):
        """Send progress update to frontend via WebSocket"""
        try:
            from src.socketio_bus import progress_queue
            
            # Calculate overall progress
            total_sub_steps = sum(len(step.sub_steps) for step in self.main_steps)
            completed_sub_steps = sum(
                len([s for s in step.sub_steps if s.status == StepStatus.SUCCESS])
                for step in self.main_steps
            )
            overall_progress = int((completed_sub_steps / total_sub_steps) * 100)
            
            # Get current active step
            current_step = None
            for step in self.main_steps:
                if step.status == StepStatus.RUNNING:
                    current_step = step
                    break
            
            # Prepare data for frontend
            progress_data = {
                'account_id': self.account_id,
                'overall_progress': overall_progress,
                'current_step': {
                    'id': current_step.id if current_step else None,
                    'name': current_step.name if current_step else "En attente",
                    'progress': current_step.progress_percentage if current_step else 0
                } if current_step else None,
                'steps': [
                    {
                        'id': step.id,
                        'name': step.name,
                        'status': step.status.value,
                        'progress': step.progress_percentage,
                        'sub_steps': [
                            {
                                'id': sub_step.id,
                                'name': sub_step.name,
                                'status': sub_step.status.value,
                                'execution_time': sub_step.details.get('execution_time')
                            }
                            for sub_step in step.sub_steps
                        ]
                    }
                    for step in self.main_steps
                ],
                'recent_logs': [
                    {
                        'timestamp': log.timestamp.isoformat(),
                        'level': log.level.value,
                        'message': log.message,
                        'step_id': log.step_id,
                        'sub_step_id': log.sub_step_id,
                        'details': log.details,
                        'execution_time': log.execution_time
                    }
                    for log in self.logs[-10:]  # Last 10 logs
                ],
                'timestamp': datetime.now().isoformat()
            }
            
            room_name = f"account_{self.account_id}"
            data = dict(progress_data)
            data['_room'] = room_name
            try:
                progress_queue.put_nowait(data)
            except Exception:
                pass
            
        except Exception as e:
            logger.error(f"Error sending progress update: {e}")

    def send_completion(self, success: bool, result: Dict[str, Any] = None, error: str = None):
        """Send completion notification"""
        try:
            from src.socketio_bus import progress_queue
            
            completion_data = {
                'account_id': self.account_id,
                'success': success,
                'message': 'Compte LinkedIn créé avec succès!' if success else f'Erreur: {error}',
                'result': result or {},
                'error': error,
                'timestamp': datetime.now().isoformat(),
                'total_logs': len(self.logs),
                'execution_summary': self._get_execution_summary()
            }
            
            room_name = f"account_{self.account_id}"
            data = dict(completion_data)
            data['_room'] = room_name
            try:
                progress_queue.put_nowait(data)
            except Exception:
                pass
            
        except Exception as e:
            logger.error(f"Error sending completion update: {e}")

    def _get_execution_summary(self) -> Dict[str, Any]:
        """Generate execution summary"""
        successful_steps = sum(1 for step in self.main_steps if step.status == StepStatus.SUCCESS)
        failed_steps = sum(1 for step in self.main_steps if step.status == StepStatus.ERROR)
        
        total_execution_time = 0
        for log in self.logs:
            if log.execution_time:
                total_execution_time += log.execution_time
        
        return {
            'total_steps': len(self.main_steps),
            'successful_steps': successful_steps,
            'failed_steps': failed_steps,
            'total_logs': len(self.logs),
            'total_execution_time': total_execution_time,
            'error_logs': len([log for log in self.logs if log.level == LogLevel.ERROR]),
            'warning_logs': len([log for log in self.logs if log.level == LogLevel.WARNING])
        }



