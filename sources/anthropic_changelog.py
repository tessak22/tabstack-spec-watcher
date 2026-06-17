"""
Anthropic changelog watcher.
Source: https://docs.anthropic.com/en/release-notes/api
Uses /extract to pull changelog entries, surfaces new model versions, deprecations, breaking changes.
"""

from tabstack import Tabstack
from datetime import datetime, timezone
from schema import SpecChange

ANTHROPIC_URL = "https://docs.anthropic.com/en/release-notes/api"

SCHEMA = {
    "type": "object",
    "properties": {
        "entries": {
            "type": "array",
            "description": "All changelog entries on the page, newest first",
            "items": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "Release date, e.g. 'June 2025'"},
                    "title": {"type": "string"},
                    "description": {"type": "string", "description": "Full text of the entry"},
                    "is_deprecation": {"type": "boolean", "description": "True if this entry announces a deprecation"},
                    "is_breaking": {"type": "boolean", "description": "True if this entry announces a breaking change or model removal"},
                    "models_affected": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Model names mentioned, e.g. ['claude-3-opus-20240229']"
                    }
                }
            }
        }
    }
}


def fetch(client: Tabstack | None = None) -> dict:
    """
    Fetch current Anthropic changelog entries.
    Returns raw dict suitable for diffing.
    """
    if client is None:
        client = Tabstack()

    result = client.extract.json(
        url=ANTHROPIC_URL,
        json_schema=SCHEMA,
        effort="standard",
    )

    fetched_at = datetime.now(timezone.utc).isoformat()

    return {
        "source": "Anthropic",
        "url": ANTHROPIC_URL,
        "fetched_at": fetched_at,
        "entries": result.get("entries", []),
    }


def diff(previous: dict, current: dict) -> list[SpecChange]:
    """
    Compare two fetch() results. Return SpecChange for new entries since last run.
    Keyed on title — if a title is new, it's a new entry.
    """
    if not previous:
        return []

    prev_titles = {e["title"] for e in previous.get("entries", [])}
    changes = []

    for entry in current.get("entries", []):
        if entry["title"] in prev_titles:
            continue  # already seen

        is_breaking = entry.get("is_breaking", False)
        is_deprecation = entry.get("is_deprecation", False)

        if is_breaking:
            change_type = "breaking"
            severity = "high"
        elif is_deprecation:
            change_type = "breaking"
            severity = "medium"
        else:
            change_type = "additive"
            severity = "low"

        changes.append(SpecChange(
            source="Anthropic",
            name=entry.get("title", "Untitled"),
            change_type=change_type,
            severity=severity,
            summary=entry.get("description", "")[:300],
            affects=entry.get("models_affected", ["Anthropic API"]),
            stage_before=None,
            stage_after=None,
            version_before=None,
            version_after=entry.get("date"),
            link=ANTHROPIC_URL,
            fetched_at=current["fetched_at"],
        ))

    return changes


if __name__ == "__main__":
    import json
    client = Tabstack()
    print("Fetching Anthropic changelog...")
    result = fetch(client)
    print(f"Found {len(result['entries'])} entries")
    print(json.dumps(result, indent=2))
