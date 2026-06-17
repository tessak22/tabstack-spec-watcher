"""
Deno release watcher.
Source: https://github.com/denoland/deno/releases
"""

from tabstack import Tabstack
from datetime import datetime, timezone
from schema import SpecChange
from sources._utils import classify_semver_change, GITHUB_RELEASES_SCHEMA

DENO_URL = "https://github.com/denoland/deno/releases"


def fetch(client: Tabstack | None = None) -> dict:
    if client is None:
        client = Tabstack()

    result = client.extract.json(
        url=DENO_URL,
        json_schema=GITHUB_RELEASES_SCHEMA,
        effort="standard",
    )

    return {
        "source": "Deno",
        "url": DENO_URL,
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

        if release.get("is_security"):
            severity = "high"
            change_type = "breaking"

        changes.append(SpecChange(
            source="Deno",
            name=f"Deno {version}",
            change_type=change_type,
            severity=severity,
            summary=release.get("highlights", f"Deno {version} released."),
            affects=["Deno runtime", "Deno standard library"],
            stage_before=None,
            stage_after=None,
            version_before=prev_version,
            version_after=version,
            link=DENO_URL,
            fetched_at=current["fetched_at"],
        ))

    return changes


if __name__ == "__main__":
    import json
    client = Tabstack()
    print("Fetching Deno releases...")
    result = fetch(client)
    print(f"Found {len(result['releases'])} releases")
    print(json.dumps(result, indent=2))
