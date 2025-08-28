import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Button } from '@/components/ui/button.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Label } from '@/components/ui/label.jsx'
import { Textarea } from '@/components/ui/textarea.jsx'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select.jsx'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table.jsx'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog.jsx'
import { Alert, AlertDescription } from '@/components/ui/alert.jsx'
import { Progress } from '@/components/ui/progress.jsx'
import { 
  Bot, 
  Play, 
  Pause, 
  Square, 
  Plus, 
  Eye, 
  Edit, 
  Trash2,
  Clock,
  CheckCircle,
  AlertTriangle,
  Users,
  MessageSquare,
  UserPlus,
  Search,
  Calendar,
  Target,
  Activity
} from 'lucide-react'

const AutomationControl = () => {
  const [jobs, setJobs] = useState([
    {
      id: 'job_001',
      name: 'Tech Professionals Outreach',
      type: 'connection_requests',
      status: 'running',
      progress: 65,
      account: 'marie.dubois@emailondeck.com',
      target: 'Data Scientists in Paris',
      created: '2024-01-20 09:00',
      lastActivity: '2024-01-20 14:30',
      completed: 13,
      total: 20,
      successRate: 85,
      estimatedCompletion: '2024-01-20 18:00'
    },
    {
      id: 'job_002',
      name: 'Content Engagement Campaign',
      type: 'post_engagement',
      status: 'scheduled',
      progress: 0,
      account: 'pierre.martin@tempmail.org',
      target: 'Finance Industry Posts',
      created: '2024-01-20 10:30',
      lastActivity: null,
      completed: 0,
      total: 50,
      successRate: null,
      estimatedCompletion: '2024-01-21 12:00'
    },
    {
      id: 'job_003',
      name: 'Profile Research Batch',
      type: 'profile_research',
      status: 'completed',
      progress: 100,
      account: 'sophie.bernard@guerrillamail.com',
      target: 'Marketing Managers',
      created: '2024-01-19 14:00',
      lastActivity: '2024-01-19 16:45',
      completed: 25,
      total: 25,
      successRate: 96,
      estimatedCompletion: '2024-01-19 16:45'
    }
  ])

  const [selectedJob, setSelectedJob] = useState(null)
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [newJob, setNewJob] = useState({
    name: '',
    type: '',
    account: '',
    target: '',
    parameters: {}
  })

  const jobTypes = [
    { value: 'connection_requests', label: 'Connection Requests', icon: UserPlus },
    { value: 'message_sending', label: 'Message Sending', icon: MessageSquare },
    { value: 'profile_research', label: 'Profile Research', icon: Search },
    { value: 'post_engagement', label: 'Post Engagement', icon: Activity },
    { value: 'content_posting', label: 'Content Posting', icon: MessageSquare }
  ]

  const statusColors = {
    running: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
    scheduled: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
    paused: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
    completed: 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200',
    failed: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'running':
        return <Play className="h-4 w-4 text-green-600" />
      case 'scheduled':
        return <Clock className="h-4 w-4 text-blue-600" />
      case 'paused':
        return <Pause className="h-4 w-4 text-yellow-600" />
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-gray-600" />
      case 'failed':
        return <AlertTriangle className="h-4 w-4 text-red-600" />
      default:
        return null
    }
  }

  const handleJobAction = (jobId, action) => {
    setJobs(prev => prev.map(job => {
      if (job.id === jobId) {
        switch (action) {
          case 'start':
            return { ...job, status: 'running' }
          case 'pause':
            return { ...job, status: 'paused' }
          case 'stop':
            return { ...job, status: 'completed' }
          case 'delete':
            return null
          default:
            return job
        }
      }
      return job
    }).filter(Boolean))
  }

  const createJob = () => {
    const jobId = `job_${Date.now()}`
    const newJobData = {
      id: jobId,
      name: newJob.name,
      type: newJob.type,
      status: 'scheduled',
      progress: 0,
      account: newJob.account,
      target: newJob.target,
      created: new Date().toISOString(),
      lastActivity: null,
      completed: 0,
      total: newJob.parameters.total || 10,
      successRate: null,
      estimatedCompletion: new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString()
    }

    setJobs(prev => [...prev, newJobData])
    setIsCreateDialogOpen(false)
    setNewJob({
      name: '',
      type: '',
      account: '',
      target: '',
      parameters: {}
    })
  }

  // Simulate real-time updates for running jobs
  useEffect(() => {
    const interval = setInterval(() => {
      setJobs(prev => prev.map(job => {
        if (job.status === 'running' && job.progress < 100) {
          const newProgress = Math.min(100, job.progress + Math.random() * 5)
          const newCompleted = Math.floor((newProgress / 100) * job.total)
          return {
            ...job,
            progress: newProgress,
            completed: newCompleted,
            lastActivity: new Date().toISOString(),
            status: newProgress >= 100 ? 'completed' : 'running'
          }
        }
        return job
      }))
    }, 3000)

    return () => clearInterval(interval)
  }, [])

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Automation Control</h2>
          <p className="text-slate-600 dark:text-slate-300">
            Manage and monitor LinkedIn automation jobs
          </p>
        </div>
        
        <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button className="bg-blue-600 hover:bg-blue-700">
              <Plus className="h-4 w-4 mr-2" />
              Create Job
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-lg">
            <DialogHeader>
              <DialogTitle>Create Automation Job</DialogTitle>
              <DialogDescription>
                Set up a new LinkedIn automation task
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="jobName">Job Name</Label>
                <Input
                  id="jobName"
                  value={newJob.name}
                  onChange={(e) => setNewJob(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="e.g., Tech Professionals Outreach"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="jobType">Job Type</Label>
                <Select value={newJob.type} onValueChange={(value) => setNewJob(prev => ({ ...prev, type: value }))}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select job type" />
                  </SelectTrigger>
                  <SelectContent>
                    {jobTypes.map((type) => (
                      <SelectItem key={type.value} value={type.value}>
                        {type.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="account">LinkedIn Account</Label>
                <Select value={newJob.account} onValueChange={(value) => setNewJob(prev => ({ ...prev, account: value }))}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select account" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="marie.dubois@emailondeck.com">Marie Dubois</SelectItem>
                    <SelectItem value="pierre.martin@tempmail.org">Pierre Martin</SelectItem>
                    <SelectItem value="sophie.bernard@guerrillamail.com">Sophie Bernard</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="target">Target Description</Label>
                <Textarea
                  id="target"
                  value={newJob.target}
                  onChange={(e) => setNewJob(prev => ({ ...prev, target: e.target.value }))}
                  placeholder="e.g., Data Scientists in Paris with 5+ years experience"
                  rows={3}
                />
              </div>
              
              {newJob.type && (
                <div className="space-y-2">
                  <Label>Job Parameters</Label>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <Label htmlFor="total" className="text-xs">Total Actions</Label>
                      <Input
                        id="total"
                        type="number"
                        value={newJob.parameters.total || ''}
                        onChange={(e) => setNewJob(prev => ({ 
                          ...prev, 
                          parameters: { ...prev.parameters, total: parseInt(e.target.value) || 0 }
                        }))}
                        placeholder="10"
                      />
                    </div>
                    <div>
                      <Label htmlFor="delay" className="text-xs">Delay (minutes)</Label>
                      <Input
                        id="delay"
                        type="number"
                        value={newJob.parameters.delay || ''}
                        onChange={(e) => setNewJob(prev => ({ 
                          ...prev, 
                          parameters: { ...prev.parameters, delay: parseInt(e.target.value) || 0 }
                        }))}
                        placeholder="5"
                      />
                    </div>
                  </div>
                </div>
              )}
              
              <Alert>
                <Bot className="h-4 w-4" />
                <AlertDescription>
                  This job will be executed automatically with built-in safety measures 
                  and human-like timing to avoid detection.
                </AlertDescription>
              </Alert>
              
              <div className="flex justify-end space-x-2">
                <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                  Cancel
                </Button>
                <Button 
                  onClick={createJob}
                  disabled={!newJob.name || !newJob.type || !newJob.account || !newJob.target}
                >
                  Create Job
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Job Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 border-green-200 dark:border-green-800">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-green-700 dark:text-green-300">
              Running Jobs
            </CardTitle>
            <Play className="h-4 w-4 text-green-600 dark:text-green-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-900 dark:text-green-100">
              {jobs.filter(job => job.status === 'running').length}
            </div>
            <p className="text-xs text-green-600 dark:text-green-400">
              Active automation tasks
            </p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 border-blue-200 dark:border-blue-800">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-blue-700 dark:text-blue-300">
              Scheduled Jobs
            </CardTitle>
            <Clock className="h-4 w-4 text-blue-600 dark:text-blue-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-900 dark:text-blue-100">
              {jobs.filter(job => job.status === 'scheduled').length}
            </div>
            <p className="text-xs text-blue-600 dark:text-blue-400">
              Waiting to execute
            </p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 border-purple-200 dark:border-purple-800">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-purple-700 dark:text-purple-300">
              Completed Today
            </CardTitle>
            <CheckCircle className="h-4 w-4 text-purple-600 dark:text-purple-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-900 dark:text-purple-100">
              {jobs.filter(job => job.status === 'completed').length}
            </div>
            <p className="text-xs text-purple-600 dark:text-purple-400">
              Successfully finished
            </p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-orange-50 to-orange-100 dark:from-orange-900/20 dark:to-orange-800/20 border-orange-200 dark:border-orange-800">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-orange-700 dark:text-orange-300">
              Success Rate
            </CardTitle>
            <Target className="h-4 w-4 text-orange-600 dark:text-orange-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-900 dark:text-orange-100">
              94.2%
            </div>
            <p className="text-xs text-orange-600 dark:text-orange-400">
              Overall automation success
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Jobs Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Bot className="h-5 w-5" />
            <span>Automation Jobs ({jobs.length})</span>
          </CardTitle>
          <CardDescription>
            Monitor and control your LinkedIn automation tasks
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Job Details</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Progress</TableHead>
                <TableHead>Account</TableHead>
                <TableHead>Performance</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {jobs.map((job) => (
                <TableRow key={job.id}>
                  <TableCell>
                    <div className="space-y-1">
                      <div className="font-medium">{job.name}</div>
                      <div className="text-sm text-slate-500">
                        {jobTypes.find(type => type.value === job.type)?.label}
                      </div>
                      <div className="text-xs text-slate-400">
                        Target: {job.target}
                      </div>
                    </div>
                  </TableCell>
                  
                  <TableCell>
                    <div className="flex items-center space-x-2">
                      {getStatusIcon(job.status)}
                      <Badge className={statusColors[job.status]}>
                        {job.status}
                      </Badge>
                    </div>
                  </TableCell>
                  
                  <TableCell>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>{job.completed}/{job.total}</span>
                        <span>{Math.round(job.progress)}%</span>
                      </div>
                      <Progress value={job.progress} className="h-2" />
                      {job.status === 'running' && (
                        <div className="text-xs text-slate-500">
                          ETA: {new Date(job.estimatedCompletion).toLocaleTimeString()}
                        </div>
                      )}
                    </div>
                  </TableCell>
                  
                  <TableCell>
                    <div className="text-sm">
                      {job.account.split('@')[0]}
                    </div>
                  </TableCell>
                  
                  <TableCell>
                    <div className="space-y-1 text-sm">
                      {job.successRate && (
                        <div className="text-green-600">
                          {job.successRate}% success
                        </div>
                      )}
                      <div className="text-slate-500">
                        Created: {new Date(job.created).toLocaleDateString()}
                      </div>
                      {job.lastActivity && (
                        <div className="text-slate-400 text-xs">
                          Last: {new Date(job.lastActivity).toLocaleTimeString()}
                        </div>
                      )}
                    </div>
                  </TableCell>
                  
                  <TableCell>
                    <div className="flex items-center space-x-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setSelectedJob(job)}
                      >
                        <Eye className="h-3 w-3" />
                      </Button>
                      
                      {job.status === 'running' ? (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleJobAction(job.id, 'pause')}
                        >
                          <Pause className="h-3 w-3" />
                        </Button>
                      ) : job.status === 'scheduled' || job.status === 'paused' ? (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleJobAction(job.id, 'start')}
                        >
                          <Play className="h-3 w-3" />
                        </Button>
                      ) : null}
                      
                      {job.status !== 'running' && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleJobAction(job.id, 'delete')}
                          className="text-red-600 hover:text-red-700"
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Job Details Modal */}
      {selectedJob && (
        <Dialog open={!!selectedJob} onOpenChange={() => setSelectedJob(null)}>
          <DialogContent className="sm:max-w-2xl">
            <DialogHeader>
              <DialogTitle>{selectedJob.name} - Job Details</DialogTitle>
              <DialogDescription>
                Detailed information and logs for this automation job
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Job Type</Label>
                  <div className="text-sm">
                    {jobTypes.find(type => type.value === selectedJob.type)?.label}
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Status</Label>
                  <Badge className={statusColors[selectedJob.status]}>
                    {selectedJob.status}
                  </Badge>
                </div>
                <div className="space-y-2">
                  <Label>Account</Label>
                  <div className="text-sm">{selectedJob.account}</div>
                </div>
                <div className="space-y-2">
                  <Label>Progress</Label>
                  <div className="text-sm">{selectedJob.completed}/{selectedJob.total} ({Math.round(selectedJob.progress)}%)</div>
                </div>
                <div className="space-y-2">
                  <Label>Created</Label>
                  <div className="text-sm">{new Date(selectedJob.created).toLocaleString()}</div>
                </div>
                <div className="space-y-2">
                  <Label>Last Activity</Label>
                  <div className="text-sm">
                    {selectedJob.lastActivity ? new Date(selectedJob.lastActivity).toLocaleString() : 'N/A'}
                  </div>
                </div>
              </div>
              
              <div className="space-y-2">
                <Label>Target Description</Label>
                <div className="text-sm p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                  {selectedJob.target}
                </div>
              </div>
              
              {selectedJob.successRate && (
                <div className="space-y-2">
                  <Label>Performance Metrics</Label>
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div className="text-center p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                      <div className="font-medium text-green-700 dark:text-green-300">Success Rate</div>
                      <div className="text-lg font-bold text-green-900 dark:text-green-100">{selectedJob.successRate}%</div>
                    </div>
                    <div className="text-center p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                      <div className="font-medium text-blue-700 dark:text-blue-300">Completed</div>
                      <div className="text-lg font-bold text-blue-900 dark:text-blue-100">{selectedJob.completed}</div>
                    </div>
                    <div className="text-center p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                      <div className="font-medium text-purple-700 dark:text-purple-300">Remaining</div>
                      <div className="text-lg font-bold text-purple-900 dark:text-purple-100">{selectedJob.total - selectedJob.completed}</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  )
}

export default AutomationControl

