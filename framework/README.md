# LinkedIn Research Framework

A comprehensive automation platform for LinkedIn research and account management, designed for enterprise research teams. This system provides AI-powered persona generation, automated account creation, and intelligent interaction capabilities while maintaining compliance with research protocols.

## 🚀 Features

### Core Capabilities
- **AI-Powered Persona Generation**: Create realistic professional personas using OpenAI
- **Automated Account Creation**: Streamlined LinkedIn account setup with verification
- **Intelligent Automation**: Human-like interaction patterns with anti-detection measures
- **Real-time Monitoring**: Live dashboard with service health and performance metrics
- **Multi-Service Integration**: 5SIM, EmailOnDeck, Geonode proxy support
- **Enterprise Security**: Comprehensive security controls and audit logging

### Dashboard Features
- **Account Management**: Monitor and control LinkedIn research accounts
- **Automation Control**: Manage and schedule automation jobs
- **Service Monitoring**: Real-time health checks for external services
- **AI Content Generation**: Create professional profiles and content
- **Settings Management**: Configure API keys and system preferences

## 📋 Prerequisites

### System Requirements
- **Operating System**: Linux (Ubuntu 20.04+ recommended)
- **Memory**: Minimum 4GB RAM (8GB+ recommended)
- **Storage**: 10GB+ available space
- **Network**: Stable internet connection

### Required Software
- **Docker**: Version 20.10+
- **Docker Compose**: Version 2.0+
- **Git**: For cloning the repository

### API Services
You'll need accounts and API keys for:
1. **OpenAI**: For AI content generation ([Get API Key](https://platform.openai.com/api-keys))
2. **5SIM**: For SMS verification ([Get API Key](https://5sim.net/settings/api))
3. **EmailOnDeck**: For email verification ([Get API Key](https://www.emailondeck.com/api))
4. **Geonode**: For proxy services ([Get Credentials](https://geonode.com/))

## 🛠️ Installation

### Quick Start

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd linkedin-research-framework
   ```

2. **Run the deployment script**:
   ```bash
   ./deploy.sh
   ```

3. **Follow the prompts** to configure API keys and start the system.

### Manual Installation

1. **Create environment file**:
   ```bash
   cp .env.example .env
   ```

2. **Edit configuration**:
   ```bash
   nano .env
   ```
   
   Update with your API keys:
   ```env
   OPENAI_API_KEY=your_openai_api_key
   FIVESIM_API_KEY=your_5sim_api_key
   EMAILONDECK_API_KEY=your_emailondeck_api_key
   GEONODE_CREDENTIALS=username:password@endpoint:port
   ```

3. **Build and start services**:
   ```bash
   docker-compose up -d
   ```

## 🎯 Usage

### Accessing the Dashboard

Once deployed, access the system at:
- **Web Dashboard**: http://localhost
- **API Endpoint**: http://localhost/api

### Initial Setup

1. **Configure API Keys**: Go to Settings → API Keys and enter your service credentials
2. **Create Personas**: Use the AI Persona Generator to create professional profiles
3. **Setup Accounts**: Create and manage LinkedIn research accounts
4. **Configure Automation**: Set up automation jobs with safety limits

### Dashboard Navigation

#### 🏠 Dashboard
- Overview of system status and recent activity
- Quick access to key metrics and alerts
- Real-time updates on automation progress

#### 👥 Accounts
- Manage LinkedIn research accounts
- Monitor account status and activity
- View connection and engagement metrics

#### 🤖 AI Personas
- Generate realistic professional personas
- Customize industry, experience, and location
- Export personas for account creation

#### ⚡ Automation
- Create and manage automation jobs
- Monitor job progress and success rates
- Configure safety limits and timing

#### 🔧 Services
- Monitor external service health
- View response times and uptime
- Check API quotas and usage

#### ⚙️ Settings
- Configure API keys and credentials
- Set automation parameters
- Manage security and notifications

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for content generation | Yes |
| `FIVESIM_API_KEY` | 5SIM API key for SMS verification | Yes |
| `EMAILONDECK_API_KEY` | EmailOnDeck API key for email verification | Yes |
| `GEONODE_CREDENTIALS` | Geonode proxy credentials | Yes |
| `DATABASE_URL` | Database connection string | No |
| `FLASK_SECRET_KEY` | Flask session secret key | No |
| `SESSION_TIMEOUT` | Session timeout in seconds | No |

### Automation Settings

Configure automation behavior in the Settings panel:

- **Max Concurrent Jobs**: Limit simultaneous automation tasks
- **Default Delay**: Time between automation actions
- **Retry Attempts**: Number of retries for failed actions
- **Safety Limits**: Enable daily/hourly action limits
- **Human-like Timing**: Add random delays to mimic human behavior

### Security Configuration

- **Session Timeout**: Automatic logout after inactivity
- **Two-Factor Authentication**: Additional security layer
- **IP Whitelisting**: Restrict access to specific IP addresses
- **Audit Logging**: Log all user actions for security

## 🔒 Security & Compliance

### Research Compliance
This system is designed for legitimate enterprise research purposes in accordance with:
- Corporate research team guidelines
- LinkedIn Terms of Service for research activities
- Data protection and privacy regulations

### Security Features
- **Encrypted Data Storage**: Sensitive data encrypted at rest
- **Secure API Communication**: HTTPS/TLS encryption
- **Access Controls**: Role-based permissions and authentication
- **Audit Logging**: Comprehensive activity tracking
- **Rate Limiting**: Protection against abuse and detection

### Best Practices
1. **Regular Updates**: Keep system and dependencies updated
2. **Strong Passwords**: Use complex passwords and 2FA
3. **Network Security**: Configure firewall and VPN access
4. **Monitoring**: Regular review of logs and alerts
5. **Backup**: Regular backup of configuration and data

## 📊 Monitoring & Maintenance

### Health Checks
The system includes built-in health monitoring:
- **Service Status**: Real-time monitoring of external services
- **Performance Metrics**: Response times and success rates
- **Resource Usage**: CPU, memory, and storage monitoring
- **Error Tracking**: Automatic error detection and alerting

### Log Management
Access logs for troubleshooting:
```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f linkedin-research-backend
docker-compose logs -f linkedin-research-frontend
```

### Backup & Recovery
Regular backup recommendations:
1. **Database**: Backup SQLite database file
2. **Configuration**: Backup .env and docker-compose.yml
3. **Logs**: Archive important log files
4. **SSL Certificates**: Backup SSL certificates if using HTTPS

## 🚨 Troubleshooting

### Common Issues

#### Services Won't Start
```bash
# Check service status
docker-compose ps

# View error logs
docker-compose logs

# Restart services
docker-compose restart
```

#### API Connection Issues
1. Verify API keys in .env file
2. Check service status in dashboard
3. Review network connectivity
4. Validate API quotas and limits

#### Performance Issues
1. Monitor resource usage: `docker stats`
2. Check available disk space: `df -h`
3. Review automation job limits
4. Optimize concurrent job settings

#### Database Issues
```bash
# Reset database (WARNING: This will delete all data)
docker-compose down
rm -f data/linkedin_research.db
docker-compose up -d
```

### Getting Help

1. **Check Logs**: Always start with system logs
2. **Review Configuration**: Verify all settings and API keys
3. **Test Connectivity**: Ensure external services are accessible
4. **Monitor Resources**: Check system resource usage

## 🔄 Updates & Maintenance

### Updating the System
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Regular Maintenance
- **Weekly**: Review logs and performance metrics
- **Monthly**: Update dependencies and security patches
- **Quarterly**: Review and rotate API keys
- **Annually**: Security audit and compliance review

## 📝 API Documentation

### Authentication
All API endpoints require authentication via session cookies or API tokens.

### Core Endpoints

#### Account Management
- `GET /api/accounts` - List all accounts
- `POST /api/accounts` - Create new account
- `PUT /api/accounts/{id}` - Update account
- `DELETE /api/accounts/{id}` - Delete account

#### Automation Jobs
- `GET /api/jobs` - List automation jobs
- `POST /api/jobs` - Create new job
- `PUT /api/jobs/{id}` - Update job
- `DELETE /api/jobs/{id}` - Cancel job

#### AI Content Generation
- `POST /api/ai/persona` - Generate persona
- `POST /api/ai/content` - Generate content
- `POST /api/ai/profile` - Generate profile text

#### Service Management
- `GET /api/services/status` - Service health check
- `POST /api/services/test` - Test service connection
- `GET /api/services/metrics` - Service metrics

### WebSocket Events
Real-time updates via WebSocket:
- `job_status_update` - Automation job progress
- `service_health_update` - Service status changes
- `account_activity` - Account activity notifications

## 📄 License

This software is provided for enterprise research purposes. Please ensure compliance with all applicable terms of service and regulations.

## 🤝 Support

For technical support and questions:
1. Review this documentation
2. Check the troubleshooting section
3. Review system logs
4. Contact your system administrator

---

**⚠️ Important Notice**: This system is designed for legitimate research purposes only. Users are responsible for ensuring compliance with all applicable terms of service, privacy regulations, and ethical guidelines.

