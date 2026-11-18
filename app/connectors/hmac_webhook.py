import hmac
import hashlib
import json
import time
import requests
from typing import Dict, Any
from app.config import settings
from app.connectors.base import BaseConnector

class HmacWebhookConnector(BaseConnector):
    connector_key = "hmac_webhook"

    def validate(self, rendition: Dict[str, Any], destination: Dict[str, Any], connection: Dict[str, Any]) -> Dict[str, Any]:
        violations = []
        if not destination.get("webhook_url") and not destination.get("base_url"):
            violations.append({"field": "destination.webhook_url", "reason": "Missing target webhook URL."})
        return {"ok": len(violations) == 0, "violations": violations}

    def publish(self, rendition: Dict[str, Any], destination: Dict[str, Any], connection: Dict[str, Any], idempotency_key: str) -> Dict[str, Any]:
        target_url = destination.get("webhook_url") or destination.get("base_url", "https://partner.example.com/webhook")
        secret = connection.get("signing_secret", "default_secret").encode("utf-8")
        body_bytes = json.dumps({"idempotency_key": idempotency_key, "rendition": rendition}).encode("utf-8")
        signature = hmac.new(secret, body_bytes, hashlib.sha256).hexdigest()

        if settings.SIMULATION_MODE or connection.get("simulate"):
            post_id = f"wh_{int(time.time())}"
            return {"platform_post_id": post_id, "live_url": f"{target_url}/events/{post_id}", "status": "live", "signature": f"sha256={signature}"}

        resp = requests.post(
            target_url,
            data=body_bytes,
            headers={"Content-Type": "application/json", "X-IncuBrix-Signature": f"sha256={signature}", "Idempotency-Key": idempotency_key},
            timeout=10
        )
        if resp.status_code not in (200, 201, 202):
            raise self.map_http_error(resp.status_code, resp.text)
        post_id = resp.json().get("id", f"wh_{int(time.time())}")
        return {"platform_post_id": str(post_id), "live_url": f"{target_url}/events/{post_id}", "status": "live"}

    def get_status(self, platform_post_id: str, connection: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "live", "live_url": f"https://partner.example.com/events/{platform_post_id}"}

    def delete(self, platform_post_id: str, connection: Dict[str, Any]) -> Dict[str, Any]:
        return {"deleted": True}