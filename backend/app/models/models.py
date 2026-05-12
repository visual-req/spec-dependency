from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ExternalDependency:
    name: str
    type: str
    evidence: str
    confidence: float

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.type,
            "evidence": self.evidence,
            "confidence": self.confidence,
        }

