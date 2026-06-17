"""
npm ecosystem watcher — React, Next.js, Vue, Vite, Remix, Astro, Svelte.
Sources: GitHub releases pages for each framework.
Tracks major version bumps (breaking) and minor releases (additive).
"""

from tabstack import Tabstack
from datetime import datetime, timezone
from schema import SpecChange
from sources._utils import classify_semver_change, infer_affects, GITHUB_RELEASES_SCHEMA

PACKAGES = {
    "React":   "https://github.com/facebook/react/releases",
    "Next.js": "https://github.com/vercel/next.js/releases",
    "Vue":     "https://github.com/vuejs/core/releases",
    "Vite":    "https://github.com/vitejs/vite/releases",
    "Remix":   "https://github.com/remix-run/remix/releases",
    "Astro":   "https://github.com/withastro/astro/releases",
    "Svelte":  "https://github.com/sveltejs/svelte/releases",
}


def fetch(client: Tabstack | None = None) -> dict:
    """
    Fetch latest releases for all tracked npm packages.
    Returns dict keyed by package name.
    """
    if client is None:
        client = Tabstack()

    fetched_at = datetime.now(timezone.utc).isoformat()
    packages = {}

    for pkg_name, url in PACKAGES.items():
        try:
            result = client.extract.json(
                url=url,
                json_schema=GITHUB_RELEASES_SCHEMA,
                effort="standard",
            )
            packages[pkg_name] = {
                "url": url,
                "releases": result.get("releases", []),
            }
        except Exception as e:
            packages[pkg_name] = {
                "url": url,
                "releases": [],
                "error": str(e),
            }

    return {
        "source": "npm ecosystem",
        "fetched_at": fetched_at,
        "packages": packages,
    }


def diff(previous: dict, current: dict) -> list[SpecChange]:
    if not previous:
        return []

    changes = []

    for pkg_name, curr_data in current.get("packages", {}).items():
        prev_data = previous.get("packages", {}).get(pkg_name, {})
        prev_versions = {r["version"] for r in prev_data.get("releases", [])}

        for release in curr_data.get("releases", []):
            version = release.get("version", "")
            if version in prev_versions or not version:
                continue

            prev_version = prev_data.get("releases", [{}])[0].get("version", "")
            change_type, severity = classify_semver_change(prev_version, version)
            highlights = release.get("highlights", "")
            affects = infer_affects(pkg_name + " " + highlights) or [pkg_name]

            changes.append(SpecChange(
                source=f"npm / {pkg_name}",
                name=f"{pkg_name} {version}",
                change_type=change_type,
                severity=severity,
                summary=highlights or f"{pkg_name} {version} released.",
                affects=affects,
                stage_before=None,
                stage_after=None,
                version_before=prev_version,
                version_after=version,
                link=curr_data.get("url", ""),
                fetched_at=current["fetched_at"],
            ))

    return changes


if __name__ == "__main__":
    import json
    client = Tabstack()
    print("Fetching npm ecosystem releases...")
    result = fetch(client)
    for pkg, data in result["packages"].items():
        count = len(data.get("releases", []))
        err = data.get("error", "")
        print(f"  {pkg}: {count} releases{' [ERROR: ' + err + ']' if err else ''}")
    print(json.dumps(result, indent=2))
