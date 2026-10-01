from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ClaimStatus(str, Enum):
    supported = "supported"
    disputed = "disputed"
    unresolved = "unresolved"
    superseded = "superseded"


class AccessStatus(str, Enum):
    public = "public"
    restricted = "restricted"
    sealed = "sealed"
    unavailable = "unavailable"


class Source(StrictModel):
    id: str = Field(min_length=1)
    issuing_body: str = Field(min_length=1)
    url: HttpUrl
    publication_date: datetime | None = None
    retrieved_at: datetime
    access_status: AccessStatus
    document_hash: str | None = None
    excerpt_locator: str | None = None


class Claim(StrictModel):
    id: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    evidence_refs: list[str] = Field(default_factory=list)
    confidence_basis: str = Field(min_length=1)
    status: ClaimStatus


class EvidencePacket(StrictModel):
    schema_version: str = "evidence_packet.v1"
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    summary: str
    jurisdiction: str = Field(min_length=1)
    sources: list[Source] = Field(min_length=1)
    claims: list[Claim] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    revision: int = Field(ge=1, default=1)

    @model_validator(mode="after")
    def validate_evidence(self):
        if self.schema_version != "evidence_packet.v1":
            raise ValueError("Unsupported schema version")
        ids = [s.id for s in self.sources]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate source IDs")
        if len({c.id for c in self.claims}) != len(self.claims):
            raise ValueError("Duplicate claim IDs")
        for claim in self.claims:
            if set(claim.evidence_refs) - set(ids):
                raise ValueError(f"Unknown source reference in claim {claim.id}")
            if claim.status == ClaimStatus.supported:
                if not claim.evidence_refs:
                    raise ValueError("Supported claims require evidence")
                if any(s.access_status != AccessStatus.public for s in self.sources if s.id in claim.evidence_refs):
                    raise ValueError("Supported claims in export require accessible public evidence")
        return self
