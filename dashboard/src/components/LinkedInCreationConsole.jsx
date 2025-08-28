import { useState, useEffect, useRef } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Button } from '@/components/ui/button.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Progress } from '@/components/ui/progress.jsx'
import { Alert, AlertDescription } from '@/components/ui/alert.jsx'

import { 
  Terminal, 
  Play, 
  Square, 
  CheckCircle, 
  AlertTriangle, 
  Clock,
  ExternalLink,
  RefreshCw
} from 'lucide-react'
import io from 'socket.io-client'

const LinkedInCreationConsole = ({ accountId, onClose, onComplete }) => {
  const [isConnected, setIsConnected] = useState(false)
  const [isCreating, setIsCreating] = useState(false)
  const [currentStep, setCurrentStep] = useState(null)
  const [progress, setProgress] = useState(0)
  const [logs, setLogs] = useState([])
  const [finalResult, setFinalResult] = useState(null)
  const [error, setError] = useState(null)
  const [manualCode, setManualCode] = useState("")
  
  const socketRef = useRef(null)
  const logsEndRef = useRef(null)
  const recentKeysRef = useRef(new Map())

  // Auto-scroll to bottom of logs
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])

  // Initialize WebSocket connection
  useEffect(() => {
    if (!accountId) return

    const socket = io(window.location.origin, {
      transports: ['websocket', 'polling'],
      path: '/socket.io/'
    })

    socketRef.current = socket

    socket.on('connect', () => {
      setIsConnected(true)
      addLog('Console connectée au serveur', 'success')
      
      // Join room for this account
      socket.emit('join_account_room', { account_id: accountId })
    })

    socket.on('disconnect', () => {
      setIsConnected(false)
      addLog('Connexion au serveur perdue', 'error')
    })

    socket.on('joined_room', (data) => {
      addLog(`Surveillance activée pour le compte ${data.account_id}`, 'info')
    })

    socket.on('progress_update', (data) => {
      setCurrentStep(data.step)
      setProgress(data.progress)
      addLog(`[${data.step}] ${data.message}`, data.status)
    })

    socket.on('enhanced_progress_update', (data) => {
      // Handle enhanced progress updates with detailed sub-steps
      setProgress(data.overall_progress)
      
      if (data.current_step) {
        setCurrentStep(data.current_step.name)
      }
      
      // Process recent logs and add them to the console
      if (data.recent_logs && data.recent_logs.length > 0) {
        data.recent_logs.forEach(logEntry => {
          const logType = {
            'debug': 'info',
            'info': 'info', 
            'success': 'success',
            'warning': 'warning',
            'error': 'error'
          }[logEntry.level] || 'info'
          
          let logMessage = logEntry.message
          
          // Add execution time if available
          if (logEntry.execution_time) {
            logMessage += ` (${logEntry.execution_time.toFixed(2)}s)`
          }
          
          // Add details if important
          if (logEntry.details && Object.keys(logEntry.details).length > 0) {
            const importantDetails = []
            if (logEntry.details.account_email) importantDetails.push(`Email: ${logEntry.details.account_email}`)
            if (logEntry.details.linkedin_url) importantDetails.push(`URL: ${logEntry.details.linkedin_url}`)
            if (logEntry.details.detection_risk) importantDetails.push(`Risk: ${logEntry.details.detection_risk}`)
            if (logEntry.details.service) importantDetails.push(`Service: ${logEntry.details.service}`)
            if (logEntry.details.proxy_service) importantDetails.push(`Proxy: ${logEntry.details.proxy_service}`)
            
            if (importantDetails.length > 0) {
              logMessage += ` | ${importantDetails.join(' | ')}`
            }
          }
          
          addLog(logMessage, logType)
        })
      }
      
      // Show step progress breakdown in console
      if (data.steps) {
        const activeStep = data.steps.find(step => step.status === 'running')
        if (activeStep && activeStep.sub_steps) {
          const completedSubSteps = activeStep.sub_steps.filter(sub => sub.status === 'success').length
          const totalSubSteps = activeStep.sub_steps.length
          addLog(`📊 Progression: ${activeStep.name} (${completedSubSteps}/${totalSubSteps} sous-étapes)`, 'info')
        }
      }
    })

    // Listen to backend WARNING/ERROR logs and mirror them in the console
    socket.on('backend_log', (data) => {
      const level = (data?.level || '').toUpperCase()
      const msg = data?.message || ''
      const loggerName = data?.logger ? `[${data.logger}] ` : ''
      if (level === 'WARNING') {
        addLog(`${loggerName}${msg}`, 'warning')
      } else if (level === 'ERROR' || level === 'CRITICAL') {
        addLog(`${loggerName}${msg}`, 'error')
      } else if (level === 'INFO') {
        addLog(`${loggerName}${msg}`, 'info')
      }
    })

    socket.on('creation_complete', (data) => {
      setIsCreating(false)
      setFinalResult(data)
      
      if (data.success) {
        addLog(`✅ Compte LinkedIn créé avec succès!`, 'success')
        if (data.result?.linkedin_url) {
          addLog(`🔗 Profile URL: ${data.result.linkedin_url}`, 'success')
        }
        setProgress(100)
        
        // Notify parent component
        onComplete?.(data)
      } else {
        addLog(`❌ Échec de la création: ${data.error}`, 'error')
        setError(data.error)
      }
    })

    socket.on('creation_error', (data) => {
      addLog(`🚨 Erreur: ${data.message}`, 'error')
      setError(data.message)
    })

    socket.on('error', (data) => {
      addLog(`⚠️ Erreur WebSocket: ${data.message}`, 'error')
    })

    return () => {
      if (socket) {
        socket.emit('leave_account_room', { account_id: accountId })
        socket.disconnect()
      }
    }
  }, [accountId])

  const addLog = (message, type = 'info') => {
    const timestamp = new Date().toLocaleTimeString()
    const key = `${type}|${message}`
    const now = Date.now()
    const last = recentKeysRef.current.get(key)
    if (last && (now - last) < 1200) {
      return
    }
    recentKeysRef.current.set(key, now)
    if (recentKeysRef.current.size > 500) {
      const entries = Array.from(recentKeysRef.current.entries()).sort((a,b)=>a[1]-b[1]).slice(0, 400)
      recentKeysRef.current = new Map(entries)
    }
    const logEntry = {
      id: Date.now() + Math.random(),
      timestamp,
      message,
      type
    }
    setLogs(prev => [...prev, logEntry])
  }

  const startCreation = async () => {
    if (!accountId || isCreating) return

    try {
      setIsCreating(true)
      setError(null)
      setFinalResult(null)
      setProgress(0)
      addLog('Démarrage de la création du compte LinkedIn...', 'info')

      const response = await fetch(`/api/accounts/${accountId}/create-linkedin`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          use_real_credentials: true,
          warmup_after_creation: true
        })
      })

      const data = await response.json()

      if (response.ok) {
        addLog(`Processus lancé en arrière-plan (WebSocket room: ${data.websocket_room})`, 'info')
      } else {
        setIsCreating(false)
        setError(data.error)
        addLog(`Erreur de démarrage: ${data.error}`, 'error')
      }
    } catch (error) {
      setIsCreating(false)
      setError(error.message)
      addLog(`Erreur de connexion: ${error.message}`, 'error')
    }
  }

  const stopCreation = () => {
    setIsCreating(false)
    addLog('Processus arrêté par l\'utilisateur', 'warning')
  }

  const clearLogs = () => {
    setLogs([])
  }

  const submitManualCode = async () => {
    if (!manualCode.trim()) return
    try {
      const response = await fetch(`/api/accounts/${accountId}/submit-email-code`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: manualCode.trim() })
      })
      const data = await response.json()
      if (response.ok) {
        addLog(`Code de vérification soumis: ${manualCode.trim()}`, 'success')
        setManualCode("")
      } else {
        addLog(`Échec d'envoi du code: ${data.error}`, 'error')
      }
    } catch (e) {
      addLog(`Erreur réseau en soumettant le code: ${e.message}`, 'error')
    }
  }

  const getLogIcon = (type) => {
    switch (type) {
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'error':
        return <AlertTriangle className="h-4 w-4 text-red-500" />
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />
      case 'info':
      default:
        return <Clock className="h-4 w-4 text-blue-500" />
    }
  }

  const getLogTextColor = (type) => {
    switch (type) {
      case 'success':
        return 'text-green-700 dark:text-green-300'
      case 'error':
        return 'text-red-700 dark:text-red-300'
      case 'warning':
        return 'text-yellow-700 dark:text-yellow-300'
      case 'info':
      default:
        return 'text-slate-700 dark:text-slate-300'
    }
  }

  return (
    <div className="space-y-4">
      {/* Header with controls */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Terminal className="h-5 w-5 text-blue-600" />
              <span>LinkedIn Account Creation Console</span>
              <Badge variant={isConnected ? "default" : "destructive"}>
                {isConnected ? "Connecté" : "Déconnecté"}
              </Badge>
            </div>
            <div className="flex items-center space-x-2">
              <Button
                onClick={clearLogs}
                variant="outline"
                size="sm"
                disabled={logs.length === 0}
              >
                Effacer
              </Button>
              <Button
                onClick={onClose}
                variant="outline"
                size="sm"
              >
                Fermer
              </Button>
            </div>
          </CardTitle>
          <CardDescription>
            Suivi en temps réel de la création du compte LinkedIn - ID: {accountId}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Progress bar */}
            {(isCreating || progress > 0) && (
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>{currentStep || "En attente..."}</span>
                  <span>{progress}%</span>
                </div>
                <Progress value={progress} className="w-full" />
              </div>
            )}

            {/* Action buttons */}
            <div className="flex items-center space-x-2">
              {!isCreating ? (
                <Button
                  onClick={startCreation}
                  disabled={!isConnected || finalResult?.success}
                  className="bg-green-600 hover:bg-green-700"
                >
                  <Play className="h-4 w-4 mr-2" />
                  Créer le compte LinkedIn
                </Button>
              ) : (
                <Button
                  onClick={stopCreation}
                  variant="destructive"
                >
                  <Square className="h-4 w-4 mr-2" />
                  Arrêter
                </Button>
              )}

              {finalResult?.success && finalResult?.result?.linkedin_url && (
                <Button
                  onClick={() => window.open(finalResult.result.linkedin_url, '_blank')}
                  variant="outline"
                >
                  <ExternalLink className="h-4 w-4 mr-2" />
                  Voir le profil
                </Button>
              )}
              {/* Manual email verification code input */}
              <div className="flex items-center space-x-2 ml-2">
                <input
                  value={manualCode}
                  onChange={(e) => setManualCode(e.target.value)}
                  placeholder="Code email reçu"
                  className="border rounded px-2 py-1 text-sm"
                />
                <Button onClick={submitManualCode} variant="outline" size="sm">Envoyer le code</Button>
              </div>
            </div>

            {/* Status alerts */}
            {error && (
              <Alert>
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  <strong>Erreur:</strong> {error}
                </AlertDescription>
              </Alert>
            )}

            {finalResult?.success && (
              <Alert className="border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-950">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <AlertDescription className="text-green-800 dark:text-green-200">
                  <strong>Succès!</strong> Le compte LinkedIn a été créé avec succès.
                  {finalResult.result?.creation_time && (
                    <span> Temps de création: {Math.round(finalResult.result.creation_time)}s</span>
                  )}
                </AlertDescription>
              </Alert>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Console logs */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Terminal className="h-4 w-4" />
            <span>Console de création</span>
            <Badge variant="outline">{logs.length} entrées</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-96 w-full rounded-md border bg-slate-50 dark:bg-slate-900 p-4 overflow-y-auto">
            <div className="font-mono text-sm space-y-2">
              {logs.length === 0 ? (
                <div className="text-slate-500 text-center py-8">
                  En attente de logs...
                </div>
              ) : (
                logs.map((log) => (
                  <div key={log.id} className="flex items-start space-x-2">
                    <span className="text-slate-500 text-xs whitespace-nowrap">
                      {log.timestamp}
                    </span>
                    {getLogIcon(log.type)}
                    <span className={`flex-1 ${getLogTextColor(log.type)}`}>
                      {log.message}
                    </span>
                  </div>
                ))
              )}
              <div ref={logsEndRef} />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default LinkedInCreationConsole
