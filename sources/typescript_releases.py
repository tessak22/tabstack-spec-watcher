"""
TypeScript release watcher.
Source: https://github.com/microsoft/TypeScript/releases
Tracks new TS releases — major compiler breaking changes, new type features.
"""

from tabstack import Tabstack
from datetime import datetime, timezone
from schema import SpecChange
from sources._utils import classify_semver_change, infer_affects, GITHUB_RELEASES_SCHEMA

TS_URL = "https://github.com/microsoft/TypeScript/releases"


def fetch(client: Tabstack | None = None) -> dict:
    if client is None:
        client = Tabstack()

    result = client.extract.json(
        url=TS_URL,
        json_schema=GITHUB_RELEASES_SCHEMA,
        effort="standard",
    )

    return {
        "source": "TypeScript",
        "url": TS_URL,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "releases": result.get("releases", []),
    }


def diff(previous: dict, current: dict) -> list[SpecChange]:
    if not previous:
        return []

    prev_versions = {r["version"] for r in previous.get("releases", [])}
    changes = []

    for release in current.get("releases", []):
        version = release.get("version", "")
        if version in prev_versions or not version:
            continue

        prev_version = previous.get("releases", [{}])[0].get("version", "")
        change_type, severity = classify_semver_change(prev_version, version)
        highlights = release.get("highlights", "")
        affects = infer_affects(version, highlights) or ["TypeScript compiler", "type checking"]

        changes.append(SpecChange(
            source="TypeScript",
            name=f"TypeScript {version}",
            change_type=change_type,
            severity=severity,
            summary=highlights or f"TypeScript {version} released.",
            affects=affects,
            stage_before=None,
            stage_after=None,
            version_before=prev_version,
            version_after=version,
            link=TS_URL,
            fetched_at=current["fetched_at"],
        ))

    return changes


if __name__ == "__main__":
    import json
    client = Tabstack()
    print("Fetching TypeScript releases...")
    result = fetch(client)
    print(f"Found {len(result['releases'])} releases")
    print(json.dumps(result, indent=2))
