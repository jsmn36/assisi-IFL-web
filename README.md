# Assisi Social Desktop Application

Professional Social Platform with Hybrid Database Support

## 🚀 Features

- ✅ Desktop application (Windows, macOS, Linux)
- ✅ Hybrid database (SQLite default, PostgreSQL optional)
- ✅ Professional UI with dashboard and charts
- ✅ Complete operations (reservations, check-in, housekeeping, audit)
- ✅ Offline-capable with local database
- ✅ Multi-user support with PostgreSQL

## 🛠️ Tech Stack

### Backend
- **Language**: Python 3.12
- **Framework**: FastAPI 0.104.1
- **Database**: SQLAlchemy 2.0 + Alembic
- **Testing**: pytest

### Frontend
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **UI Library**: shadcn/ui + Tailwind CSS
- **State**: React Query + Zustand
- **Charts**: Recharts

### Desktop
- **Framework**: Electron 28
- **Platforms**: Windows, macOS, Linux

## 📦 Installation

### Prerequisites
- Python 3.12+
- Node.js 18+
- Git

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd assisi-social-desktop
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python3.12 -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   ```

4. **Electron Setup**
   ```bash
   cd electron
   npm install
   ```

## 🏃 Running the Application

### Development Mode

**Terminal 1 - Backend**:
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

**Terminal 2 - Frontend**:
```bash
cd frontend
npm run dev
```

**Terminal 3 - Electron**:
```bash
cd electron
npm start
```

### Production Build

```bash
# Build frontend
cd frontend
npm run build

# Package Electron app
cd electron
npm run build
```

## 💾 Database Configuration

### SQLite (Default)
No configuration needed! Database created automatically at:
- **Windows**: `%USERPROFILE%/.pms-hotel/pms.db`
- **macOS**: `~/.pms-hotel/pms.db`
- **Linux**: `~/.pms-hotel/pms.db`

### PostgreSQL (Optional)
For multi-user or cloud deployment:

1. Create `.env` file in `backend/`:
   ```env
   DATABASE_URL=postgresql://user:password@host:5432/dbname
   ```

2. Restart the application

## 🧪 Testing

**Backend Tests**:
```bash
cd backend
pytest
pytest --cov=app  # with coverage
```

**Frontend Tests**:
```bash
cd frontend
npm test
```

## 📚 Documentation

- [Tech Stack Specification](docs/TECH_STACK.md)
- [Architecture Overview](docs/ARCHITECTURE.md)
- [API Documentation](http://localhost:8000/docs) (when running)
- [Development Guide](docs/DEVELOPMENT.md)

## 📊 Project Status

- [x] Day 0: Planning Complete (1,544 requirements documented)
- [x] Day 1: Foundation Setup ✅ **COMPLETE**
- [ ] Week 1-2: Core Models (59 hours)
- [ ] Week 3: State Machines (38 hours)
- [ ] Week 4: Gate Framework (22 hours)
- [ ] Week 5-6: Individual Gates (94 hours)
- [ ] Week 7-8: Business Services (106 hours)
- [ ] Week 9-10: API + Frontend Setup (100 hours)
- [ ] Week 11-13: Professional UI (140 hours)
- [ ] Week 14-15: Electron Integration (40 hours)
- [ ] Week 16-17: Testing (88 hours)
- [ ] Week 18: Deployment (36 hours)

**Total**: 884 hours / 18 weeks

## 📝 License

Private - All Rights Reserved

---

**Version**: 0.1.0  
**Last Updated**: February 5, 2026  
**Status**: ✅ Foundation Complete

## 🔒 Rate Limiting

The API implements comprehensive rate limiting:

- **IP-Based**: 60 requests/minute
- **User-Based**: Tier-based (100-1000/min)
- **Endpoint-Specific**: Critical endpoints have stricter limits

See [Rate Limiting Documentation](docs/RATE_LIMITING.md) for details.

### Rate Limit Headers
```
X-RateLimit-Limit: Maximum requests
X-RateLimit-Remaining: Requests remaining
X-RateLimit-Reset: Reset timestamp
Retry-After: Seconds to wait (on 429)
```

## ⚙️ Background Jobs

The system uses Celery for background task processing:

- **Email sending**: Async email delivery
- **Report generation**: Heavy reports run in background
- **Scheduled tasks**: Daily reports, reminders, cleanup
- **Data exports**: Large CSV/JSON exports

See [Background Jobs Documentation](docs/BACKGROUND_JOBS.md) for details.

### Running Workers
```bash
# Start worker
./run_celery_worker.sh

# Start scheduler
./run_celery_beat.sh

# Start monitoring UI
./run_flower.sh
```

Monitoring UI: http://localhost:5555
