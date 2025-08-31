# Solar Sync - Professional Solar Monitoring System

A modern, real-time solar monitoring system built with FastAPI, designed for local development with seamless Raspberry Pi deployment.

## 🌟 Features

- **Real-time Dashboard** - Live solar system monitoring with WebSocket updates
- **Responsive Design** - Beautiful yellow-themed UI that works on all devices
- **Data Simulation** - Realistic solar data for development and testing
- **Database Foundation** - SQLite with proper schema and migrations
- **Automated Deployment** - One-command Pi deployment with health checks
- **Hardware Ready** - Built with Pi constraints in mind from day one

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Git
- Docker (optional but recommended)

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/ElectricApple/solar-pi.git
   cd solar-pi
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements-dev.txt
   ```

4. **Start development server**
   ```bash
   python -m uvicorn app.main:app --reload
   ```

5. **Access the application**
   - Dashboard: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

### Docker Development

```bash
# Start with Docker
docker-compose -f docker-compose.dev.yml up

# Access at http://localhost:8000
# Database admin at http://localhost:8080
```

## 📊 Dashboard Features

### Real-time Metrics
- **Solar Power** - Current solar generation
- **Battery Status** - State of charge and power flow
- **Load Power** - Current consumption
- **Grid Power** - Import/export status

### Interactive Charts
- Real-time power flow visualization
- Historical data analysis
- Configurable time ranges

### System Status
- Temperature monitoring
- Efficiency tracking
- Event logging

## 🏗️ Project Structure

```
solar-sync/
├── app/                    # Main application
│   ├── config/            # Configuration management
│   ├── database/          # Database models and migrations
│   ├── routers/           # API endpoints
│   ├── services/          # Business logic
│   ├── static/            # CSS, JS, images
│   └── templates/         # HTML templates
├── deployment/            # Deployment scripts and configs
│   ├── docker/           # Docker configurations
│   └── scripts/          # Pi deployment scripts
├── tests/                # Test suite
└── data/                 # Database files (created automatically)
```

## 🔧 Configuration

### Environment Variables

Copy `env.example` to `.env` and customize:

```bash
# Environment
ENVIRONMENT=development
SIMULATE_HARDWARE=true
LOG_LEVEL=DEBUG

# Database
DATABASE_URL=sqlite:///./data/solar-sync-dev.db

# WebSocket
WEBSOCKET_UPDATE_INTERVAL=2
MAX_CHART_POINTS=5000
```

### Development vs Production

The system automatically detects the environment:
- **Development**: Fast updates, simulated data, debug logging
- **Production**: Optimized for Pi, real hardware, info logging

## 🥧 Raspberry Pi Deployment

### Prerequisites

1. **Pi Setup**
   - Raspberry Pi with Python 3.9+
   - SSH enabled
   - SSH key authentication configured

2. **Local Setup**
   - rsync installed
   - SSH access to Pi

### Deploy to Pi

```bash
# Deploy to default Pi (raspberrypi.local)
./deployment/scripts/deploy-to-pi.sh

# Deploy to specific Pi
./deployment/scripts/deploy-to-pi.sh pi@192.168.1.100

# Deploy with custom user
./deployment/scripts/deploy-to-pi.sh pi@192.168.1.100 myuser
```

### Pi Management

```bash
# Check service status
ssh pi@raspberrypi.local "sudo systemctl status solar-sync"

# View logs
ssh pi@raspberrypi.local "sudo journalctl -u solar-sync -f"

# Restart service
ssh pi@raspberrypi.local "sudo systemctl restart solar-sync"
```

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test
python -m pytest tests/test_api.py -v

# Run with coverage
python -m pytest tests/ --cov=app --cov-report=html
```

## 📈 API Endpoints

### Dashboard
- `GET /` - Main dashboard
- `GET /dashboard/current` - Current energy data
- `GET /dashboard/summary` - Dashboard summary
- `GET /dashboard/chart-data` - Historical chart data
- `WebSocket /dashboard/ws` - Real-time updates

### Charts
- `GET /charts/daily` - Daily aggregated data
- `GET /charts/weekly` - Weekly aggregated data
- `GET /charts/monthly` - Monthly aggregated data
- `GET /charts/analytics` - Analytics summary

### Control
- `GET /control/devices` - List devices
- `POST /control/devices/{id}/control` - Control device
- `GET /control/system/status` - System status

### Settings
- `GET /settings/` - List all settings
- `PUT /settings/{key}` - Update setting
- `GET /settings/system/info` - System information

## 🎨 UI Components

### Design System
- **Yellow Theme** - Professional solar branding
- **Responsive Grid** - Mobile-first design
- **Interactive Cards** - Hover effects and animations
- **Real-time Updates** - WebSocket-powered live data

### Components
- Metric cards with icons and gradients
- Real-time charts with Chart.js
- Event log with severity indicators
- Navigation with active states

## 🔌 Hardware Integration

### Current Support
- **Simulated Data** - Realistic solar system simulation
- **Database Storage** - Historical data persistence
- **WebSocket Updates** - Real-time data streaming

### Future Hardware Support
- RS485 communication
- Modbus protocol
- Inverter integration
- Battery monitoring
- Temperature sensors

## 🚀 Development Workflow

1. **Local Development**
   ```bash
   # Start development server
   python -m uvicorn app.main:app --reload
   
   # Make changes and see them instantly
   # Test with simulated data
   ```

2. **Docker Testing**
   ```bash
   # Test in Pi-like environment
   docker-compose -f docker-compose.dev.yml up
   ```

3. **Pi Deployment**
   ```bash
   # Deploy when ready
   ./deployment/scripts/deploy-to-pi.sh
   ```

## 🛠️ Development Commands

```bash
# Start development server
python -m uvicorn app.main:app --reload

# Run tests
python -m pytest tests/ -v

# Format code
black app/ tests/

# Lint code
flake8 app/ tests/

# Type checking
mypy app/

# Database migrations
python -c "from app.database.migrations import run_migrations; run_migrations()"
```

## 📝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Support

- **Issues**: [GitHub Issues](https://github.com/ElectricApple/solar-pi/issues)
- **Documentation**: [API Docs](http://localhost:8000/docs)
- **Community**: Join our discussions

## 🎯 Roadmap

- [ ] Hardware integration (RS485, Modbus)
- [ ] Advanced analytics and reporting
- [ ] Mobile app companion
- [ ] Cloud data sync
- [ ] Multi-site monitoring
- [ ] Alert system
- [ ] Energy optimization algorithms

---

**Built with ❤️ for the solar energy community**
