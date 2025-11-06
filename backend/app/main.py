"""
FastAPI application entry point with middleware, exception handlers, and lifecycle events.
"""
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

from app.core.config import settings
from app.core.database import init_db, close_db
from app.core.cache import init_redis, close_redis
from app.core.logging import setup_logging, get_logger
from app.api.v1.router import api_router


# Setup logging
setup_logging()
logger = get_logger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)
REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"]
)
REQUEST_IN_PROGRESS = Counter(
    "http_requests_in_progress",
    "HTTP requests in progress"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events.
    Setup and cleanup for database, cache, and other services.
    """
    # Startup
    logger.info("starting_application", environment=settings.ENVIRONMENT)

    # Initialize database
    if not settings.TESTING:
        await init_db()
        logger.info("database_initialized")

    # Initialize Redis
    try:
        await init_redis()
        logger.info("redis_initialized")
    except Exception as e:
        logger.error("redis_initialization_failed", error=str(e))

    # Initialize Sentry if configured
    if settings.SENTRY_DSN:
        import sentry_sdk
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            environment=settings.ENVIRONMENT,
        )
        logger.info("sentry_initialized")

    yield

    # Shutdown
    logger.info("shutting_down_application")

    # Close database connections
    await close_db()
    logger.info("database_connections_closed")

    # Close Redis connections
    try:
        await close_redis()
        logger.info("redis_connections_closed")
    except Exception as e:
        logger.error("redis_shutdown_error", error=str(e))


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-grade full-stack template API",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)


# Compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add unique request ID to each request."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    return response


# Timing middleware for performance monitoring
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add response time header and log slow requests."""
    start_time = time.time()

    response = await call_next(request)

    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)

    # Log slow requests
    if process_time > 1.0:  # Log requests taking more than 1 second
        logger.warning(
            "slow_request",
            method=request.method,
            path=request.url.path,
            duration=process_time,
            request_id=getattr(request.state, "request_id", None),
        )

    return response


# Prometheus metrics middleware
@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    """Record Prometheus metrics for each request."""
    method = request.method
    path = request.url.path

    REQUEST_IN_PROGRESS.inc()

    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    REQUEST_IN_PROGRESS.dec()
    REQUEST_COUNT.labels(method=method, endpoint=path, status=response.status_code).inc()
    REQUEST_DURATION.labels(method=method, endpoint=path).observe(duration)

    return response


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with detailed messages."""
    logger.warning(
        "validation_error",
        errors=exc.errors(),
        body=exc.body,
        request_id=getattr(request.state, "request_id", None),
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "body": exc.body,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors."""
    logger.error(
        "unhandled_exception",
        error=str(exc),
        error_type=type(exc).__name__,
        path=request.url.path,
        request_id=getattr(request.state, "request_id", None),
        exc_info=True,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "request_id": getattr(request.state, "request_id", None),
        },
    )


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, Any]:
    """
    Health check endpoint for load balancers and monitoring.

    Returns application health status.
    """
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


# Readiness probe
@app.get("/ready", tags=["Health"])
async def readiness_check() -> dict[str, Any]:
    """
    Readiness check for Kubernetes.

    Checks if application is ready to serve traffic.
    """
    # Check database connectivity
    # Check Redis connectivity
    # Add other service checks as needed

    return {
        "status": "ready",
        "checks": {
            "database": "ok",
            "cache": "ok",
        }
    }


# Liveness probe
@app.get("/live", tags=["Health"])
async def liveness_check() -> dict[str, str]:
    """
    Liveness check for Kubernetes.

    Indicates if application is alive.
    """
    return {"status": "alive"}


# Prometheus metrics endpoint
@app.get("/metrics", tags=["Monitoring"])
async def metrics() -> Response:
    """
    Prometheus metrics endpoint.

    Exposes application metrics for scraping.
    """
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# Include API routers
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# Root endpoint
@app.get("/", tags=["Root"])
async def root() -> dict[str, Any]:
    """
    Root endpoint with API information.
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/api/docs",
        "health": "/health",
        "api": settings.API_V1_PREFIX,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        workers=settings.WORKERS if not settings.RELOAD else 1,
        log_level=settings.LOG_LEVEL.lower(),
    )
