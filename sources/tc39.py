"""
TC39 proposal watcher.
Source: https://github.com/tc39/proposals (README.md)
Uses /extract to pull proposal table, classifies stage changes as breaking/additive/informational.
"""

from tabstack import Tabstack
from datetime import datetime, timezone
from schema import SpecChange
from sources._utils import infer_affects

TC39_URL = "https://github.com/tc39/proposals"

SCHEMA = {
    "type": "object",
    "properties": {
        "stage4": {
            "type": "array",
            "description": "Finished proposals at Stage 4 (in spec or landing in next version)",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "link": {"type": "string"}
                }
            }
        },
        "stage3": {
            "type": "array",
            "description": "Candidate proposals at Stage 3",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "link": {"type": "string"}
                }
            }
        },
        "stage2_7": {
            "type": "array",
            "description": "Proposals at Stage 2.7",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "link": {"type": "string"}
                }
            }
        },
        "stage2": {
            "type": "array",
            "description": "Draft proposals at Stage 2",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "link": {"type": "string"}
                }
            }
        },
        "stage1": {
            "type": "array",
            "description": "Proposals at Stage 1",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "link": {"type": "string"}
                }
            }
        }
    }
}

STAGE_SEVERITY = {
    "Stage 4": "high",       # in the spec — ship it or break things
    "Stage 3": "medium",     # candidates — implementations starting
    "Stage 2.7": "medium",
    "Stage 2": "low",
    "Stage 1": "low",
}

STAGE_CHANGE_TYPE = {
    "Stage 4": "breaking",   # Stage 4 = real behavioral change incoming
    "Stage 3": "additive",
    "Stage 2.7": "additive",
    "Stage 2": "informational",
    "Stage 1": "informational",
}


def fetch(client: Tabstack | None = None) -> dict:
    """
    Fetch current TC39 proposal state.
    Returns raw dict suitable for diffing or direct consumption.
    """
    if client is None:
        client = Tabstack()

    result = client.extract.json(
        url=TC39_URL,
        json_schema=SCHEMA,
        effort="standard",
    )

    fetched_at = datetime.now(timezone.utc).isoformat()

    # Normalize into flat list with stage labels
    proposals = []
    stage_map = {
        "stage4": "Stage 4",
        "stage3": "Stage 3",
        "stage2_7": "Stage 2.7",
        "stage2": "Stage 2",
        "stage1": "Stage 1",
    }
    for key, label in stage_map.items():
        for p in result.get(key, []):
            proposals.append({
                "name": p.get("name", ""),
                "description": p.get("description", ""),
                "link": p.get("link", TC39_URL),
                "stage": label,
            })

    return {
        "source": "TC39",
        "url": TC39_URL,
        "fetched_at": fetched_at,
        "proposals": proposals,
    }


def diff(previous: dict, current: dict) -> list[SpecChange]:
    """
    Compare two fetch() results. Return SpecChange list for anything that moved stages.
    Pass previous={} on first run — returns nothing (no baseline to diff against).
    """
    if not previous:
        return []

    prev_map = {p["name"]: p["stage"] for p in previous.get("proposals", [])}
    curr_map = {p["name"]: p for p in current.get("proposals", [])}

    changes = []
    for name, proposal in curr_map.items():
        current_stage = proposal["stage"]
        previous_stage = prev_map.get(name)

        if previous_stage is None:
            # New proposal appeared
            changes.append(SpecChange(
                source="TC39",
                name=name,
                change_type="informational",
                severity="low",
                summary=f"New TC39 proposal added at {current_stage}: {proposal.get('description', '')}",
                affects=infer_affects(name, proposal.get("description", "")),
                stage_before=None,
                stage_after=current_stage,
                version_before=None,
                version_after=None,
                link=proposal.get("link", TC39_URL),
                fetched_at=current["fetched_at"],
            ))
        elif previous_stage != current_stage:
            # Stage advanced
            changes.append(SpecChange(
                source="TC39",
                name=name,
                change_type=STAGE_CHANGE_TYPE.get(current_stage, "informational"),
                severity=STAGE_SEVERITY.get(current_stage, "low"),
                summary=f"{name} advanced from {previous_stage} to {current_stage}: {proposal.get('description', '')}",
                affects=infer_affects(name, proposal.get("description", "")),
                stage_before=previous_stage,
                stage_after=current_stage,
                version_before=None,
                version_after=None,
                link=proposal.get("link", TC39_URL),
                fetched_at=current["fetched_at"],
            ))

    return changes


if __name__ == "__main__":
    import json
    client = Tabstack()
    print("Fetching TC39 proposals...")
    result = fetch(client)
    print(f"Found {len(result['proposals'])} proposals across all stages")
    print(json.dumps(result, indent=2))
