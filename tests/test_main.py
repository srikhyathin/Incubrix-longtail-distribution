from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_and_ready():
    assert client.get("/health").status_code == 200
    assert client.get("/ready").status_code == 200

def test_certify_all_six_core_connectors():
    connectors = [
        ("discourse", {"base_url": "https://forum.test.local"}),
        ("lemmy", {"base_url": "http://localhost:8536", "community_id": 1}),
        ("devto", {"base_url": "https://dev.to"}),
        ("ghost", {"base_url": "http://localhost:2368"}),
        ("hmac_webhook", {"webhook_url": "https://partner.test.local/hook"}),
        ("assisted", {"submit_url": "https://community.test.local/submit"}),
    ]
    for key, dest in connectors:
        resp = client.post("/api/v1/certify", json={"connector_key": key, "destination": dest, "connection": {"simulate": True}})
        assert resp.status_code == 200
        body = resp.json()
        assert body["certified"] is True, f"Failed certification for {key}: {body}"

def test_hard_cases_rules_and_idempotency():
    base_payload = {
        "connector_key": "discourse",
        "rendition": {"title": "Valid Title", "body": "Clean post body", "is_promotional": False},
        "destination": {"base_url": "https://forum.test.local", "frequency_cap_max": 2, "self_promo_allowed": False, "disclosure_required": True},
        "connection": {"simulate": True}
    }
    # 1. Idempotency check
    r1 = client.post("/api/v1/jobs", json=base_payload, headers={"Idempotency-Key": "idem-999"})
    r2 = client.post("/api/v1/jobs", json=base_payload, headers={"Idempotency-Key": "idem-999"})
    assert r1.status_code == 202
    assert r1.json()["job_id"] == r2.json()["job_id"]

    # 2. Frequency cap exceeded
    cap_payload = {**base_payload, "state": {"posts_in_window": 2}}
    r_cap = client.post("/api/v1/jobs", json=cap_payload)
    assert r_cap.status_code == 422
    assert r_cap.json()["error"]["code"] == "DEST_RULE_FREQUENCY_CAP"

    # 3. Self-promotion blocked
    promo_payload = {**base_payload, "rendition": {**base_payload["rendition"], "is_promotional": True}}
    r_promo = client.post("/api/v1/jobs", json=promo_payload)
    assert r_promo.status_code == 422
    assert r_promo.json()["error"]["code"] == "DEST_SPEC_VIOLATION"

    # 4. Missing AI disclosure blocked
    ai_payload = {**base_payload, "rendition": {"title": "AI Post", "body": "Generated text", "is_ai_generated": True, "ai_disclosed": False}}
    r_ai = client.post("/api/v1/jobs", json=ai_payload)
    assert r_ai.status_code == 422
    assert r_ai.json()["error"]["code"] == "DEST_SPEC_VIOLATION"