import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Button } from '@/components/ui/button.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Progress } from '@/components/ui/progress.jsx'
import { Alert, AlertDescription } from '@/components/ui/alert.jsx'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts'
import { 
  Globe, 
  CheckCircle, 
  AlertTriangle, 
  Clock, 
  Zap, 
  RefreshCw,
  Phone,
  Mail,
  Shield,
  Activity,
  TrendingUp,
  TrendingDown,
  Server,
  Wifi,
  Database
} from 'lucide-react'

const ServiceMonitor = () => {
  const [services, setServices] = useState({
    '5SIM': {
      name: '5SIM SMS Service',
      status: 'healthy',
      responseTime: 245,
      uptime: 99.8,
      lastCheck: new Date(),
      endpoint: 'https://5sim.net/v1',
      description: 'SMS verification service for account creation',
      metrics: {
        requestsToday: 156,
        successRate: 94.2,
        avgResponseTime: 245,
        errorRate: 5.8
      },
      recentActivity: [
        { time: '14:30', action: 'SMS received', status: 'success' },
        { time: '14:25', action: 'Number requested', status: 'success' },
        { time: '14:20', action: 'SMS timeout', status: 'error' },
        { time: '14:15', action: 'SMS received', status: 'success' }
      ]
    },
    'EmailOnDeck': {
      name: 'EmailOnDeck Email Service',
      status: 'healthy',
      responseTime: 189,
      uptime: 99.9,
      lastCheck: new Date(),
      endpoint: 'https://www.emailondeck.com/api',
      description: 'Temporary email service for account verification',
      metrics: {
        requestsToday: 89,
        successRate: 97.8,
        avgResponseTime: 189,
        errorRate: 2.2
      },
      recentActivity: [
        { time: '14:35', action: 'Email received', status: 'success' },
        { time: '14:30', action: 'Mailbox created', status: 'success' },
        { time: '14:25', action: 'Email received', status: 'success' },
        { time: '14:20', action: 'Mailbox created', status: 'success' }
      ]
    },
    'Geonode': {
      name: 'Geonode Proxy Service',
      status: 'warning',
      responseTime: 456,
      uptime: 98.5,
      lastCheck: new Date(),
      endpoint: 'https://premium-residential.geonode.com',
      description: 'Residential proxy network for geographic distribution',
      metrics: {
        requestsToday: 234,
        successRate: 89.3,
        avgResponseTime: 456,
        errorRate: 10.7
      },
      recentActivity: [
        { time: '14:32', action: 'Proxy rotation', status: 'success' },
        { time: '14:28', action: 'Connection timeout', status: 'error' },
        { time: '14:25', action: 'Proxy assigned', status: 'success' },
        { time: '14:22', action: 'IP changed', status: 'success' }
      ]
    },
    'OpenAI': {
      name: 'OpenAI API Service',
      status: 'healthy',
      responseTime: 423,
      uptime: 99.7,
      lastCheck: new Date(),
      endpoint: 'https://api.openai.com/v1',
      description: 'AI content generation and persona creation',
      metrics: {
        requestsToday: 67,
        successRate: 98.5,
        avgResponseTime: 423,
        errorRate: 1.5
      },
      recentActivity: [
        { time: '14:33', action: 'Persona generated', status: 'success' },
        { time: '14:28', action: 'Content created', status: 'success' },
        { time: '14:25', action: 'Rate limit hit', status: 'warning' },
        { time: '14:20', action: 'Profile text generated', status: 'success' }
      ]
    }
  })

  const [responseTimeHistory, setResponseTimeHistory] = useState([
    { time: '14:00', '5SIM': 230, 'EmailOnDeck': 180, 'Geonode': 420, 'OpenAI': 400 },
    { time: '14:05', '5SIM': 245, 'EmailOnDeck': 175, 'Geonode': 445, 'OpenAI': 415 },
    { time: '14:10', '5SIM': 235, 'EmailOnDeck': 190, 'Geonode': 480, 'OpenAI': 430 },
    { time: '14:15', '5SIM': 250, 'EmailOnDeck': 185, 'Geonode': 465, 'OpenAI': 420 },
    { time: '14:20', '5SIM': 240, 'EmailOnDeck': 195, 'Geonode': 470, 'OpenAI': 435 },
    { time: '14:25', '5SIM': 245, 'EmailOnDeck': 189, 'Geonode': 456, 'OpenAI': 423 }
  ])

  const [isRefreshing, setIsRefreshing] = useState(false)

  // Simulate real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      setServices(prev => {
        const updated = { ...prev }
        Object.keys(updated).forEach(serviceName => {
          const service = updated[serviceName]
          // Simulate response time fluctuations
          const baseTime = service.responseTime
          const variation = (Math.random() - 0.5) * 50
          service.responseTime = Math.max(100, Math.floor(baseTime + variation))
          
          // Update last check time
          service.lastCheck = new Date()
          
          // Occasionally change status
          if (Math.random() < 0.05) {
            if (service.status === 'healthy' && Math.random() < 0.3) {
              service.status = 'warning'
            } else if (service.status === 'warning' && Math.random() < 0.7) {
              service.status = 'healthy'
            }
          }
        })
        return updated
      })

      // Update response time history
      setResponseTimeHistory(prev => {
        const newEntry = {
          time: new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' }),
          '5SIM': services['5SIM'].responseTime,
          'EmailOnDeck': services['EmailOnDeck'].responseTime,
          'Geonode': services['Geonode'].responseTime,
          'OpenAI': services['OpenAI'].responseTime
        }
        return [...prev.slice(-5), newEntry]
      })
    }, 5000)

    return () => clearInterval(interval)
  }, [services])

  const refreshServices = async () => {
    setIsRefreshing(true)
    // Simulate API calls to check service status
    await new Promise(resolve => setTimeout(resolve, 2000))
    setIsRefreshing(false)
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
      case 'warning':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
      case 'error':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-600" />
      case 'error':
        return <AlertTriangle className="h-4 w-4 text-red-600" />
      default:
        return <Clock className="h-4 w-4 text-gray-600" />
    }
  }

  const getServiceIcon = (serviceName) => {
    switch (serviceName) {
      case '5SIM':
        return <Phone className="h-5 w-5 text-blue-600" />
      case 'EmailOnDeck':
        return <Mail className="h-5 w-5 text-green-600" />
      case 'Geonode':
        return <Globe className="h-5 w-5 text-orange-600" />
      case 'OpenAI':
        return <Shield className="h-5 w-5 text-purple-600" />
      default:
        return <Server className="h-5 w-5 text-gray-600" />
    }
  }

  const overallHealth = Object.values(services).every(s => s.status === 'healthy')
  const avgResponseTime = Math.round(Object.values(services).reduce((sum, s) => sum + s.responseTime, 0) / Object.keys(services).length)
  const totalRequests = Object.values(services).reduce((sum, s) => sum + s.metrics.requestsToday, 0)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Service Monitor</h2>
          <p className="text-slate-600 dark:text-slate-300">
            Monitor external service health and performance
          </p>
        </div>
        
        <Button 
          onClick={refreshServices}
          disabled={isRefreshing}
          variant="outline"
        >
          {isRefreshing ? (
            <>
              <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
              Refreshing...
            </>
          ) : (
            <>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh All
            </>
          )}
        </Button>
      </div>

      {/* Overall Status */}
      <Alert className={overallHealth ? 'border-green-200 bg-green-50 dark:bg-green-900/20' : 'border-yellow-200 bg-yellow-50 dark:bg-yellow-900/20'}>
        {overallHealth ? (
          <CheckCircle className="h-4 w-4 text-green-600" />
        ) : (
          <AlertTriangle className="h-4 w-4 text-yellow-600" />
        )}
        <AlertDescription>
          {overallHealth 
            ? 'All services are operational and performing within normal parameters.'
            : 'Some services are experiencing issues. Check individual service status below.'
          }
        </AlertDescription>
      </Alert>

      {/* Service Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 border-blue-200 dark:border-blue-800">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-blue-700 dark:text-blue-300">
              Services Online
            </CardTitle>
            <Activity className="h-4 w-4 text-blue-600 dark:text-blue-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-900 dark:text-blue-100">
              {Object.values(services).filter(s => s.status !== 'error').length}/{Object.keys(services).length}
            </div>
            <p className="text-xs text-blue-600 dark:text-blue-400">
              Operational services
            </p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 border-green-200 dark:border-green-800">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-green-700 dark:text-green-300">
              Avg Response Time
            </CardTitle>
            <Zap className="h-4 w-4 text-green-600 dark:text-green-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-900 dark:text-green-100">
              {avgResponseTime}ms
            </div>
            <p className="text-xs text-green-600 dark:text-green-400">
              Across all services
            </p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 border-purple-200 dark:border-purple-800">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-purple-700 dark:text-purple-300">
              Requests Today
            </CardTitle>
            <Database className="h-4 w-4 text-purple-600 dark:text-purple-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-900 dark:text-purple-100">
              {totalRequests}
            </div>
            <p className="text-xs text-purple-600 dark:text-purple-400">
              Total API calls
            </p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-orange-50 to-orange-100 dark:from-orange-900/20 dark:to-orange-800/20 border-orange-200 dark:border-orange-800">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-orange-700 dark:text-orange-300">
              Avg Uptime
            </CardTitle>
            <TrendingUp className="h-4 w-4 text-orange-600 dark:text-orange-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-900 dark:text-orange-100">
              {(Object.values(services).reduce((sum, s) => sum + s.uptime, 0) / Object.keys(services).length).toFixed(1)}%
            </div>
            <p className="text-xs text-orange-600 dark:text-orange-400">
              Last 30 days
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Response Time Chart */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Activity className="h-5 w-5 text-blue-600" />
            <span>Response Time Trends</span>
          </CardTitle>
          <CardDescription>
            Real-time response time monitoring for all services
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={responseTimeHistory}>
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis dataKey="time" className="text-xs" />
              <YAxis className="text-xs" />
              <Tooltip />
              <Line type="monotone" dataKey="5SIM" stroke="#3b82f6" strokeWidth={2} dot={{ r: 3 }} />
              <Line type="monotone" dataKey="EmailOnDeck" stroke="#10b981" strokeWidth={2} dot={{ r: 3 }} />
              <Line type="monotone" dataKey="Geonode" stroke="#f59e0b" strokeWidth={2} dot={{ r: 3 }} />
              <Line type="monotone" dataKey="OpenAI" stroke="#8b5cf6" strokeWidth={2} dot={{ r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Service Details */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {Object.entries(services).map(([serviceName, service]) => (
          <Card key={serviceName}>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  {getServiceIcon(serviceName)}
                  <span>{service.name}</span>
                </div>
                <div className="flex items-center space-x-2">
                  {getStatusIcon(service.status)}
                  <Badge className={getStatusColor(service.status)}>
                    {service.status}
                  </Badge>
                </div>
              </CardTitle>
              <CardDescription>
                {service.description}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Service Metrics */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <div className="text-slate-500">Response Time</div>
                  <div className="font-medium">{service.responseTime}ms</div>
                </div>
                <div>
                  <div className="text-slate-500">Uptime</div>
                  <div className="font-medium">{service.uptime}%</div>
                </div>
                <div>
                  <div className="text-slate-500">Requests Today</div>
                  <div className="font-medium">{service.metrics.requestsToday}</div>
                </div>
                <div>
                  <div className="text-slate-500">Success Rate</div>
                  <div className="font-medium">{service.metrics.successRate}%</div>
                </div>
              </div>

              {/* Performance Bar */}
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Performance</span>
                  <span>{service.metrics.successRate}%</span>
                </div>
                <Progress value={service.metrics.successRate} className="h-2" />
              </div>

              {/* Recent Activity */}
              <div className="space-y-2">
                <div className="text-sm font-medium">Recent Activity</div>
                <div className="space-y-1">
                  {service.recentActivity.slice(0, 3).map((activity, index) => (
                    <div key={index} className="flex items-center justify-between text-xs">
                      <span className="text-slate-600 dark:text-slate-300">
                        {activity.time} - {activity.action}
                      </span>
                      <Badge 
                        variant="outline" 
                        className={
                          activity.status === 'success' ? 'text-green-600 border-green-200' :
                          activity.status === 'warning' ? 'text-yellow-600 border-yellow-200' :
                          'text-red-600 border-red-200'
                        }
                      >
                        {activity.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>

              {/* Service Endpoint */}
              <div className="text-xs text-slate-500 border-t pt-2">
                <div>Endpoint: {service.endpoint}</div>
                <div>Last checked: {service.lastCheck.toLocaleTimeString()}</div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Service Usage Chart */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <BarChart className="h-5 w-5 text-purple-600" />
            <span>Daily Request Volume</span>
          </CardTitle>
          <CardDescription>
            API request distribution across services today
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={Object.entries(services).map(([name, service]) => ({
              name,
              requests: service.metrics.requestsToday,
              successRate: service.metrics.successRate
            }))}>
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis dataKey="name" className="text-xs" />
              <YAxis className="text-xs" />
              <Tooltip />
              <Bar dataKey="requests" fill="#3b82f6" name="Requests" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  )
}

export default ServiceMonitor

