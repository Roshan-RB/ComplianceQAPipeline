import logging
import uuid
from contextlib import asynccontextmanager
from typing import List

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from backend.src.api.telemetry import setup_telemetry
from backend.src.config import validate_audit_environment
from backend.src.graph.workflow import app as compliance_graph

load_dotenv(override=True)
validate_audit_environment()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("child-safety-api")


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Telemetry starts only when the API process actually starts serving.
    setup_telemetry()
    yield


app = FastAPI(
    title="Child Safety Guardian AI API",
    description="API for auditing video content against YouTube Child Safety Policy guidelines.",
    version="1.0.0",
    lifespan=lifespan,
)


class AuditRequest(BaseModel):
    """Defines the expected structure of incoming API requests."""

    video_url: str


class ComplianceIssue(BaseModel):
    """Defines the structure of a single child safety policy violation."""

    category: str
    severity: str
    description: str


class AuditResponse(BaseModel):
    """Defines the structure of API responses."""

    session_id: str
    video_id: str
    status: str
    final_report: str
    compliance_results: List[ComplianceIssue]
    retrieved_policies: List[str]


@app.post("/audit", response_model=AuditResponse)
async def audit_video(request: AuditRequest):
    """Trigger the child safety audit workflow for a YouTube video."""
    session_id = str(uuid.uuid4())
    video_id_short = f"vid_{session_id[:8]}"

    logger.info(f"Received Audit Request: {request.video_url} (Session: {session_id})")

    initial_inputs = {
        "video_url": request.video_url,
        "video_id": video_id_short,
        "compliance_results": [],
        "errors": [],
    }

    try:
        final_state = compliance_graph.invoke(initial_inputs)
        return AuditResponse(
            session_id=session_id,
            video_id=final_state.get("video_id"),
            status=final_state.get("final_status", "UNKNOWN"),
            final_report=final_state.get("final_report", "No report generated."),
            compliance_results=final_state.get("compliance_results", []),
            retrieved_policies=final_state.get("retrieved_policies", []),
        )
    except Exception as exc:
        logger.error(f"Audit Failed: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Workflow Execution Failed: {exc}",
        )


@app.get("/health")
def health_check():
    """Simple endpoint to verify the API is running."""
    return {"status": "healthy", "service": "Child Safety Guardian AI"}
