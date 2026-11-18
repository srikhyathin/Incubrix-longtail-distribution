import time
from typing import Dict, Any
from app.connectors.base import BaseConnector

class DiscourseConnector(BaseConnector):
    connector_key = "discourse"

    def validate(self, rendition: Dict[str, Any], destination: Dict[str, Any], connection: Dict[str, Any]) -> Dict[str, Any]:
        violations = []
        if len(rendition.get("title", "")) > 255:
            violations.append({"field": "title", "reason": "Title exceeds 255 characters."})
        return {"ok": len(violations) == 0, "violations": violations}

    def publish(self, rendition: Dict[str, Any], destination: Dict[str, Any], connection: Dict[str, Any], idempotency_key: str) -> Dict[str, Any]:
        post_id = f"disc_post_{int(time.time())}"
        base_url = destination.get("base_url", "https://forum.example.com")
        return {
            "platform_post_id": post_id,
            "live_url": f"{base_url}/t/{post_id}",
            "status": "live"
        }

    def get_status(self, platform_post_id: str, connection: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "live", "live_url": f"https://forum.example.com/t/{platform_post_id}"}

    def delete(self, platform_post_id: str, connection: Dict[str, Any]) -> Dict[str, Any]:
        return {"deleted": True}