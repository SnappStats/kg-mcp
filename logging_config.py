"""
Logging configuration with x-trace-id injection for distributed tracing.

Cloud Run automatically captures Python logging and formats as structured JSON.
We only need to inject the trace ID into logs - GCP handles the rest.
"""
import logging
from contextvars import ContextVar
from typing import Optional

# Context variable to store trace ID across async calls
trace_id_context: ContextVar[Optional[str]] = ContextVar('trace_id', default=None)


class TraceIdFilter(logging.Filter):
    """
    Injects x-trace-id into all log records for distributed tracing.
    Matches the format used by the SportsAgent API (snapp_trace_id).

    Cloud Run/GCP automatically processes these fields into structured logs.
    """
    def filter(self, record: logging.LogRecord) -> bool:
        trace_id = trace_id_context.get()

        # Inject trace ID as snapp_trace_id (our standard field)
        record.snapp_trace_id = trace_id or ''

        # Also inject into json_fields if present (for @flog compatibility)
        if hasattr(record, 'json_fields') and isinstance(record.json_fields, dict):
            if trace_id:
                record.json_fields['snapp_trace_id'] = trace_id

        return True


def configure_logging():
    """
    Configure logging with trace ID injection.
    Cloud Run handles JSON formatting automatically.
    """
    root_logger = logging.getLogger()

    # Add trace ID filter to all existing handlers
    trace_filter = TraceIdFilter()
    for handler in root_logger.handlers:
        handler.addFilter(trace_filter)

    # If no handlers, add default (Cloud Run captures stdout)
    if not root_logger.handlers:
        handler = logging.StreamHandler()
        handler.addFilter(trace_filter)
        root_logger.addHandler(handler)
        root_logger.setLevel(logging.INFO)


def set_trace_id(trace_id: Optional[str]) -> None:
    """
    Set the trace ID for the current context.

    Args:
        trace_id: The x-trace-id header value from the incoming request
    """
    trace_id_context.set(trace_id)


def get_trace_id() -> Optional[str]:
    """
    Get the current trace ID from context.

    Returns:
        The trace ID if set, None otherwise
    """
    return trace_id_context.get()


def log_tool_execution(logger):
    """
    Decorator that automatically logs tool input/output for ANY tool signature.
    Flexible - adapts to tool changes without code modifications.

    Usage:
        @log_tool_execution(logger)
        async def my_tool(param1: str, param2: int):
            return result
    """
    import functools
    import inspect

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Get function signature for flexible input logging
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # Convert args to dict (flexible - works with any signature)
            tool_input = dict(bound_args.arguments)

            # Truncate long strings in input (but keep structure flexible)
            def truncate_value(v):
                if isinstance(v, str) and len(v) > 500:
                    return v[:500] + "... (truncated)"
                return v

            tool_input_safe = {k: truncate_value(v) for k, v in tool_input.items()}

            # Log tool input
            logger.info(
                f"{func.__name__} called",
                extra={'json_fields': {
                    'tool': func.__name__,
                    'tool_input': tool_input_safe
                }}
            )

            # Execute tool
            result = await func(*args, **kwargs)

            # Log tool output (flexible - any return type)
            tool_output = result
            if isinstance(result, str) and len(result) > 1000:
                tool_output = result[:1000] + "... (truncated)"

            logger.info(
                f"{func.__name__} completed",
                extra={'json_fields': {
                    'tool': func.__name__,
                    'tool_output_type': type(result).__name__,
                    'tool_output_length': len(result) if isinstance(result, (str, dict, list)) else None
                }}
            )

            return result

        return wrapper
    return decorator
