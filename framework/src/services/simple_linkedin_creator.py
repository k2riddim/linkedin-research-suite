"""
Simple LinkedIn Creator - Basic working version for debugging
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, Any
from src.models.account import Account
from src.models.persona import Persona, PersonaUsage
from src.models import db

logger = logging.getLogger(__name__)

class SimpleProgressTracker:
    """Simple progress tracker for debugging"""
    
    def __init__(self, account_id: str):
        self.account_id = account_id
        self.step = 0
        self.total_steps = 8
        
    def send_progress(self, step: int, message: str, status: str = 'running'):
        """Send simple progress update"""
        logger.info(f"DEBUG: send_progress called - step {step}, message: {message}")
        try:
            from src.socketio_bus import progress_queue
            
            progress_data = {
                'step': f"Étape {step + 1}",
                'step_index': step,
                'total_steps': self.total_steps,
                'progress': int((step / self.total_steps) * 100),
                'message': message,
                'status': status,
                'timestamp': datetime.now().isoformat(),
                'details': {}
            }
            
            room_name = f"account_{self.account_id}"
            data = dict(progress_data)
            data['_room'] = room_name
            try:
                progress_queue.put_nowait(data)
            except Exception:
                pass
            
            logger.info(f"[{self.account_id}] Step {step + 1}/{self.total_steps}: {message}")
            
        except Exception as e:
            logger.error(f"Error sending progress update: {e}")
    
    def send_completion(self, success: bool, result: Dict = None, error: str = None):
        """Send completion update"""
        try:
            from src.socketio_bus import progress_queue
            
            completion_data = {
                'account_id': self.account_id,
                'success': success,
                'message': 'Compte LinkedIn créé avec succès!' if success else f'Erreur: {error}',
                'result': result or {},
                'error': error,
                'timestamp': datetime.now().isoformat()
            }
            
            room_name = f"account_{self.account_id}"
            data = dict(completion_data)
            data['_room'] = room_name
            try:
                progress_queue.put_nowait(data)
            except Exception:
                pass
            
            logger.info(f"[{self.account_id}] Creation completed: {'SUCCESS' if success else 'FAILED'}")
            
        except Exception as e:
            logger.error(f"Error sending completion update: {e}")

async def create_linkedin_account_simple(account_id: str) -> Dict[str, Any]:
    """
    Simple LinkedIn account creation for debugging
    """
    logger.info(f"DEBUG: create_linkedin_account_simple STARTED for account {account_id}")
    progress = SimpleProgressTracker(account_id)
    
    try:
        # Step 0: Initialize
        progress.send_progress(0, "🔄 Initialisation du processus...")
        await asyncio.sleep(1)
        
        # Get account from database
        account = Account.query.get(account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found")
        
        progress.send_progress(0, f"✅ Compte trouvé: {account.email}", 'success')
        await asyncio.sleep(1)
        
        # Step 1: Check persona
        progress.send_progress(1, "🔄 Vérification de la persona...")
        await asyncio.sleep(1)
        
        persona = None
        if account.persona_id:
            persona = Persona.query.get(account.persona_id)
            if persona:
                progress.send_progress(1, f"✅ Persona: {persona.demographic_data.get('first_name', 'Unknown')}", 'success')
            else:
                progress.send_progress(1, "⚠️ Persona non trouvée", 'warning')
        else:
            progress.send_progress(1, "⚠️ Aucune persona liée", 'warning')
        
        await asyncio.sleep(1)
        
        # Step 2: Simulate external services
        progress.send_progress(2, "🔄 Configuration des services externes...")
        await asyncio.sleep(2)
        
        progress.send_progress(2, "✅ Services configurés (simulé)", 'success')
        await asyncio.sleep(1)
        
        # Step 3: Simulate browser launch
        progress.send_progress(3, "🔄 Lancement du navigateur...")
        await asyncio.sleep(2)
        
        # Simulate potential browser issue
        try:
            # This will show us if browser automation works
            progress.send_progress(3, "✅ Navigateur lancé (simulé)", 'success')
            await asyncio.sleep(1)
        except Exception as e:
            progress.send_progress(3, f"❌ Erreur navigateur: {e}", 'error')
            raise
        
        # Step 4: Simulate LinkedIn navigation
        progress.send_progress(4, "🔄 Navigation vers LinkedIn...")
        await asyncio.sleep(2)
        
        progress.send_progress(4, "✅ Page LinkedIn chargée (simulé)", 'success')
        await asyncio.sleep(1)
        
        # Step 5: Simulate account creation
        progress.send_progress(5, "🔄 Création du compte LinkedIn...")
        await asyncio.sleep(3)
        
        # Simulate form filling
        progress.send_progress(5, "📝 Remplissage du formulaire...", 'running')
        await asyncio.sleep(2)
        
        progress.send_progress(5, "✅ Formulaire soumis (simulé)", 'success')
        await asyncio.sleep(1)
        
        # Step 6: Simulate verification
        progress.send_progress(6, "🔄 Vérification email...")
        await asyncio.sleep(3)
        
        progress.send_progress(6, "✅ Email vérifié (simulé)", 'success')
        await asyncio.sleep(1)
        
        # Step 7: Finalization
        progress.send_progress(7, "🔄 Finalisation...")
        await asyncio.sleep(1)
        
        # Update account in database
        account.status = 'completed'
        account.linkedin_created = True
        account.linkedin_creation_completed = datetime.utcnow()
        account.linkedin_url = f"https://linkedin.com/in/{account.first_name.lower()}-{account.last_name.lower()}-simulated"
        
        # Create persona usage record
        if persona:
            persona_usage = PersonaUsage(
                persona_id=persona.id,
                account_id=account.id,
                usage_type='linkedin_creation',
                success=True,
                notes='LinkedIn account created successfully (SIMULATED for debugging)'
            )
            db.session.add(persona_usage)
        
        db.session.commit()
        
        progress.send_progress(7, "✅ Finalisation terminée", 'success')
        
        # Send completion
        result = {
            'account_id': account_id,
            'linkedin_url': account.linkedin_url,
            'creation_time': 15.5,  # Simulated
            'verification': {'verified': True, 'method': 'email'},
            'profile_setup': persona is not None,
            'detection_risk': 0.1,
            'simulated': True
        }
        
        progress.send_completion(True, result)
        
        logger.info(f"Simulated LinkedIn account creation completed for {account_id}")
        return result
        
    except Exception as e:
        logger.error(f"Simulated LinkedIn account creation failed for {account_id}: {e}")
        
        # Update account with failure status
        try:
            account = Account.query.get(account_id)
            if account:
                account.status = 'failed'
                account.linkedin_creation_failed = datetime.utcnow()
                db.session.commit()
        except Exception as db_error:
            logger.error(f"Failed to update account status: {db_error}")
        
        # Send failure notification
        progress.send_completion(False, error=str(e))
        
        return {
            'success': False,
            'error': str(e),
            'account_id': account_id
        }
