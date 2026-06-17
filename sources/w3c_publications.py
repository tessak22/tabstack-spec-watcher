"""
W3C recent publications watcher.
Source: https://www.w3.org/TR/tr-status-all
Tracks new W3C Recommendations, Candidate Recommendations, and Working Drafts
that developers need to care about (CSS, HTML, WebAuthn, Web Crypto, ARIA, etc.).
"""

from tabstack import Tabstack
from datetime import datetime, timezone
from schema import SpecChange
from sources._utils import infer_affects

W3C_URL = "https://www.w3.org/TR/"

SCHEMA = {
    "type": "object",
    "properties": {
        "publications": {
            "type": "array",
            "description": "Recent W3C publications, newest first",
            "items": {
                "type": "object",
                "properties": {
                    "title":        {"type": "string"},
                    "status":       {"type": "string", "description": "e.g. 'Recommendation', 'Candidate Recommendation', 'Working Draft'"},
                    "date":         {"type": "string"},
                    "url":          {"type": "string"},
                    "description":  {"type": "string"},
                },
            },
        }
    },
}

STATUS_SEVERITY = {
    "Recommendation":            "high",
    "Candidate Recommendation":  "medium",
    "Proposed Recommendation":   "medium",
    "Working Draft":             "low",
    "Note":                      "low",
}

STATUS_CHANGE_TYPE = {
    "Recommendation":            "breaking",
    "Candidate Recommendation":  "additive",
    "Proposed Recommendation":   "additive",
    "Working Draft":             "informational",
    "Note":                      "informational",
}


def fetch(client: Tabstack | None = None) -> dict:
    if client is None:
        client = Tabstack()

    result = client.extract.json(
        url=W3C_URL,
        json_schema=SCHEMA,
        effort="standard",
    )

    return {
        "source": "W3C",
        "url": W3C_URL,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "publications": result.get("publications", []),
    }


def diff(previous: dict, current: dict) -> list[SpecChange]:
    if not previous:
        return []

    prev_urls = {p["url"] for p in previous.get("publications", []) if p.get("url")}
    prev_titles = {p["title"] for p in previous.get("publications", []) if p.get("title")}
    changes = []

    for pub in current.get("publications", []):
        url = pub.get("url", "")
        title = pub.get("title", "")

        if url in prev_urls or title in prev_titles:
            continue

        status = pub.get("status", "Working Draft")
        change_type = STATUS_CHANGE_TYPE.get(status, "informational")
        severity = STATUS_SEVERITY.get(status, "low")
        description = pub.get("description", "")
        affects = infer_affects(title, description) or ["web platform"]

        changes.append(SpecChange(
            source="W3C",
            name=title,
            change_type=change_type,
            severity=severity,
            summary=f"{title} published as {status}. {description}"[:300],
            affects=affects,
            stage_before=None,
            stage_after=status,
            version_before=None,
            version_after=pub.get("date"),
            link=url or W3C_URL,
            fetched_at=current["fetched_at"],
        ))

    return changes


if __name__ == "__main__":
    import json
    client = Tabstack()
    print("Fetching W3C publications...")
    result = fetch(client)
    print(f"Found {len(result['publications'])} publications")
    print(json.dumps(result, indent=2))
