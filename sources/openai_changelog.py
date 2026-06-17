"""
OpenAI changelog watcher.
Source: https://platform.openai.com/docs/changelog
"""

from tabstack import Tabstack
from datetime import datetime, timezone
from schema import SpecChange

OPENAI_URL = "https://platform.openai.com/docs/changelog"

SCHEMA = {
    "type": "object",
    "properties": {
        "entries": {
            "type": "array",
            "description": "All changelog entries on the page, newest first",
            "items": {
                "type": "object",
                "properties": {
                    "date": {"type": "string"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "is_deprecation": {"type": "boolean"},
                    "is_breaking": {"type": "boolean"},
                    "models_affected": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                }
            }
        }
    }
}


def fetch(client: Tabstack | None = None) -> dict:
    if client is None:
        client = Tabstack()

    result = client.extract.json(
        url=OPENAI_URL,
        json_schema=SCHEMA,
        effort="standard",
    )

    return {
        "source": "OpenAI",
        "url": OPENAI_URL,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "entries": result.get("entries", []),
    }


def diff(previous: dict, current: dict) -> list[SpecChange]:
    if not previous:
        return []

    prev_titles = {e["title"] for e in previous.get("entries", [])}
    changes = []

    for entry in current.get("entries", []):
        if entry["title"] in prev_titles:
            continue

        is_breaking = entry.get("is_breaking", False)
        is_deprecation = entry.get("is_deprecation", False)

        changes.append(SpecChange(
            source="OpenAI",
            name=entry.get("title", "Untitled"),
            change_type="breaking" if (is_breaking or is_deprecation) else "additive",
            severity="high" if is_breaking else ("medium" if is_deprecation else "low"),
            summary=entry.get("description", "")[:300],
            affects=entry.get("models_affected", ["OpenAI API"]),
            stage_before=None,
            stage_after=None,
            version_before=None,
            version_after=entry.get("date"),
            link=OPENAI_URL,
            fetched_at=current["fetched_at"],
        ))

    return changes


if __name__ == "__main__":
    import json
    client = Tabstack()
    print("Fetching OpenAI changelog...")
    result = fetch(client)
    print(f"Found {len(result['entries'])} entries")
    print(json.dumps(result, indent=2))
