#!/bin/bash

# LinkedIn Research Framework - Docker Build Script
# Builds and pushes Docker images for production deployment

set -e

echo "🏗️  LinkedIn Research Framework - Docker Build Script"
echo "======================================================"

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

# Default values
IMAGE_NAME=${IMAGE_NAME:-"linkedin-research-framework"}
TAG=${TAG:-"latest"}
REGISTRY=${REGISTRY:-""}
PUSH=${PUSH:-false}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --name=*)
      IMAGE_NAME="${1#*=}"
      shift
      ;;
    --tag=*)
      TAG="${1#*=}"
      shift
      ;;
    --registry=*)
      REGISTRY="${1#*=}"
      shift
      ;;
    --push)
      PUSH=true
      shift
      ;;
    --help)
      echo "Usage: $0 [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --name=NAME        Docker image name (default: linkedin-research-framework)"
      echo "  --tag=TAG          Docker image tag (default: latest)"
      echo "  --registry=URL     Docker registry URL (optional)"
      echo "  --push             Push image to registry after build"
      echo "  --help             Show this help message"
      echo ""
      echo "Examples:"
      echo "  $0 --push"
      echo "  $0 --registry=your-registry.com --name=linkedin-research --tag=v1.0.0 --push"
      exit 0
      ;;
    *)
      print_error "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Full image name
FULL_IMAGE_NAME="${REGISTRY}${REGISTRY:+/}${IMAGE_NAME}:${TAG}"

print_status "Building Docker image: ${FULL_IMAGE_NAME}"

# Check if .env file exists
if [ ! -f .env ]; then
    print_error "Environment file .env not found. Please create it with your API keys."
    exit 1
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

# Build the Docker image
print_status "Building production Docker image..."
docker build -f Dockerfile -t "${FULL_IMAGE_NAME}" .

print_success "Docker image built successfully: ${FULL_IMAGE_NAME}"

# Get image size
IMAGE_SIZE=$(docker images "${FULL_IMAGE_NAME}" --format "table {{.Size}}" | tail -n1)
print_status "Image size: ${IMAGE_SIZE}"

# Push to registry if requested
if [ "$PUSH" = true ]; then
    print_status "Pushing image to registry..."

    # Check if we're logged into the registry
    if [ -n "$REGISTRY" ]; then
        print_status "Make sure you're logged into the registry: docker login ${REGISTRY}"
    fi

    docker push "${FULL_IMAGE_NAME}"
    print_success "Image pushed successfully!"
fi

# Show deployment instructions
echo ""
echo "🎉 Docker image ready for deployment!"
echo ""
echo "📋 Deployment Options:"
echo ""
echo "1. 📦 Portainer Deployment:"
echo "   - Use docker-compose.prod.yml"
echo "   - Update image name to: ${FULL_IMAGE_NAME}"
echo ""
echo "2. 🐳 Docker Compose Deployment:"
echo "   docker run -d \\"
echo "     --name linkedin-research \\"
echo "     -p 8080:80 -p 5001:5000 \\"
echo "     --env-file .env \\"
echo "     -v ./data:/app/data \\"
echo "     -v ./logs:/app/logs \\"
echo "     ${FULL_IMAGE_NAME}"
echo ""
echo "3. 🐳 Kubernetes Deployment:"
echo "   - Use the image in your Kubernetes manifests"
echo "   - Image: ${FULL_IMAGE_NAME}"
echo ""
echo "📝 Remember to:"
echo "   - Set up proper environment variables"
echo "   - Configure SSL certificates for production"
echo "   - Set up proper volume mounts for data persistence"
echo "   - Configure firewall rules"

print_success "Build completed successfully! 🚀"






