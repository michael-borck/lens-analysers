#!/usr/bin/env python3
"""Regenerate the family table in README.md from each package's MANIFEST.

Single source of truth: each analyser declares its capabilities in a `MANIFEST`
(name, accepts, extensions, auto_routable, role). This script discovers those by
loading every package's `manifest.py` from the local workspace and rewrites the
table between markers in README.md, so the table never drifts from reality.

    python scripts/generate_family_table.py           # rewrite README.md
    python scripts/generate_family_table.py --check    # exit 1 if out of date (CI)

Routing facts (extensions, routable, which packages exist) come from the manifests.
The one-line human blurb is editorial and kept here; packages without a blurb fall
back to their `accepts` list, so a newly added analyser still appears automatically.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # the umbrella docs repo (holds README.md)
WORKSPACE = ROOT.parent  # the workspace dir; every analyser repo is a sibling of the umbrella
README = ROOT / "README.md"
START = "<!-- family-table:start -->"
END = "<!-- family-table:end -->"
GH = "https://github.com/michael-borck"
PYPI = "https://pypi.org/project"
EXCLUDE = (".venv", "site-packages", "node_modules", "/tests/", "/build/", "/dist/", "/.git/")

# Editorial one-liners (the only hand-maintained part). Keyed by package name.
BLURBS = {
    "document-analyser": "PDF, DOCX, PPTX, TXT, MD — text, readability, .pptx slide-design",
    "speech-analyser": "audio/video — transcript + speech metrics",
    "video-analyser": "video — frames, scenes, transcript + visual quality",
    "records-analyser": "CSV, Excel, SQLite, Parquet, JSON — data profiling",
    "spreadsheet-analyser": "Excel — formula logic, dependencies, error cells, hygiene smells",
    "site-analyser": "deployed URL or static-site dir — accessibility, structure, SEO, links, validity",
    "diagram-analyser": "mermaid / PlantUML / Graphviz / drawio — nodes, edges, cycles, depth, naming",
    "provenance-analyser": "document metadata — creator app, editing time, authorship, AI-gen markers",
    "code-analyser": "source code — style, complexity, quality",
    "image-analyser": "images — metadata, quality, OCR, captions, barcodes",
    "wordpress-analyser": "WordPress PHP — hooks, API usage, quality",
    "git-analyser": "git repositories — commit history + churn",
    "conversation-analyser": "human-AI conversations — engagement + critical-thinking",
    "bundle-analyser": "folders & zips — analyse a collection of files",
    "auto-analyser": "any file — detects format and routes to the right tool",
    "cite-sight": "citations & references — verify (Crossref/OpenAlex), DOI, format, cross-refs",
}


def _load_manifest(path: Path) -> dict | None:
    try:
        spec = importlib.util.spec_from_file_location(f"_m_{path.parent.name}", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        m = getattr(mod, "MANIFEST", None)
        return m if isinstance(m, dict) and m.get("name") else None
    except Exception:
        return None


def _pkg_version(manifest_path: Path) -> str:
    """Read a member's current version from its repo's pyproject.toml.

    Reliable + offline (the manifest's own `version` is the *installed* version,
    which is "0.0.0" when the package isn't installed in the generator's env). Walks
    up from the manifest file to the first dir holding a pyproject.toml.
    """
    for parent in manifest_path.parents:
        pp = parent / "pyproject.toml"
        if pp.exists():
            for line in pp.read_text().splitlines():
                s = line.strip()
                if s.startswith("version") and "=" in s:
                    return s.split("=", 1)[1].strip().strip('"').strip("'")
            break
    return "—"


def discover() -> list[dict]:
    found: dict[str, dict] = {}
    for path in WORKSPACE.glob("*/**/manifest.py"):
        if any(x in str(path) for x in EXCLUDE):
            continue
        m = _load_manifest(path)
        if m and m["name"] not in found:
            m["_display_version"] = _pkg_version(path)
            found[m["name"]] = m
    # Language-neutral members (e.g. the TypeScript cite-sight) declare a
    # manifest.json at their repo root instead of a Python manifest.py.
    for path in WORKSPACE.glob("*/manifest.json"):
        if any(x in str(path) for x in EXCLUDE):
            continue
        try:
            m = json.loads(path.read_text())
        except Exception:
            continue
        if isinstance(m, dict) and m.get("name") and m["name"] not in found:
            m["_display_version"] = str(m.get("version") or "—")
            found[m["name"]] = m
    return list(found.values())


def _routable(m: dict) -> str:
    if m.get("role") == "orchestrator":
        return "orchestrator"
    return "auto" if m.get("auto_routable") else "explicit"


def _sort_key(m: dict) -> tuple:
    order = {"auto": 0, "explicit": 1, "orchestrator": 2}
    return (order[_routable(m)], m["name"])


def build_table(manifests: list[dict]) -> str:
    rows = [
        "| Package | Version | Handles | Extensions | Routable | Links |",
        "|---|---|---|---|---|---|",
    ]
    for m in sorted(manifests, key=_sort_key):
        name = m["name"]
        ver = m.get("_display_version", "—")
        handles = BLURBS.get(name) or ", ".join(m.get("accepts", [])) or "—"
        exts = ", ".join(f"`{e}`" for e in m.get("extensions", [])) or "—"
        repo = m.get("repo") or f"{GH}/{name}"
        link_parts = [f"[repo]({repo})"]
        pypi = m.get("pypi", True)  # default Python member; False = not on PyPI
        if pypi is not False:
            url = pypi if isinstance(pypi, str) else f"{PYPI}/{name}/"
            link_parts.insert(0, f"[PyPI]({url})")
        links = " · ".join(link_parts)
        rows.append(f"| [{name}]({repo}) | {ver} | {handles} | {exts} | {_routable(m)} | {links} |")
    return "\n".join(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="exit 1 if README is out of date")
    args = ap.parse_args()

    text = README.read_text()
    if START not in text or END not in text:
        print(f"error: markers {START} / {END} not found in README.md", file=sys.stderr)
        return 2

    manifests = discover()
    if not manifests:
        print("error: no manifests discovered", file=sys.stderr)
        return 2

    table = build_table(manifests)
    pre, post = text.split(START)[0], text.split(END)[1]
    new = f"{pre}{START}\n\n{table}\n\n{END}{post}"

    if new == text:
        print(f"README family table up to date ({len(manifests)} packages).")
        return 0
    if args.check:
        print("README family table is OUT OF DATE — run generate_family_table.py", file=sys.stderr)
        return 1
    README.write_text(new)
    print(f"README family table regenerated ({len(manifests)} packages).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
