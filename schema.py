"""
Shared output schema for all spec watcher sources.
Every source returns a list of SpecChange objects.
"""

from dataclasses import dataclass, asdict
from typing import Literal
import json

ChangeType = Literal["breaking", "additive", "informational"]
Severity   = Literal["high", "medium", "low"]

@dataclass
class SpecChange:
    source: str          # "TC39" | "IETF" | "WHATWG" | "Anthropic" | "OpenAI" | "W3C"
    name: str            # proposal/spec/RFC name
    change_type: ChangeType
    severity: Severity
    summary: str         # one sentence, plain English
    affects: list[str]   # e.g. ["date handling", "auth flows"]
    stage_before: str | None  # for TC39: "Stage 2"
    stage_after: str | None   # for TC39: "Stage 3"
    version_before: str | None
    version_after: str | None
    link: str
    fetched_at: str      # ISO 8601

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
