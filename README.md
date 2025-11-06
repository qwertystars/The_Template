# Full Stack Template - Production Ready

A comprehensive, production-grade full-stack application template designed for rapid development of MVPs, hackathon projects, and scalable applications.

## 🚀 Features

### Backend
- **FastAPI** with async/await support
- **PostgreSQL 15+** with async SQLAlchemy 2.0
- **Redis** for caching and session storage
- **Celery** for background tasks with Flower monitoring
- **JWT Authentication** with refresh tokens
- **OAuth 2.0** support (Google, GitHub)
- **Role-Based Access Control (RBAC)**
- **2FA/MFA** with TOTP
- **Email verification** and password reset flows
- **API versioning** (v1, v2 structure)
- **OpenAPI documentation** (Swagger UI)
- **WebSocket support** for real-time features

### Frontend
- **React 18** with TypeScript (strict mode)
- **Vite 5+** with optimized build configuration
- **shadcn/ui** components with Radix UI primitives
- **Tailwind CSS** with custom design tokens
- **TanStack Query** (React Query) for data fetching
- **Zustand** for state management
- **React Router v6** for routing
- **Zod** for runtime validation

### DevOps & Infrastructure
- **Docker** multi-stage builds
- **docker-compose** for local development
- **Kubernetes** manifests and Helm charts
- **Terraform** modules for AWS (VPC, ECS, RDS, S3, CloudFront)
- **GitHub Actions** CI/CD pipelines
- **Prometheus** for metrics
- **Grafana** for dashboards
- **OpenTelemetry** for distributed tracing
- **Sentry** for error tracking

### Security
- OWASP Top 10 protections
- Security headers configured
- CORS configuration
- SQL injection prevention
- XSS protection and CSP headers
- Rate limiting per user/IP
- Secrets management support
- Container scanning with Trivy
- SAST with Semgrep

### Testing
- Backend: pytest with fixtures and mocking
- Frontend: Vitest + React Testing Library
- E2E: Playwright
- Load testing: Locust
- Test coverage > 80% enforced

## 📋 Prerequisites

- **Docker** and **Docker Compose**
- **Node.js 20+** (for local frontend development)
- **Python 3.11+** (for local backend development)
- **Poetry** (Python dependency management)
- **Make** (for convenience commands)

## 🏃 Quick Start (< 5 minutes)

### 1. Clone the repository

```bash
git clone <repository-url>
cd The_Template
```

### 2. Copy environment files

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

### 3. Start all services

```bash
make up
```

This will start:
- PostgreSQL on port 5432
- Redis on port 6379
- Backend API (internal, accessed via Nginx)
- Frontend + API on port 80 (Nginx reverse proxy)
- Flower (Celery monitoring) on port 5555
- Prometheus on port 9090
- Grafana on port 3000

### 4. Access the application

**Everything is accessible on port 80:**
- **Frontend**: http://localhost
- **API Documentation**: http://localhost/api/docs
- **API Health**: http://localhost/api/health
- **Any API endpoint**: http://localhost/api/v1/...

**Monitoring services:**
- **Flower**: http://localhost:5555
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090

### 5. Run database migrations

```bash
make migrate
```

### 6. (Optional) Seed the database

```bash
make seed
```

## 📁 Project Structure

```
.
├── backend/                 # FastAPI backend
│   ├── alembic/            # Database migrations
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   │   └── v1/
│   │   │       ├── endpoints/
│   │   │       └── router.py
│   │   ├── core/           # Core configuration
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   ├── database.py
│   │   │   ├── cache.py
│   │   │   └── logging.py
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   ├── tasks/          # Celery tasks
│   │   └── main.py         # FastAPI app
│   ├── tests/              # Backend tests
│   ├── Dockerfile
│   └── pyproject.toml
│
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   │   └── ui/        # shadcn/ui components
│   │   ├── pages/         # Page components
│   │   ├── hooks/         # Custom hooks
│   │   ├── lib/           # Utilities
│   │   │   ├── api.ts     # API client
│   │   │   ├── auth.ts    # Auth utilities
│   │   │   └── utils.ts   # Helper functions
│   │   ├── stores/        # Zustand stores
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── tests/             # Frontend tests
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── vite.config.ts
│   └── package.json
│
├── infra/                 # Infrastructure as Code
│   ├── terraform/         # Terraform modules
│   ├── kubernetes/        # K8s manifests
│   └── helm/             # Helm charts
│
├── monitoring/            # Observability
│   ├── grafana/          # Grafana dashboards
│   ├── prometheus/       # Prometheus config
│   └── alertmanager/     # Alert rules
│
├── docs/                  # Documentation
│   ├── architecture/      # Architecture docs
│   ├── api/              # API documentation
│   └── deployment/       # Deployment guides
│
├── .github/              # GitHub Actions
│   └── workflows/
│
├── docker-compose.yml    # Development setup
├── Makefile             # Convenience commands
└── README.md            # This file
```

## 🛠️ Development

### Backend Development

```bash
# Install dependencies
cd backend
poetry install

# Activate virtual environment
poetry shell

# Run backend locally
uvicorn app.main:app --reload

# Run tests
pytest

# Run tests with coverage
pytest --cov=app --cov-report=html

# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

### Frontend Development

```bash
# Install dependencies
cd frontend
npm install

# Run frontend locally
npm run dev

# Run tests
npm test

# Run E2E tests
npm run test:e2e

# Build for production
npm run build
```

### Using Make Commands

```bash
# Start development environment
make dev

# Build all images
make build

# Start all services
make up

# Stop all services
make down

# View logs
make logs

# Run tests
make test

# Run linters
make lint

# Format code
make format

# Database migrations
make migrate

# Access backend shell
make shell-backend

# Access database
make shell-db
```

## 🔐 Authentication Flow

1. **Register**: POST `/api/v1/auth/register`
2. **Verify Email**: POST `/api/v1/auth/verify-email`
3. **Login**: POST `/api/v1/auth/login` (returns access + refresh tokens)
4. **Refresh Token**: POST `/api/v1/auth/refresh`
5. **Get Profile**: GET `/api/v1/users/me` (requires auth)

### Example: Login Request

```bash
curl -X POST "http://localhost/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=yourpassword"
```

## 🚀 Deployment

### Docker Compose (Production)

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Kubernetes

```bash
# Apply manifests
kubectl apply -f infra/kubernetes/

# Or use Helm
helm install myapp infra/helm/
```

### Terraform (AWS)

```bash
cd infra/terraform/environments/prod
terraform init
terraform plan
terraform apply
```

## 📊 Monitoring

### Prometheus Metrics

- HTTP request duration
- Request count by endpoint
- Error rates
- Custom business metrics

### Grafana Dashboards

Pre-configured dashboards for:
- Application performance
- Infrastructure metrics
- Business metrics
- Database performance

### Health Checks

- **Liveness**: `/live` - Is the app running?
- **Readiness**: `/ready` - Is the app ready to serve traffic?
- **Health**: `/health` - Detailed health status

## 🔧 Configuration

### Environment Variables

#### Backend (.env)
```env
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-password
```

#### Frontend (.env)
```env
VITE_API_URL=http://localhost:8000
VITE_APP_NAME="Your App Name"
```

## 🧪 Testing

### Backend Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run with verbose output
pytest -v
```

### Frontend Tests

```bash
# Unit tests
npm test

# E2E tests
npm run test:e2e

# Coverage
npm run test:coverage
```

## 📝 API Documentation

Interactive API documentation is available at:
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **OpenAPI JSON**: http://localhost:8000/api/openapi.json

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- FastAPI for the excellent Python web framework
- React team for the amazing frontend library
- shadcn/ui for beautiful UI components
- All open-source contributors

## 📞 Support

For issues and questions:
- Create an issue on GitHub
- Check the documentation in `/docs`
- Review the API documentation at `/api/docs`

---

**Built with ❤️ for rapid development and production deployment**
