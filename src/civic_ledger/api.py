import os
import sqlite3
from fastapi import FastAPI, Depends, Header, HTTPException
from fastapi.responses import HTMLResponse
from .models import EvidencePacket
from .storage import connect

app = FastAPI(title="Civic Ledger", version="0.2.0")

def operator(x_operator_token: str | None = Header(default=None)):
    import secrets
    expected = os.environ.get("CIVIC_LEDGER_TOKEN")
    if not expected or not x_operator_token or not secrets.compare_digest(x_operator_token, expected):
        raise HTTPException(401, "Operator token required")

@app.get("/health")
def health():
    return {"status": "ok", "engine": "civic-ledger"}

@app.post("/v1/evidence/validate", response_model=EvidencePacket)
def validate_packet(packet: EvidencePacket):
    return packet

@app.post("/v1/evidence", status_code=201, dependencies=[Depends(operator)])
def store_packet(packet: EvidencePacket):
    with connect() as db:
        try:
            db.execute("INSERT INTO packets (id, revision, payload) VALUES (?, ?, ?)",
                       (packet.id, packet.revision, packet.model_dump_json()))
        except sqlite3.IntegrityError:
            raise HTTPException(409, "This packet revision already exists")
    return {"id": packet.id, "revision": packet.revision, "stored": True}

@app.get("/v1/evidence/{packet_id}/{revision}", response_model=EvidencePacket, dependencies=[Depends(operator)])
def read_packet(packet_id: str, revision: int):
    with connect() as db:
        row = db.execute("SELECT payload FROM packets WHERE id=? AND revision=?",
                         (packet_id, revision)).fetchone()
    if not row:
        raise HTTPException(404, "Packet revision not found")
    return EvidencePacket.model_validate_json(row[0])

@app.get("/v1/evidence/{packet_id}/{revision}/record", response_class=HTMLResponse, dependencies=[Depends(operator)])
def show_record(packet_id: str, revision: int):
    from html import escape
    packet = read_packet(packet_id, revision)
    items = "".join(f'<li><a href="{escape(str(s.url), quote=True)}" rel="noopener noreferrer">{escape(s.issuing_body)}</a> — {escape(s.access_status.value)}; retrieved {escape(s.retrieved_at.isoformat())}</li>' for s in packet.sources)
    claims = "".join(f'<li>{escape(c.statement)} [{escape(c.status.value)}] — sources: {escape(", ".join(c.evidence_refs))}</li>' for c in packet.claims)
    return f'<!doctype html><html lang="en"><meta charset="utf-8"><title>Show Me the Record</title><main><h1>{escape(packet.title)}</h1><p>{escape(packet.summary)}</p><h2>Sources</h2><ul>{items}</ul><h2>Claims</h2><ul>{claims}</ul><h2>Limitations</h2><p>{escape("; ".join(packet.limitations))}</p><small>Revision {packet.revision} · Jurisdiction {escape(packet.jurisdiction)}</small></main></html>'
