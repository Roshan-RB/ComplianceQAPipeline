import os           # Access environment variables (like API keys)
import logging      # Python's built-in logging system
from azure.monitor.opentelemetry import configure_azure_monitor  
# ↑ Azure's OpenTelemetry integration - tracks app performance, errors, requests

from opentelemetry import trace
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.urllib3 import URLLib3Instrumentor

# ========== CREATE A DEDICATED LOGGER ==========
logger = logging.getLogger("child-safety-guardian-telemetry")


def setup_telemetry():
    """
    Initializes Azure Monitor OpenTelemetry with full dependency tracking.
    
    Configures:
    - Cloud role name (shows "Child Safety Guardian AI" in Application Map)
    - HTTP dependency tracking (requests + urllib3 libraries)
    - FastAPI auto-instrumentation (incoming requests)
    - Custom tracer for workflow spans
    """
    
    # ========== STEP 1: RETRIEVE CONNECTION STRING ==========
    connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    
    # ========== STEP 2: CHECK IF CONFIGURED ==========
    if not connection_string:
        logger.warning("No Instrumentation Key found. Telemetry is DISABLED.")
        return

    # ========== STEP 3: SET SERVICE NAME ==========
    # This sets the cloud role name that appears in the Application Map center node
    # Without this, it shows as "unknown_service"
    os.environ.setdefault("OTEL_SERVICE_NAME", "Child Safety Guardian AI")

    # ========== STEP 4: CONFIGURE AZURE MONITOR ==========
    try:
        configure_azure_monitor(
            connection_string=connection_string,
            logger_name="child-safety-guardian-tracer"
        )
        logger.info("✅ Azure Monitor Tracking Enabled & Connected!")
        
        # ========== STEP 5: EXPLICITLY INSTRUMENT HTTP LIBRARIES ==========
        # These ensure ALL outgoing HTTP calls show as dependencies in the App Map
        
        # Instruments the `requests` library (used by Azure SDKs, Video Indexer API calls)
        try:
            RequestsInstrumentor().instrument()
            logger.info("✅ Requests library instrumented")
        except Exception:
            logger.debug("Requests instrumentor already active or not needed")
        
        # Instruments urllib3 (used internally by requests, yt-dlp, and Azure SDKs)
        try:
            URLLib3Instrumentor().instrument()
            logger.info("✅ URLLib3 library instrumented")
        except Exception:
            logger.debug("URLLib3 instrumentor already active or not needed")
        
    except Exception as e:
        logger.error(f"Failed to initialize Azure Monitor: {e}")


def get_tracer(name: str = "child-safety-guardian"):
    """
    Returns an OpenTelemetry tracer for creating custom spans.
    
    Usage in other modules:
        from backend.src.api.telemetry import get_tracer
        tracer = get_tracer()
        with tracer.start_as_current_span("my_operation"):
            # ... your code ...
    """
    return trace.get_tracer(name)