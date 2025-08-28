#!/bin/bash

# LinkedIn Research Framework - Native Raspberry Pi Deployment
# Lightweight deployment without Docker for better performance

set -e

echo "🐧 LinkedIn Research Framework - Native Raspberry Pi Deployment"
echo "================================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root for security reasons"
   exit 1
fi

# Install system dependencies
print_status "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv nginx sqlite3

# Create virtual environment
print_status "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Verify virtual environment activation
print_status "Verifying virtual environment..."
if [[ "$VIRTUAL_ENV" != "" ]]; then
    print_success "Virtual environment activated: $VIRTUAL_ENV"
else
    print_error "Failed to activate virtual environment"
    exit 1
fi

# Use virtual environment python explicitly
PYTHON_EXEC="$VIRTUAL_ENV/bin/python"
PIP_EXEC="$VIRTUAL_ENV/bin/pip"

# Install Python dependencies
print_status "Installing Python dependencies..."
$PIP_EXEC install --upgrade pip
$PIP_EXEC install -r requirements.txt

# Install gunicorn for production server
print_status "Installing gunicorn for production deployment..."
$PIP_EXEC install gunicorn

# Install Playwright browsers for Raspberry Pi
print_status "Installing Playwright browsers (optimized for Pi)..."
$PIP_EXEC install playwright

# Verify virtual environment is working
print_status "Verifying Playwright installation..."
if $PYTHON_EXEC -c "import playwright; print('Playwright version:', playwright.__version__)" 2>/dev/null; then
    print_success "Playwright installed successfully"
    $PYTHON_EXEC -c "
from playwright.sync_api import sync_playwright
print('Installing Chromium browser...')
with sync_playwright() as p:
    p.chromium.install()
print('Chromium browser installed successfully')
"
else
    print_error "Failed to import Playwright. Check virtual environment."
    exit 1
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p data logs static

# Create environment file if it doesn't exist
if [ ! -f .env ]; then
    print_status "Creating environment configuration file..."
    cat > .env << EOF
# LinkedIn Research Framework Configuration
# Copy this file and update with your actual API keys

# OpenAI API Key (required for AI content generation)
OPENAI_API_KEY=your_openai_api_key_here

# 5SIM API Key (required for SMS verification)
FIVESIM_API_KEY=your_5sim_api_key_here

# EmailOnDeck API Key (required for email verification)
EMAILONDECK_API_KEY=your_emailondeck_api_key_here

# Geonode Proxy Credentials (required for proxy rotation)
# Format: username:password@endpoint:port
GEONODE_CREDENTIALS=your_geonode_credentials_here

# Database Configuration
DATABASE_URL=sqlite:///data/linkedin_research.db

# Flask Configuration
FLASK_ENV=production
FLASK_SECRET_KEY=$(openssl rand -hex 32)

# Raspberry Pi optimizations
MAX_WORKERS=2
WORKER_TIMEOUT=30
MAX_REQUESTS=1000

# Security Configuration
SESSION_TIMEOUT=3600
ENABLE_RATE_LIMITING=true
MAX_REQUESTS_PER_MINUTE=30
EOF
    print_warning "Environment file created at .env"
    print_warning "Please edit .env and add your actual API keys before continuing!"
    echo ""
    echo "Required API keys:"
    echo "1. OpenAI API Key - Get from: https://platform.openai.com/api-keys"
    echo "2. 5SIM API Key - Get from: https://5sim.net/settings/api"
    echo "3. EmailOnDeck API Key - Get from: https://www.emailondeck.com/api"
    echo "4. Geonode Proxy Credentials - Get from: https://geonode.com/"
    echo ""
    read -p "Press Enter after updating the .env file to continue..."
fi

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Validate required environment variables
print_status "Validating configuration..."
required_vars=("OPENAI_API_KEY" "FIVESIM_API_KEY" "EMAILONDECK_API_KEY" "GEONODE_CREDENTIALS")
missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ] || [ "${!var}" = "your_${var,,}_here" ] || [ "${!var}" = "your_${var,,}_api_key_here" ] || [ "${!var}" = "your_${var,,}_credentials_here" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    print_error "Missing or invalid configuration for: ${missing_vars[*]}"
    print_error "Please update the .env file with valid API keys"
    exit 1
fi

print_success "Configuration validated successfully!"

# Configure nginx for Raspberry Pi
print_status "Configuring nginx..."
sudo tee /etc/nginx/sites-available/linkedin-research > /dev/null << EOF
server {
    listen 8080;
    server_name localhost;

    # Raspberry Pi optimizations
    client_max_body_size 50M;
    client_body_timeout 12;
    client_header_timeout 12;
    keepalive_timeout 15;
    send_timeout 10;

    root /home/chorizo/projects/linkedin-research-framework/static;
    index index.html;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;

    # API proxy to Flask backend
    location /api/ {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # Timeouts optimized for Raspberry Pi
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # WebSocket support
    location /socket.io/ {
        proxy_pass http://127.0.0.1:5001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Static files with caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Frontend routing
    location / {
        try_files \$uri \$uri/ /index.html;
    }

    # Health check
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF

# Enable the site
sudo ln -sf /etc/nginx/sites-available/linkedin-research /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# Create systemd service for the Flask app
print_status "Creating systemd service..."
sudo tee /etc/systemd/system/linkedin-research.service > /dev/null << EOF
[Unit]
Description=LinkedIn Research Framework
After=network.target

[Service]
Type=simple
User=chorizo
WorkingDirectory=/home/chorizo/projects/linkedin-research-framework
Environment=PATH=/home/chorizo/projects/linkedin-research-framework/venv/bin
ExecStart=/home/chorizo/projects/linkedin-research-framework/venv/bin/gunicorn \
    --workers 2 \
    --threads 2 \
    --bind 127.0.0.1:5001 \
    --timeout 30 \
    --access-logfile /home/chorizo/projects/linkedin-research-framework/logs/access.log \
    --error-logfile /home/chorizo/projects/linkedin-research-framework/logs/error.log \
    src.main:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Start the service
sudo systemctl daemon-reload
sudo systemctl enable linkedin-research.service
sudo systemctl start linkedin-research.service

# Wait for service to start
print_status "Waiting for service to start..."
sleep 5

# Check if service is running
if sudo systemctl is-active --quiet linkedin-research.service; then
    print_success "Service started successfully!"
    echo ""
    echo "🎉 LinkedIn Research Framework is now running!"
    echo ""
    echo "🌐 Access the dashboard at: http://localhost:8080"
    echo "🔌 API endpoint: http://localhost:5001/api"
    echo ""
    echo "To view logs: sudo journalctl -u linkedin-research -f"
    echo "To restart: sudo systemctl restart linkedin-research"
    echo "To stop: sudo systemctl stop linkedin-research"
    echo ""
else
    print_error "Failed to start service. Check logs with: sudo journalctl -u linkedin-research -f"
    exit 1
fi

print_success "Native Raspberry Pi deployment completed! 🎉"
