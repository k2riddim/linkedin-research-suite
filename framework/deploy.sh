#!/bin/bash

# LinkedIn Research Framework Deployment Script
# This script helps deploy the LinkedIn Research Framework system

set -e

echo "🚀 LinkedIn Research Framework Deployment Script"
echo "================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_warning "Docker is not installed. Installing Docker for Raspberry Pi..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    print_warning "Please log out and back in, or run 'newgrp docker' for Docker to work properly"
    sleep 3
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_warning "Docker Compose is not installed. Installing..."
    sudo apt-get update
    sudo apt-get install -y docker-compose-plugin
fi

# Deployment method selection
print_status "Choose your deployment method:"
echo "1. 🐳 Docker deployment (for NAS/Portainer - slower on Pi)"
echo "2. 🔧 Native Framework deployment (backend + static frontend)"
echo "3. 📊 Native Dashboard deployment (React frontend only)"
echo "4. 🤝 Deploy BOTH Framework + Dashboard (recommended for Pi)"
echo "5. 📦 Build Docker image for registry/NAS deployment"
echo "6. Exit"
read -p "Choose deployment method (1/2/3/4/5/6): " -n 1 -r
echo
case $REPLY in
    1)
        print_status "Using Docker deployment..."
        ;;
    2)
        print_status "Switching to native Framework deployment..."
        ./deploy-native.sh
        exit 0
        ;;
    3)
        print_status "Dashboard deployment requires Framework backend. Running dual deployment..."
        cd /home/chorizo/projects
        ./deploy-both.sh
        exit 0
        ;;
    4)
        print_status "Switching to dual deployment (Framework + Dashboard)..."
        cd /home/chorizo/projects
        ./deploy-both.sh
        exit 0
        ;;
    5)
        print_status "Building Docker image for registry deployment..."
        ./build-docker.sh --push
        exit 0
        ;;
    6)
        print_status "Exiting deployment script"
        exit 0
        ;;
    *)
        print_error "Invalid option. Exiting."
        exit 1
        ;;
esac

# Raspberry Pi specific checks (only for Docker deployment)
print_status "Checking Raspberry Pi compatibility..."
TOTAL_MEM=$(free -m | awk '/^Mem:/{print $2}')
if [ $TOTAL_MEM -lt 2048 ]; then
    print_warning "Warning: Only ${TOTAL_MEM}MB RAM detected. 4GB+ recommended for optimal performance."
    read -p "Continue with Docker anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Consider using native deployment instead:"
        echo "  ./deploy-native.sh"
        exit 1
    fi
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p data logs ssl

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

# Security Configuration
SESSION_TIMEOUT=3600
ENABLE_RATE_LIMITING=true
MAX_REQUESTS_PER_MINUTE=60
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

# Build and start services
print_status "Building Docker images..."
docker-compose build

print_status "Starting services..."
docker-compose up -d

# Wait for services to be ready
print_status "Waiting for services to start..."
sleep 10

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    print_success "Services started successfully!"
    echo ""
    echo "🎉 LinkedIn Research Framework is now running!"
    echo ""
    echo "🌐 Access the dashboard at: http://localhost:8080"
    echo "🔌 API endpoint: http://localhost:5001/api"
    echo "🔒 HTTPS (if configured): https://localhost:8443"
    echo ""
    echo "To view logs: docker-compose logs -f"
    echo "To stop services: docker-compose down"
    echo "To restart services: docker-compose restart"
    echo ""
    print_warning "Important Security Notes:"
    echo "1. Change default passwords and API keys"
    echo "2. Enable HTTPS in production"
    echo "3. Configure firewall rules"
    echo "4. Regular security updates"
    echo "5. Monitor system logs"
else
    print_error "Failed to start services. Check logs with: docker-compose logs"
    exit 1
fi

# Create systemd service for auto-start (optional)
read -p "Do you want to create a systemd service for auto-start? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Creating systemd service..."
    
    sudo tee /etc/systemd/system/linkedin-research.service > /dev/null << EOF
[Unit]
Description=LinkedIn Research Framework
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$(pwd)
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable linkedin-research.service
    print_success "Systemd service created and enabled!"
    echo "The service will start automatically on boot."
fi

print_success "Deployment completed successfully! 🎉"

