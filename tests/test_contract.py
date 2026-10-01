from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from civic_ledger.models import EvidencePacket

NOW = datetime.now(timezone.utc)
BASE = dict(id="packet-1", title="Test", summary="Sample", jurisdiction="US",
            sources=[dict(id="source-1", issuing_body="Example Agency",
                          url="https://example.gov/record", retrieved_at=NOW,
                          access_status="public")],
            claims=[dict(id="claim-1", statement="An example event occurred",
                         evidence_refs=["source-1"], confidence_basis="Direct source",
                         status="supported")])

def test_valid_packet():
    assert EvidencePacket(**BASE).schema_version == "evidence_packet.v1"

def test_rejects_missing_source():
    data = {**BASE, "claims": [{**BASE["claims"][0], "evidence_refs": ["missing"]}]}
    with pytest.raises(ValidationError):
        EvidencePacket(**data)

def test_rejects_sealed_supporting_source():
    data = {**BASE, "sources": [{**BASE["sources"][0], "access_status": "sealed"}]}
    with pytest.raises(ValidationError):
        EvidencePacket(**data)
