App.jsx
import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Progress } from '@/components/ui/progress.jsx'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert.jsx'
import { 
  Users, 
  Bot, 
  Brain, 
  Activity, 
  Settings, 
  Plus, 
  Play, 
  Pause, 
  AlertTriangle,
  CheckCircle,
  Clock,
  TrendingUp,
  Globe,
  Shield,
  Zap
} from 'lucide-react'
import './App.css'

// Import dashboard components
import Dashboard from './components/Dashboard'
import AccountManager from './components/AccountManager'
import PersonaGenerator from './components/PersonaGenerator'
import AutomationControl from './components/AutomationControl'
import ServiceMonitor from './components/ServiceMonitor'
import SettingsPanel from './components/SettingsPanel'

function App() {
  const [activeTab, setActiveTab] = useState('dashboard')
  const [systemStatus, setSystemStatus] = useState({
    services: {
      '5SIM': { healthy: true, response_time: 245 },
      'EmailOnDeck': { healthy: true, response_time: 189 },
      'Geonode': { healthy: true, response_time: 156 },
      'OpenAI': { healthy: true, response_time: 423 }
    },
    accounts: {
      total: 12,
      active: 8,
      pending: 3,
      suspended: 1
    },
    automation: {
      running_jobs: 2,
      completed_today: 15,
      success_rate: 94.2
    }
  })

  const [realTimeData, setRealTimeData] = useState({
    activeConnections: 0,
    messagesProcessed: 0,
    lastUpdate: new Date()
  })

  // Simulate real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      setRealTimeData(prev => ({
        activeConnections: Math.floor(Math.random() * 10) + 5,
        messagesProcessed: prev.messagesProcessed + Math.floor(Math.random() * 3),
        lastUpdate: new Date()
      }))
    }, 5000)

    return () => clearInterval(interval)
  }, [])

  const navigationItems = [
    { id: 'dashboard', label: 'Dashboard', icon: Activity },
    { id: 'accounts', label: 'Accounts', icon: Users },
    { id: 'personas', label: 'AI Personas', icon: Brain },
    { id: 'automation', label: 'Automation', icon: Bot },
    { id: 'services', label: 'Services', icon: Globe },
    { id: 'settings', label: 'Settings', icon: Settings }
  ]

  const getStatusColor = (healthy) => healthy ? 'text-green-500' : 'text-red-500'
  const getStatusIcon = (healthy) => healthy ? CheckCircle : AlertTriangle

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      {/* Header */}
      <header className="bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <Shield className="h-8 w-8 text-blue-600" />
                <h1 className="text-xl font-bold text-slate-900 dark:text-white">
                  LinkedIn Research Framework
                </h1>
              </div>
              <Badge variant="secondary" className="bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                Enterprise Research Platform
              </Badge>
            </div>
            
            <div className="flex items-center space-x-4">
              {/* Real-time status indicators */}
              <div className="flex items-center space-x-2 text-sm text-slate-600 dark:text-slate-300">
                <div className="flex items-center space-x-1">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                  <span>{realTimeData.activeConnections} active</span>
                </div>
                <div className="flex items-center space-x-1">
                  <Zap className="h-4 w-4" />
                  <span>{realTimeData.messagesProcessed} processed</span>
                </div>
              </div>
              
              {/* System health indicator */}
              <div className="flex items-center space-x-2">
                {Object.values(systemStatus.services).every(s => s.healthy) ? (
                  <Badge variant="default" className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                    <CheckCircle className="h-3 w-3 mr-1" />
                    All Systems Operational
                  </Badge>
                ) : (
                  <Badge variant="destructive">
                    <AlertTriangle className="h-3 w-3 mr-1" />
                    Service Issues Detected
                  </Badge>
                )}
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          {/* Navigation Tabs */}
          <TabsList className="grid w-full grid-cols-6 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
            {navigationItems.map((item) => {
              const Icon = item.icon
              return (
                <TabsTrigger 
                  key={item.id} 
                  value={item.id}
                  className="flex items-center space-x-2 data-[state=active]:bg-blue-50 data-[state=active]:text-blue-700 dark:data-[state=active]:bg-blue-900 dark:data-[state=active]:text-blue-200"
                >
                  <Icon className="h-4 w-4" />
                  <span className="hidden sm:inline">{item.label}</span>
                </TabsTrigger>
              )
            })}
          </TabsList>

          {/* Dashboard Overview */}
          <TabsContent value="dashboard" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {/* Accounts Overview */}
              <Card className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 border-blue-200 dark:border-blue-800">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-blue-700 dark:text-blue-300">
                    LinkedIn Accounts
                  </CardTitle>
                  <Users className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-blue-900 dark:text-blue-100">
                    {systemStatus.accounts.total}
                  </div>
                  <p className="text-xs text-blue-600 dark:text-blue-400">
                    {systemStatus.accounts.active} active, {systemStatus.accounts.pending} pending
                  </p>
                  <div className="mt-2">
                    <Progress 
                      value={(systemStatus.accounts.active / systemStatus.accounts.total) * 100} 
                      className="h-2"
                    />
                  </div>
                </CardContent>
              </Card>

              {/* Automation Status */}
              <Card className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 border-green-200 dark:border-green-800">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-green-700 dark:text-green-300">
                    Automation Jobs
                  </CardTitle>
                  <Bot className="h-4 w-4 text-green-600 dark:text-green-400" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-green-900 dark:text-green-100">
                    {systemStatus.automation.running_jobs}
                  </div>
                  <p className="text-xs text-green-600 dark:text-green-400">
                    {systemStatus.automation.completed_today} completed today
                  </p>
                  <div className="mt-2 flex items-center space-x-2">
                    <TrendingUp className="h-3 w-3 text-green-600" />
                    <span className="text-xs text-green-600 dark:text-green-400">
                      {systemStatus.automation.success_rate}% success rate
                    </span>
                  </div>
                </CardContent>
              </Card>

              {/* AI Content Generation */}
              <Card className="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 border-purple-200 dark:border-purple-800">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-purple-700 dark:text-purple-300">
                    AI Personas
                  </CardTitle>
                  <Brain className="h-4 w-4 text-purple-600 dark:text-purple-400" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-purple-900 dark:text-purple-100">
                    24
                  </div>
                  <p className="text-xs text-purple-600 dark:text-purple-400">
                    Generated this week
                  </p>
                  <div className="mt-2">
                    <Badge variant="secondary" className="bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200">
                      OpenAI Connected
                    </Badge>
                  </div>
                </CardContent>
              </Card>

              {/* Service Health */}
              <Card className="bg-gradient-to-br from-orange-50 to-orange-100 dark:from-orange-900/20 dark:to-orange-800/20 border-orange-200 dark:border-orange-800">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-orange-700 dark:text-orange-300">
                    Service Health
                  </CardTitle>
                  <Activity className="h-4 w-4 text-orange-600 dark:text-orange-400" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-orange-900 dark:text-orange-100">
                    {Object.values(systemStatus.services).filter(s => s.healthy).length}/4
                  </div>
                  <p className="text-xs text-orange-600 dark:text-orange-400">
                    Services operational
                  </p>
                  <div className="mt-2 space-y-1">
                    {Object.entries(systemStatus.services).map(([name, status]) => {
                      const StatusIcon = getStatusIcon(status.healthy)
                      return (
                        <div key={name} className="flex items-center justify-between text-xs">
                          <span className="text-orange-700 dark:text-orange-300">{name}</span>
                          <StatusIcon className={`h-3 w-3 ${getStatusColor(status.healthy)}`} />
                        </div>
                      )
                    })}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Recent Activity */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Clock className="h-5 w-5" />
                  <span>Recent Activity</span>
                </CardTitle>
                <CardDescription>
                  Latest automation and system events
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center space-x-4 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
                    <CheckCircle className="h-5 w-5 text-green-600" />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-green-900 dark:text-green-100">
                        LinkedIn account created successfully
                      </p>
                      <p className="text-xs text-green-600 dark:text-green-400">
                        Account: marie.dubois@emailondeck.com • 2 minutes ago
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                    <Brain className="h-5 w-5 text-blue-600" />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-blue-900 dark:text-blue-100">
                        AI persona generated
                      </p>
                      <p className="text-xs text-blue-600 dark:text-blue-400">
                        Technology sector, Senior level • 5 minutes ago
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-4 p-3 bg-orange-50 dark:bg-orange-900/20 rounded-lg border border-orange-200 dark:border-orange-800">
                    <AlertTriangle className="h-5 w-5 text-orange-600" />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-orange-900 dark:text-orange-100">
                        SMS verification timeout
                      </p>
                      <p className="text-xs text-orange-600 dark:text-orange-400">
                        Account: test.user@example.com • 8 minutes ago
                      </p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Account Management */}
          <TabsContent value="accounts">
            <AccountManager />
          </TabsContent>

          {/* AI Persona Generator */}
          <TabsContent value="personas">
            <PersonaGenerator />
          </TabsContent>

          {/* Automation Control */}
          <TabsContent value="automation">
            <AutomationControl />
          </TabsContent>

          {/* Service Monitor */}
          <TabsContent value="services">
            <ServiceMonitor />
          </TabsContent>

          {/* Settings */}
          <TabsContent value="settings">
            <SettingsPanel />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}

export default App