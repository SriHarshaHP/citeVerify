import pytest
from starlette.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_api_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"
    assert data["app"] == "CiteVerify"

def test_api_demo_verification(client):
    res = client.post("/api/verify/demo")
    assert res.status_code == 200
    data = res.json()
    assert data["document_name"] == "demo_doc.txt"
    assert data["total_claims"] == 8
    assert len(data["claim_cards"]) == 8

def test_api_review_override_and_audit(client):
    # First get latest report
    res = client.get("/api/reports/latest")
    assert res.status_code == 200
    
    # Override claim C2
    override_payload = {
        "claim_id": "C2",
        "action": "overridden",
        "new_verdict": "UNSUPPORTED",
        "note": "Peer reviewer determined number discrepancy is severe."
    }
    res_override = client.post("/api/review/action", json=override_payload)
    assert res_override.status_code == 200
    override_data = res_override.json()
    assert override_data["reviewer_status"] == "overridden"
    assert override_data["audit_entry"]["action"] == "overridden"

    # Verify audit retrieval endpoint
    res_audit = client.get("/api/audit/claim/C2")
    assert res_audit.status_code == 200
    audit_data = res_audit.json()
    assert len(audit_data["entries"]) >= 2  # generated + overridden

def test_api_exports(client):
    # Test JSON export
    res_json = client.get("/api/export/json")
    assert res_json.status_code == 200
    assert "CiteVerify" in res_json.text

    # Test CSV export
    res_csv = client.get("/api/export/csv")
    assert res_csv.status_code == 200
    assert "Claim ID" in res_csv.text

    # Test HTML printable export
    res_html = client.get("/api/export/html")
    assert res_html.status_code == 200
    assert "<!DOCTYPE html>" in res_html.text
    assert "Evidence-Backed Verification Report" in res_html.text

def test_frontend_index_served(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "<!DOCTYPE html>" in res.text
    assert "CiteVerify" in res.text
