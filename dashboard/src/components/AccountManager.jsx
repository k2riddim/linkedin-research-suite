import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Button } from '@/components/ui/button.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Label } from '@/components/ui/label.jsx'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select.jsx'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table.jsx'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog.jsx'
import { Alert, AlertDescription } from '@/components/ui/alert.jsx'
import LinkedInCreationConsole from './LinkedInCreationConsole.jsx'
import { 
  Plus, 
  Users, 
  Eye, 
  Edit, 
  Trash2, 
  Play, 
  Pause, 
  CheckCircle, 
  AlertTriangle, 
  Clock,
  Mail,
  Phone,
  Globe,
  Shield
} from 'lucide-react'

const AccountManager = () => {
  const [accounts, setAccounts] = useState([])
  const [personas, setPersonas] = useState([])
  const [loading, setLoading] = useState(true)

  const [selectedAccount, setSelectedAccount] = useState(null)
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [filterStatus, setFilterStatus] = useState('all')
  const [searchTerm, setSearchTerm] = useState('')
  const [consoleAccountId, setConsoleAccountId] = useState(null)
  const [isConsoleOpen, setIsConsoleOpen] = useState(false)

  const [newAccount, setNewAccount] = useState({
    persona_id: '',
    email_service: 'emailondeck',
    proxy_service: 'geonode',
    verification_method: 'email',
    profile_completion_level: 'full'
  })

  // Load data on component mount
  useEffect(() => {
    loadAccounts()
    loadPersonas()
  }, [])

  const loadAccounts = async () => {
    try {
      setLoading(true)
      const response = await fetch('/api/accounts')
      const data = await response.json()
      
      if (response.ok) {
        // Transform API data to match frontend format
        const transformedAccounts = data.map(account => ({
          id: account.id,
          email: account.email,
          name: `${account.first_name} ${account.last_name}`,
          status: transformStatus(account.status),
          created: new Date(account.created_at).toLocaleDateString(),
          lastActivity: account.updated_at ? new Date(account.updated_at).toLocaleString() : 'Never',
          profileUrl: account.linkedin_url,
          industry: account.profile_data?.industry || 'Unknown',
          connections: account.profile_data?.connections || 0,
          posts: account.profile_data?.posts || 0,
          proxy: account.profile_data?.creation_settings?.proxy_service || 'Unknown',
          riskLevel: calculateRiskLevel(account),
          persona_id: account.persona_id
        }))
        
        setAccounts(transformedAccounts)
      }
    } catch (error) {
      console.error('Error loading accounts:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadPersonas = async () => {
    try {
      const response = await fetch('/api/ai/personas')
      const data = await response.json()
      
      if (response.ok) {
        setPersonas(data.personas || [])
      }
    } catch (error) {
      console.error('Error loading personas:', error)
    }
  }

  const transformStatus = (apiStatus) => {
    const statusMap = {
      'new': 'pending',
      'creating_linkedin': 'creating',
      'verifying_email': 'creating',
      'verifying_sms': 'creating',
      'completed': 'active',
      'failed': 'suspended'
    }
    return statusMap[apiStatus] || 'pending'
  }

  const calculateRiskLevel = (account) => {
    if (account.status === 'failed') return 'high'
    if (account.status === 'completed' && account.linkedin_created) return 'low'
    return 'medium'
  }

  const createAccountFromPersona = async () => {
    try {
      setLoading(true)
      
      if (!newAccount.persona_id) {
        alert('Please select a persona')
        return
      }

      const response = await fetch('/api/accounts/create-from-persona', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newAccount)
      })

      const data = await response.json()

      if (response.ok) {
        // Refresh accounts list
        await loadAccounts()
        setIsCreateDialogOpen(false)
        setNewAccount({
          persona_id: '',
          email_service: 'emailondeck',
          proxy_service: 'geonode',
          verification_method: 'email',
          profile_completion_level: 'full'
        })
        
        // Immediately start LinkedIn creation with console
        const newAccountId = data.id
        setConsoleAccountId(newAccountId)
        setIsConsoleOpen(true)
      } else {
        alert(`Error: ${data.error}`)
      }
    } catch (error) {
      console.error('Error creating account:', error)
      alert('Failed to create account')
    } finally {
      setLoading(false)
    }
  }

  const startLinkedInCreation = (accountId) => {
    // Open the console for real-time tracking
    setConsoleAccountId(accountId)
    setIsConsoleOpen(true)
  }

  const handleConsoleComplete = async (result) => {
    // Refresh accounts list when creation completes
    await loadAccounts()
  }

  const handleConsoleClose = () => {
    setIsConsoleOpen(false)
    setConsoleAccountId(null)
  }

  const deleteAccount = async (accountId) => {
    if (!confirm('Are you sure you want to delete this account?')) {
      return
    }

    try {
      const response = await fetch(`/api/accounts/${accountId}`, {
        method: 'DELETE'
      })

      if (response.ok) {
        await loadAccounts()
        alert('Account deleted successfully!')
      } else {
        const data = await response.json()
        alert(`Error: ${data.error}`)
      }
    } catch (error) {
      console.error('Error deleting account:', error)
      alert('Failed to delete account')
    }
  }

  const statusColors = {
    active: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
    pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
    suspended: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
    creating: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
  }

  const riskColors = {
    low: 'text-green-600',
    medium: 'text-yellow-600',
    high: 'text-red-600'
  }

  const filteredAccounts = accounts.filter(account => {
    const matchesStatus = filterStatus === 'all' || account.status === filterStatus
    const matchesSearch = account.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         account.email.toLowerCase().includes(searchTerm.toLowerCase())
    return matchesStatus && matchesSearch
  })

  const handleCreateAccount = async () => {
    try {
      // Simulate account creation process
      const accountId = `acc_${Date.now()}`
      const newAccountData = {
        id: accountId,
        email: `${newAccount.firstName.toLowerCase()}.${newAccount.lastName.toLowerCase()}@emailondeck.com`,
        name: `${newAccount.firstName} ${newAccount.lastName}`,
        status: 'creating',
        created: new Date().toISOString().split('T')[0],
        lastActivity: new Date().toISOString(),
        profileUrl: null,
        industry: newAccount.industry,
        connections: 0,
        posts: 0,
        proxy: 'FR-Paris-004',
        riskLevel: 'low'
      }

      setAccounts(prev => [...prev, newAccountData])
      setIsCreateDialogOpen(false)
      setNewAccount({
        firstName: '',
        lastName: '',
        industry: '',
        experienceLevel: '',
        location: 'Paris, France'
      })

      // Simulate status updates
      setTimeout(() => {
        setAccounts(prev => prev.map(acc => 
          acc.id === accountId ? { ...acc, status: 'pending' } : acc
        ))
      }, 3000)

      setTimeout(() => {
        setAccounts(prev => prev.map(acc => 
          acc.id === accountId ? { 
            ...acc, 
            status: 'active',
            profileUrl: `https://linkedin.com/in/${newAccount.firstName.toLowerCase()}-${newAccount.lastName.toLowerCase()}-${newAccount.industry.toLowerCase()}`
          } : acc
        ))
      }, 8000)

    } catch (error) {
      console.error('Error creating account:', error)
    }
  }

  const handleAccountAction = (accountId, action) => {
    setAccounts(prev => prev.map(acc => {
      if (acc.id === accountId) {
        switch (action) {
          case 'pause':
            return { ...acc, status: 'suspended' }
          case 'resume':
            return { ...acc, status: 'active' }
          case 'delete':
            return null
          default:
            return acc
        }
      }
      return acc
    }).filter(Boolean))
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case 'pending':
        return <Clock className="h-4 w-4 text-yellow-600" />
      case 'suspended':
        return <AlertTriangle className="h-4 w-4 text-red-600" />
      case 'creating':
        return <Clock className="h-4 w-4 text-blue-600 animate-spin" />
      default:
        return null
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Account Management</h2>
          <p className="text-slate-600 dark:text-slate-300">
            Manage LinkedIn research accounts and automation
          </p>
        </div>
        
        <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button className="bg-blue-600 hover:bg-blue-700">
              <Plus className="h-4 w-4 mr-2" />
              Create Account
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle>Create New LinkedIn Account</DialogTitle>
              <DialogDescription>
                Generate a new LinkedIn account with AI-powered persona
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="persona">Select AI Persona</Label>
                <Select value={newAccount.persona_id} onValueChange={(value) => setNewAccount(prev => ({ ...prev, persona_id: value }))}>
                  <SelectTrigger>
                    <SelectValue placeholder="Choose a generated persona" />
                  </SelectTrigger>
                  <SelectContent>
                    {personas.map((persona) => (
                      <SelectItem key={persona.persona_id} value={persona.persona_id}>
                        {persona.demographic_data.first_name} {persona.demographic_data.last_name} 
                        - {persona.professional_data.current_position} ({persona.professional_data.industry})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {personas.length === 0 && (
                  <p className="text-sm text-slate-500">No personas available. Generate personas first in the AI Persona Generator.</p>
                )}
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="emailService">Email Service</Label>
                  <Select value={newAccount.email_service} onValueChange={(value) => setNewAccount(prev => ({ ...prev, email_service: value }))}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="emailondeck">EmailOnDeck</SelectItem>
                      <SelectItem value="fivesim">5SIM</SelectItem>
                      <SelectItem value="manual">Manual</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="proxyService">Proxy Service</Label>
                  <Select value={newAccount.proxy_service} onValueChange={(value) => setNewAccount(prev => ({ ...prev, proxy_service: value }))}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="geonode">GeoNode</SelectItem>
                      <SelectItem value="manual">Manual</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="verificationMethod">Verification Method</Label>
                <Select value={newAccount.verification_method} onValueChange={(value) => setNewAccount(prev => ({ ...prev, verification_method: value }))}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="email">Email Only</SelectItem>
                    <SelectItem value="sms">SMS Only</SelectItem>
                    <SelectItem value="both">Email + SMS</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="profileLevel">Profile Completion Level</Label>
                <Select value={newAccount.profile_completion_level} onValueChange={(value) => setNewAccount(prev => ({ ...prev, profile_completion_level: value }))}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="basic">Basic (Name, Headline)</SelectItem>
                    <SelectItem value="full">Full (Complete Profile)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <Alert>
                <Shield className="h-4 w-4" />
                <AlertDescription>
                  This will create a complete LinkedIn account with AI-generated persona, 
                  professional content, and automated setup process.
                </AlertDescription>
              </Alert>
              
              <div className="flex justify-end space-x-2">
                <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                  Cancel
                </Button>
                <Button 
                  onClick={createAccountFromPersona}
                  disabled={!newAccount.persona_id || loading}
                >
                  {loading ? 'Creating...' : 'Create Account'}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Filters and Search */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <Input
                placeholder="Search accounts by name or email..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="max-w-sm"
              />
            </div>
            <Select value={filterStatus} onValueChange={setFilterStatus}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="suspended">Suspended</SelectItem>
                <SelectItem value="creating">Creating</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Accounts Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Users className="h-5 w-5" />
            <span>LinkedIn Accounts ({filteredAccounts.length})</span>
          </CardTitle>
          <CardDescription>
            Manage and monitor your LinkedIn research accounts
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Account</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Industry</TableHead>
                <TableHead>Activity</TableHead>
                <TableHead>Risk Level</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredAccounts.map((account) => (
                <TableRow key={account.id}>
                  <TableCell>
                    <div className="space-y-1">
                      <div className="font-medium">{account.name}</div>
                      <div className="text-sm text-slate-500 flex items-center space-x-1">
                        <Mail className="h-3 w-3" />
                        <span>{account.email}</span>
                      </div>
                      {account.profileUrl && (
                        <div className="text-sm text-blue-600 flex items-center space-x-1">
                          <Globe className="h-3 w-3" />
                          <a href={account.profileUrl} target="_blank" rel="noopener noreferrer" className="hover:underline">
                            View Profile
                          </a>
                        </div>
                      )}
                    </div>
                  </TableCell>
                  
                  <TableCell>
                    <div className="flex items-center space-x-2">
                      {getStatusIcon(account.status)}
                      <Badge className={statusColors[account.status]}>
                        {account.status}
                      </Badge>
                    </div>
                  </TableCell>
                  
                  <TableCell>
                    <Badge variant="outline">{account.industry}</Badge>
                  </TableCell>
                  
                  <TableCell>
                    <div className="space-y-1 text-sm">
                      <div>{account.connections} connections</div>
                      <div>{account.posts} posts</div>
                      <div className="text-slate-500">
                        Last: {new Date(account.lastActivity).toLocaleDateString()}
                      </div>
                    </div>
                  </TableCell>
                  
                  <TableCell>
                    <Badge variant="outline" className={riskColors[account.riskLevel]}>
                      {account.riskLevel} risk
                    </Badge>
                  </TableCell>
                  
                  <TableCell>
                    <div className="flex items-center space-x-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setSelectedAccount(account)}
                      >
                        <Eye className="h-3 w-3" />
                      </Button>
                      
                      {account.status === 'pending' ? (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => startLinkedInCreation(account.id)}
                          disabled={loading}
                        >
                          <Play className="h-3 w-3" />
                        </Button>
                      ) : null}
                      
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => deleteAccount(account.id)}
                        className="text-red-600 hover:text-red-700"
                        disabled={loading}
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Account Details Modal */}
      {selectedAccount && (
        <Dialog open={!!selectedAccount} onOpenChange={() => setSelectedAccount(null)}>
          <DialogContent className="sm:max-w-2xl">
            <DialogHeader>
              <DialogTitle>{selectedAccount.name} - Account Details</DialogTitle>
              <DialogDescription>
                Detailed information and activity for this LinkedIn account
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Email</Label>
                  <div className="text-sm">{selectedAccount.email}</div>
                </div>
                <div className="space-y-2">
                  <Label>Status</Label>
                  <Badge className={statusColors[selectedAccount.status]}>
                    {selectedAccount.status}
                  </Badge>
                </div>
                <div className="space-y-2">
                  <Label>Industry</Label>
                  <div className="text-sm">{selectedAccount.industry}</div>
                </div>
                <div className="space-y-2">
                  <Label>Risk Level</Label>
                  <Badge variant="outline" className={riskColors[selectedAccount.riskLevel]}>
                    {selectedAccount.riskLevel} risk
                  </Badge>
                </div>
                <div className="space-y-2">
                  <Label>Connections</Label>
                  <div className="text-sm">{selectedAccount.connections}</div>
                </div>
                <div className="space-y-2">
                  <Label>Posts</Label>
                  <div className="text-sm">{selectedAccount.posts}</div>
                </div>
                <div className="space-y-2">
                  <Label>Proxy</Label>
                  <div className="text-sm">{selectedAccount.proxy}</div>
                </div>
                <div className="space-y-2">
                  <Label>Created</Label>
                  <div className="text-sm">{selectedAccount.created}</div>
                </div>
              </div>
              
              {selectedAccount.profileUrl && (
                <div className="space-y-2">
                  <Label>Profile URL</Label>
                  <a 
                    href={selectedAccount.profileUrl} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-sm text-blue-600 hover:underline block"
                  >
                    {selectedAccount.profileUrl}
                  </a>
                </div>
              )}
            </div>
          </DialogContent>
        </Dialog>
      )}

      {/* LinkedIn Creation Console */}
      {isConsoleOpen && consoleAccountId && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-slate-900 rounded-lg shadow-xl w-full max-w-6xl max-h-[90vh] overflow-auto">
            <LinkedInCreationConsole
              accountId={consoleAccountId}
              onClose={handleConsoleClose}
              onComplete={handleConsoleComplete}
            />
          </div>
        </div>
      )}
    </div>
  )
}

export default AccountManager

