import logging
import os

from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.urllib3 import URLLib3Instrumentor

logger = logging.getLogger("child-safety-guardian-telemetry")
_telemetry_initialized = False


def setup_telemetry():
    """
    Initialize Azure Monitor OpenTelemetry once for the current process.

    This is intentionally idempotent so repeated startup hooks or reloads do
    not attempt to instrument the same libraries more than once.
    """
    global _telemetry_initialized

    if _telemetry_initialized:
        logger.debug("Telemetry setup already completed. Skipping duplicate initialization.")
        return

    connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if not connection_string:
        logger.warning("No Instrumentation Key found. Telemetry is disabled.")
        _telemetry_initialized = True
        return

    os.environ.setdefault("OTEL_SERVICE_NAME", "Child Safety Guardian AI")

    try:
        configure_azure_monitor(
            connection_string=connection_string,
            logger_name="child-safety-guardian-tracer",
        )
        _telemetry_initialized = True
        logger.info("Azure Monitor tracking enabled.")

        try:
            RequestsInstrumentor().instrument()
            logger.info("Requests library instrumented.")
        except Exception:
            logger.debug("Requests instrumentor already active or not needed.")

        try:
            URLLib3Instrumentor().instrument()
            logger.info("URLLib3 library instrumented.")
        except Exception:
            logger.debug("URLLib3 instrumentor already active or not needed.")

    except Exception as exc:
        logger.error(f"Failed to initialize Azure Monitor: {exc}")


def get_tracer(name: str = "child-safety-guardian"):
    """Return an OpenTelemetry tracer for creating custom spans."""
    return trace.get_tracer(name)
