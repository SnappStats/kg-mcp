import os
from ddtrace import patch_all, tracer as dd_tracer
from logger import logger

def instrument_service():
    if os.getenv("DD_ENABLED", "") != 1:
        return
    
    if os.getenv("DD_AGENT_APM_HOST"):
        service_env = os.getenv("DD_ENV", "unset")
        
        patch_all()
        
        dd_tracer.configure(
            hostname=os.getenv("DD_AGENT_HOST"),
            port=int(os.getenv("DD_AGENT_TRACE_PORT", "8126")),
            service_name=os.getenv("DD_SERVICE", "kg-mcp"),
            env=service_env
        )
        
        if os.getenv("DD_AGENT_SYSLOG_HOST") and os.getenv("DD_AGENT_SYSLOG_PORT"):
            logger.add(
                f"syslog://{os.getenv('DD_AGENT_SYSLOG_HOST')}:{os.getenv('DD_AGENT_SYSLOG_PORT')}",
                level="INFO",
                format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {name}:{function}:{line} | {message}",
                serialize=True,
                backtrace=True,
                diagnose=True
            )
