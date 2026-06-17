"""
Google AI / Gemini changelog watcher.
Source: https://ai.google.dev/gemini-api/docs/changelog
Tracks model deprecations, new models, API breaking changes.
"""

from tabstack import Tabstack
from datetime import datetime, timezone
from schema import SpecChange

GOOGLE_AI_URL = "https://ai.google.dev/gemini-api/docs/changelog"

SCHEMA = {
    "type": "object",
    "properties": {
        "entries": {
            "type": "array",
            "description": "Changelog entries, newest first",
            "items": {
                "type": "object",
                "properties": {
                    "date":             {"type": "string"},
                    "title":            {"type": "string"},
                    "description":      {"type": "string"},
                    "is_deprecation":   {"type": "boolean"},
                    "is_breaking":      {"type": "boolean"},
                    "models_affected":  {"type": "array", "items": {"type": "string"}},
                },
            },
        }
    },
}


def fetch(client: Tabstack | None = None) -> dict:
    if client is None:
        client = Tabstack()

    result = client.extract.json(
        url=GOOGLE_AI_URL,
        json_schema=SCHEMA,
        effort="standard",
    )

    return {
        "source": "Google AI",
        "url": GOOGLE_AI_URL,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "entries": result.get("entries", []),
    }


def diff(previous: dict, current: dict) -> list[SpecChange]:
    if not previous:
        return []

    prev_titles = {e["title"] for e in previous.get("entries", [])}
    changes = []

    for entry in current.get("entries", []):
        if entry.get("title") in prev_titles:
            continue

        is_breaking = entry.get("is_breaking", False)
        is_deprecation = entry.get("is_deprecation", False)

        change_type = "breaking" if (is_breaking or is_deprecation) else "additive"
        severity = "high" if is_breaking else ("medium" if is_deprecation else "low")

        changes.append(SpecChange(
            source="Google AI",
            name=entry.get("title", "Untitled"),
            change_type=change_type,
            severity=severity,
            summary=entry.get("description", "")[:300],
            affects=entry.get("models_affected") or ["Gemini API"],
            stage_before=None,
            stage_after=None,
            version_before=None,
            version_after=entry.get("date"),
            link=GOOGLE_AI_URL,
            fetched_at=current["fetched_at"],
        ))

    return changes


if __name__ == "__main__":
    import json
    client = Tabstack()
    print("Fetching Google AI changelog...")
    result = fetch(client)
    print(f"Found {len(result['entries'])} entries")
    print(json.dumps(result, indent=2))
