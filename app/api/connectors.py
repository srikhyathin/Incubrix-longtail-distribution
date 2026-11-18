from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse
from typing import Dict, Any
from app.connectors.base import ConnectorError
from app.connectors.discourse import DiscourseConnector
from app.connectors.lemmy import LemmyConnector
from app.connectors.devto import DevtoConnector
from app.connectors.ghost import GhostConnector
from app.connectors.hmac_webhook import HmacWebhookConnector
from app.connectors.assisted import AssistedConnector

router = APIRouter()

CONNECTOR_REGISTRY = {
    "discourse": DiscourseConnector(),
    "lemmy": LemmyConnector(),
    "devto": DevtoConnector(),
    "ghost": GhostConnector(),
    "hmac_webhook": HmacWebhookConnector(),
    "assisted": AssistedConnector(),
}

@router.post("/{connector_key}/{method}")
def invoke_connector_method(connector_key: str, method: str, payload: Dict[str, Any] = Body(...)):
    connector = CONNECTOR_REGISTRY.get(connector_key)
    if not connector:
        return JSONResponse(
            status_code=404,
            content={"error": {"code": "CONNECTOR_DISABLED", "message": f"Unknown or disabled connector: {connector_key}", "retryable": False, "details": {}}}
        )

    try:
        if method == "validate":
            return connector.validate(payload.get("rendition", {}), payload.get("destination", {}), payload.get("connection", {}))
        elif method == "publish":
            return connector.publish(payload.get("rendition", {}), payload.get("destination", {}), payload.get("connection", {}), payload.get("idempotency_key", ""))
        elif method == "get_status":
            return connector.get_status(payload.get("platform_post_id", ""), payload.get("connection", {}))
        elif method == "delete":
            return connector.delete(payload.get("platform_post_id", ""), payload.get("connection", {}))
        elif method == "fetch_metrics":
            return connector.fetch_metrics(payload.get("platform_post_id", ""), payload.get("connection", {}), payload.get("since"))
        elif method == "refresh_auth":
            return connector.refresh_auth(payload.get("connection", {}))
        elif method == "build_assist_pack":
            return connector.build_assist_pack(payload.get("rendition", {}), payload.get("destination", {}))
        else:
            return JSONResponse(
                status_code=400,
                content={"error": {"code": "DEST_SPEC_VIOLATION", "message": f"Unsupported method: {method}", "retryable": False, "details": {}}}
            )
    except ConnectorError as ce:
        return JSONResponse(
            status_code=422,
            content={"error": {"code": ce.code, "message": ce.message, "retryable": ce.retryable, "details": ce.details}}
        )