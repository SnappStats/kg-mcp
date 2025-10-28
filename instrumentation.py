import os
from datadog import initialize
from ddtrace import patch_all, tracer as dd_tracer
from logger import logger

def instrument_service():
    if os.getenv("DD_AGENT") and os.getenv("DD_AGENT_SYSLOG_PORT"):
        logger.add(
            f"syslog://{os.getenv('DD_AGENT')}:{os.getenv('DD_AGENT_SYSLOG_PORT')}",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {name}:{function}:{line} | {message}",
            serialize=True,
            backtrace=True,
            diagnose=True
        )
        
        service_env = os.getenv("DD_ENV", "unset")

        config = {
            "api_key": os.getenv("DD_API_KEY"),
            "statsd_host": os.getenv("DD_AGENT_HOST"),
            "statsd_port": os.getenv("DD_AGENT_STATSD_PORT"),
            "statsd_constant_tags": [f"env:{service_env}"],
        }

        initialize(**config)
        
        patch_all()
        
        dd_tracer.configure(
            hostname=os.getenv("DD_AGENT_HOST"),
            port=int(os.getenv("DD_AGENT_TRACE_PORT", "8126")),
            service_name=os.getenv("DD_SERVICE", "kg-mcp"),
            env=service_env
        )
