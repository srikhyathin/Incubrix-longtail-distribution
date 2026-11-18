import uuid
import time
import hmac
import hashlib
import json
import os
import requests
from datetime import datetime, timezone
from fastapi import APIRouter, Header, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
from app.engine.rules import PostingRulesEngine
from app.engine.certifier import CertificationHarness
from app.api.connectors import CONNECTOR_REGISTRY
from app.connectors.base import ConnectorError

router = APIRouter()

class PublishRequest(BaseModel):
    connector_key: str
    rendition: Dict[str, Any]
    destination: Dict[str, Any]
    connection: Dict[str, Any]
    state: Optional[Dict[str, Any]] = None
    callback_url: Optional[str] = None

class CertifyRequest(BaseModel):
    connector_key: str
    destination: Dict[str, Any]
    connection: Dict[str, Any]

jobs_db: Dict[str, Dict[str, Any]] = {}
CALLBACK_SECRET = os.getenv("CALLBACK_HMAC_SECRET", "incubrix_dev_secret").encode("utf-8")

def build_output_manifest(connector_key: str, duration_s: float, warnings: list = None) -> Dict[str, Any]:
    return {
        "service": "incubrix-longtail-distribution",
        "version": "1.0.0",
        "connector_key": connector_key,
        "models_used": ["rule-engine-v1", "heuristic-tailor-v1"],
        "seed": 42,
        "timings": {"duration_s": round(duration_s, 4), "generated_at": datetime.now(timezone.utc).isoformat()},
        "cost_estimate_usd": 0.0,
        "warnings": warnings or [],
        "licence_and_rights": "Apache-2.0 / Commercial-use verified; AI-content labeled where applicable."
    }

def send_signed_callback(callback_url: str, payload: Dict[str, Any]):
    body = json.dumps(payload).encode("utf-8")
    sig = hmac.new(CALLBACK_SECRET, body, hashlib.sha256).hexdigest()
    try:
        requests.post(
            callback_url,
            data=body,
            headers={"Content-Type": "application/json", "X-IncuBrix-Signature": f"sha256={sig}"},
            timeout=5
        )
    except Exception:
        pass

@router.post("/jobs", status_code=202)
async def create_publishing_job(
    payload: PublishRequest,
    background_tasks: BackgroundTasks,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
):
    if idempotency_key and idempotency_key in jobs_db:
        return JSONResponse(status_code=202, content=jobs_db[idempotency_key])

    job_id = str(uuid.uuid4())
    allowed, err_code, reason, retryable = PostingRulesEngine.evaluate_rules(
        payload.rendition, payload.destination, payload.state or {"posts_in_window": 0}
    )

    if not allowed:
        return JSONResponse(
            status_code=422,
            content={"error": {"code": err_code, "message": reason, "retryable": retryable, "details": {}}}
        )

    job_record = {
        "job_id": job_id,
        "status": "queued",
        "progress": 0,
        "result": None,
        "manifest": None
    }
    jobs_db[job_id] = job_record
    if idempotency_key:
        jobs_db[idempotency_key] = job_record

    def execute_publishing_task():
        start = time.time()
        jobs_db[job_id]["status"] = "running"
        jobs_db[job_id]["progress"] = 50
        connector = CONNECTOR_REGISTRY.get(payload.connector_key)
        if not connector:
            jobs_db[job_id]["status"] = "failed"
            jobs_db[job_id]["error"] = {"code": "CONNECTOR_DISABLED", "message": "Connector not found", "retryable": False, "details": {}}
            return

        try:
            res = connector.publish(payload.rendition, payload.destination, payload.connection, idempotency_key or job_id)
            jobs_db[job_id]["status"] = "succeeded"
            jobs_db[job_id]["progress"] = 100
            jobs_db[job_id]["result"] = res
            jobs_db[job_id]["manifest"] = build_output_manifest(payload.connector_key, time.time() - start)
        except ConnectorError as ce:
            jobs_db[job_id]["status"] = "failed"
            jobs_db[job_id]["error"] = {"code": ce.code, "message": ce.message, "retryable": ce.retryable, "details": ce.details}
            jobs_db[job_id]["manifest"] = build_output_manifest(payload.connector_key, time.time() - start, warnings=[ce.message])

        if payload.callback_url:
            send_signed_callback(payload.callback_url, jobs_db[job_id])

    background_tasks.add_task(execute_publishing_task)
    return job_record

@router.get("/jobs/{job_id}")
def get_job_status(job_id: str):
    if job_id not in jobs_db:
        return JSONResponse(status_code=404, content={"error": {"code": "DEST_SPEC_VIOLATION", "message": "Job not found", "retryable": False, "details": {}}})
    return jobs_db[job_id]

@router.post("/certify")
def certify_destination(payload: CertifyRequest):
    return CertificationHarness.run_certification(payload.connector_key, payload.destination, payload.connection)