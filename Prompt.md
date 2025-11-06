You are an expert full-stack architect, DevOps engineer, and security specialist.  
Create a **production-grade, problem-agnostic full-stack project template** that serves as the ultimate starting point for hackathons, MVPs, and world problem-solving projects.

---

## Tech Stack

**Backend**
- Python 3.11+ with FastAPI (async/await patterns)
- PostgreSQL 15+ with connection pooling (pgbouncer)
- SQLAlchemy 2.0+ (async) + Alembic migrations
- Redis for caching and session storage
- Celery for background tasks + Flower for monitoring
- API versioning strategy built-in

**Frontend**
- React 18+ with TypeScript (strict mode)
- Vite 5+ with optimized build config
- shadcn/ui + Radix UI primitives
- Tailwind CSS with custom design tokens
- TanStack Query (React Query) for data fetching
- Zustand for state management
- React Router v6 for routing
- Zod for runtime validation

**Database & Caching**
- PostgreSQL with full-text search configured
- Redis for caching, rate limiting, and pub/sub
- Database connection pooling and query optimization examples

**Authentication & Authorization**
- JWT (access + refresh tokens) with secure HTTP-only cookies
- OAuth 2.0 scaffold (Google, GitHub providers)
- Role-based access control (RBAC) system
- Rate limiting per user/IP
- Email verification flow
- Password reset with secure tokens
- 2FA/MFA scaffold (TOTP)

**API & Documentation**
- FastAPI auto-generated OpenAPI docs
- API versioning (v1, v2 structure)
- Request/response schemas with Pydantic v2
- GraphQL endpoint option (Strawberry)
- WebSocket support for real-time features
- API rate limiting and throttling

**DevOps & Infrastructure**
- Docker multi-stage builds (optimized for size)
- docker-compose for local development
- Kubernetes manifests (deployments, services, ingress)
- Terraform modules for AWS (VPC, ECS, RDS, S3, CloudFront, Route53)
- Alternative: Terraform for GCP and Azure
- Helm charts for K8s deployments
- Infrastructure as Code best practices

**CI/CD**
- GitHub Actions (matrix testing, caching, secrets)
- GitLab CI alternative configuration
- Automated versioning and changelog generation
- Blue-green deployment strategy
- Rollback mechanisms
- Environment promotion (dev → staging → prod)

**Observability & Monitoring**
- Structured logging (JSON) with correlation IDs
- Prometheus metrics + custom business metrics
- Grafana dashboards (pre-configured)
- OpenTelemetry for distributed tracing
- Sentry for error tracking
- ELK/Loki stack integration example
- Performance monitoring (APM)
- Uptime monitoring and health checks

**Security**
- OWASP Top 10 protections built-in
- Helmet.js equivalent for FastAPI (security headers)
- CORS configuration (environment-based)
- SQL injection prevention (parameterized queries)
- XSS protection and CSP headers
- Secrets management (AWS Secrets Manager, HashiCorp Vault)
- Dependabot for dependency updates
- Trivy for container scanning
- SAST (Static Application Security Testing) with Semgrep
- Pre-commit hooks for secret detection (gitleaks)
- SSL/TLS configuration with auto-renewal (Let's Encrypt)

**Testing**
- Backend: pytest with fixtures, mocking, coverage reports
- Frontend: Vitest + React Testing Library
- E2E: Playwright with CI integration
- Load testing: Locust configuration
- Contract testing: Pact
- Test coverage threshold enforcement (80%+)

**Developer Experience**
- VSCode devcontainer with all extensions
- Pre-commit hooks (black, isort, flake8, mypy, eslint, prettier)
- EditorConfig for consistency
- Comprehensive Makefile with all common commands
- Hot reload for both backend and frontend
- API client generation (openapi-generator)
- Database seeding and fixtures
- Sample data generators

---

## Deliverables

### 1. Repository Structure
```
project-root/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml
│   │   ├── cd.yml
│   │   ├── security-scan.yml
│   │   └── release.yml
│   ├── ISSUE_TEMPLATE/
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── dependabot.yml
├── backend/
│   ├── alembic/
│   │   ├── versions/
│   │   └── env.py
│   ├── app/
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── endpoints/
│   │   │   │   │   ├── auth.py
│   │   │   │   │   ├── users.py
│   │   │   │   │   └── items.py
│   │   │   │   └── router.py
│   │   │   └── deps.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   ├── database.py
│   │   │   ├── cache.py
│   │   │   └── logging.py
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── tasks/  (celery tasks)
│   │   ├── middleware/
│   │   └── main.py
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── conftest.py
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── poetry.lock
│   └── .env.example
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/  (shadcn components)
│   │   │   ├── layouts/
│   │   │   └── features/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── lib/
│   │   │   ├── api.ts
│   │   │   ├── auth.ts
│   │   │   └── utils.ts
│   │   ├── stores/
│   │   ├── types/
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── tests/
│   │   ├── unit/
│   │   └── e2e/
│   ├── Dockerfile
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── .env.example
├── infra/
│   ├── terraform/
│   │   ├── modules/
│   │   │   ├── vpc/
│   │   │   ├── ecs/
│   │   │   ├── rds/
│   │   │   └── s3-cloudfront/
│   │   ├── environments/
│   │   │   ├── dev/
│   │   │   ├── staging/
│   │   │   └── prod/
│   │   ├── main.tf
│   │   └── variables.tf
│   ├── kubernetes/
│   │   ├── base/
│   │   └── overlays/
│   └── helm/
├── monitoring/
│   ├── grafana/
│   │   └── dashboards/
│   ├── prometheus/
│   │   └── rules/
│   └── alertmanager/
├── docs/
│   ├── architecture/
│   │   ├── diagrams/
│   │   └── decisions/ (ADRs)
│   ├── api/
│   └── deployment/
├── scripts/
│   ├── seed-db.py
│   ├── backup.sh
│   └── deploy.sh
├── .devcontainer/
│   └── devcontainer.json
├── .vscode/
│   ├── settings.json
│   └── extensions.json
├── docker-compose.yml
├── docker-compose.prod.yml
├── Makefile
├── README.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── LICENSE
└── .gitignore
```

### 2. Backend Implementation

**Complete files required:**

`backend/app/main.py` - FastAPI entrypoint with:
- Lifespan events for startup/shutdown
- Middleware stack (CORS, compression, request ID, rate limiting)
- Exception handlers
- API router mounting
- Health and metrics endpoints
- OpenTelemetry instrumentation

`backend/app/core/config.py` - Settings management using Pydantic BaseSettings:
- Environment-based configuration
- Database URLs with async support
- Redis configuration
- JWT secrets
- CORS origins
- Feature flags
- Observability settings

`backend/app/core/security.py` - Security utilities:
- Password hashing (bcrypt)
- JWT token creation/verification
- OAuth2 password bearer
- API key validation
- Rate limiting decorators

`backend/app/core/database.py` - Database setup:
- Async SQLAlchemy engine
- Session management with context managers
- Connection pooling
- Query optimization helpers

`backend/app/api/v1/endpoints/auth.py` - Complete auth flow:
- Registration with email verification
- Login (returns access + refresh tokens)
- Token refresh
- Password reset flow
- OAuth login endpoints
- Logout and token revocation

`backend/app/api/v1/endpoints/users.py` - User CRUD:
- Get current user
- Update profile
- Delete account
- List users (admin only)
- Role management

`backend/app/models/` - SQLAlchemy models:
- User model with relationships
- BaseModel with common fields (id, created_at, updated_at)
- Soft delete support

`backend/app/schemas/` - Pydantic schemas:
- Request/response models
- Validation rules
- Serialization examples

`backend/app/tasks/celery_app.py` - Celery configuration:
- Email sending task
- Report generation
- Data processing examples

`backend/tests/conftest.py` - pytest fixtures:
- Test database
- Test client
- Authenticated user fixture
- Mock data factories

`backend/Dockerfile` - Multi-stage build:
- Build stage with dependencies
- Runtime stage (slim)
- Non-root user
- Health check

`backend/pyproject.toml` - Poetry configuration with all dependencies organized

### 3. Frontend Implementation

**Complete files required:**

`frontend/src/main.tsx` - App entry point with:
- React Query provider
- Router setup
- Auth provider
- Theme provider

`frontend/src/App.tsx` - Main app component:
- Route definitions
- Protected routes
- Layout structure
- Error boundaries

`frontend/src/lib/api.ts` - API client:
- Axios/fetch wrapper with interceptors
- Token refresh logic
- Error handling
- Type-safe endpoints

`frontend/src/lib/auth.ts` - Auth utilities:
- Token storage
- User state management
- Login/logout functions
- Permission checks

`frontend/src/pages/Login.tsx` - Complete login page with shadcn/ui components

`frontend/src/pages/Dashboard.tsx` - Dashboard with:
- Data fetching
- Charts (recharts)
- Real-time updates
- Responsive design

`frontend/src/components/ui/` - shadcn/ui components:
- button, input, card, dialog, dropdown, table, etc.
- All properly typed

`frontend/src/hooks/useAuth.ts` - Custom auth hook

`frontend/vite.config.ts` - Vite configuration:
- Path aliases
- Proxy for API
- Build optimizations
- Environment variables

`frontend/tailwind.config.js` - Tailwind with:
- Custom theme
- shadcn/ui integration
- Typography plugin

`frontend/Dockerfile` - Multi-stage build:
- Build stage with node
- Nginx stage for serving
- Optimized for production

### 4. Infrastructure as Code

`infra/terraform/main.tf` - Complete AWS setup:
- VPC with public/private subnets
- RDS PostgreSQL with backups
- ECS Fargate cluster
- Application Load Balancer
- S3 + CloudFront for frontend
- Route53 DNS
- ACM certificates
- WAF rules
- Secrets Manager integration

`infra/terraform/modules/` - Reusable modules for each resource

`infra/kubernetes/` - K8s manifests:
- Deployments with rolling updates
- Services (ClusterIP, LoadBalancer)
- Ingress with TLS
- ConfigMaps and Secrets
- HorizontalPodAutoscaler
- PodDisruptionBudget

### 5. CI/CD Pipelines

`.github/workflows/ci.yml` - Complete CI pipeline:
- Matrix testing (Python 3.10, 3.11, 3.12)
- Linting and formatting checks
- Unit and integration tests
- Frontend tests (Jest + Playwright)
- Coverage reporting
- Security scans
- Docker image building
- Caching for speed

`.github/workflows/cd.yml` - Deployment pipeline:
- Deploy to dev on push to develop
- Deploy to staging on push to main
- Deploy to prod on release tags
- Terraform plan/apply
- Database migrations
- Smoke tests post-deployment
- Rollback capability

`.github/workflows/security-scan.yml` - Security checks:
- Trivy container scanning
- Semgrep SAST
- Dependency audits
- Secret detection

### 6. Observability Stack

`monitoring/grafana/dashboards/` - Pre-configured dashboards:
- Application performance (latency, throughput, errors)
- Infrastructure metrics (CPU, memory, disk)
- Business metrics (user signups, API usage)
- Database performance

`monitoring/prometheus/` - Prometheus configuration:
- Scrape configs
- Alert rules (high error rate, slow responses, down services)
- Recording rules

### 7. Developer Experience

`Makefile` - Comprehensive commands:
```makefile
dev:          # Start local development
test:         # Run all tests
lint:         # Run linters
format:       # Format code
build:        # Build Docker images
deploy-dev:   # Deploy to dev
migrate:      # Run database migrations
seed:         # Seed database
clean:        # Clean artifacts
logs:         # Tail logs
shell:        # Open shell in container
```

`.devcontainer/devcontainer.json` - VSCode devcontainer:
- All extensions installed
- Forwarded ports
- Post-create commands
- Environment setup

`.pre-commit-config.yaml` - Pre-commit hooks:
- black, isort, flake8, mypy
- eslint, prettier
- gitleaks (secret detection)
- trailing whitespace removal

### 8. Documentation

`README.md` - Complete guide with:
- Project overview and architecture
- Quick start (< 5 minutes)
- Prerequisites
- Local development setup
- Environment variables guide
- API documentation links
- Deployment guide
- Troubleshooting
- Contributing guidelines
- License

`docs/architecture/` - Architecture documentation:
- System design diagram (C4 model)
- Database schema (ER diagram)
- API flow diagrams
- Infrastructure diagram
- Security architecture
- Decision records (ADRs)

`docs/api/` - API documentation:
- Authentication guide
- Endpoint reference
- Request/response examples
- Error codes
- Rate limiting info

`CONTRIBUTING.md` - Contributor guide:
- Code style
- Branch naming
- Commit conventions
- PR process
- Development workflow

### 9. Security & Compliance

- HTTPS enforced everywhere
- Secrets rotation strategy
- Audit logging for sensitive operations
- GDPR compliance helpers (data export, deletion)
- Security headers configured
- Input validation and sanitization
- SQL injection prevention
- XSS protection
- CSRF protection
- Rate limiting per endpoint
- API key management
- Vulnerability scanning in CI

### 10. Testing Strategy

- Unit test coverage > 80%
- Integration tests for API endpoints
- E2E tests for critical user flows
- Load testing configuration (1000+ req/s target)
- Smoke tests for production
- Contract tests between frontend/backend
- Mutation testing examples
- Visual regression testing (Percy/Chromatic)

### 11. Extensibility & Patterns

**Plugin Architecture:**
- Pluggable authentication providers
- Custom middleware examples
- Feature flags system
- Multi-tenancy scaffold
- Event-driven architecture with message queues
- Webhook system for integrations

**Code Examples:**
- Adding a new API endpoint (with tests)
- Creating a new database model
- Adding a new frontend page
- Implementing a background task
- Adding a new metric
- Creating a new deployment environment

### 12. Performance Optimization

- Database query optimization examples
- Caching strategies (Redis)
- CDN configuration
- Image optimization pipeline
- Code splitting in frontend
- Lazy loading components
- API response compression
- Database indexing strategy
- Connection pooling
- Query result pagination

---

## Output Format

1. **Design Overview (500 words)**
   - Architecture decisions and rationale
   - Why this stack for production
   - Scalability considerations
   - Cost optimization strategies

2. **Complete Repository Tree**
   - Every file and folder listed
   - With brief description comments

3. **Full File Contents**
   - Every file mentioned above in full, working code
   - No TODOs or placeholders
   - Production-quality code with comments
   - Type hints and documentation

4. **Setup Instructions**
   - Step-by-step commands that work
   - Expected outputs
   - Common issues and solutions

5. **Customization Guide**
   - How to adapt for specific use cases
   - What to change for different problems
   - Feature addition guide

---

## Critical Requirements

✅ **All code must be production-ready** - no placeholders, todos, or "implement this later"
✅ **Everything must be runnable** - `docker-compose up` should work immediately
✅ **Secure by default** - all security best practices implemented
✅ **Well-documented** - every complex section explained
✅ **Type-safe** - TypeScript strict mode, Python type hints
✅ **Tested** - comprehensive test suite included
✅ **Observable** - logging, metrics, tracing built-in
✅ **Deployable** - can go to production with minimal changes
✅ **Maintainable** - clean code, clear patterns, easy to extend
✅ **Cost-effective** - optimized for minimal cloud costs

---

## Success Criteria

The resulting template should allow a developer to:
1. Clone the repo
2. Run `make dev` 
3. Have a fully working app in < 5 minutes
4. Add their specific business logic
5. Deploy to production in < 1 hour
6. Scale to 10,000+ users without code changes

---

**Goal:** Create the **ultimate full-stack template** that combines enterprise-grade architecture with rapid development speed. This should be the last boilerplate anyone ever needs - comprehensive enough for production, yet simple enough for hackathons.
