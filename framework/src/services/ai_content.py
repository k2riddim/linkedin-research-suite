import openai
import asyncio
import logging
import random
import json
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime

from src.config import config

logger = logging.getLogger(__name__)

class IndustryType(Enum):
    TECHNOLOGY = "technology"
    FINANCE = "finance"
    HEALTHCARE = "healthcare"
    MARKETING = "marketing"
    CONSULTING = "consulting"
    EDUCATION = "education"
    MANUFACTURING = "manufacturing"
    RETAIL = "retail"

class ExperienceLevel(Enum):
    ENTRY_LEVEL = "entry_level"
    MID_LEVEL = "mid_level"
    SENIOR_LEVEL = "senior_level"
    EXECUTIVE = "executive"

@dataclass
class DemographicData:
    """Demographic information for persona"""
    first_name: str
    last_name: str
    age: int
    location: str
    nationality: str
    languages: List[str]

@dataclass
class ProfessionalData:
    """Professional background information"""
    current_position: str
    current_company: str
    industry: str
    experience_years: int
    education: List[Dict[str, str]]
    previous_positions: List[Dict[str, str]]

@dataclass
class SkillsData:
    """Skills and certifications"""
    technical_skills: List[str]
    soft_skills: List[str]
    certifications: List[str]
    languages_spoken: List[Dict[str, str]]

@dataclass
class ContentData:
    """Generated content for profile"""
    headline: str
    summary: str
    about_section: str
    sample_posts: List[str]

@dataclass
class VisualAssets:
    """Visual assets for profile"""
    profile_photo_description: str
    background_image_description: str
    company_logo_description: Optional[str] = None

@dataclass
class PersonaProfile:
    """Complete persona profile"""
    demographic_data: DemographicData
    professional_data: ProfessionalData
    skills_data: SkillsData
    content_data: ContentData
    visual_assets: VisualAssets
    persona_id: str
    created_at: datetime

@dataclass
class GeneratedContent:
    """Generated content result"""
    content_type: str
    content: str
    engagement_elements: List[str]
    persona_id: str
    success: bool
    error_message: Optional[str] = None

class AIContentGenerator:
    """
    Generates professional content using OpenAI

    Algorithm Flow:
    1. Analyze persona and industry context
    2. Generate content prompts based on templates
    3. Call OpenAI API with optimized parameters
    4. Process and validate generated content
    5. Optimize for engagement and authenticity
    """

    def __init__(self):
        self.client = openai.OpenAI(
            api_key=config.external_services.openai_api_key
        )
        self.model = "gpt-4"  # Use GPT-4 for better quality
        
    def optimize_openai_parameters(self, content_type: str, experience_level: ExperienceLevel) -> Dict[str, Any]:
        """Optimize OpenAI parameters based on content type and experience"""
        base_params = {
            "model": self.model,
            "temperature": 0.7,
            "max_tokens": 1000,
            "top_p": 0.9,
            "frequency_penalty": 0.1,
            "presence_penalty": 0.1
        }
        
        # Adjust parameters based on content type
        if content_type == "headline":
            base_params.update({
                "temperature": 0.8,
                "max_tokens": 100,
                "frequency_penalty": 0.2
            })
        elif content_type == "summary":
            base_params.update({
                "temperature": 0.6,
                "max_tokens": 500,
                "frequency_penalty": 0.0
            })
        elif content_type == "post":
            base_params.update({
                "temperature": 0.9,
                "max_tokens": 300,
                "presence_penalty": 0.2
            })
        
        # Adjust for experience level
        if experience_level == ExperienceLevel.EXECUTIVE:
            base_params["temperature"] = max(0.5, base_params["temperature"] - 0.1)
        elif experience_level == ExperienceLevel.ENTRY_LEVEL:
            base_params["temperature"] = min(0.9, base_params["temperature"] + 0.1)
        
        return base_params

    async def generate_with_retry(self, prompt: str, params: Dict[str, Any], max_retries: int = 3) -> str:
        """Generate content with retry logic"""
        for attempt in range(max_retries):
            try:
                response = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    messages=[{"role": "user", "content": prompt}],
                    **params
                )
                
                content = response.choices[0].message.content.strip()
                logger.info(f"Content generated successfully (attempt {attempt + 1})")
                return content
                
            except Exception as e:
                logger.warning(f"Content generation attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise e
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        raise Exception("Failed to generate content after all retries")

    async def validate_and_optimize_content(self, content: str, content_type: str, persona: PersonaProfile) -> str:
        """Validate and optimize generated content"""
        # Basic validation
        if not content or len(content.strip()) < 10:
            raise ValueError("Generated content is too short")
        
        # Content-specific validation
        if content_type == "headline" and len(content) > 220:
            # Truncate headline if too long
            content = content[:217] + "..."
        elif content_type == "summary" and len(content) > 2000:
            # Truncate summary if too long
            content = content[:1997] + "..."
        
        # Remove any inappropriate content markers
        content = content.replace("[PLACEHOLDER]", "")
        content = content.replace("[INSERT_NAME]", persona.demographic_data.first_name)
        content = content.replace("[INSERT_COMPANY]", persona.professional_data.current_company)
        
        return content.strip()

    async def generate_engagement_elements(self, content: str, content_type: str) -> List[str]:
        """Generate engagement elements for content"""
        elements = []
        
        if content_type == "post":
            # Generate hashtags
            hashtag_prompt = f"""
            Generate 3-5 relevant professional hashtags for this LinkedIn post:
            "{content}"
            
            Return only the hashtags, one per line, starting with #.
            """
            
            try:
                hashtags_response = await self.generate_with_retry(
                    hashtag_prompt,
                    {"model": self.model, "temperature": 0.5, "max_tokens": 100},
                    max_retries=2
                )
                
                hashtags = [line.strip() for line in hashtags_response.split('\n') if line.strip().startswith('#')]
                elements.extend(hashtags[:5])
                
            except Exception as e:
                logger.warning(f"Failed to generate hashtags: {e}")
                # Fallback hashtags
                elements.extend(["#LinkedIn", "#Professional", "#Career"])
        
        return elements

    async def generate_professional_content(self, content_type: str, persona: PersonaProfile) -> GeneratedContent:
        """Generate professional content for persona"""
        try:
            # Generate content prompt based on type
            prompt = self.create_content_prompt(content_type, persona)
            
            # Map experience years to ExperienceLevel enum
            years = persona.professional_data.experience_years
            if years <= 2:
                experience_level = ExperienceLevel.ENTRY_LEVEL
            elif years <= 7:
                experience_level = ExperienceLevel.MID_LEVEL
            elif years <= 15:
                experience_level = ExperienceLevel.SENIOR_LEVEL
            else:
                experience_level = ExperienceLevel.EXECUTIVE

            # Optimize OpenAI parameters
            openai_params = self.optimize_openai_parameters(
                content_type=content_type,
                experience_level=experience_level
            )

            # Generate content with retry logic
            generated_content = await self.generate_with_retry(
                prompt=prompt,
                params=openai_params,
                max_retries=3
            )

            # Validate and optimize content
            validated_content = await self.validate_and_optimize_content(
                content=generated_content,
                content_type=content_type,
                persona=persona
            )

            # Generate engagement elements
            engagement_elements = await self.generate_engagement_elements(
                content=validated_content,
                content_type=content_type
            )

            return GeneratedContent(
                content_type=content_type,
                content=validated_content,
                engagement_elements=engagement_elements,
                persona_id=persona.persona_id,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error generating content for {content_type}: {e}")
            return GeneratedContent(
                content_type=content_type,
                content="",
                engagement_elements=[],
                persona_id=persona.persona_id,
                success=False,
                error_message=str(e)
            )

    def create_content_prompt(self, content_type: str, persona: PersonaProfile) -> str:
        """Create content generation prompt based on type and persona"""
        base_context = f"""
        You are creating professional LinkedIn content for a {persona.professional_data.current_position} 
        at {persona.professional_data.current_company} in the {persona.professional_data.industry} industry.
        
        Profile details:
        - Name: {persona.demographic_data.first_name} {persona.demographic_data.last_name}
        - Experience: {persona.professional_data.experience_years} years
        - Location: {persona.demographic_data.location}
        - Key skills: {', '.join(persona.skills_data.technical_skills[:3])}
        
        The content should be professional, authentic, and engaging for a French professional audience.
        IMPORTANT: Generate ALL content in FRENCH language only. Use proper French grammar, expressions, and professional terminology.
        """
        
        if content_type == "headline":
            return f"""
            {base_context}
            
            Créez un titre LinkedIn convaincant (moins de 220 caractères) qui:
            - Met en valeur leur rôle actuel et leur expertise
            - Montre la proposition de valeur
            - Est engageant et professionnel
            - Utilise des mots-clés pertinents du secteur
            
            Rédigez UNIQUEMENT en français. Retournez seulement le texte du titre, sans guillemets ni formatage supplémentaire.
            """
            
        elif content_type == "summary":
            return f"""
            {base_context}
            
            Créez un résumé LinkedIn professionnel (300-500 mots) qui:
            - Raconte leur histoire professionnelle
            - Met en valeur les principales réalisations et compétences
            - Montre la personnalité tout en restant professionnel
            - Inclut un appel à l'action
            - Utilise la première personne
            
            Rédigez UNIQUEMENT en français. Retournez seulement le texte du résumé.
            """
            
        elif content_type == "about":
            return f"""
            {base_context}
            
            Créez une section "À propos" (200-300 mots) qui:
            - Fournit un aperçu professionnel
            - Met en valeur l'expertise et la passion
            - Montre ce qui les rend uniques
            - Inclut une invitation à prendre contact
            
            Rédigez UNIQUEMENT en français. Retournez seulement le texte de la section À propos.
            """
            
        elif content_type == "post":
            return f"""
            {base_context}
            
            Créez une publication LinkedIn engageante (100-200 mots) qui:
            - Partage une perspective ou expérience professionnelle
            - Apporte de la valeur à leur réseau
            - Encourage l'engagement
            - Reflète leur expertise
            - Utilise un ton conversationnel mais professionnel
            
            Rédigez UNIQUEMENT en français. Retournez seulement le texte de la publication, sans hashtags (ils seront générés séparément).
            """
        
        else:
            return f"{base_context}\n\nCréez du contenu professionnel de type {content_type} en français uniquement."


class PersonaGenerator:
    """
    Generates realistic professional personas using AI

    Algorithm Flow:
    1. Select industry and experience level
    2. Generate demographic data (name, age, location)
    3. Create professional background (education, experience)
    4. Generate realistic skills and certifications
    5. Create professional summary and headline
    6. Generate visual assets (profile photo, background)
    7. Validate persona completeness and realism
    """

    def __init__(self):
        self.content_generator = AIContentGenerator()
        self.french_first_names = [
            "Antoine", "Pierre", "Jean", "Louis", "Nicolas", "Alexandre", "François", "Julien", "Thomas", "Maxime",
            "Marie", "Sophie", "Catherine", "Isabelle", "Nathalie", "Sylvie", "Céline", "Amélie", "Claire", "Émilie"
        ]
        self.french_last_names = [
            "Martin", "Bernard", "Dubois", "Thomas", "Robert", "Richard", "Petit", "Durand", "Leroy", "Moreau",
            "Simon", "Laurent", "Lefebvre", "Michel", "Garcia", "David", "Bertrand", "Roux", "Vincent", "Fournier"
        ]
        self.french_cities = [
            "Paris", "Lyon", "Marseille", "Toulouse", "Nice", "Nantes", "Strasbourg", "Montpellier", "Bordeaux", "Lille"
        ]

    async def generate_demographic_data(self, industry: IndustryType, experience_level: ExperienceLevel) -> DemographicData:
        """Generate realistic demographic data"""
        first_name = random.choice(self.french_first_names)
        last_name = random.choice(self.french_last_names)
        
        # Age based on experience level
        age_ranges = {
            ExperienceLevel.ENTRY_LEVEL: (22, 28),
            ExperienceLevel.MID_LEVEL: (28, 38),
            ExperienceLevel.SENIOR_LEVEL: (35, 50),
            ExperienceLevel.EXECUTIVE: (40, 60)
        }
        
        min_age, max_age = age_ranges[experience_level]
        age = random.randint(min_age, max_age)
        
        location = f"{random.choice(self.french_cities)}, France"
        
        return DemographicData(
            first_name=first_name,
            last_name=last_name,
            age=age,
            location=location,
            nationality="French",
            languages=["French", "English"]
        )

    async def generate_professional_background(self, demographic_data: DemographicData, 
                                             industry: IndustryType, 
                                             experience_level: ExperienceLevel) -> ProfessionalData:
        """Generate professional background using AI"""
        
        experience_years = {
            ExperienceLevel.ENTRY_LEVEL: random.randint(0, 3),
            ExperienceLevel.MID_LEVEL: random.randint(3, 8),
            ExperienceLevel.SENIOR_LEVEL: random.randint(8, 15),
            ExperienceLevel.EXECUTIVE: random.randint(15, 25)
        }[experience_level]
        
        prompt = f"""
        Generate a realistic professional background for a French professional:
        
        Name: {demographic_data.first_name} {demographic_data.last_name}
        Age: {demographic_data.age}
        Industry: {industry.value}
        Experience Level: {experience_level.value}
        Years of Experience: {experience_years}
        Location: {demographic_data.location}
        
        IMPORTANT: Generate ALL content in FRENCH language only. Use French company names, French educational institutions, and French job titles.
        
        Return a JSON object with:
        {{
            "current_position": "Titre du poste en français",
            "current_company": "Nom d'entreprise française",
            "industry": "{industry.value}",
            "experience_years": {experience_years},
            "education": [
                {{"degree": "Diplôme en français", "school": "École/Université française", "year": "Année"}}
            ],
            "previous_positions": [
                {{"title": "Titre du poste en français", "company": "Entreprise française", "duration": "Durée en français"}}
            ]
        }}
        
        Make it realistic for the French market and industry with authentic French professional terminology.
        """
        
        try:
            response = await self.content_generator.generate_with_retry(
                prompt,
                {"model": "gpt-4", "temperature": 0.7, "max_tokens": 800},
                max_retries=3
            )
            
            # Parse JSON response
            data = json.loads(response)
            
            return ProfessionalData(
                current_position=data["current_position"],
                current_company=data["current_company"],
                industry=data["industry"],
                experience_years=data["experience_years"],
                education=data["education"],
                previous_positions=data["previous_positions"]
            )
            
        except Exception as e:
            logger.error(f"Error generating professional background: {e}")
            # Fallback data in French
            return ProfessionalData(
                current_position=f"Spécialiste {industry.value.title()} {experience_level.value.replace('_', ' ').title()}",
                current_company="TechCorp France",
                industry=industry.value,
                experience_years=experience_years,
                education=[{"degree": "Master en Informatique", "school": "Université de Paris", "year": "2015"}],
                previous_positions=[{"title": "Analyste Junior", "company": "StartupCo France", "duration": "2 ans"}]
            )

    async def generate_skills_and_certifications(self, professional_data: ProfessionalData,
                                               industry: IndustryType,
                                               experience_level: ExperienceLevel) -> SkillsData:
        """Generate skills and certifications"""
        
        prompt = f"""
        Generate realistic skills and certifications for a {professional_data.current_position} 
        in {industry.value} with {professional_data.experience_years} years of experience.
        
        IMPORTANT: Generate ALL skills and certifications in FRENCH language only.
        
        Return a JSON object with:
        {{
            "technical_skills": ["compétence technique 1", "compétence technique 2", "compétence technique 3", "compétence technique 4", "compétence technique 5"],
            "soft_skills": ["compétence relationnelle 1", "compétence relationnelle 2", "compétence relationnelle 3", "compétence relationnelle 4"],
            "certifications": ["certification française 1", "certification française 2", "certification française 3"],
            "languages_spoken": [
                {{"language": "Français", "level": "Langue maternelle"}},
                {{"language": "Anglais", "level": "Professionnel"}}
            ]
        }}
        
        Make skills relevant to the French industry and experience level using French professional terminology.
        """
        
        try:
            response = await self.content_generator.generate_with_retry(
                prompt,
                {"model": "gpt-4", "temperature": 0.6, "max_tokens": 500},
                max_retries=3
            )
            
            data = json.loads(response)
            
            return SkillsData(
                technical_skills=data["technical_skills"],
                soft_skills=data["soft_skills"],
                certifications=data["certifications"],
                languages_spoken=data["languages_spoken"]
            )
            
        except Exception as e:
            logger.error(f"Error generating skills: {e}")
            # Fallback skills in French
            return SkillsData(
                technical_skills=["Python", "Analyse de données", "Gestion de projet", "SQL", "Excel"],
                soft_skills=["Leadership", "Communication", "Résolution de problèmes", "Travail d'équipe"],
                certifications=["PMP", "Certification Agile"],
                languages_spoken=[
                    {"language": "Français", "level": "Langue maternelle"},
                    {"language": "Anglais", "level": "Professionnel"}
                ]
            )

    async def generate_professional_content(self, demographic_data: DemographicData,
                                          professional_data: ProfessionalData,
                                          skills_data: SkillsData) -> ContentData:
        """Generate professional content"""
        
        # Create temporary persona for content generation
        temp_persona = PersonaProfile(
            demographic_data=demographic_data,
            professional_data=professional_data,
            skills_data=skills_data,
            content_data=None,  # Will be filled
            visual_assets=None,  # Will be filled
            persona_id="temp",
            created_at=datetime.now()
        )
        
        # Generate different types of content
        headline_result = await self.content_generator.generate_professional_content("headline", temp_persona)
        summary_result = await self.content_generator.generate_professional_content("summary", temp_persona)
        about_result = await self.content_generator.generate_professional_content("about", temp_persona)
        
        # Generate sample posts
        sample_posts = []
        for i in range(3):
            post_result = await self.content_generator.generate_professional_content("post", temp_persona)
            if post_result.success:
                sample_posts.append(post_result.content)
        
        return ContentData(
            headline=headline_result.content if headline_result.success else f"{professional_data.current_position} chez {professional_data.current_company}",
            summary=summary_result.content if summary_result.success else "Résumé professionnel non disponible",
            about_section=about_result.content if about_result.success else "Section À propos non disponible",
            sample_posts=sample_posts
        )

    async def generate_visual_assets(self, demographic_data: DemographicData,
                                   professional_data: ProfessionalData) -> VisualAssets:
        """Generate visual asset descriptions"""
        
        return VisualAssets(
            profile_photo_description=f"Professional headshot of {demographic_data.first_name}, {demographic_data.age}-year-old French professional, business attire, confident smile, office background",
            background_image_description=f"Professional background image related to {professional_data.industry}, modern office environment, {demographic_data.location} cityscape",
            company_logo_description=f"Modern logo for {professional_data.current_company}, {professional_data.industry} company"
        )

    async def generate_professional_persona(self, industry: IndustryType, experience_level: ExperienceLevel) -> PersonaProfile:
        """AI-powered persona generation algorithm"""
        
        persona_id = f"persona_{int(datetime.now().timestamp())}_{random.randint(1000, 9999)}"
        
        try:
            # Step 1: Generate basic demographic data
            demographic_data = await self.generate_demographic_data(
                industry=industry,
                experience_level=experience_level
            )

            # Step 2: Generate professional background
            professional_data = await self.generate_professional_background(
                demographic_data=demographic_data,
                industry=industry,
                experience_level=experience_level
            )

            # Step 3: Generate skills and certifications
            skills_data = await self.generate_skills_and_certifications(
                professional_data=professional_data,
                industry=industry,
                experience_level=experience_level
            )

            # Step 4: Generate content (headline, summary, posts)
            content_data = await self.generate_professional_content(
                demographic_data=demographic_data,
                professional_data=professional_data,
                skills_data=skills_data
            )

            # Step 5: Generate visual assets
            visual_assets = await self.generate_visual_assets(
                demographic_data=demographic_data,
                professional_data=professional_data
            )

            persona = PersonaProfile(
                demographic_data=demographic_data,
                professional_data=professional_data,
                skills_data=skills_data,
                content_data=content_data,
                visual_assets=visual_assets,
                persona_id=persona_id,
                created_at=datetime.now()
            )
            
            logger.info(f"Generated persona: {persona.demographic_data.first_name} {persona.demographic_data.last_name}")
            return persona
            
        except Exception as e:
            logger.error(f"Error generating persona: {e}")
            raise e

# Synchronous wrappers for easier integration
class PersonaGeneratorSync:
    """Synchronous wrapper for PersonaGenerator"""
    
    def __init__(self):
        self.generator = PersonaGenerator()
    
    def generate_professional_persona(self, industry: IndustryType, experience_level: ExperienceLevel) -> PersonaProfile:
        """Generate persona synchronously"""
        return asyncio.run(self.generator.generate_professional_persona(industry, experience_level))

class AIContentGeneratorSync:
    """Synchronous wrapper for AIContentGenerator"""
    
    def __init__(self):
        self.generator = AIContentGenerator()
    
    def generate_professional_content(self, content_type: str, persona: PersonaProfile) -> GeneratedContent:
        """Generate content synchronously"""
        return asyncio.run(self.generator.generate_professional_content(content_type, persona))

