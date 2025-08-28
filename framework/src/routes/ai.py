from flask import Blueprint, jsonify, request
import asyncio
import logging
from src.models import db
from src.models.persona import Persona, PersonaUsage
from src.services.ai_content import (
    PersonaGenerator, AIContentGenerator, 
    IndustryType, ExperienceLevel,
    PersonaGeneratorSync, AIContentGeneratorSync
)

logger = logging.getLogger(__name__)
ai_bp = Blueprint('ai', __name__)

@ai_bp.route('/ai/personas/generate', methods=['POST'])
def generate_persona():
    """Generate a new professional persona"""
    try:
        data = request.json or {}
        
        # Parse industry and experience level
        industry_str = data.get('industry', 'technology')
        experience_str = data.get('experience_level', 'mid_level')
        
        try:
            industry = IndustryType(industry_str)
        except ValueError:
            return jsonify({'error': f'Invalid industry: {industry_str}'}), 400
        
        try:
            experience_level = ExperienceLevel(experience_str)
        except ValueError:
            return jsonify({'error': f'Invalid experience level: {experience_str}'}), 400
        
        # Generate persona
        generator = PersonaGeneratorSync()
        persona_profile = generator.generate_professional_persona(industry, experience_level)
        
        # Store persona in database
        persona_db = Persona.from_persona_profile(persona_profile)
        db.session.add(persona_db)
        
        try:
            # First commit to get the persona ID
            db.session.commit()
            
            # Then create usage record with the actual persona ID
            persona_usage = PersonaUsage(
                persona_id=persona_db.id,
                usage_type='generation',
                success=True,
                notes='AI persona generated via API'
            )
            db.session.add(persona_usage)
            db.session.commit()
            
            logger.info(f"Persona stored in database: {persona_db.id}")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to store persona in database: {e}")
            return jsonify({'error': 'Failed to store persona'}), 500
        
        # Convert to JSON-serializable format using database model
        result = persona_db.to_dict()
        
        logger.info(f"Generated persona: {persona_db.first_name} {persona_db.last_name}")
        return jsonify(result), 201
        
    except Exception as e:
        logger.error(f"Error generating persona: {e}")
        return jsonify({'error': 'Failed to generate persona'}), 500

@ai_bp.route('/ai/personas', methods=['GET'])
def get_personas():
    """Get list of stored personas"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Query personas with pagination
        personas_query = Persona.query.filter_by(is_active=True).order_by(Persona.created_at.desc())
        personas = personas_query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        result = {
            'personas': [persona.to_dict() for persona in personas.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': personas.total,
                'pages': personas.pages,
                'has_prev': personas.has_prev,
                'has_next': personas.has_next
            }
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting personas: {e}")
        return jsonify({'error': 'Failed to get personas'}), 500

@ai_bp.route('/ai/personas/<persona_id>', methods=['GET'])
def get_persona(persona_id):
    """Get specific persona by ID"""
    try:
        persona = Persona.query.filter_by(persona_id=persona_id, is_active=True).first()
        
        if not persona:
            return jsonify({'error': 'Persona not found'}), 404
        
        return jsonify(persona.to_dict())
        
    except Exception as e:
        logger.error(f"Error getting persona {persona_id}: {e}")
        return jsonify({'error': 'Failed to get persona'}), 500

@ai_bp.route('/ai/personas/<persona_id>', methods=['DELETE'])
def delete_persona(persona_id):
    """Soft delete a persona (only if not linked to any accounts)"""
    try:
        persona = Persona.query.filter_by(persona_id=persona_id, is_active=True).first()
        
        if not persona:
            return jsonify({'error': 'Persona not found'}), 404
        
        # Check if persona is linked to any accounts
        from src.models.account import Account
        linked_accounts = Account.query.filter_by(persona_id=persona.id).count()
        
        if linked_accounts > 0:
            return jsonify({
                'error': 'Cannot delete persona - it is linked to existing LinkedIn accounts',
                'linked_accounts': linked_accounts
            }), 409
        
        # Check if persona has been used for account creation attempts
        usage_count = PersonaUsage.query.filter_by(
            persona_id=persona.id,
            usage_type='account_creation'
        ).count()
        
        if usage_count > 0:
            return jsonify({
                'error': 'Cannot delete persona - it has been used for account creation',
                'usage_count': usage_count
            }), 409
        
        # Soft delete
        persona.is_active = False
        
        # Create usage record
        persona_usage = PersonaUsage(
            persona_id=persona.id,
            usage_type='deletion',
            success=True,
            notes='Persona soft deleted via API - no linked accounts found'
        )
        db.session.add(persona_usage)
        
        db.session.commit()
        
        logger.info(f"Persona {persona_id} soft deleted - no linked accounts")
        return jsonify({'message': 'Persona deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting persona {persona_id}: {e}")
        return jsonify({'error': 'Failed to delete persona'}), 500

@ai_bp.route('/ai/personas/<persona_id>', methods=['PATCH'])
def update_persona(persona_id):
    """Update persona fields"""
    try:
        persona = Persona.query.filter_by(persona_id=persona_id, is_active=True).first()
        
        if not persona:
            return jsonify({'error': 'Persona not found'}), 404
        
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update allowed fields
        if 'first_name' in data:
            persona.first_name = data['first_name']
        if 'last_name' in data:
            persona.last_name = data['last_name']
        if 'manual_email' in data:
            persona.manual_email = data['manual_email']
        if 'manual_email_password' in data:
            persona.manual_email_password = data['manual_email_password']
        
        # Update timestamp
        from datetime import datetime
        persona.updated_at = datetime.utcnow()
        
        # Create usage record
        persona_usage = PersonaUsage(
            persona_id=persona.id,
            usage_type='update',
            success=True,
            notes=f'Persona updated via API - fields: {", ".join(data.keys())}'
        )
        db.session.add(persona_usage)
        
        db.session.commit()
        
        logger.info(f"Persona {persona_id} updated successfully")
        return jsonify({'message': 'Persona updated successfully', 'persona': persona.to_dict()})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating persona {persona_id}: {e}")
        return jsonify({'error': 'Failed to update persona'}), 500

@ai_bp.route('/ai/content/generate', methods=['POST'])
def generate_content():
    """Generate content for a persona"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['content_type', 'persona_data']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        content_type = data['content_type']
        persona_data = data['persona_data']
        
        # Validate content type
        valid_types = ['headline', 'summary', 'about', 'post']
        if content_type not in valid_types:
            return jsonify({'error': f'Invalid content type. Must be one of: {valid_types}'}), 400
        
        # Reconstruct persona object (simplified version)
        from src.services.ai_content import PersonaProfile, DemographicData, ProfessionalData, SkillsData, ContentData, VisualAssets
        from datetime import datetime
        
        persona = PersonaProfile(
            demographic_data=DemographicData(**persona_data['demographic_data']),
            professional_data=ProfessionalData(**persona_data['professional_data']),
            skills_data=SkillsData(**persona_data['skills_data']),
            content_data=ContentData(**persona_data.get('content_data', {
                'headline': '', 'summary': '', 'about_section': '', 'sample_posts': []
            })),
            visual_assets=VisualAssets(**persona_data.get('visual_assets', {
                'profile_photo_description': '', 'background_image_description': ''
            })),
            persona_id=persona_data.get('persona_id', 'temp'),
            created_at=datetime.now()
        )
        
        # Generate content
        generator = AIContentGeneratorSync()
        result = generator.generate_professional_content(content_type, persona)
        
        # Return result
        response = {
            'content_type': result.content_type,
            'content': result.content,
            'engagement_elements': result.engagement_elements,
            'persona_id': result.persona_id,
            'success': result.success,
            'error_message': result.error_message
        }
        
        if result.success:
            logger.info(f"Generated {content_type} content for persona {result.persona_id}")
            return jsonify(response), 201
        else:
            logger.error(f"Failed to generate {content_type} content: {result.error_message}")
            return jsonify(response), 500
        
    except Exception as e:
        logger.error(f"Error generating content: {e}")
        return jsonify({'error': 'Failed to generate content'}), 500

@ai_bp.route('/ai/industries', methods=['GET'])
def get_industries():
    """Get available industries"""
    industries = [
        {'value': industry.value, 'label': industry.value.replace('_', ' ').title()}
        for industry in IndustryType
    ]
    return jsonify(industries)

@ai_bp.route('/ai/experience-levels', methods=['GET'])
def get_experience_levels():
    """Get available experience levels"""
    levels = [
        {'value': level.value, 'label': level.value.replace('_', ' ').title()}
        for level in ExperienceLevel
    ]
    return jsonify(levels)

@ai_bp.route('/ai/content-types', methods=['GET'])
def get_content_types():
    """Get available content types"""
    content_types = [
        {
            'value': 'headline',
            'label': 'LinkedIn Headline',
            'description': 'Professional headline for LinkedIn profile'
        },
        {
            'value': 'summary',
            'label': 'Professional Summary',
            'description': 'Detailed professional summary for LinkedIn'
        },
        {
            'value': 'about',
            'label': 'About Section',
            'description': 'About section for LinkedIn profile'
        },
        {
            'value': 'post',
            'label': 'LinkedIn Post',
            'description': 'Engaging LinkedIn post content'
        }
    ]
    return jsonify(content_types)

@ai_bp.route('/ai/personas/validate', methods=['POST'])
def validate_persona():
    """Validate a persona profile"""
    try:
        data = request.json
        
        if not data:
            return jsonify({'error': 'No persona data provided'}), 400
        
        # Basic validation
        validation_errors = []
        
        # Check demographic data
        if 'demographic_data' not in data:
            validation_errors.append('Missing demographic_data')
        else:
            demo = data['demographic_data']
            required_demo_fields = ['first_name', 'last_name', 'age', 'location']
            for field in required_demo_fields:
                if field not in demo or not demo[field]:
                    validation_errors.append(f'Missing or empty demographic field: {field}')
        
        # Check professional data
        if 'professional_data' not in data:
            validation_errors.append('Missing professional_data')
        else:
            prof = data['professional_data']
            required_prof_fields = ['current_position', 'current_company', 'industry']
            for field in required_prof_fields:
                if field not in prof or not prof[field]:
                    validation_errors.append(f'Missing or empty professional field: {field}')
        
        # Check skills data
        if 'skills_data' not in data:
            validation_errors.append('Missing skills_data')
        else:
            skills = data['skills_data']
            if 'technical_skills' not in skills or not skills['technical_skills']:
                validation_errors.append('Missing technical_skills')
        
        # Return validation result
        is_valid = len(validation_errors) == 0
        
        result = {
            'is_valid': is_valid,
            'errors': validation_errors,
            'completeness_score': max(0, 1 - (len(validation_errors) / 10))  # Simple scoring
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error validating persona: {e}")
        return jsonify({'error': 'Failed to validate persona'}), 500

@ai_bp.route('/ai/personas/enhance', methods=['POST'])
def enhance_persona():
    """Enhance an existing persona with additional content"""
    try:
        data = request.json
        
        if not data or 'persona_data' not in data:
            return jsonify({'error': 'No persona data provided'}), 400
        
        enhancement_type = data.get('enhancement_type', 'content')
        persona_data = data['persona_data']
        
        # Reconstruct persona object
        from src.services.ai_content import PersonaProfile, DemographicData, ProfessionalData, SkillsData, ContentData, VisualAssets
        from datetime import datetime
        
        persona = PersonaProfile(
            demographic_data=DemographicData(**persona_data['demographic_data']),
            professional_data=ProfessionalData(**persona_data['professional_data']),
            skills_data=SkillsData(**persona_data['skills_data']),
            content_data=ContentData(**persona_data.get('content_data', {
                'headline': '', 'summary': '', 'about_section': '', 'sample_posts': []
            })),
            visual_assets=VisualAssets(**persona_data.get('visual_assets', {
                'profile_photo_description': '', 'background_image_description': ''
            })),
            persona_id=persona_data.get('persona_id', 'temp'),
            created_at=datetime.now()
        )
        
        # Generate enhancements based on type
        generator = AIContentGeneratorSync()
        enhancements = {}
        
        if enhancement_type == 'content':
            # Generate additional posts
            additional_posts = []
            for i in range(3):
                post_result = generator.generate_professional_content('post', persona)
                if post_result.success:
                    additional_posts.append({
                        'content': post_result.content,
                        'engagement_elements': post_result.engagement_elements
                    })
            
            enhancements['additional_posts'] = additional_posts
        
        elif enhancement_type == 'skills':
            # This would enhance skills based on industry trends
            # For now, return the existing skills with suggestions
            enhancements['skill_suggestions'] = [
                'Digital Marketing', 'Data Analytics', 'Project Management', 'Leadership'
            ]
        
        result = {
            'persona_id': persona.persona_id,
            'enhancement_type': enhancement_type,
            'enhancements': enhancements,
            'success': True
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error enhancing persona: {e}")
        return jsonify({'error': 'Failed to enhance persona'}), 500

@ai_bp.route('/ai/test', methods=['POST'])
def test_ai_services():
    """Test AI services connectivity"""
    try:
        # Test OpenAI connectivity
        generator = AIContentGeneratorSync()
        
        # Create a simple test persona
        from src.services.ai_content import PersonaProfile, DemographicData, ProfessionalData, SkillsData, ContentData, VisualAssets
        from datetime import datetime
        
        test_persona = PersonaProfile(
            demographic_data=DemographicData(
                first_name="Test",
                last_name="User",
                age=30,
                location="Paris",
                nationality="French",
                languages=["French", "English"]
            ),
            professional_data=ProfessionalData(
                current_position="Software Engineer",
                current_company="TechCorp",
                industry="technology",
                experience_years=5,
                education=[],
                previous_positions=[]
            ),
            skills_data=SkillsData(
                technical_skills=["Python", "JavaScript"],
                soft_skills=["Communication"],
                certifications=[],
                languages_spoken=[]
            ),
            content_data=ContentData(
                headline="", summary="", about_section="", sample_posts=[]
            ),
            visual_assets=VisualAssets(
                profile_photo_description="", background_image_description=""
            ),
            persona_id="test",
            created_at=datetime.now()
        )
        
        # Test content generation
        result = generator.generate_professional_content('headline', test_persona)
        
        return jsonify({
            'ai_services_available': True,
            'openai_connected': result.success,
            'test_content_generated': result.success,
            'error_message': result.error_message if not result.success else None
        })
        
    except Exception as e:
        logger.error(f"Error testing AI services: {e}")
        return jsonify({
            'ai_services_available': False,
            'openai_connected': False,
            'test_content_generated': False,
            'error_message': str(e)
        }), 500

