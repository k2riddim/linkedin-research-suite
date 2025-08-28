#!/usr/bin/env node

import express from 'express';
import { Stagehand } from '@browserbasehq/stagehand';

const app = express();
const PORT = process.env.STAGEHAND_PORT || 8080;

// Middleware
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));

// CORS
app.use((req, res, next) => {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept, Authorization, x-bb-api-key, x-bb-project-id, x-model-api-key, x-language');
    if (req.method === 'OPTIONS') {
        res.sendStatus(200);
    } else {
        next();
    }
});

// Store active sessions
const sessions = new Map();

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

// Start a new browser session
app.post('/sessions/start', async (req, res) => {
    try {
        console.log('[STAGEHAND] Starting new session...');
        console.log('[STAGEHAND] Headers:', req.headers);
        console.log('[STAGEHAND] Body:', req.body);

        const {
            env = 'BROWSERBASE',
            headless = true,
            debugDom = false,
            modelName = 'gpt-4o'
        } = req.body;

        // Extract API keys from headers
        const browserbaseApiKey = req.headers['x-bb-api-key'];
        const browserbaseProjectId = req.headers['x-bb-project-id'];
        const modelApiKey = req.headers['x-model-api-key'];

        if (!browserbaseApiKey || !browserbaseProjectId) {
            return res.status(400).json({
                success: false,
                error: 'Missing Browserbase API key or project ID'
            });
        }

        if (!modelApiKey) {
            return res.status(400).json({
                success: false,
                error: 'Missing model API key'
            });
        }

        // Create Stagehand instance
        const stagehand = new Stagehand({
            env,
            apiKey: browserbaseApiKey,
            projectId: browserbaseProjectId,
            headless,
            debugDom,
            modelName,
            modelClientOptions: {
                apiKey: modelApiKey
            }
        });

        await stagehand.init();
        
        // Get the session ID from the API object  
        const browserbaseSessionId = stagehand.api?.sessionId || stagehand.browserbaseSessionID;
        
        if (!browserbaseSessionId) {
            throw new Error('Failed to get Browserbase session ID from Stagehand - available properties: ' + Object.keys(stagehand).join(', '));
        }
        
        const localSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        sessions.set(localSessionId, stagehand);

        console.log(`[STAGEHAND] Session ${localSessionId} created successfully`);
        console.log(`[STAGEHAND] Browserbase session ID: ${browserbaseSessionId}`);

        // Generate the proper live URL for Browserbase
        const liveUrl = `https://www.browserbase.com/sessions/${browserbaseSessionId}/live`;
        
        // Try to get a public viewing URL if available from stagehand
        let publicLiveUrl = liveUrl;
        try {
            // Check if stagehand provides a live URL directly
            if (stagehand.api && stagehand.api.liveUrl) {
                publicLiveUrl = stagehand.api.liveUrl;
            } else if (stagehand.liveUrl) {
                publicLiveUrl = stagehand.liveUrl;
            }
        } catch (e) {
            // Fallback to default live URL
            console.log(`[STAGEHAND] Using default live URL format`);
        }

        res.json({
            success: true,
            data: {
                sessionId: browserbaseSessionId, // Return the Browserbase session ID
                localSessionId: localSessionId,
                liveUrl: publicLiveUrl,
                status: 'active'
            }
        });

    } catch (error) {
        console.error('[STAGEHAND] Error creating session:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Execute actions on existing sessions
app.post('/sessions/:sessionId/:method', async (req, res) => {
    const { sessionId, method } = req.params;
    
    try {
        // Find session by either local ID or Browserbase session ID
        let stagehand = sessions.get(sessionId);
        
        if (!stagehand) {
            // Try to find by Browserbase session ID
            for (const [localId, staghandInstance] of sessions) {
                const bbSessionId = staghandInstance.api?.sessionId || staghandInstance.browserbaseSessionID;
                if (bbSessionId === sessionId) {
                    stagehand = staghandInstance;
                    break;
                }
            }
        }
        
        if (!stagehand) {
            return res.status(404).json({
                success: false,
                error: 'Session not found'
            });
        }

        console.log(`[STAGEHAND] Executing ${method} on session ${sessionId}`);
        console.log(`[STAGEHAND] Payload:`, req.body);

        let result;

        switch (method) {
            case 'goto':
            case 'navigate':
                const { url, options = {} } = req.body;
                await stagehand.page.goto(url, options);
                result = { success: true, url };
                break;

            case 'act':
                try {
                    const { action, ...actOptions } = req.body;
                    console.log(`[STAGEHAND] Executing act with action: "${action}"`);
                    result = await stagehand.page.act(action, actOptions);
                    console.log(`[STAGEHAND] Act completed successfully`);
                } catch (actError) {
                    console.error(`[STAGEHAND] Act failed:`, actError.message);
                    throw new Error(`Act failed: ${actError.message}`);
                }
                break;

            case 'observe':
                try {
                    const { instruction, ...observeOptions } = req.body;
                    console.log(`[STAGEHAND] Executing observe with instruction: "${instruction}"`);
                    result = await stagehand.page.observe(instruction, observeOptions);
                    console.log(`[STAGEHAND] Observe completed successfully`);
                } catch (observeError) {
                    console.error(`[STAGEHAND] Observe failed:`, observeError.message);
                    throw new Error(`Observe failed: ${observeError.message}`);
                }
                break;

            case 'extract':
                try {
                    const { extractInstruction, ...extractOptions } = req.body;
                    console.log(`[STAGEHAND] Executing extract with instruction: "${extractInstruction}"`);
                    result = await stagehand.page.extract(extractInstruction, extractOptions);
                    console.log(`[STAGEHAND] Extract completed successfully`);
                } catch (extractError) {
                    console.error(`[STAGEHAND] Extract failed:`, extractError.message);
                    throw new Error(`Extract failed: ${extractError.message}`);
                }
                break;

            case 'screenshot':
                const screenshotOptions = req.body.options || {};
                result = await stagehand.page.screenshot(screenshotOptions);
                break;

            default:
                return res.status(400).json({
                    success: false,
                    error: `Unknown method: ${method}`
                });
        }

        res.json({
            success: true,
            result: result
        });

    } catch (error) {
        console.error(`[STAGEHAND] Error executing ${method}:`, error);
        
        // Extract meaningful error message
        let errorMessage = error.message || 'Unknown error';
        
        // Check for specific error types
        if (error.message && error.message.includes('Target page, context or browser has been closed')) {
            errorMessage = 'Browser session has been closed or terminated';
        } else if (error.message && error.message.includes('Navigation timeout')) {
            errorMessage = 'Navigation timeout exceeded';
        } else if (error.message && error.message.includes('Cannot connect to session')) {
            errorMessage = 'Session is no longer available';
        }
        
        res.status(500).json({
            success: false,
            error: errorMessage,
            details: error.stack ? error.stack.split('\n')[0] : 'No additional details'
        });
    }
});

// Close session
app.delete('/sessions/:sessionId', async (req, res) => {
    const { sessionId } = req.params;
    
    try {
        // Find session by either local ID or Browserbase session ID
        let stagehand = sessions.get(sessionId);
        let localSessionId = sessionId;
        
        if (!stagehand) {
            // Try to find by Browserbase session ID
            for (const [localId, staghandInstance] of sessions) {
                const bbSessionId = staghandInstance.api?.sessionId || staghandInstance.browserbaseSessionID;
                if (bbSessionId === sessionId) {
                    stagehand = staghandInstance;
                    localSessionId = localId;
                    break;
                }
            }
        }
        
        if (stagehand) {
            await stagehand.close();
            sessions.delete(localSessionId);
            console.log(`[STAGEHAND] Session ${sessionId} closed`);
        }

        res.json({
            success: true,
            message: 'Session closed'
        });

    } catch (error) {
        console.error(`[STAGEHAND] Error closing session ${sessionId}:`, error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// List active sessions
app.get('/sessions', (req, res) => {
    const activeSessions = Array.from(sessions.keys()).map(localId => {
        const stagehand = sessions.get(localId);
        const browserbaseSessionId = stagehand?.api?.sessionId || stagehand?.browserbaseSessionID;
        const liveUrl = `https://www.browserbase.com/sessions/${browserbaseSessionId}/live`;
        
        return {
            localId,
            sessionId: browserbaseSessionId, // For compatibility with AI agent
            browserbaseSessionId,
            liveUrl,
            status: 'active',
            created: new Date().toISOString() // Note: we could track creation time if needed
        };
    });
    
    res.json({
        success: true,
        sessions: activeSessions,
        count: activeSessions.length
    });
});

// Clean up all sessions (administrative endpoint)
app.post('/sessions/cleanup', async (req, res) => {
    try {
        console.log('[STAGEHAND] Administrative cleanup requested');
        
        const cleanupPromises = [];
        const sessionIds = Array.from(sessions.keys());
        
        for (const [localSessionId, stagehand] of sessions) {
            cleanupPromises.push(
                (async () => {
                    try {
                        const browserbaseSessionId = stagehand.api?.sessionId || stagehand.browserbaseSessionID;
                        console.log(`[STAGEHAND] Cleaning up session ${localSessionId} (Browserbase: ${browserbaseSessionId})`);
                        
                        await stagehand.close();
                        sessions.delete(localSessionId);
                        
                        return { localSessionId, browserbaseSessionId, success: true };
                    } catch (error) {
                        console.error(`[STAGEHAND] Failed to cleanup session ${localSessionId}:`, error.message);
                        return { localSessionId, success: false, error: error.message };
                    }
                })()
            );
        }
        
        const results = await Promise.all(cleanupPromises);
        const successful = results.filter(r => r.success).length;
        const failed = results.filter(r => !r.success).length;
        
        console.log(`[STAGEHAND] Cleanup completed: ${successful} successful, ${failed} failed`);
        
        res.json({
            success: true,
            message: `Cleaned up ${successful} sessions, ${failed} failed`,
            results: results,
            summary: {
                total: sessionIds.length,
                successful,
                failed
            }
        });
        
    } catch (error) {
        console.error('[STAGEHAND] Cleanup failed:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Error handling middleware
app.use((error, req, res, next) => {
    console.error('[STAGEHAND] Server error:', error);
    res.status(500).json({
        success: false,
        error: 'Internal server error'
    });
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
    console.log(`[STAGEHAND] Server running on http://0.0.0.0:${PORT}`);
    console.log(`[STAGEHAND] Health check: http://0.0.0.0:${PORT}/health`);
});

// Graceful shutdown function
async function gracefulShutdown(signal) {
    console.log(`\n[STAGEHAND] Received ${signal}, shutting down gracefully...`);
    
    const sessionClosePromises = [];
    
    // Close all active sessions
    for (const [localSessionId, stagehand] of sessions) {
        sessionClosePromises.push(
            (async () => {
                try {
                    const browserbaseSessionId = stagehand.api?.sessionId || stagehand.browserbaseSessionID;
                    console.log(`[STAGEHAND] Closing session ${localSessionId} (Browserbase: ${browserbaseSessionId})`);
                    
                    await stagehand.close();
                    console.log(`[STAGEHAND] ✅ Closed session ${localSessionId}`);
                } catch (error) {
                    console.error(`[STAGEHAND] ❌ Error closing session ${localSessionId}:`, error.message);
                }
            })()
        );
    }
    
    // Wait for all sessions to close (with timeout)
    try {
        await Promise.race([
            Promise.all(sessionClosePromises),
            new Promise(resolve => setTimeout(resolve, 5000)) // 5 second timeout
        ]);
        console.log(`[STAGEHAND] All sessions closed successfully`);
    } catch (error) {
        console.error(`[STAGEHAND] Timeout or error during session cleanup:`, error.message);
    }
    
    // Clear the sessions map
    sessions.clear();
    
    console.log(`[STAGEHAND] Shutdown complete`);
    process.exit(0);
}

// Handle both SIGINT (Ctrl+C) and SIGTERM (systemctl stop)
process.on('SIGINT', () => gracefulShutdown('SIGINT'));
process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));

// Handle uncaught exceptions to cleanup sessions
process.on('uncaughtException', async (error) => {
    console.error('[STAGEHAND] Uncaught exception:', error);
    await gracefulShutdown('uncaughtException');
});

process.on('unhandledRejection', async (reason, promise) => {
    console.error('[STAGEHAND] Unhandled rejection at:', promise, 'reason:', reason);
    await gracefulShutdown('unhandledRejection');
});
