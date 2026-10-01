from datetime import datetime, timezone
from fastapi.testclient import TestClient
from civic_ledger.api import app

def test_store_and_record(monkeypatch, tmp_path):
    monkeypatch.setenv("CIVIC_LEDGER_DB", str(tmp_path / "ledger.db"))
    monkeypatch.setenv("CIVIC_LEDGER_TOKEN", "test-token")
    client = TestClient(app)
    payload = {"id":"p1","title":"Example","summary":"A sample record","jurisdiction":"US",
      "sources":[{"id":"s1","issuing_body":"Example agency","url":"https://example.gov/doc",
                  "retrieved_at":datetime.now(timezone.utc).isoformat(),"access_status":"public"}],
      "claims":[{"id":"c1","statement":"Example claim","evidence_refs":["s1"],
                 "confidence_basis":"Primary record","status":"supported"}]}
    assert client.post("/v1/evidence", json=payload).status_code == 401
    headers = {"x-operator-token":"test-token"}
    assert client.post("/v1/evidence", json=payload, headers=headers).status_code == 201
    assert client.post("/v1/evidence", json=payload, headers=headers).status_code == 409
    assert client.get("/v1/evidence/p1/1", headers=headers).json()["id"] == "p1"
    page = client.get("/v1/evidence/p1/1/record", headers=headers)
    assert page.status_code == 200 and "Show Me the Record" in page.text
