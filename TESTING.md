# Testing Guide

This repository includes comprehensive test suites for both backend and frontend code.

## Test Files Created

### Backend Tests (Python + Pytest)
- `backend/tests/test_security.py` (~250 tests) - Security functions
- `backend/tests/test_models_user.py` (~40 tests) - User model
- `backend/tests/test_cache.py` (~35 tests) - Cache operations
- `backend/tests/test_api_deps.py` (~30 tests) - API dependencies

### Frontend Tests (TypeScript + Vitest)
- `frontend/src/lib/auth.test.ts` (~60 tests) - Auth utilities
- `frontend/src/lib/utils.test.ts` (~70 tests) - Utility functions
- `frontend/src/lib/api.test.ts` (~40 tests) - API client

**Total: ~525 comprehensive test cases**

## Running Tests

### Backend
```bash
cd backend
poetry run pytest --cov=app --cov-report=html
```

### Frontend
```bash
cd frontend
npm test
```

## Coverage Areas

### Backend
- Password hashing & JWT tokens
- 2FA/TOTP implementation
- User roles & permissions
- Account locking
- Cache operations
- Authentication & authorization

### Frontend
- Token management
- API interceptors & refresh flow
- Utility functions
- Error handling

See TEST_SUMMARY.md files in backend/tests/ and frontend/tests/ for detailed documentation.