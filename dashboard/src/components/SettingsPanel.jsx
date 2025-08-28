import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Button } from '@/components/ui/button.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Label } from '@/components/ui/label.jsx'
import { Textarea } from '@/components/ui/textarea.jsx'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select.jsx'
import { Switch } from '@/components/ui/switch.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
import { Alert, AlertDescription } from '@/components/ui/alert.jsx'
import { 
  Settings, 
  Key, 
  Shield, 
  Bell, 
  Globe, 
  Database, 
  Save,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  Eye,
  EyeOff,
  Download,
  Upload,
  Trash2
} from 'lucide-react'

const SettingsPanel = () => {
  const [settings, setSettings] = useState({
    apiKeys: {
      openai: 'sk-proj-***************************',
      fivesim: '***************************',
      emailondeck: '***************************',
      geonode: '***************************'
    },
    automation: {
      maxConcurrentJobs: 5,
      defaultDelay: 300,
      retryAttempts: 3,
      enableSafetyLimits: true,
      humanLikeTiming: true,
      proxyRotation: true
    },
    notifications: {
      emailAlerts: true,
      jobCompletion: true,
      serviceErrors: true,
      dailyReports: false,
      webhookUrl: ''
    },
    security: {
      sessionTimeout: 60,
      enableTwoFactor: false,
      ipWhitelist: '',
      encryptData: true,
      auditLogging: true
    },
    general: {
      timezone: 'Europe/Paris',
      language: 'en',
      theme: 'system',
      autoSave: true,
      debugMode: false
    }
  })

  const [showApiKeys, setShowApiKeys] = useState({
    openai: false,
    fivesim: false,
    emailondeck: false,
    geonode: false
  })

  const [isSaving, setIsSaving] = useState(false)
  const [saveStatus, setSaveStatus] = useState(null)

  const handleSettingChange = (category, key, value) => {
    setSettings(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [key]: value
      }
    }))
  }

  const toggleApiKeyVisibility = (service) => {
    setShowApiKeys(prev => ({
      ...prev,
      [service]: !prev[service]
    }))
  }

  const saveSettings = async () => {
    setIsSaving(true)
    try {
      // Simulate API call to save settings
      await new Promise(resolve => setTimeout(resolve, 1500))
      setSaveStatus('success')
      setTimeout(() => setSaveStatus(null), 3000)
    } catch (error) {
      setSaveStatus('error')
      setTimeout(() => setSaveStatus(null), 3000)
    } finally {
      setIsSaving(false)
    }
  }

  const exportSettings = () => {
    const dataStr = JSON.stringify(settings, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = 'linkedin-research-settings.json'
    link.click()
  }

  const importSettings = (event) => {
    const file = event.target.files[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (e) => {
        try {
          const importedSettings = JSON.parse(e.target.result)
          setSettings(importedSettings)
          setSaveStatus('imported')
          setTimeout(() => setSaveStatus(null), 3000)
        } catch (error) {
          setSaveStatus('error')
          setTimeout(() => setSaveStatus(null), 3000)
        }
      }
      reader.readAsText(file)
    }
  }

  const resetSettings = () => {
    if (confirm('Are you sure you want to reset all settings to default values?')) {
      // Reset to default settings
      setSettings({
        apiKeys: {
          openai: '',
          fivesim: '',
          emailondeck: '',
          geonode: ''
        },
        automation: {
          maxConcurrentJobs: 3,
          defaultDelay: 300,
          retryAttempts: 3,
          enableSafetyLimits: true,
          humanLikeTiming: true,
          proxyRotation: true
        },
        notifications: {
          emailAlerts: true,
          jobCompletion: true,
          serviceErrors: true,
          dailyReports: false,
          webhookUrl: ''
        },
        security: {
          sessionTimeout: 60,
          enableTwoFactor: false,
          ipWhitelist: '',
          encryptData: true,
          auditLogging: true
        },
        general: {
          timezone: 'Europe/Paris',
          language: 'en',
          theme: 'system',
          autoSave: true,
          debugMode: false
        }
      })
      setSaveStatus('reset')
      setTimeout(() => setSaveStatus(null), 3000)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Settings</h2>
          <p className="text-slate-600 dark:text-slate-300">
            Configure system settings and preferences
          </p>
        </div>
        
        <div className="flex space-x-2">
          <Button variant="outline" onClick={exportSettings}>
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
          <label>
            <Button variant="outline" asChild>
              <span>
                <Upload className="h-4 w-4 mr-2" />
                Import
              </span>
            </Button>
            <input
              type="file"
              accept=".json"
              onChange={importSettings}
              className="hidden"
            />
          </label>
          <Button 
            onClick={saveSettings}
            disabled={isSaving}
            className="bg-blue-600 hover:bg-blue-700"
          >
            {isSaving ? (
              <>
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="h-4 w-4 mr-2" />
                Save Settings
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Save Status */}
      {saveStatus && (
        <Alert className={
          saveStatus === 'success' || saveStatus === 'imported' || saveStatus === 'reset' 
            ? 'border-green-200 bg-green-50 dark:bg-green-900/20' 
            : 'border-red-200 bg-red-50 dark:bg-red-900/20'
        }>
          {saveStatus === 'success' || saveStatus === 'imported' || saveStatus === 'reset' ? (
            <CheckCircle className="h-4 w-4 text-green-600" />
          ) : (
            <AlertTriangle className="h-4 w-4 text-red-600" />
          )}
          <AlertDescription>
            {saveStatus === 'success' && 'Settings saved successfully!'}
            {saveStatus === 'imported' && 'Settings imported successfully!'}
            {saveStatus === 'reset' && 'Settings reset to default values!'}
            {saveStatus === 'error' && 'Failed to save settings. Please try again.'}
          </AlertDescription>
        </Alert>
      )}

      {/* Settings Tabs */}
      <Tabs defaultValue="api" className="space-y-4">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="api">API Keys</TabsTrigger>
          <TabsTrigger value="automation">Automation</TabsTrigger>
          <TabsTrigger value="notifications">Notifications</TabsTrigger>
          <TabsTrigger value="security">Security</TabsTrigger>
          <TabsTrigger value="general">General</TabsTrigger>
        </TabsList>

        {/* API Keys Tab */}
        <TabsContent value="api" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Key className="h-5 w-5 text-blue-600" />
                <span>API Configuration</span>
              </CardTitle>
              <CardDescription>
                Configure API keys for external services
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* OpenAI API Key */}
              <div className="space-y-2">
                <Label htmlFor="openai-key">OpenAI API Key</Label>
                <div className="flex space-x-2">
                  <Input
                    id="openai-key"
                    type={showApiKeys.openai ? 'text' : 'password'}
                    value={settings.apiKeys.openai}
                    onChange={(e) => handleSettingChange('apiKeys', 'openai', e.target.value)}
                    placeholder="sk-proj-..."
                    className="flex-1"
                  />
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => toggleApiKeyVisibility('openai')}
                  >
                    {showApiKeys.openai ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </Button>
                </div>
                <p className="text-xs text-slate-500">
                  Used for AI content generation and persona creation
                </p>
              </div>

              {/* 5SIM API Key */}
              <div className="space-y-2">
                <Label htmlFor="fivesim-key">5SIM API Key</Label>
                <div className="flex space-x-2">
                  <Input
                    id="fivesim-key"
                    type={showApiKeys.fivesim ? 'text' : 'password'}
                    value={settings.apiKeys.fivesim}
                    onChange={(e) => handleSettingChange('apiKeys', 'fivesim', e.target.value)}
                    placeholder="Enter 5SIM API key"
                    className="flex-1"
                  />
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => toggleApiKeyVisibility('fivesim')}
                  >
                    {showApiKeys.fivesim ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </Button>
                </div>
                <p className="text-xs text-slate-500">
                  SMS verification service for account creation
                </p>
              </div>

              {/* EmailOnDeck API Key */}
              <div className="space-y-2">
                <Label htmlFor="emailondeck-key">EmailOnDeck API Key</Label>
                <div className="flex space-x-2">
                  <Input
                    id="emailondeck-key"
                    type={showApiKeys.emailondeck ? 'text' : 'password'}
                    value={settings.apiKeys.emailondeck}
                    onChange={(e) => handleSettingChange('apiKeys', 'emailondeck', e.target.value)}
                    placeholder="Enter EmailOnDeck API key"
                    className="flex-1"
                  />
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => toggleApiKeyVisibility('emailondeck')}
                  >
                    {showApiKeys.emailondeck ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </Button>
                </div>
                <p className="text-xs text-slate-500">
                  Temporary email service for account verification
                </p>
              </div>

              {/* Geonode API Key */}
              <div className="space-y-2">
                <Label htmlFor="geonode-key">Geonode Proxy Credentials</Label>
                <div className="flex space-x-2">
                  <Input
                    id="geonode-key"
                    type={showApiKeys.geonode ? 'text' : 'password'}
                    value={settings.apiKeys.geonode}
                    onChange={(e) => handleSettingChange('apiKeys', 'geonode', e.target.value)}
                    placeholder="username:password@endpoint:port"
                    className="flex-1"
                  />
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => toggleApiKeyVisibility('geonode')}
                  >
                    {showApiKeys.geonode ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </Button>
                </div>
                <p className="text-xs text-slate-500">
                  Residential proxy network for geographic distribution
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Automation Tab */}
        <TabsContent value="automation" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Settings className="h-5 w-5 text-green-600" />
                <span>Automation Settings</span>
              </CardTitle>
              <CardDescription>
                Configure automation behavior and safety limits
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label htmlFor="max-jobs">Max Concurrent Jobs</Label>
                  <Input
                    id="max-jobs"
                    type="number"
                    value={settings.automation.maxConcurrentJobs}
                    onChange={(e) => handleSettingChange('automation', 'maxConcurrentJobs', parseInt(e.target.value))}
                    min="1"
                    max="10"
                  />
                  <p className="text-xs text-slate-500">
                    Maximum number of automation jobs running simultaneously
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="default-delay">Default Delay (seconds)</Label>
                  <Input
                    id="default-delay"
                    type="number"
                    value={settings.automation.defaultDelay}
                    onChange={(e) => handleSettingChange('automation', 'defaultDelay', parseInt(e.target.value))}
                    min="60"
                    max="3600"
                  />
                  <p className="text-xs text-slate-500">
                    Default delay between automation actions
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="retry-attempts">Retry Attempts</Label>
                  <Input
                    id="retry-attempts"
                    type="number"
                    value={settings.automation.retryAttempts}
                    onChange={(e) => handleSettingChange('automation', 'retryAttempts', parseInt(e.target.value))}
                    min="1"
                    max="5"
                  />
                  <p className="text-xs text-slate-500">
                    Number of retry attempts for failed actions
                  </p>
                </div>
              </div>

              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Enable Safety Limits</Label>
                    <p className="text-xs text-slate-500">
                      Enforce daily and hourly action limits to prevent detection
                    </p>
                  </div>
                  <Switch
                    checked={settings.automation.enableSafetyLimits}
                    onCheckedChange={(checked) => handleSettingChange('automation', 'enableSafetyLimits', checked)}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Human-like Timing</Label>
                    <p className="text-xs text-slate-500">
                      Add random delays to mimic human behavior
                    </p>
                  </div>
                  <Switch
                    checked={settings.automation.humanLikeTiming}
                    onCheckedChange={(checked) => handleSettingChange('automation', 'humanLikeTiming', checked)}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Proxy Rotation</Label>
                    <p className="text-xs text-slate-500">
                      Automatically rotate proxies to avoid IP blocking
                    </p>
                  </div>
                  <Switch
                    checked={settings.automation.proxyRotation}
                    onCheckedChange={(checked) => handleSettingChange('automation', 'proxyRotation', checked)}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Notifications Tab */}
        <TabsContent value="notifications" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Bell className="h-5 w-5 text-yellow-600" />
                <span>Notification Settings</span>
              </CardTitle>
              <CardDescription>
                Configure alerts and notifications
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Email Alerts</Label>
                    <p className="text-xs text-slate-500">
                      Receive email notifications for important events
                    </p>
                  </div>
                  <Switch
                    checked={settings.notifications.emailAlerts}
                    onCheckedChange={(checked) => handleSettingChange('notifications', 'emailAlerts', checked)}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Job Completion</Label>
                    <p className="text-xs text-slate-500">
                      Notify when automation jobs complete
                    </p>
                  </div>
                  <Switch
                    checked={settings.notifications.jobCompletion}
                    onCheckedChange={(checked) => handleSettingChange('notifications', 'jobCompletion', checked)}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Service Errors</Label>
                    <p className="text-xs text-slate-500">
                      Alert when external services experience issues
                    </p>
                  </div>
                  <Switch
                    checked={settings.notifications.serviceErrors}
                    onCheckedChange={(checked) => handleSettingChange('notifications', 'serviceErrors', checked)}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Daily Reports</Label>
                    <p className="text-xs text-slate-500">
                      Receive daily summary reports
                    </p>
                  </div>
                  <Switch
                    checked={settings.notifications.dailyReports}
                    onCheckedChange={(checked) => handleSettingChange('notifications', 'dailyReports', checked)}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="webhook-url">Webhook URL (Optional)</Label>
                <Input
                  id="webhook-url"
                  value={settings.notifications.webhookUrl}
                  onChange={(e) => handleSettingChange('notifications', 'webhookUrl', e.target.value)}
                  placeholder="https://your-webhook-endpoint.com"
                />
                <p className="text-xs text-slate-500">
                  Send notifications to a custom webhook endpoint
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Security Tab */}
        <TabsContent value="security" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Shield className="h-5 w-5 text-red-600" />
                <span>Security Settings</span>
              </CardTitle>
              <CardDescription>
                Configure security and access controls
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label htmlFor="session-timeout">Session Timeout (minutes)</Label>
                  <Input
                    id="session-timeout"
                    type="number"
                    value={settings.security.sessionTimeout}
                    onChange={(e) => handleSettingChange('security', 'sessionTimeout', parseInt(e.target.value))}
                    min="15"
                    max="480"
                  />
                  <p className="text-xs text-slate-500">
                    Automatic logout after inactivity
                  </p>
                </div>
              </div>

              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Two-Factor Authentication</Label>
                    <p className="text-xs text-slate-500">
                      Enable 2FA for additional security
                    </p>
                  </div>
                  <Switch
                    checked={settings.security.enableTwoFactor}
                    onCheckedChange={(checked) => handleSettingChange('security', 'enableTwoFactor', checked)}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Data Encryption</Label>
                    <p className="text-xs text-slate-500">
                      Encrypt sensitive data at rest
                    </p>
                  </div>
                  <Switch
                    checked={settings.security.encryptData}
                    onCheckedChange={(checked) => handleSettingChange('security', 'encryptData', checked)}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Audit Logging</Label>
                    <p className="text-xs text-slate-500">
                      Log all user actions for security auditing
                    </p>
                  </div>
                  <Switch
                    checked={settings.security.auditLogging}
                    onCheckedChange={(checked) => handleSettingChange('security', 'auditLogging', checked)}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="ip-whitelist">IP Whitelist (Optional)</Label>
                <Textarea
                  id="ip-whitelist"
                  value={settings.security.ipWhitelist}
                  onChange={(e) => handleSettingChange('security', 'ipWhitelist', e.target.value)}
                  placeholder="192.168.1.1&#10;10.0.0.0/8"
                  rows={3}
                />
                <p className="text-xs text-slate-500">
                  Restrict access to specific IP addresses (one per line)
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* General Tab */}
        <TabsContent value="general" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Globe className="h-5 w-5 text-purple-600" />
                <span>General Settings</span>
              </CardTitle>
              <CardDescription>
                Configure general application preferences
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label htmlFor="timezone">Timezone</Label>
                  <Select value={settings.general.timezone} onValueChange={(value) => handleSettingChange('general', 'timezone', value)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Europe/Paris">Europe/Paris</SelectItem>
                      <SelectItem value="Europe/London">Europe/London</SelectItem>
                      <SelectItem value="America/New_York">America/New_York</SelectItem>
                      <SelectItem value="America/Los_Angeles">America/Los_Angeles</SelectItem>
                      <SelectItem value="Asia/Tokyo">Asia/Tokyo</SelectItem>
                      <SelectItem value="UTC">UTC</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="language">Language</Label>
                  <Select value={settings.general.language} onValueChange={(value) => handleSettingChange('general', 'language', value)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="en">English</SelectItem>
                      <SelectItem value="fr">Français</SelectItem>
                      <SelectItem value="es">Español</SelectItem>
                      <SelectItem value="de">Deutsch</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="theme">Theme</Label>
                  <Select value={settings.general.theme} onValueChange={(value) => handleSettingChange('general', 'theme', value)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="system">System</SelectItem>
                      <SelectItem value="light">Light</SelectItem>
                      <SelectItem value="dark">Dark</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Auto-save</Label>
                    <p className="text-xs text-slate-500">
                      Automatically save changes as you work
                    </p>
                  </div>
                  <Switch
                    checked={settings.general.autoSave}
                    onCheckedChange={(checked) => handleSettingChange('general', 'autoSave', checked)}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Debug Mode</Label>
                    <p className="text-xs text-slate-500">
                      Enable detailed logging for troubleshooting
                    </p>
                  </div>
                  <Switch
                    checked={settings.general.debugMode}
                    onCheckedChange={(checked) => handleSettingChange('general', 'debugMode', checked)}
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Danger Zone */}
          <Card className="border-red-200 dark:border-red-800">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2 text-red-700 dark:text-red-300">
                <AlertTriangle className="h-5 w-5" />
                <span>Danger Zone</span>
              </CardTitle>
              <CardDescription>
                Irreversible actions that affect your entire configuration
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex justify-between items-center p-4 border border-red-200 dark:border-red-800 rounded-lg">
                <div>
                  <h4 className="font-medium text-red-900 dark:text-red-100">Reset All Settings</h4>
                  <p className="text-sm text-red-600 dark:text-red-400">
                    This will reset all settings to their default values. This action cannot be undone.
                  </p>
                </div>
                <Button variant="destructive" onClick={resetSettings}>
                  <Trash2 className="h-4 w-4 mr-2" />
                  Reset Settings
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default SettingsPanel

