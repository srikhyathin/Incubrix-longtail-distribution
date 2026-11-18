import os
import json
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any
from app.api.connectors import CONNECTOR_REGISTRY
from app.connectors.base import ConnectorError

EVIDENCE_DIR = os.getenv("EVIDENCE_DIR", "certification_evidence")
os.makedirs(EVIDENCE_DIR, exist_ok=True)

class CertificationHarness:
    @staticmethod
    def run_certification(connector_key: str, destination: Dict[str, Any], connection: Dict[str, Any]) -> Dict[str, Any]:
        connector = CONNECTOR_REGISTRY.get(connector_key)
        if not connector:
            return {"certified": False, "error": "CONNECTOR_DISABLED", "reason": f"Unknown connector: {connector_key}"}

        run_id = f"cert_{connector_key}_{uuid.uuid4().hex[:8]}"
        start_time = time.time()
        test_rendition = {
            "title": f"[IncuBrix Certification Test] {run_id}",
            "body": "Automated end-to-end connector verification post. Will be deleted immediately.",
            "is_promotional": False,
            "is_ai_generated": False,
            "ai_disclosed": True
        }

        evidence: Dict[str, Any] = {
            "run_id": run_id,
            "connector_key": connector_key,
            "destination": destination.get("name") or destination.get("base_url") or destination.get("url"),
            "started_at": datetime.now(timezone.utc).isoformat(),
            "steps": {}
        }

        try:
            # 1. Validate
            val_res = connector.validate(test_rendition, destination, connection)
            evidence["steps"]["validate"] = val_res
            if not val_res.get("ok"):
                raise ConnectorError("DEST_SPEC_VIOLATION", "Validation failed during certification.", details=val_res)

            # Assisted tier does not auto-publish; build pack and certify L1
            if connector_key == "assisted":
                pack_res = connector.build_assist_pack(test_rendition, destination)
                evidence["steps"]["build_assist_pack"] = pack_res
                evidence["certified"] = True
                evidence["level"] = "L1"
                evidence["duration_s"] = round(time.time() - start_time, 4)
                return CertificationHarness._save_evidence(run_id, evidence)

            # 2. Publish
            pub_res = connector.publish(test_rendition, destination, connection, idempotency_key=run_id)
            evidence["steps"]["publish"] = pub_res
            post_id = pub_res["platform_post_id"]

            # 3. Confirm live URL via get_status
            status_res = connector.get_status(post_id, connection)
            evidence["steps"]["get_status"] = status_res
            if status_res.get("status") != "live":
                raise ConnectorError("PLATFORM_UNAVAILABLE", f"Post did not reach live status: {status_res}")

            # 4. Delete test post within 10 minutes
            del_res = connector.delete(post_id, connection)
            evidence["steps"]["delete"] = del_res
            if not del_res.get("deleted"):
                raise ConnectorError("PLATFORM_UNAVAILABLE", "Failed to clean up certification test post.")

            evidence["certified"] = True
            evidence["level"] = "L3"
            evidence["completed_at"] = datetime.now(timezone.utc).isoformat()
            evidence["duration_s"] = round(time.time() - start_time, 4)

        except ConnectorError as ce:
            evidence["certified"] = False
            evidence["level"] = "L0"
            evidence["error"] = {"code": ce.code, "message": ce.message, "details": ce.details}
            evidence["duration_s"] = round(time.time() - start_time, 4)

        return CertificationHarness._save_evidence(run_id, evidence)

    @staticmethod
    def _save_evidence(run_id: str, evidence: Dict[str, Any]) -> Dict[str, Any]:
        filepath = os.path.join(EVIDENCE_DIR, f"{run_id}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(evidence, f, indent=2)
        evidence["evidence_file"] = filepath
        return evidence