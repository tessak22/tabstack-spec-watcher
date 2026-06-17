"""
WebAssembly proposals watcher.
Source: https://github.com/WebAssembly/proposals
Tracks proposal phase changes (Phase 1–5, mirroring TC39 stages).
"""

from tabstack import Tabstack
from datetime import datetime, timezone
from schema import SpecChange

WASM_URL = "https://github.com/WebAssembly/proposals"

SCHEMA = {
    "type": "object",
    "properties": {
        "phase5": {
            "type": "array",
            "description": "Phase 5: Standardized proposals",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "link": {"type": "string"},
                },
            },
        },
        "phase4": {
            "type": "array",
            "description": "Phase 4: Standardization",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "link": {"type": "string"},
                },
            },
        },
        "phase3": {
            "type": "array",
            "description": "Phase 3: Implementation",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "link": {"type": "string"},
                },
            },
        },
        "phase2": {
            "type": "array",
            "description": "Phase 2: Proposed spec text",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "link": {"type": "string"},
                },
            },
        },
        "phase1": {
            "type": "array",
            "description": "Phase 1: Feature proposal",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "link": {"type": "string"},
                },
            },
        },
    },
}

PHASE_SEVERITY = {
    "Phase 5": "high",
    "Phase 4": "high",
    "Phase 3": "medium",
    "Phase 2": "low",
    "Phase 1": "low",
}

PHASE_CHANGE_TYPE = {
    "Phase 5": "breaking",
    "Phase 4": "breaking",
    "Phase 3": "additive",
    "Phase 2": "informational",
    "Phase 1": "informational",
}

PHASE_KEYS = {
    "phase5": "Phase 5",
    "phase4": "Phase 4",
    "phase3": "Phase 3",
    "phase2": "Phase 2",
    "phase1": "Phase 1",
}


def fetch(client: Tabstack | None = None) -> dict:
    if client is None:
        client = Tabstack()

    result = client.extract.json(
        url=WASM_URL,
        json_schema=SCHEMA,
        effort="standard",
    )

    fetched_at = datetime.now(timezone.utc).isoformat()
    proposals = []
    for key, label in PHASE_KEYS.items():
        for p in result.get(key, []):
            proposals.append({
                "name": p.get("name", ""),
                "description": p.get("description", ""),
                "link": p.get("link", WASM_URL),
                "phase": label,
            })

    return {
        "source": "WebAssembly",
        "url": WASM_URL,
        "fetched_at": fetched_at,
        "proposals": proposals,
    }


def diff(previous: dict, current: dict) -> list[SpecChange]:
    if not previous:
        return []

    prev_map = {p["name"]: p["phase"] for p in previous.get("proposals", [])}
    curr_map = {p["name"]: p for p in current.get("proposals", [])}

    changes = []
    for name, proposal in curr_map.items():
        current_phase = proposal["phase"]
        previous_phase = prev_map.get(name)

        if previous_phase is None:
            changes.append(SpecChange(
                source="WebAssembly",
                name=name,
                change_type="informational",
                severity="low",
                summary=f"New Wasm proposal added at {current_phase}: {proposal.get('description', '')}",
                affects=["WebAssembly"],
                stage_before=None,
                stage_after=current_phase,
                version_before=None,
                version_after=None,
                link=proposal.get("link", WASM_URL),
                fetched_at=current["fetched_at"],
            ))
        elif previous_phase != current_phase:
            changes.append(SpecChange(
                source="WebAssembly",
                name=name,
                change_type=PHASE_CHANGE_TYPE.get(current_phase, "informational"),
                severity=PHASE_SEVERITY.get(current_phase, "low"),
                summary=f"{name} advanced from {previous_phase} to {current_phase}: {proposal.get('description', '')}",
                affects=["WebAssembly"],
                stage_before=previous_phase,
                stage_after=current_phase,
                version_before=None,
                version_after=None,
                link=proposal.get("link", WASM_URL),
                fetched_at=current["fetched_at"],
            ))

    return changes


if __name__ == "__main__":
    import json
    client = Tabstack()
    print("Fetching WebAssembly proposals...")
    result = fetch(client)
    print(f"Found {len(result['proposals'])} proposals")
    print(json.dumps(result, indent=2))
