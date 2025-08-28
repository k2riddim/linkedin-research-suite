#!/usr/bin/env node

/**
 * LinkedIn Research Suite - Unified Server
 * 
 * This script manages both the Python backend (framework) and React frontend (dashboard)
 * as a single unified service. It handles process spawning, logging, error handling,
 * and graceful shutdown.
 */

import { spawn, exec } from 'child_process';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { createWriteStream } from 'fs';

// ES module setup
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Configuration
const CONFIG = {
    logFile: path.join(__dirname, 'logs', 'unified-server.log'),
    backend: {
        cwd: path.join(__dirname, 'framework'),
        command: 'python',
        args: ['src/main.py'],
        env: {
            ...process.env,
            PYTHONPATH: path.join(__dirname, 'framework'),
            FLASK_ENV: process.env.NODE_ENV === 'production' ? 'production' : 'development'
        },
        port: 5001
    },
    frontend: {
        cwd: path.join(__dirname, 'dashboard'),
        command: 'npm',
        args: process.env.NODE_ENV === 'production' ? ['run', 'preview', '--', '--host', '0.0.0.0', '--port', '5173'] : ['run', 'dev', '--', '--host', '0.0.0.0'],
        env: {
            ...process.env,
            NODE_ENV: process.env.NODE_ENV || 'development',
            VITE_API_URL: process.env.VITE_API_URL || 'http://localhost:5001'
        },
        port: 5173
    }
};

class UnifiedServer {
    constructor() {
        this.processes = {
            backend: null,
            frontend: null
        };
        this.logStream = null;
        this.isShuttingDown = false;
        this.restartCounts = {
            backend: 0,
            frontend: 0
        };
        this.maxRestarts = 3;
        this.restartDelay = 5000; // 5 seconds
        
        this.setupLogging();
        this.setupSignalHandlers();
    }

    setupLogging() {
        // Ensure logs directory exists
        const logsDir = path.dirname(CONFIG.logFile);
        if (!fs.existsSync(logsDir)) {
            fs.mkdirSync(logsDir, { recursive: true });
        }

        // Create log stream
        this.logStream = createWriteStream(CONFIG.logFile, { flags: 'a' });
        
        // Log startup
        this.log('INFO', 'LinkedIn Research Suite - Unified Server Starting');
        this.log('INFO', `Node Environment: ${process.env.NODE_ENV || 'development'}`);
        this.log('INFO', `Process ID: ${process.pid}`);
    }

    log(level, message, service = 'MAIN') {
        const timestamp = new Date().toISOString();
        const logMessage = `[${timestamp}] [${level}] [${service}] ${message}\n`;
        
        // Write to log file
        if (this.logStream) {
            this.logStream.write(logMessage);
        }
        
        // Also write to console
        console.log(logMessage.trim());
    }

    setupSignalHandlers() {
        const signals = ['SIGTERM', 'SIGINT', 'SIGUSR2'];
        
        signals.forEach(signal => {
            process.on(signal, () => {
                this.log('INFO', `Received ${signal}, starting graceful shutdown...`);
                this.shutdown();
            });
        });

        process.on('uncaughtException', (error) => {
            this.log('ERROR', `Uncaught Exception: ${error.message}`, 'MAIN');
            this.log('ERROR', error.stack, 'MAIN');
            this.shutdown(1);
        });

        process.on('unhandledRejection', (reason, promise) => {
            this.log('ERROR', `Unhandled Rejection at: ${promise}, reason: ${reason}`, 'MAIN');
            this.shutdown(1);
        });
    }

    async checkPrerequisites() {
        this.log('INFO', 'Checking prerequisites...');
        
        // Check if backend directory exists
        if (!fs.existsSync(CONFIG.backend.cwd)) {
            throw new Error(`Backend directory not found: ${CONFIG.backend.cwd}`);
        }

        // Check if frontend directory exists
        if (!fs.existsSync(CONFIG.frontend.cwd)) {
            throw new Error(`Frontend directory not found: ${CONFIG.frontend.cwd}`);
        }

        // Check if main.py exists
        const mainPyPath = path.join(CONFIG.backend.cwd, 'src', 'main.py');
        if (!fs.existsSync(mainPyPath)) {
            throw new Error(`Backend main.py not found: ${mainPyPath}`);
        }

        // Check if package.json exists
        const packageJsonPath = path.join(CONFIG.frontend.cwd, 'package.json');
        if (!fs.existsSync(packageJsonPath)) {
            throw new Error(`Frontend package.json not found: ${packageJsonPath}`);
        }

        // Check for virtual environment (optional but recommended)
        const venvPath = path.join(CONFIG.backend.cwd, 'venv');
        if (fs.existsSync(venvPath)) {
            CONFIG.backend.command = path.join(venvPath, 'bin', 'python');
            this.log('INFO', 'Using virtual environment for Python backend');
        }

        this.log('INFO', 'Prerequisites check passed');
    }

    spawnProcess(name, config) {
        this.log('INFO', `Starting ${name} process...`, name.toUpperCase());
        this.log('INFO', `Command: ${config.command} ${config.args.join(' ')}`, name.toUpperCase());
        this.log('INFO', `Working Directory: ${config.cwd}`, name.toUpperCase());

        const process = spawn(config.command, config.args, {
            cwd: config.cwd,
            env: config.env,
            stdio: ['pipe', 'pipe', 'pipe']
        });

        // Handle process output
        process.stdout.on('data', (data) => {
            const message = data.toString().trim();
            if (message) {
                this.log('INFO', message, name.toUpperCase());
            }
        });

        process.stderr.on('data', (data) => {
            const message = data.toString().trim();
            if (message) {
                this.log('ERROR', message, name.toUpperCase());
            }
        });

        // Handle process events
        process.on('spawn', () => {
            this.log('INFO', `${name} process spawned (PID: ${process.pid})`, name.toUpperCase());
        });

        process.on('error', (error) => {
            this.log('ERROR', `${name} process error: ${error.message}`, name.toUpperCase());
            this.handleProcessFailure(name);
        });

        process.on('exit', (code, signal) => {
            if (!this.isShuttingDown) {
                this.log('ERROR', `${name} process exited unexpectedly (code: ${code}, signal: ${signal})`, name.toUpperCase());
                this.handleProcessFailure(name);
            } else {
                this.log('INFO', `${name} process exited gracefully`, name.toUpperCase());
            }
        });

        return process;
    }

    async handleProcessFailure(processName) {
        const restartCount = this.restartCounts[processName];
        
        if (restartCount >= this.maxRestarts) {
            this.log('ERROR', `${processName} exceeded maximum restart attempts (${this.maxRestarts})`, processName.toUpperCase());
            this.shutdown(1);
            return;
        }

        this.restartCounts[processName]++;
        this.log('INFO', `Restarting ${processName} in ${this.restartDelay}ms (attempt ${this.restartCounts[processName]}/${this.maxRestarts})`, processName.toUpperCase());
        
        setTimeout(() => {
            if (!this.isShuttingDown) {
                this.startProcess(processName);
            }
        }, this.restartDelay);
    }

    startProcess(name) {
        if (this.processes[name]) {
            this.processes[name].kill('SIGTERM');
        }

        const config = CONFIG[name];
        this.processes[name] = this.spawnProcess(name, config);
    }

    async waitForHealthcheck(name, port, maxAttempts = 30) {
        const checkHealth = () => {
            return new Promise((resolve) => {
                exec(`curl -f http://localhost:${port}/api/health || curl -f http://localhost:${port}`, 
                     { timeout: 5000 }, 
                     (error) => {
                    resolve(!error);
                });
            });
        };

        this.log('INFO', `Waiting for ${name} to be healthy on port ${port}...`, name.toUpperCase());
        
        for (let attempt = 1; attempt <= maxAttempts; attempt++) {
            if (await checkHealth()) {
                this.log('INFO', `${name} is healthy!`, name.toUpperCase());
                return true;
            }
            
            if (attempt < maxAttempts) {
                await new Promise(resolve => setTimeout(resolve, 2000));
            }
        }
        
        this.log('WARNING', `${name} health check timed out after ${maxAttempts * 2} seconds`, name.toUpperCase());
        return false;
    }

    async start() {
        try {
            await this.checkPrerequisites();
            
            this.log('INFO', 'Starting services...');
            
            // Start backend first
            this.startProcess('backend');
            
            // Wait a bit for backend to start
            await new Promise(resolve => setTimeout(resolve, 3000));
            
            // Start frontend
            this.startProcess('frontend');
            
            // Wait for both services to be healthy
            await this.waitForHealthcheck('backend', CONFIG.backend.port);
            await this.waitForHealthcheck('frontend', CONFIG.frontend.port);
            
            this.log('INFO', '🚀 LinkedIn Research Suite is running!');
            this.log('INFO', `📊 Dashboard: http://localhost:${CONFIG.frontend.port}`);
            this.log('INFO', `🔧 API: http://localhost:${CONFIG.backend.port}/api`);
            this.log('INFO', 'Press Ctrl+C to stop the services');
            
        } catch (error) {
            this.log('ERROR', `Failed to start: ${error.message}`);
            this.shutdown(1);
        }
    }

    async shutdown(exitCode = 0) {
        if (this.isShuttingDown) {
            this.log('WARNING', 'Shutdown already in progress...');
            return;
        }

        this.isShuttingDown = true;
        this.log('INFO', 'Shutting down services...');

        const shutdownPromises = [];
        
        // Shutdown both processes
        for (const [name, process] of Object.entries(this.processes)) {
            if (process && !process.killed) {
                shutdownPromises.push(new Promise((resolve) => {
                    const timeout = setTimeout(() => {
                        this.log('WARNING', `Force killing ${name} process...`, name.toUpperCase());
                        process.kill('SIGKILL');
                        resolve();
                    }, 10000); // 10 second timeout

                    process.on('exit', () => {
                        clearTimeout(timeout);
                        this.log('INFO', `${name} process stopped`, name.toUpperCase());
                        resolve();
                    });

                    this.log('INFO', `Stopping ${name} process...`, name.toUpperCase());
                    process.kill('SIGTERM');
                }));
            }
        }

        // Wait for all processes to shutdown
        await Promise.all(shutdownPromises);
        
        // Close log stream
        if (this.logStream) {
            this.logStream.end();
        }

        this.log('INFO', 'LinkedIn Research Suite shutdown complete');
        process.exit(exitCode);
    }
}

// Main execution
async function main() {
    const server = new UnifiedServer();
    await server.start();
}

// Handle if running directly
if (import.meta.url === `file://${process.argv[1]}`) {
    main().catch((error) => {
        console.error('Fatal error:', error);
        process.exit(1);
    });
}

export default UnifiedServer;