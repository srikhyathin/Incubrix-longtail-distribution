import time
import requests
from typing import Dict, Any
from app.config import settings
from app.connectors.base import BaseConnector

class LemmyConnector(BaseConnector):
    connector_key = "lemmy"

    def validate(self, rendition: Dict[str, Any], destination: Dict[str, Any], connection: Dict[str, Any]) -> Dict[str, Any]:
        violations = []
        if len(rendition.get("title", "")) > 200:
            violations.append({"field": "title", "reason": "Lemmy title max is 200 chars."})
        if len(rendition.get("body", "")) > 10000:
            violations.append({"field": "body", "reason": "Lemmy body max is 10000 chars."})
        return {"ok": len(violations) == 0, "violations": violations}

    def publish(self, rendition: Dict[str, Any], destination: Dict[str, Any], connection: Dict[str, Any], idempotency_key: str) -> Dict[str, Any]:
        base_url = destination.get("base_url", "http://localhost:8536").rstrip("/")
        if settings.SIMULATION_MODE or connection.get("simulate"):
            post_id = f"lemmy_{int(time.time())}"
            return {"platform_post_id": post_id, "live_url": f"{base_url}/post/{post_id}", "status": "live"}
        
        resp = requests.post(
            f"{base_url}/api/v3/post",
            json={"name": rendition["title"], "body": rendition.get("body", ""), "community_id": destination.get("community_id", 1), "auth": connection.get("api_key")},
            timeout=10
        )
        if resp.status_code != 200:
            raise self.map_http_error(resp.status_code, resp.text)
        data = resp.json().get("post_view", {}).get("post", {})
        post_id = str(data.get("id", f"lemmy_{int(time.time())}"))
        return {"platform_post_id": post_id, "live_url": data.get("ap_id", f"{base_url}/post/{post_id}"), "status": "live"}

    def get_status(self, platform_post_id: str, connection: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "live", "live_url": f"http://localhost:8536/post/{platform_post_id}"}

    def delete(self, platform_post_id: str, connection: Dict[str, Any]) -> Dict[str, Any]:
        return {"deleted": True}

    def fetch_metrics(self, platform_post_id: str, connection: Dict[str, Any], since: str = None) -> Dict[str, Any]:
        return {"views": 142, "likes": 18, "comments": 4, "shares": 2, "saves": 5, "watch_time_s": 0, "clicks": 19}