# LinkedIn Research Suite

A consolidated research platform combining LinkedIn automation framework with a modern dashboard interface.

## Project Structure

```
linkedin-research-suite/
├── framework/           # Backend Python application
│   ├── src/            # Python source code
│   ├── data/           # Database and data files
│   ├── logs/           # Application logs
│   ├── requirements.txt # Python dependencies
│   └── ...             # Docker, deployment scripts
├── dashboard/          # Frontend React application
│   ├── src/           # React source code
│   ├── package.json   # Node.js dependencies
│   └── ...            # Vite configuration
├── requirements.txt   # Consolidated Python dependencies
├── .env              # Environment configuration
└── .gitignore        # Git ignore rules
```

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- pnpm (for frontend)

### Setup

1. **Clone and enter the project:**
   ```bash
   git clone <repository-url>
   cd linkedin-research-suite
   ```

2. **Set up the backend (framework):**
   ```bash
   cd framework
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Set up the frontend (dashboard):**
   ```bash
   cd dashboard
   pnpm install
   ```

4. **Configure environment:**
   ```bash
   cp env.template .env
   # Edit .env with your API keys and configuration
   ```

### Running the Application

#### Option 1: Unified Server (Recommended)
```bash
# Start both backend and frontend together
npm start

# For development mode
npm run dev

# For production mode  
npm run prod
```

#### Option 2: Manual Startup
**Backend (from framework/ directory):**
```bash
python src/main.py
```

**Frontend (from dashboard/ directory):**
```bash
pnpm dev
```

The backend will run on `http://localhost:5001` and the frontend on `http://localhost:5173`.

### Service Management

The unified server can be managed as a systemd service:

```bash
# Install service
sudo cp linkedin_research.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable linkedin_research

# Control service
sudo systemctl start linkedin_research
sudo systemctl stop linkedin_research
sudo systemctl status linkedin_research

# View logs
npm run logs
# or
sudo journalctl -u linkedin_research -f
```

## Features

### Framework (Backend)
- LinkedIn account creation automation
- AI-powered persona generation
- Proxy rotation and verification services
- Real-time progress tracking via WebSockets
- RESTful API for all operations

### Dashboard (Frontend)
- Modern React interface with Tailwind CSS
- Real-time account creation monitoring
- Persona management and generation
- Service status monitoring
- Analytics and reporting

## Configuration

Key environment variables:
- `OPENAI_API_KEY`: Required for AI content generation
- `FIVESIM_API_KEY`: Required for SMS verification
- `EMAILONDECK_API_KEY`: Required for email verification
- `GEONODE_CREDENTIALS`: Required for proxy rotation
- `DATABASE_URL`: Database connection string

## Development

### Backend Development
```bash
cd framework
source venv/bin/activate
python src/main.py
```

### Frontend Development
```bash
cd dashboard
pnpm dev
```

### Docker Deployment
```bash
cd framework
docker-compose up
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

[Add your license information here]
