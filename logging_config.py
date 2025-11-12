"""
Logging configuration with x-trace-id injection for distributed tracing using loguru.

Loguru provides structured JSON logging with automatic context injection.
"""
import sys
from contextvars import ContextVar
from typing import Optional
from loguru import logger

# Context variable to store trace ID across async calls
trace_id_context: ContextVar[Optional[str]] = ContextVar('trace_id', default=None)

# Flag to ensure configure_logging is only called once
_logging_configured = False


def trace_id_patcher(record):
    """
    Loguru patcher to inject snapp_trace_id into all log records.
    This runs for every log call and adds the trace ID from context.
    Defensive - handles missing extra dict and None trace IDs.
    """
    try:
        trace_id = trace_id_context.get()
        # Ensure extra dict exists (should always be there in loguru, but be safe)
        if "extra" not in record:
            record["extra"] = {}
        record["extra"]["snapp_trace_id"] = trace_id if trace_id else ''
    except Exception:
        # If anything goes wrong, don't break logging
        pass


def configure_logging():
    """
    Configure loguru with trace ID injection.
    Removes default handler and adds structured JSON logging to stderr.
    Safe to call multiple times - will only configure once.
    """
    global _logging_configured

    # Only configure once to avoid duplicate handlers
    if _logging_configured:
        return

    try:
        # Remove default handler
        logger.remove()

        # Add stderr handler with JSON output
        logger.add(
            sys.stderr,
            level="INFO",
            serialize=True,  # JSON output
            backtrace=True,
            diagnose=True,
            enqueue=True,  # Thread-safe async logging
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {name}:{function}:{line} | {message}",
        )

        # Configure patcher to inject trace ID into all logs
        logger.configure(patcher=trace_id_patcher)

        _logging_configured = True
    except Exception as e:
        # If configuration fails, at least ensure we have basic logging
        print(f"Warning: Failed to configure loguru: {e}", file=sys.stderr)
        # Don't set _logging_configured so it can retry


def set_trace_id(trace_id: Optional[str]) -> None:
    """
    Set the trace ID for the current context.
    Safe - handles None and invalid trace IDs gracefully.

    Args:
        trace_id: The x-trace-id header value from the incoming request (can be None)
    """
    try:
        # Store trace ID (None is valid - means no trace ID present)
        trace_id_context.set(trace_id)
    except Exception:
        # If setting fails, don't break execution
        # Logging will continue without trace ID
        pass


def get_trace_id() -> Optional[str]:
    """
    Get the current trace ID from context.
    Safe - returns None if not set or if retrieval fails.

    Returns:
        The trace ID if set, None otherwise
    """
    try:
        return trace_id_context.get()
    except Exception:
        return None
