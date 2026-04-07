import json
import re
from typing import List, Literal

from pydantic import BaseModel, ValidationError


class AuditIssue(BaseModel):
    category: str
    severity: str
    description: str


class AuditResponsePayload(BaseModel):
    compliance_results: List[AuditIssue]
    status: Literal["PASS", "FAIL"]
    final_report: str


def _extract_json_payload(content: str) -> str:
    stripped = content.strip()
    fenced_match = re.search(r"```(?:json)?\s*(.*?)```", stripped, re.DOTALL)
    if fenced_match:
        return fenced_match.group(1).strip()
    return stripped


def parse_audit_response(content: str) -> AuditResponsePayload:
    if not content or not content.strip():
        raise ValueError("LLM returned an empty audit response.")

    payload_text = _extract_json_payload(content)

    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise ValueError("LLM returned invalid JSON for the audit response.") from exc

    try:
        return AuditResponsePayload.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"LLM audit response schema validation failed: {exc}") from exc
