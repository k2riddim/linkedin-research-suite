import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Button } from '@/components/ui/button.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Label } from '@/components/ui/label.jsx'
import { Textarea } from '@/components/ui/textarea.jsx'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
import { Alert, AlertDescription } from '@/components/ui/alert.jsx'
import { Progress } from '@/components/ui/progress.jsx'
import { Checkbox } from '@/components/ui/checkbox.jsx'
import { 
  Brain, 
  Wand2, 
  User, 
  Users,
  Briefcase, 
  GraduationCap, 
  MessageSquare, 
  Image, 
  Download,
  Copy,
  RefreshCw,
  CheckCircle,
  Sparkles,
  Globe,
  MapPin,
  Calendar,
  Trash2,
  AlertTriangle,
  CheckSquare,
  Square,
  Edit2,
  Check,
  X
} from 'lucide-react'

const PersonaGenerator = () => {
  const [generationStep, setGenerationStep] = useState(0)
  const [isGenerating, setIsGenerating] = useState(false)
  const [generatedPersona, setGeneratedPersona] = useState(null)
  const [existingPersonas, setExistingPersonas] = useState([])
  const [loading, setLoading] = useState(false)
  const [selectedPersonas, setSelectedPersonas] = useState(new Set())
  const [deleting, setDeleting] = useState(new Set())
  const [currentStepMessage, setCurrentStepMessage] = useState('')
  const [editingPersona, setEditingPersona] = useState(null)
  const [editForm, setEditForm] = useState({ firstName: '', lastName: '', manualEmail: '', manualPassword: '' })
  const [updating, setUpdating] = useState(new Set())

  const generationSteps = [
    'Initialisation...',
    'Génération du profil démographique...',
    'Création du background professionnel...',
    'Génération des compétences...',
    'Création du contenu LinkedIn...',
    'Finalisation des assets visuels...',
    'Sauvegarde en base de données...'
  ]
  
  const [personaConfig, setPersonaConfig] = useState({
    industry: '',
    experienceLevel: '',
    location: 'Paris, France',
    specialization: '',
    companySize: '',
    educationLevel: ''
  })

  const [generatedContent, setGeneratedContent] = useState({
    headline: '',
    summary: '',
    aboutSection: '',
    samplePosts: []
  })

  const industries = [
    { value: 'technology', label: 'Technology' },
    { value: 'finance', label: 'Finance' },
    { value: 'healthcare', label: 'Healthcare' },
    { value: 'marketing', label: 'Marketing' },
    { value: 'consulting', label: 'Consulting' },
    { value: 'education', label: 'Education' },
    { value: 'manufacturing', label: 'Manufacturing' },
    { value: 'retail', label: 'Retail' }
  ]

  const experienceLevels = [
    { value: 'entry_level', label: 'Entry Level (0-2 years)' },
    { value: 'mid_level', label: 'Mid Level (3-7 years)' },
    { value: 'senior_level', label: 'Senior Level (8-15 years)' },
    { value: 'executive', label: 'Executive (15+ years)' }
  ]

  // Load existing personas on component mount
  useEffect(() => {
    loadExistingPersonas()
  }, [])

  const loadExistingPersonas = async () => {
    try {
      setLoading(true)
      const response = await fetch('/api/ai/personas')
      const data = await response.json()
      
      if (response.ok) {
        setExistingPersonas(data.personas || [])
      } else {
        console.error('Failed to load personas:', data.error)
      }
    } catch (error) {
      console.error('Error loading personas:', error)
    } finally {
      setLoading(false)
    }
  }

  const togglePersonaSelection = (personaId) => {
    const newSelected = new Set(selectedPersonas)
    if (newSelected.has(personaId)) {
      newSelected.delete(personaId)
    } else {
      newSelected.add(personaId)
    }
    setSelectedPersonas(newSelected)
  }

  const selectAllPersonas = () => {
    const allIds = new Set(existingPersonas.map(p => p.persona_id))
    setSelectedPersonas(allIds)
  }

  const clearSelection = () => {
    setSelectedPersonas(new Set())
  }

  const deletePersona = async (personaId) => {
    if (!confirm('Êtes-vous sûr de vouloir supprimer cette persona ? Cette action est irréversible.')) {
      return
    }

    try {
      setDeleting(prev => new Set([...prev, personaId]))
      
      const response = await fetch(`/api/ai/personas/${personaId}`, {
        method: 'DELETE'
      })

      if (response.ok) {
        // Remove from existing personas list
        setExistingPersonas(prev => prev.filter(p => p.persona_id !== personaId))
        // Remove from selection if selected
        setSelectedPersonas(prev => {
          const newSet = new Set(prev)
          newSet.delete(personaId)
          return newSet
        })
      } else {
        const data = await response.json()
        alert(`Erreur lors de la suppression: ${data.error}`)
      }
    } catch (error) {
      console.error('Error deleting persona:', error)
      alert('Erreur lors de la suppression de la persona')
    } finally {
      setDeleting(prev => {
        const newSet = new Set(prev)
        newSet.delete(personaId)
        return newSet
      })
    }
  }

  const startEditPersona = (persona) => {
    setEditingPersona(persona.persona_id)
    setEditForm({
      firstName: persona.demographic_data.first_name,
      lastName: persona.demographic_data.last_name,
      manualEmail: persona.manual_email || '',
      manualPassword: persona.manual_email_password || ''
    })
  }

  const cancelEdit = () => {
    setEditingPersona(null)
    setEditForm({ firstName: '', lastName: '', manualEmail: '', manualPassword: '' })
  }

  const savePersonaEdit = async (personaId) => {
    if (!editForm.firstName.trim() || !editForm.lastName.trim()) {
      alert('Le prénom et le nom ne peuvent pas être vides')
      return
    }

    try {
      setUpdating(prev => new Set([...prev, personaId]))
      
      const response = await fetch(`/api/ai/personas/${personaId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          first_name: editForm.firstName.trim(),
          last_name: editForm.lastName.trim(),
          manual_email: editForm.manualEmail.trim() || null,
          manual_email_password: editForm.manualPassword || null
        })
      })

      if (response.ok) {
        // Update the persona in the list
        setExistingPersonas(prev => prev.map(p => 
          p.persona_id === personaId 
            ? {
                ...p,
                demographic_data: {
                  ...p.demographic_data,
                  first_name: editForm.firstName.trim(),
                  last_name: editForm.lastName.trim()
                },
                manual_email: editForm.manualEmail.trim() || null,
                manual_email_password: editForm.manualPassword || null
              }
            : p
        ))
        setEditingPersona(null)
        setEditForm({ firstName: '', lastName: '', manualEmail: '', manualPassword: '' })
      } else {
        const data = await response.json()
        alert(`Erreur lors de la modification: ${data.error}`)
      }
    } catch (error) {
      console.error('Error updating persona:', error)
      alert('Erreur lors de la modification de la persona')
    } finally {
      setUpdating(prev => {
        const newSet = new Set(prev)
        newSet.delete(personaId)
        return newSet
      })
    }
  }



  const generatePersona = async () => {
    setIsGenerating(true)
    setGenerationStep(0)
    setCurrentStepMessage(generationSteps[0])

    try {
      // Step 1: Call backend API to generate persona
      setGenerationStep(1)
      setCurrentStepMessage(generationSteps[1])
      
      const response = await fetch('/api/ai/personas/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          industry: personaConfig.industry,
          experience_level: personaConfig.experienceLevel
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const persona = await response.json()

      // Simulate progressive steps for UX (since backend generates everything at once)
      setGenerationStep(2)
      setCurrentStepMessage(generationSteps[2])
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      setGenerationStep(3)
      setCurrentStepMessage(generationSteps[3])
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      setGenerationStep(4)
      setCurrentStepMessage(generationSteps[4])
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      setGenerationStep(5)
      setCurrentStepMessage(generationSteps[5])
      await new Promise(resolve => setTimeout(resolve, 1000))

      // Transform API response to match frontend format
      const transformedPersona = {
        id: persona.persona_id,
        demographic: {
          firstName: persona.demographic_data.first_name,
          lastName: persona.demographic_data.last_name,
          age: persona.demographic_data.age,
          location: persona.demographic_data.location,
          nationality: persona.demographic_data.nationality,
          languages: persona.demographic_data.languages
        },
        professional: {
          currentPosition: persona.professional_data.current_position,
          currentCompany: persona.professional_data.current_company,
          industry: persona.professional_data.industry,
          experienceYears: persona.professional_data.experience_years,
          education: persona.professional_data.education,
          previousPositions: persona.professional_data.previous_positions
        },
        skills: {
          technical: persona.skills_data.technical_skills,
          soft: persona.skills_data.soft_skills,
          certifications: persona.skills_data.certifications,
          languages: persona.skills_data.languages_spoken
        },
        content: {
          headline: persona.content_data.headline,
          summary: persona.content_data.summary,
          aboutSection: persona.content_data.about_section,
          samplePosts: persona.content_data.sample_posts
        },
        visualAssets: {
          profilePhotoDescription: persona.visual_assets.profile_photo_description,
          backgroundImageDescription: persona.visual_assets.background_image_description,
          companyLogoDescription: persona.visual_assets.company_logo_description
        }
      }

      setGeneratedPersona(transformedPersona)
      setGeneratedContent(transformedPersona.content)
      setGenerationStep(6)
      setCurrentStepMessage(generationSteps[6])
      await new Promise(resolve => setTimeout(resolve, 500))
      
      // Refresh the personas list
      await loadExistingPersonas()
      
    } catch (error) {
      console.error('Error generating persona:', error)
    } finally {
      setIsGenerating(false)
    }
  }

  const regenerateContent = async (contentType) => {
    if (!generatedPersona) return

    try {
      const response = await fetch('/api/ai/content/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content_type: contentType,
          persona_data: {
            demographic_data: {
              first_name: generatedPersona.demographic.firstName,
              last_name: generatedPersona.demographic.lastName,
              age: generatedPersona.demographic.age,
              location: generatedPersona.demographic.location,
              nationality: generatedPersona.demographic.nationality,
              languages: generatedPersona.demographic.languages
            },
            professional_data: {
              current_position: generatedPersona.professional.currentPosition,
              current_company: generatedPersona.professional.currentCompany,
              industry: generatedPersona.professional.industry,
              experience_years: generatedPersona.professional.experienceYears,
              education: generatedPersona.professional.education,
              previous_positions: generatedPersona.professional.previousPositions
            },
            skills_data: {
              technical_skills: generatedPersona.skills.technical,
              soft_skills: generatedPersona.skills.soft,
              certifications: generatedPersona.skills.certifications,
              languages_spoken: generatedPersona.skills.languages
            },
            persona_id: generatedPersona.id
          }
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()

      if (result.success) {
        setGeneratedContent(prev => ({
          ...prev,
          [contentType]: result.content
        }))
      }
    } catch (error) {
      console.error('Error regenerating content:', error)
    }
  }

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white">AI Persona Generator</h2>
          <p className="text-slate-600 dark:text-slate-300">
            Create realistic professional personas for LinkedIn research
          </p>
        </div>
        
        <Button 
          onClick={generatePersona}
          disabled={isGenerating || !personaConfig.industry || !personaConfig.experienceLevel}
          className="bg-purple-600 hover:bg-purple-700"
        >
          {isGenerating ? (
            <>
              <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
              {currentStepMessage}
            </>
          ) : (
            <>
              <Wand2 className="h-4 w-4 mr-2" />
              Generate Persona
            </>
          )}
        </Button>
      </div>

      {/* Existing Personas */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Users className="h-5 w-5 text-blue-600" />
              <span>Existing Personas ({existingPersonas.length})</span>
              {selectedPersonas.size > 0 && (
                <Badge variant="outline" className="bg-blue-50 text-blue-700">
                  {selectedPersonas.size} sélectionnée(s)
                </Badge>
              )}
            </div>
            <div className="flex items-center space-x-2">
              {selectedPersonas.size > 0 && (
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={clearSelection}
                >
                  Désélectionner ({selectedPersonas.size})
                </Button>
              )}
              <Button 
                variant="outline" 
                size="sm" 
                onClick={loadExistingPersonas}
                disabled={loading}
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                Actualiser
              </Button>
            </div>
          </CardTitle>
          <CardDescription>
            Personas IA générées précédemment - Gérez et modifiez vos personas
          </CardDescription>
          {existingPersonas.length > 0 && (
            <div className="flex items-center space-x-2 pt-2">
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={selectAllPersonas}
                className="text-xs"
              >
                <CheckSquare className="h-3 w-3 mr-1" />
                Tout sélectionner
              </Button>
            </div>
          )}
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <RefreshCw className="h-6 w-6 animate-spin text-slate-400" />
              <span className="ml-2 text-slate-600">Loading personas...</span>
            </div>
          ) : existingPersonas.length === 0 ? (
            <div className="text-center py-8 text-slate-500">
              <Brain className="h-12 w-12 mx-auto mb-4 text-slate-300" />
              <p>No personas generated yet.</p>
              <p className="text-sm">Generate your first persona using the form below.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {existingPersonas.map((persona) => (
                <Card 
                  key={persona.persona_id} 
                  className={`hover:shadow-md transition-all cursor-pointer ${
                    selectedPersonas.has(persona.persona_id) 
                      ? 'ring-2 ring-blue-500 bg-blue-50 dark:bg-blue-950' 
                      : ''
                  }`}
                  onClick={() => togglePersonaSelection(persona.persona_id)}
                >
                  <CardContent className="p-4">
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <div className="w-10 h-10 bg-gradient-to-br from-purple-400 to-blue-500 rounded-full flex items-center justify-center text-white font-semibold">
                            {persona.demographic_data.first_name[0]}{persona.demographic_data.last_name[0]}
                          </div>
                          <div className="flex-1">
                            {editingPersona === persona.persona_id ? (
                              <div className="space-y-2">
                                <div className="flex space-x-2">
                                  <Input
                                    value={editForm.firstName}
                                    onChange={(e) => setEditForm(prev => ({ ...prev, firstName: e.target.value }))}
                                    placeholder="Prénom"
                                    className="text-sm h-8"
                                  />
                                  <Input
                                    value={editForm.lastName}
                                    onChange={(e) => setEditForm(prev => ({ ...prev, lastName: e.target.value }))}
                                    placeholder="Nom"
                                    className="text-sm h-8"
                                  />
                                </div>
                                <div className="flex space-x-2">
                                  <Input
                                    value={editForm.manualEmail}
                                    onChange={(e) => setEditForm(prev => ({ ...prev, manualEmail: e.target.value }))}
                                    placeholder="Manual email (optional)"
                                    className="text-sm h-8"
                                  />
                                  <Input
                                    type="password"
                                    value={editForm.manualPassword}
                                    onChange={(e) => setEditForm(prev => ({ ...prev, manualPassword: e.target.value }))}
                                    placeholder="Email password (optional)"
                                    className="text-sm h-8"
                                  />
                                </div>
                                <p className="text-sm text-slate-600 dark:text-slate-300">
                                  {persona.demographic_data.age} ans • {persona.demographic_data.location}
                                </p>
                              </div>
                            ) : (
                              <div>
                                <h3 className="font-semibold text-slate-900 dark:text-white">
                                  {persona.demographic_data.first_name} {persona.demographic_data.last_name}
                                </h3>
                                <p className="text-sm text-slate-600 dark:text-slate-300">
                                  {persona.demographic_data.age} ans • {persona.demographic_data.location}
                                </p>
                              </div>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          {editingPersona === persona.persona_id ? (
                            <>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={(e) => {
                                  e.stopPropagation()
                                  savePersonaEdit(persona.persona_id)
                                }}
                                disabled={updating.has(persona.persona_id)}
                                className="text-green-600 hover:text-green-700 hover:bg-green-50 p-1"
                              >
                                {updating.has(persona.persona_id) ? (
                                  <RefreshCw className="h-4 w-4 animate-spin" />
                                ) : (
                                  <Check className="h-4 w-4" />
                                )}
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={(e) => {
                                  e.stopPropagation()
                                  cancelEdit()
                                }}
                                className="text-gray-600 hover:text-gray-700 hover:bg-gray-50 p-1"
                              >
                                <X className="h-4 w-4" />
                              </Button>
                            </>
                          ) : (
                            <>
                              <Checkbox
                                checked={selectedPersonas.has(persona.persona_id)}
                                onChange={() => togglePersonaSelection(persona.persona_id)}
                                className="data-[state=checked]:bg-blue-600 data-[state=checked]:border-blue-600"
                              />
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={(e) => {
                                  e.stopPropagation()
                                  startEditPersona(persona)
                                }}
                                className="text-blue-600 hover:text-blue-700 hover:bg-blue-50 p-1"
                              >
                                <Edit2 className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={(e) => {
                                  e.stopPropagation()
                                  deletePersona(persona.persona_id)
                                }}
                                disabled={deleting.has(persona.persona_id)}
                                className="text-red-600 hover:text-red-700 hover:bg-red-50 p-1"
                              >
                                {deleting.has(persona.persona_id) ? (
                                  <RefreshCw className="h-4 w-4 animate-spin" />
                                ) : (
                                  <Trash2 className="h-4 w-4" />
                                )}
                              </Button>
                            </>
                          )}
                        </div>
                      </div>
                      
                      <div className="space-y-2">
                        <div className="text-sm">
                          <span className="font-medium text-slate-700 dark:text-slate-300">Poste:</span>
                          <p className="text-slate-600 dark:text-slate-400 truncate">
                            {persona.professional_data.current_position}
                          </p>
                        </div>
                        <div className="text-sm">
                          <span className="font-medium text-slate-700 dark:text-slate-300">Entreprise:</span>
                          <p className="text-slate-600 dark:text-slate-400 truncate">
                            {persona.professional_data.current_company}
                          </p>
                        </div>
                        <div className="flex items-center space-x-2 text-sm">
                          <Badge variant="outline" className="text-xs">
                            {persona.professional_data.industry}
                          </Badge>
                          <Badge variant="outline" className="text-xs">
                            {persona.professional_data.experience_years} ans d'exp.
                          </Badge>
                        </div>
                      </div>
                      
                      <div className="flex items-center justify-between">
                        <div className="text-xs text-slate-500">
                          Créé le {new Date(persona.created_at).toLocaleDateString('fr-FR')}
                        </div>
                        {selectedPersonas.has(persona.persona_id) && (
                          <Badge variant="default" className="text-xs bg-blue-600">
                            Sélectionnée
                          </Badge>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Configuration Panel */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Brain className="h-5 w-5 text-purple-600" />
            <span>Persona Configuration</span>
          </CardTitle>
          <CardDescription>
            Configure the parameters for AI persona generation
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="industry">Industry *</Label>
              <Select value={personaConfig.industry} onValueChange={(value) => setPersonaConfig(prev => ({ ...prev, industry: value }))}>
                <SelectTrigger>
                  <SelectValue placeholder="Select industry" />
                </SelectTrigger>
                <SelectContent>
                  {industries.map((industry) => (
                    <SelectItem key={industry.value} value={industry.value}>
                      {industry.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="experienceLevel">Experience Level *</Label>
              <Select value={personaConfig.experienceLevel} onValueChange={(value) => setPersonaConfig(prev => ({ ...prev, experienceLevel: value }))}>
                <SelectTrigger>
                  <SelectValue placeholder="Select experience level" />
                </SelectTrigger>
                <SelectContent>
                  {experienceLevels.map((level) => (
                    <SelectItem key={level.value} value={level.value}>
                      {level.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="location">Location</Label>
              <Input
                id="location"
                value={personaConfig.location}
                onChange={(e) => setPersonaConfig(prev => ({ ...prev, location: e.target.value }))}
                placeholder="Paris, France"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="specialization">Specialization</Label>
              <Input
                id="specialization"
                value={personaConfig.specialization}
                onChange={(e) => setPersonaConfig(prev => ({ ...prev, specialization: e.target.value }))}
                placeholder="e.g., Machine Learning, Digital Marketing"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="companySize">Company Size</Label>
              <Select value={personaConfig.companySize} onValueChange={(value) => setPersonaConfig(prev => ({ ...prev, companySize: value }))}>
                <SelectTrigger>
                  <SelectValue placeholder="Select company size" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="startup">Startup (1-50)</SelectItem>
                  <SelectItem value="small">Small (51-200)</SelectItem>
                  <SelectItem value="medium">Medium (201-1000)</SelectItem>
                  <SelectItem value="large">Large (1000+)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="educationLevel">Education Level</Label>
              <Select value={personaConfig.educationLevel} onValueChange={(value) => setPersonaConfig(prev => ({ ...prev, educationLevel: value }))}>
                <SelectTrigger>
                  <SelectValue placeholder="Select education level" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="bachelor">Bachelor's Degree</SelectItem>
                  <SelectItem value="master">Master's Degree</SelectItem>
                  <SelectItem value="phd">PhD</SelectItem>
                  <SelectItem value="professional">Professional Certification</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {isGenerating && (
            <Alert>
              <Sparkles className="h-4 w-4" />
              <AlertDescription>
                <div className="space-y-2">
                  <div>{generationSteps[generationStep]}</div>
                  <Progress value={(generationStep / 6) * 100} className="h-2" />
                </div>
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Generated Persona */}
      {generatedPersona && (
        <Tabs defaultValue="overview" className="space-y-4">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="professional">Professional</TabsTrigger>
            <TabsTrigger value="content">Content</TabsTrigger>
            <TabsTrigger value="skills">Skills</TabsTrigger>
            <TabsTrigger value="assets">Assets</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <User className="h-5 w-5 text-blue-600" />
                  <span>Persona Overview</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <div>
                      <h3 className="text-lg font-semibold">
                        {generatedPersona.demographic.firstName} {generatedPersona.demographic.lastName}
                      </h3>
                      <p className="text-slate-600 dark:text-slate-300">
                        {generatedPersona.professional.currentPosition} at {generatedPersona.professional.currentCompany}
                      </p>
                    </div>
                    
                    <div className="space-y-2">
                      <div className="flex items-center space-x-2 text-sm">
                        <MapPin className="h-4 w-4 text-slate-500" />
                        <span>{generatedPersona.demographic.location}</span>
                      </div>
                      <div className="flex items-center space-x-2 text-sm">
                        <Calendar className="h-4 w-4 text-slate-500" />
                        <span>{generatedPersona.demographic.age} years old</span>
                      </div>
                      <div className="flex items-center space-x-2 text-sm">
                        <Briefcase className="h-4 w-4 text-slate-500" />
                        <span>{generatedPersona.professional.experienceYears} years experience</span>
                      </div>
                      <div className="flex items-center space-x-2 text-sm">
                        <Globe className="h-4 w-4 text-slate-500" />
                        <span>{generatedPersona.demographic.languages.join(', ')}</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="space-y-4">
                    <div>
                      <h4 className="font-medium mb-2">Industry & Expertise</h4>
                      <Badge variant="outline" className="mb-2">
                        {generatedPersona.professional.industry}
                      </Badge>
                      <div className="flex flex-wrap gap-1">
                        {generatedPersona.skills.technical.slice(0, 4).map((skill) => (
                          <Badge key={skill} variant="secondary" className="text-xs">
                            {skill}
                          </Badge>
                        ))}
                      </div>
                    </div>
                    
                    <div>
                      <h4 className="font-medium mb-2">Education</h4>
                      {generatedPersona.professional.education.map((edu, index) => (
                        <div key={index} className="text-sm text-slate-600 dark:text-slate-300">
                          <div className="font-medium">{edu.degree}</div>
                          <div>{edu.school} • {edu.year}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Professional Tab */}
          <TabsContent value="professional" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Briefcase className="h-5 w-5 text-green-600" />
                  <span>Professional Background</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div>
                  <h4 className="font-medium mb-3">Current Position</h4>
                  <div className="p-4 bg-slate-50 dark:bg-slate-800 rounded-lg">
                    <div className="font-medium">{generatedPersona.professional.currentPosition}</div>
                    <div className="text-slate-600 dark:text-slate-300">{generatedPersona.professional.currentCompany}</div>
                    <div className="text-sm text-slate-500 mt-1">{generatedPersona.professional.industry}</div>
                  </div>
                </div>
                
                <div>
                  <h4 className="font-medium mb-3">Work Experience</h4>
                  <div className="space-y-3">
                    {generatedPersona.professional.previousPositions.map((position, index) => (
                      <div key={index} className="p-3 border border-slate-200 dark:border-slate-700 rounded-lg">
                        <div className="font-medium">{position.title}</div>
                        <div className="text-slate-600 dark:text-slate-300">{position.company}</div>
                        <div className="text-sm text-slate-500">{position.duration}</div>
                      </div>
                    ))}
                  </div>
                </div>
                
                <div>
                  <h4 className="font-medium mb-3">Education</h4>
                  <div className="space-y-3">
                    {generatedPersona.professional.education.map((edu, index) => (
                      <div key={index} className="p-3 border border-slate-200 dark:border-slate-700 rounded-lg">
                        <div className="font-medium">{edu.degree}</div>
                        <div className="text-slate-600 dark:text-slate-300">{edu.school}</div>
                        <div className="text-sm text-slate-500">{edu.year}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Content Tab */}
          <TabsContent value="content" className="space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span>LinkedIn Headline</span>
                    <div className="flex space-x-2">
                      <Button variant="outline" size="sm" onClick={() => regenerateContent('headline')}>
                        <RefreshCw className="h-3 w-3" />
                      </Button>
                      <Button variant="outline" size="sm" onClick={() => copyToClipboard(generatedContent.headline)}>
                        <Copy className="h-3 w-3" />
                      </Button>
                    </div>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <Textarea
                    value={generatedContent.headline}
                    onChange={(e) => setGeneratedContent(prev => ({ ...prev, headline: e.target.value }))}
                    rows={3}
                    className="resize-none"
                  />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span>About Section</span>
                    <div className="flex space-x-2">
                      <Button variant="outline" size="sm" onClick={() => regenerateContent('aboutSection')}>
                        <RefreshCw className="h-3 w-3" />
                      </Button>
                      <Button variant="outline" size="sm" onClick={() => copyToClipboard(generatedContent.aboutSection)}>
                        <Copy className="h-3 w-3" />
                      </Button>
                    </div>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <Textarea
                    value={generatedContent.aboutSection}
                    onChange={(e) => setGeneratedContent(prev => ({ ...prev, aboutSection: e.target.value }))}
                    rows={4}
                    className="resize-none"
                  />
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>Professional Summary</span>
                  <div className="flex space-x-2">
                    <Button variant="outline" size="sm" onClick={() => regenerateContent('summary')}>
                      <RefreshCw className="h-3 w-3" />
                    </Button>
                    <Button variant="outline" size="sm" onClick={() => copyToClipboard(generatedContent.summary)}>
                      <Copy className="h-3 w-3" />
                    </Button>
                  </div>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Textarea
                  value={generatedContent.summary}
                  onChange={(e) => setGeneratedContent(prev => ({ ...prev, summary: e.target.value }))}
                  rows={6}
                  className="resize-none"
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <MessageSquare className="h-5 w-5 text-blue-600" />
                  <span>Sample LinkedIn Posts</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {generatedContent.samplePosts.map((post, index) => (
                  <div key={index} className="p-4 bg-slate-50 dark:bg-slate-800 rounded-lg">
                    <div className="flex justify-between items-start mb-2">
                      <span className="text-sm font-medium">Post {index + 1}</span>
                      <Button variant="outline" size="sm" onClick={() => copyToClipboard(post)}>
                        <Copy className="h-3 w-3" />
                      </Button>
                    </div>
                    <p className="text-sm">{post}</p>
                  </div>
                ))}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Skills Tab */}
          <TabsContent value="skills" className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle>Technical Skills</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    {generatedPersona.skills.technical.map((skill) => (
                      <Badge key={skill} variant="default">
                        {skill}
                      </Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Soft Skills</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    {generatedPersona.skills.soft.map((skill) => (
                      <Badge key={skill} variant="secondary">
                        {skill}
                      </Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Certifications</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {generatedPersona.skills.certifications.map((cert) => (
                      <div key={cert} className="flex items-center space-x-2">
                        <CheckCircle className="h-4 w-4 text-green-600" />
                        <span className="text-sm">{cert}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Languages</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {generatedPersona.skills.languages.map((lang) => (
                      <div key={lang.language} className="flex justify-between items-center">
                        <span className="text-sm">{lang.language}</span>
                        <Badge variant="outline">{lang.level}</Badge>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Assets Tab */}
          <TabsContent value="assets" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Image className="h-5 w-5 text-purple-600" />
                  <span>Visual Assets</span>
                </CardTitle>
                <CardDescription>
                  AI-generated descriptions for visual content creation
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Profile Photo Description</Label>
                  <Textarea
                    value={generatedPersona.visualAssets.profilePhotoDescription}
                    readOnly
                    rows={2}
                    className="resize-none bg-slate-50 dark:bg-slate-800"
                  />
                  <Button variant="outline" size="sm" onClick={() => copyToClipboard(generatedPersona.visualAssets.profilePhotoDescription)}>
                    <Copy className="h-3 w-3 mr-2" />
                    Copy Description
                  </Button>
                </div>

                <div className="space-y-2">
                  <Label>Background Image Description</Label>
                  <Textarea
                    value={generatedPersona.visualAssets.backgroundImageDescription}
                    readOnly
                    rows={2}
                    className="resize-none bg-slate-50 dark:bg-slate-800"
                  />
                  <Button variant="outline" size="sm" onClick={() => copyToClipboard(generatedPersona.visualAssets.backgroundImageDescription)}>
                    <Copy className="h-3 w-3 mr-2" />
                    Copy Description
                  </Button>
                </div>

                <div className="space-y-2">
                  <Label>Company Logo Description</Label>
                  <Textarea
                    value={generatedPersona.visualAssets.companyLogoDescription}
                    readOnly
                    rows={2}
                    className="resize-none bg-slate-50 dark:bg-slate-800"
                  />
                  <Button variant="outline" size="sm" onClick={() => copyToClipboard(generatedPersona.visualAssets.companyLogoDescription)}>
                    <Copy className="h-3 w-3 mr-2" />
                    Copy Description
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}

      {/* Export Options */}
      {generatedPersona && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Download className="h-5 w-5 text-green-600" />
              <span>Export Persona</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex space-x-4">
              <Button variant="outline">
                <Download className="h-4 w-4 mr-2" />
                Export as JSON
              </Button>
              <Button variant="outline">
                <Download className="h-4 w-4 mr-2" />
                Export as PDF
              </Button>
              <Button>
                <User className="h-4 w-4 mr-2" />
                Create LinkedIn Account
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default PersonaGenerator

