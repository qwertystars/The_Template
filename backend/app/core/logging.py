"""
Structured logging configuration with correlation IDs and JSON output.
Integrates with OpenTelemetry for distributed tracing.
"""
import logging
import sys
import structlog
from typing import Any
from pythonjsonlogger import jsonlogger
from app.core.config import settings


def setup_logging() -> None:
    """Configure structured logging for the application."""

    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper()),
    )

    # Processors for structlog
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # Add JSON formatting for production
    if settings.LOG_FORMAT == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance

    Example:
        logger = get_logger(__name__)
        logger.info("user_created", user_id=123, email="user@example.com")
    """
    return structlog.get_logger(name)


class JSONLogFormatter(jsonlogger.JsonFormatter):
    """Custom JSON log formatter with additional fields."""

    def add_fields(
        self,
        log_record: dict[str, Any],
        record: logging.LogRecord,
        message_dict: dict[str, Any]
    ) -> None:
        """Add custom fields to log records."""
        super().add_fields(log_record, record, message_dict)

        # Add custom fields
        log_record["logger"] = record.name
        log_record["level"] = record.levelname
        log_record["timestamp"] = self.formatTime(record, self.datefmt)

        # Add correlation ID if available
        if hasattr(record, "correlation_id"):
            log_record["correlation_id"] = record.correlation_id

        # Add user ID if available
        if hasattr(record, "user_id"):
            log_record["user_id"] = record.user_id

        # Add request ID if available
        if hasattr(record, "request_id"):
            log_record["request_id"] = record.request_id


# Logging middleware helper
class LoggingContext:
    """Context manager for adding context to logs."""

    def __init__(self, **kwargs: Any):
        self.context = kwargs

    def __enter__(self) -> None:
        """Bind context variables."""
        structlog.contextvars.bind_contextvars(**self.context)

    def __exit__(self, *args: Any) -> None:
        """Clear context variables."""
        structlog.contextvars.clear_contextvars()


# Audit logging helpers
class AuditLogger:
    """Helper class for audit logging."""

    def __init__(self):
        self.logger = get_logger("audit")

    def log_auth_event(
        self,
        event: str,
        user_id: int | None = None,
        email: str | None = None,
        ip_address: str | None = None,
        success: bool = True,
        **kwargs: Any
    ) -> None:
        """Log authentication events."""
        self.logger.info(
            event,
            event_type="auth",
            user_id=user_id,
            email=email,
            ip_address=ip_address,
            success=success,
            **kwargs
        )

    def log_data_access(
        self,
        resource: str,
        action: str,
        user_id: int,
        resource_id: str | int | None = None,
        **kwargs: Any
    ) -> None:
        """Log data access events."""
        self.logger.info(
            f"{action}_{resource}",
            event_type="data_access",
            resource=resource,
            action=action,
            user_id=user_id,
            resource_id=resource_id,
            **kwargs
        )

    def log_admin_action(
        self,
        action: str,
        user_id: int,
        target_user_id: int | None = None,
        **kwargs: Any
    ) -> None:
        """Log administrative actions."""
        self.logger.info(
            action,
            event_type="admin_action",
            action=action,
            user_id=user_id,
            target_user_id=target_user_id,
            **kwargs
        )

    def log_security_event(
        self,
        event: str,
        severity: str = "medium",
        user_id: int | None = None,
        ip_address: str | None = None,
        **kwargs: Any
    ) -> None:
        """Log security-related events."""
        log_method = getattr(self.logger, severity.lower(), self.logger.warning)
        log_method(
            event,
            event_type="security",
            severity=severity,
            user_id=user_id,
            ip_address=ip_address,
            **kwargs
        )


# Initialize audit logger
audit_logger = AuditLogger()


# Performance logging helper
def log_performance(operation: str, duration_ms: float, **kwargs: Any) -> None:
    """
    Log performance metrics.

    Args:
        operation: Name of the operation
        duration_ms: Duration in milliseconds
        **kwargs: Additional context
    """
    logger = get_logger("performance")
    logger.info(
        "performance_metric",
        operation=operation,
        duration_ms=duration_ms,
        **kwargs
    )
