# LinkedIn Research Framework - Docker Deployment Guide

This guide covers Docker deployment options for different environments.

## 📋 Deployment Methods

### 1. 🐧 Raspberry Pi Development (Native)
**Best for**: Development on Raspberry Pi
**Performance**: Optimized for low-resource environment

```bash
# Native deployment (recommended for Pi development)
./deploy-native.sh

# Access at: http://localhost:8080
# API at: http://localhost:5001/api
```

### 2. 🐳 Raspberry Pi Development (Docker)
**Best for**: Testing Docker setup on Pi
**Performance**: Slower due to container overhead

```bash
# Docker deployment on Pi
./deploy.sh
# Choose option 1 when prompted
```

### 3. 📦 NAS/Portainer Production (Docker)
**Best for**: Production deployment on powerful hardware

```bash
# Build and push Docker image
./build-docker.sh --registry=your-registry.com --name=linkedin-research --tag=v1.0.0 --push

# On your NAS/Portainer, use docker-compose.prod.yml
```

## 🏗️ Docker Compose Files

### docker-compose.yml
- **Purpose**: Simple development setup
- **Use case**: Local development and testing
- **Features**: Hot reload, debug logging

### docker-compose.dev.yml
- **Purpose**: Advanced development setup
- **Use case**: Full development environment with database
- **Features**: PostgreSQL, Redis, debugging, Adminer

```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# With database
docker-compose -f docker-compose.dev.yml --profile database up -d
```

### docker-compose.prod.yml
- **Purpose**: Production deployment
- **Use case**: NAS, cloud servers, Portainer
- **Features**: Resource limits, health checks, optimized for production

```bash
# Start production environment
docker-compose -f docker-compose.prod.yml up -d

# With Redis caching
docker-compose -f docker-compose.prod.yml --profile cache up -d
```

## 🏗️ Building Docker Images

### Basic Build
```bash
# Build for local use
./build-docker.sh

# Build with custom name
./build-docker.sh --name=my-linkedin-research --tag=v1.0.0
```

### Build and Push to Registry
```bash
# Push to Docker Hub
./build-docker.sh --push

# Push to private registry
./build-docker.sh --registry=my-registry.com --push

# Full example
./build-docker.sh \
  --registry=your-registry.com \
  --name=linkedin-research \
  --tag=v1.0.0 \
  --push
```

## 📦 Portainer Deployment

### Step 1: Build and Push Image
```bash
# On your development machine
./build-docker.sh --registry=your-registry.com --tag=v1.0.0 --push
```

### Step 2: Deploy in Portainer

1. **Create Stack** in Portainer
2. **Use docker-compose.prod.yml** content
3. **Update image name** to your pushed image:
   ```yaml
   image: your-registry.com/linkedin-research-framework:v1.0.0
   ```
4. **Configure environment variables** (see Environment section)
5. **Set up volumes** for data persistence

### Portainer docker-compose.yml Example:
```yaml
version: '3.8'

services:
  linkedin-research-backend:
    image: your-registry.com/linkedin-research-framework:v1.0.0
    restart: unless-stopped
    ports:
      - "5001:5000"
    environment:
      - FLASK_ENV=production
      - FLASK_SECRET_KEY=your-secret-key
      - DATABASE_URL=sqlite:///data/linkedin_research.db
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - FIVESIM_API_KEY=${FIVESIM_API_KEY}
      - EMAILONDECK_API_KEY=${EMAILONDECK_API_KEY}
      - GEONODE_CREDENTIALS=${GEONODE_CREDENTIALS}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M

  linkedin-research-frontend:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "8080:80"
    volumes:
      - ./static:/usr/share/nginx/html
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - linkedin-research-backend
    deploy:
      resources:
        limits:
          memory: 256M
        reservations:
          memory: 64M

networks:
  default:
    driver: bridge
```

## ⚙️ Environment Configuration

### Required Environment Variables
```bash
# API Keys (REQUIRED)
OPENAI_API_KEY=your_openai_key
FIVESIM_API_KEY=your_5sim_key
EMAILONDECK_API_KEY=your_emailondeck_key
GEONODE_CREDENTIALS=username:password@endpoint:port

# Flask Configuration
FLASK_ENV=production
FLASK_SECRET_KEY=your-secret-key

# Database Configuration
DATABASE_URL=sqlite:///data/linkedin_research.db

# PostgreSQL Configuration (Optional - overrides DATABASE_URL)
POSTGRES_HOST=your-postgres-server    # Can be IP address
POSTGRES_IP=192.168.1.100             # Alternative to POSTGRES_HOST
POSTGRES_DB=linkedin_research
POSTGRES_USER=linkedin_user
POSTGRES_PASSWORD=your_postgres_password
POSTGRES_PORT=5432

# Security
SESSION_TIMEOUT=3600
ENABLE_RATE_LIMITING=true
MAX_REQUESTS_PER_MINUTE=60

# Docker Configuration
BACKEND_PORT=5001
FRONTEND_HTTP_PORT=8080
FRONTEND_HTTPS_PORT=8443
```

### Port Configuration
- **5001**: Flask backend API
- **8080**: Nginx frontend (HTTP)
- **8443**: Nginx frontend (HTTPS - if configured)

## 🗂️ Volume Management

### Persistent Data
```yaml
volumes:
  - ./data:/app/data      # SQLite database
  - ./logs:/app/logs      # Application logs
  - ./ssl:/app/ssl        # SSL certificates
  - ./static:/app/static  # Static files
```

### Backup Strategy
```bash
# Backup data
tar -czf backup-$(date +%Y%m%d).tar.gz data/ logs/

# Backup database only
cp data/linkedin_research.db ./backups/
```

## 🔧 Maintenance

### Updating Images
```bash
# Build new version
./build-docker.sh --tag=v1.1.0 --push

# In Portainer, update stack with new image tag
# Or redeploy with new tag
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

### Logs
```bash
# View logs
docker-compose -f docker-compose.prod.yml logs -f

# View specific service logs
docker-compose -f docker-compose.prod.yml logs -f linkedin-research-backend
```

### Scaling
```bash
# Scale backend (if needed)
docker-compose -f docker-compose.prod.yml up -d --scale linkedin-research-backend=2

# Note: Requires sticky sessions for multiple backends
```

## 🚨 Troubleshooting

### Common Issues

#### Port Conflicts
```bash
# Check used ports
ss -tlnp | grep :5001
ss -tlnp | grep :8080

# Change ports in docker-compose.prod.yml
BACKEND_PORT=5002
FRONTEND_HTTP_PORT=8081
```

#### Memory Issues
```bash
# Monitor memory usage
docker stats

# Adjust memory limits in docker-compose.prod.yml
deploy:
  resources:
    limits:
      memory: 512M  # Reduce if needed
```

#### Permission Issues
```bash
# Fix volume permissions
sudo chown -R 1000:1000 data/ logs/
```

## 📊 Monitoring

### Health Checks
- **Backend**: http://localhost:5001/api/health
- **Frontend**: http://localhost:8080/health

### Metrics
```bash
# Container resource usage
docker stats

# Application logs
docker-compose -f docker-compose.prod.yml logs --tail=100 -f
```

## 🔒 Security

### Production Checklist
- [ ] Use strong `FLASK_SECRET_KEY`
- [ ] Enable HTTPS with SSL certificates
- [ ] Set up proper firewall rules
- [ ] Use environment variables for secrets
- [ ] Regular security updates
- [ ] Monitor logs for suspicious activity

### SSL Configuration
```bash
# Place certificates in ssl/ directory
ssl/
├── cert.pem
└── key.pem

# Update nginx.conf for SSL
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    # ... rest of SSL configuration
}
```

---

## 🚀 Quick Start for Portainer

1. **Build and push image**:
   ```bash
   ./build-docker.sh --registry=your-registry.com --tag=v1.0.0 --push
   ```

2. **Create Portainer stack** with `docker-compose.prod.yml`

3. **Configure environment variables** in Portainer

4. **Set up volumes** for data persistence

5. **Deploy** and access at `http://your-nas:8080`

That's it! 🎉
