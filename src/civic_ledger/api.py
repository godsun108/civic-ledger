from fastapi import FastAPI
from .models import EvidencePacket

app = FastAPI(title="Civic Ledger", version="0.1.0")

@app.get("/health")
def health():
    return {"status": "ok", "engine": "civic-ledger"}

@app.post("/v1/evidence/validate", response_model=EvidencePacket)
def validate_packet(packet: EvidencePacket):
    """Validate and echo a packet; this endpoint does not ingest, store, or publish it."""
    return packet
