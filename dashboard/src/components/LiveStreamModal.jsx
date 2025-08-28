import { useEffect, useState, useCallback } from 'react'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog.jsx'
import { Button } from '@/components/ui/button.jsx'
import { Alert, AlertDescription } from '@/components/ui/alert.jsx'
import { ExternalLink, RefreshCw, Monitor, Loader2 } from 'lucide-react'

const LiveStreamModal = ({ open, onOpenChange, accountId }) => {
  const [liveUrl, setLiveUrl] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [isIframeLoading, setIsIframeLoading] = useState(true)

  const fetchLiveUrl = useCallback(async () => {
    if (!accountId) {
      setError('No account ID provided')
      return
    }

    try {
      setLoading(true)
      setError(null)
      
      const response = await fetch(`/api/automation/ai/account/${accountId}/live`)
      const data = await response.json()
      
      if (!response.ok) {
        throw new Error(data.error || `HTTP ${response.status}`)
      }
      
      if (data?.live_url) {
        setLiveUrl(data.live_url)
        setIsIframeLoading(true)
      } else {
        setLiveUrl(null)
        setError('No live session available')
      }
    } catch (err) {
      setError(`Failed to fetch live URL: ${err.message}`)
      setLiveUrl(null)
    } finally {
      setLoading(false)
    }
  }, [accountId])

  const handleIframeLoad = () => {
    setIsIframeLoading(false)
  }

  const handleIframeError = () => {
    setIsIframeLoading(false)
    setError('Failed to load Browserbase live stream')
  }

  useEffect(() => {
    if (open && accountId) {
      fetchLiveUrl()
    }
  }, [open, accountId, fetchLiveUrl])

  // Auto-refresh every 30 seconds if no live URL found
  useEffect(() => {
    if (open && !liveUrl && !loading) {
      const interval = setInterval(fetchLiveUrl, 30000)
      return () => clearInterval(interval)
    }
  }, [open, liveUrl, loading, fetchLiveUrl])

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-6xl max-h-[85vh] overflow-hidden">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Monitor className="h-5 w-5" />
            Browserbase Live Stream
          </DialogTitle>
          <DialogDescription>
            Real-time view of the AI browser automation session for account: {accountId}
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4">
          {/* Controls */}
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <Button 
                onClick={fetchLiveUrl} 
                variant="outline" 
                size="sm" 
                disabled={loading}
                className="flex items-center gap-2"
              >
                {loading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCw className="h-4 w-4" />
                )}
                {loading ? 'Loading...' : 'Refresh'}
              </Button>
              
              {liveUrl && (
                <Button 
                  onClick={() => window.open(liveUrl, '_blank')} 
                  variant="outline" 
                  size="sm"
                  className="flex items-center gap-2"
                >
                  <ExternalLink className="h-4 w-4" />
                  Open in new tab
                </Button>
              )}
            </div>
            
            {liveUrl && (
              <div className="text-xs text-green-600 dark:text-green-400 flex items-center gap-1">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                Live Session Active
              </div>
            )}
          </div>

          {/* Error Display */}
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Content Area */}
          <div className="relative">
            {!liveUrl && !loading && (
              <div className="flex flex-col items-center justify-center h-[50vh] bg-slate-50 dark:bg-slate-900 rounded-lg border-2 border-dashed">
                <Monitor className="h-12 w-12 text-slate-400 mb-4" />
                <h3 className="text-lg font-semibold text-slate-600 dark:text-slate-300 mb-2">
                  No Live Session
                </h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 text-center max-w-md">
                  Start an AI automation task to see the live browser stream here. 
                  Sessions will appear automatically when active.
                </p>
              </div>
            )}

            {liveUrl && (
              <div className="relative w-full">
                {isIframeLoading && (
                  <div className="absolute inset-0 flex items-center justify-center bg-slate-50 dark:bg-slate-900 rounded-lg z-10">
                    <div className="flex flex-col items-center gap-4">
                      <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
                      <p className="text-sm text-slate-600 dark:text-slate-300">
                        Loading Browserbase live stream...
                      </p>
                    </div>
                  </div>
                )}
                
                <iframe
                  src={liveUrl}
                  title="Browserbase Live Browser Stream"
                  className="w-full h-[65vh] rounded-lg border"
                  sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-popups-to-escape-sandbox"
                  referrerPolicy="strict-origin-when-cross-origin"
                  onLoad={handleIframeLoad}
                  onError={handleIframeError}
                  style={{ 
                    backgroundColor: '#f8fafc',
                    border: '1px solid #e2e8f0'
                  }}
                />
              </div>
            )}
          </div>

          {/* Status Info */}
          {liveUrl && (
            <div className="text-xs text-slate-500 dark:text-slate-400 bg-slate-50 dark:bg-slate-900 p-3 rounded-lg">
              <strong>Live URL:</strong> {liveUrl}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}

export default LiveStreamModal
