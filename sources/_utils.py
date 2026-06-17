"""
Shared utilities for tabstack-spec-watcher sources.
"""
import re
from typing import Optional

# Keyword → domain tag mapping for affects inference
AFFECTS_MAP = [
    (["temporal", "date", "time", "clock", "timezone"],              ["date/time handling"]),
    (["async", "await", "promise", "concurrent", "microtask"],       ["async/await", "concurrency"]),
    (["iterator", "generator", "iterable", "for..of"],               ["iterators", "generators"]),
    (["regex", "regexp", "regular expression"],                       ["regular expressions"]),
    (["class", "private field", "decorator", "accessor"],             ["OOP", "classes"]),
    (["module", "import", "export", "esm", "commonjs", "require"],   ["modules", "imports"]),
    (["type", "typeof", "instanceof", "interface", "generic"],        ["type checking"]),
    (["array", "typed array", "arraybuffer", "collection"],          ["arrays", "collections"]),
    (["object", "prototype", "proxy", "reflect"],                    ["objects", "metaprogramming"]),
    (["dom", "shadow dom", "web component", "custom element"],       ["DOM", "Web Components"]),
    (["worker", "service worker", "shared worker"],                  ["Web Workers"]),
    (["auth", "crypto", "webcrypto", "jwt", "oauth", "webauthn"],    ["auth", "cryptography"]),
    (["wasm", "webassembly", "gc", "simd", "linear memory"],         ["WebAssembly"]),
    (["css", "style", "layout", "flexbox", "grid", "cascade"],       ["CSS"]),
    (["fetch", "websocket", "http", "cors", "stream", "network"],    ["networking", "fetch API"]),
    (["error", "exception", "stack trace", "cause"],                 ["error handling"]),
    (["record", "tuple", "immutable", "value type"],                 ["data structures"]),
    (["intl", "locale", "i18n", "unicode", "text segmentation"],     ["internationalization"]),
    (["signal", "observable", "reactive"],                           ["reactivity", "signals"]),
    (["json", "serialization", "parse"],                             ["JSON", "serialization"]),
    (["nullish", "optional chaining", "?."],                         ["null handling"]),
    (["string", "template literal"],                                 ["strings"]),
    (["bigint", "numeric", "float", "integer"],                      ["numbers", "math"]),
    (["symbol", "well-known symbol"],                                ["symbols"]),
    (["weakmap", "weakset", "weakref", "finalization"],              ["memory management"]),
    (["source map", "devtools", "inspector"],                        ["debugging", "developer tooling"]),
    (["pipeline", "operator", "|>"],                                 ["functional programming"]),
    (["pattern matching", "match"],                                  ["pattern matching"]),
    (["tail call", "optimization", "jit"],                           ["runtime performance"]),
]


def infer_affects(name: str, description: str = "") -> list[str]:
    """
    Infer affected domains from a proposal/change name and description.
    Returns a list of domain tags, or ["JavaScript"] as fallback.
    """
    text = (name + " " + description).lower()
    matched = []
    seen: set[str] = set()

    for keywords, domains in AFFECTS_MAP:
        if any(kw in text for kw in keywords):
            for d in domains:
                if d not in seen:
                    matched.append(d)
                    seen.add(d)

    return matched if matched else ["JavaScript"]


def parse_semver(version_str: str) -> Optional[tuple[int, int, int]]:
    """
    Parse a version string into (major, minor, patch).
    Handles: "v1.2.3", "1.2.3", "Node.js 22.0.0", "22.0.0-rc1".
    Returns None if unparseable.
    """
    if not version_str:
        return None
    m = re.search(r"(\d+)\.(\d+)\.(\d+)", version_str)
    if m:
        return (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    m = re.search(r"v?(\d+)$", version_str.strip())
    if m:
        return (int(m.group(1)), 0, 0)
    return None


def classify_semver_change(prev_version: str, curr_version: str) -> tuple[str, str]:
    """
    Returns (change_type, severity) based on semver bump.
    major → breaking/high, minor → additive/medium, patch → informational/low
    """
    prev = parse_semver(prev_version)
    curr = parse_semver(curr_version)

    if prev is None or curr is None:
        return ("additive", "medium")

    if curr[0] > prev[0]:
        return ("breaking", "high")
    elif curr[1] > prev[1]:
        return ("additive", "medium")
    else:
        return ("informational", "low")


# Shared JSON schema for GitHub releases pages
GITHUB_RELEASES_SCHEMA = {
    "type": "object",
    "properties": {
        "releases": {
            "type": "array",
            "description": "Recent releases listed on the page, newest first",
            "items": {
                "type": "object",
                "properties": {
                    "version":    {"type": "string", "description": "Version tag, e.g. 'v22.4.0' or '5.8.3'"},
                    "date":       {"type": "string", "description": "Release date string"},
                    "title":      {"type": "string", "description": "Release title or tag name"},
                    "highlights": {"type": "string", "description": "Key changes, 2-3 sentences max"},
                    "is_breaking":{"type": "boolean", "description": "True if release notes mention breaking changes"},
                    "is_security":{"type": "boolean", "description": "True if this is a security release"},
                    "is_lts":     {"type": "boolean", "description": "True if this is an LTS/stable release"},
                },
            },
        }
    },
}
