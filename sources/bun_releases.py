"""
Bun release watcher.
Source: https://github.com/oven-sh/bun/releases
"""

from tabstack import Tabstack
from datetime import datetime, timezone
from schema import SpecChange
from sources._utils import classify_semver_change, GITHUB_RELEASES_SCHEMA

BUN_URL = "https://github.com/oven-sh/bun/releases"


def fetch(client: Tabstack | None = None) -> dict:
    if client is None:
        client = Tabstack()

    result = client.extract.json(
        url=BUN_URL,
        json_schema=GITHUB_RELEASES_SCHEMA,
        effort="standard",
    )

    return {
        "source": "Bun",
        "url": BUN_URL,
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

        changes.append(SpecChange(
            source="Bun",
            name=f"Bun {version}",
            change_type=change_type,
            severity=severity,
            summary=release.get("highlights", f"Bun {version} released."),
            affects=["Bun runtime", "Bun bundler", "Bun test runner"],
            stage_before=None,
            stage_after=None,
            version_before=prev_version,
            version_after=version,
            link=BUN_URL,
            fetched_at=current["fetched_at"],
        ))

    return changes


if __name__ == "__main__":
    import json
    client = Tabstack()
    print("Fetching Bun releases...")
    result = fetch(client)
    print(f"Found {len(result['releases'])} releases")
    print(json.dumps(result, indent=2))
