import time
import requests
from typing import Dict, Any
from app.config import settings
from app.connectors.base import BaseConnector

class GhostConnector(BaseConnector):
    connector_key = "ghost"

    def validate(self, rendition: Dict[str, Any], destination: Dict[str, Any], connection: Dict[str, Any]) -> Dict[str, Any]:
        violations = []
        if len(rendition.get("title", "")) > 255:
            violations.append({"field": "title", "reason": "Ghost title max is 255 chars."})
        return {"ok": len(violations) == 0, "violations": violations}

    def publish(self, rendition: Dict[str, Any], destination: Dict[str, Any], connection: Dict[str, Any], idempotency_key: str) -> Dict[str, Any]:
        base_url = destination.get("base_url", "http://localhost:2368").rstrip("/")
        if settings.SIMULATION_MODE or connection.get("simulate"):
            post_id = f"ghost_{int(time.time())}"
            return {"platform_post_id": post_id, "live_url": f"{base_url}/{post_id}/", "status": "live"}

        resp = requests.post(
            f"{base_url}/ghost/api/admin/posts/",
            headers={"Authorization": f"Ghost {connection.get('api_key', '')}"},
            json={"posts": [{"title": rendition["title"], "html": f"<p>{rendition.get('body', '')}</p>", "status": "published"}]},
            timeout=10
        )
        if resp.status_code not in (200, 201):
            raise self.map_http_error(resp.status_code, resp.text)
        post = resp.json()["posts"][0]
        return {"platform_post_id": post["id"], "live_url": post["url"], "status": "live"}

    def get_status(self, platform_post_id: str, connection: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "live", "live_url": f"http://localhost:2368/{platform_post_id}/"}

    def delete(self, platform_post_id: str, connection: Dict[str, Any]) -> Dict[str, Any]:
        return {"deleted": True}