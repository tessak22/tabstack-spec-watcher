"""
tabstack-spec-watcher — main entry point.

Usage:
  python watch.py                     # run all sources, diff against last snapshot
  python watch.py --source tc39       # single source
  python watch.py --snapshot-only     # fetch + store, no diff output (first run baseline)
  python watch.py --one-shot          # fetch + print current state, no snapshot written
  python watch.py --format json       # output as JSON (default: human-readable)

Snapshot files are stored in ./snapshots/<source>.json
Changes are printed to stdout — pipe to Slack, email, Hermes, whatever you want.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from tabstack import Tabstack

# Add parent dir to path for schema import
sys.path.insert(0, str(Path(__file__).parent))
from schema import SpecChange

SNAPSHOT_DIR = Path(__file__).parent / "snapshots"
SNAPSHOT_DIR.mkdir(exist_ok=True)

SOURCES = {
    "tc39": "sources.tc39",
    "anthropic": "sources.anthropic_changelog",
    "openai": "sources.openai_changelog",
}


def load_snapshot(source: str) -> dict:
    path = SNAPSHOT_DIR / f"{source}.json"
    if path.exists():
        return json.loads(path.read_text())
    return {}


def save_snapshot(source: str, data: dict):
    path = SNAPSHOT_DIR / f"{source}.json"
    path.write_text(json.dumps(data, indent=2))


def run_source(name: str, client: Tabstack, one_shot: bool, snapshot_only: bool) -> list[SpecChange]:
    import importlib
    mod = importlib.import_module(SOURCES[name])

    print(f"[{name}] fetching...", file=sys.stderr)
    current = mod.fetch(client)
    print(f"[{name}] done", file=sys.stderr)

    if one_shot:
        # Don't diff, don't save — just return current state as informational items
        return []  # caller prints current directly

    previous = load_snapshot(name)
    changes = mod.diff(previous, current)

    if not snapshot_only:
        save_snapshot(name, current)
    else:
        save_snapshot(name, current)

    return changes


def format_human(changes: list[SpecChange]) -> str:
    if not changes:
        return "No changes detected."

    lines = []
    for c in sorted(changes, key=lambda x: {"high": 0, "medium": 1, "low": 2}[x.severity]):
        emoji = {"breaking": "🔴", "additive": "🟡", "informational": "ℹ️"}[c.change_type]
        lines.append(f"{emoji} [{c.severity.upper()}] {c.source} — {c.name}")
        lines.append(f"   {c.summary}")
        if c.stage_before and c.stage_after:
            lines.append(f"   Stage: {c.stage_before} → {c.stage_after}")
        if c.affects:
            lines.append(f"   Affects: {', '.join(c.affects)}")
        lines.append(f"   {c.link}")
        lines.append("")
    return "\n".join(lines)


def format_json(changes: list[SpecChange]) -> str:
    return json.dumps([c.to_dict() for c in changes], indent=2)


def main():
    parser = argparse.ArgumentParser(description="Tabstack spec watcher")
    parser.add_argument("--source", choices=list(SOURCES.keys()), help="Run single source only")
    parser.add_argument("--snapshot-only", action="store_true", help="Fetch and store baseline, no diff output")
    parser.add_argument("--one-shot", action="store_true", help="Fetch and print current state, no snapshot written")
    parser.add_argument("--format", choices=["human", "json"], default="human")
    args = parser.parse_args()

    client = Tabstack()
    sources_to_run = [args.source] if args.source else list(SOURCES.keys())

    all_changes: list[SpecChange] = []
    for name in sources_to_run:
        changes = run_source(name, client, args.one_shot, args.snapshot_only)
        all_changes.extend(changes)

    if args.snapshot_only:
        print(f"Snapshots saved for: {', '.join(sources_to_run)}", file=sys.stderr)
        return

    output = format_json(all_changes) if args.format == "json" else format_human(all_changes)
    print(output)


if __name__ == "__main__":
    main()
