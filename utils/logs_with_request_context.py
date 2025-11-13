from functools import wraps
from typing import Callable, TypeVar, ParamSpec
import inspect

from fastmcp.server.dependencies import get_http_headers
from utils.logger import logger

P = ParamSpec('P')
R = TypeVar('R')

def log_with_request_context(func: Callable[P, R]) -> Callable[P, R]:
    @wraps(func)
    async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        headers = get_http_headers()
        graph_id = headers['x-graph-id']
        user_id = headers.get('x-author-id', 'anonymous')
        trace_id = headers.get('x-trace-id')
        logger.info(f"received trace id: {trace_id}")
        with logger.contextualize(
            tool=func.__name__,
            user_id=user_id,
            graph_id=graph_id,
            trace_id=trace_id
        ):
            logger.info(f"{func.__name__} called")
            result = await func(*args, **kwargs)
            logger.info(f"{func.__name__} completed")
            return result
    
    @wraps(func)
    def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        headers = get_http_headers()
        graph_id = headers['x-graph-id']
        user_id = headers.get('x-author-id', 'anonymous')
        trace_id = headers.get('x-trace-id')
        
        with logger.contextualize(
            tool=func.__name__,
            user_id=user_id,
            graph_id=graph_id,
            trace_id=trace_id
        ):
            logger.info(f"{func.__name__} called")
            result = func(*args, **kwargs)
            logger.info(f"{func.__name__} completed")
            return result
    
    return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper
