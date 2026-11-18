from typing import Dict, Any
from app.connectors.base import BaseConnector

class AssistedConnector(BaseConnector):
    connector_key = "assisted"

    def validate(self, rendition: Dict[str, Any], destination: Dict[str, Any], connection: Dict[str, Any]) -> Dict[str, Any]:
        return {"ok": True, "violations": []}

    def publish(self, rendition: Dict[str, Any], destination: Dict[str, Any], connection: Dict[str, Any], idempotency_key: str) -> Dict[str, Any]:
        pack = self.build_assist_pack(rendition, destination)
        return {"platform_post_id": f"assist_{idempotency_key}", "live_url": pack["deep_link"], "status": "pending_manual_post"}

    def get_status(self, platform_post_id: str, connection: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "pending_manual_post", "live_url": ""}

    def delete(self, platform_post_id: str, connection: Dict[str, Any]) -> Dict[str, Any]:
        return {"deleted": True}

    def build_assist_pack(self, rendition: Dict[str, Any], destination: Dict[str, Any]) -> Dict[str, Any]:
        checklist = [
            f"Verify self-promotion allowed: {destination.get('self_promo_allowed', False)}",
            f"Link policy compliance: {destination.get('link_policy', 'no_direct_links')}",
        ]
        if destination.get("disclosure_required"):
            checklist.append("MANDATORY: Include explicit AI-generated content disclosure tag.")
        return {
            "files": rendition.get("media_urls", []),
            "caption": f"{rendition.get('title', '')}\n\n{rendition.get('body', '')}".strip(),
            "deep_link": destination.get("submit_url") or destination.get("url", "https://community.example.com/submit"),
            "checklist": checklist
        }