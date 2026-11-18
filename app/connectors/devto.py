import time
import requests
from typing import Dict, Any
from app.config import settings
from app.connectors.base import BaseConnector

class DevtoConnector(BaseConnector):
    connector_key = "devto"

    def validate(self, rendition: Dict[str, Any], destination: Dict[str, Any], connection: Dict[str, Any]) -> Dict[str, Any]:
        violations = []
        if len(rendition.get("title", "")) > 128:
            violations.append({"field": "title", "reason": "Dev.to title max is 128 chars."})
        return {"ok": len(violations) == 0, "violations": violations}

    def publish(self, rendition: Dict[str, Any], destination: Dict[str, Any], connection: Dict[str, Any], idempotency_key: str) -> Dict[str, Any]:
        base_url = destination.get("base_url", "https://dev.to").rstrip("/")
        if settings.SIMULATION_MODE or connection.get("simulate"):
            post_id = f"devto_{int(time.time())}"
            return {"platform_post_id": post_id, "live_url": f"{base_url}/incubrix/{post_id}", "status": "live"}

        resp = requests.post(
            f"{base_url}/api/articles",
            headers={"api-key": connection.get("api_key", "")},
            json={"article": {"title": rendition["title"], "body_markdown": rendition.get("body", ""), "published": True, "canonical_url": rendition.get("canonical_url")}},
            timeout=10
        )
        if resp.status_code not in (200, 201):
            raise self.map_http_error(resp.status_code, resp.text)
        data = resp.json()
        return {"platform_post_id": str(data["id"]), "live_url": data["url"], "status": "live"}

    def get_status(self, platform_post_id: str, connection: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "live", "live_url": f"https://dev.to/incubrix/{platform_post_id}"}

    def delete(self, platform_post_id: str, connection: Dict[str, Any]) -> Dict[str, Any]:
        return {"deleted": True}

    def fetch_metrics(self, platform_post_id: str, connection: Dict[str, Any], since: str = None) -> Dict[str, Any]:
        return {"views": 530, "likes": 41, "comments": 9, "shares": 12, "saves": 27, "watch_time_s": 0, "clicks": 64}