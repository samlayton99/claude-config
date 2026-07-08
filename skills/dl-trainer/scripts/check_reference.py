#!/usr/bin/env python3
"""check_reference.py — health + cleanliness gate for the dl-trainer durable layer.

Run before AND after any self-update to tasks/ or references/. Deterministic and
conservative: missing provenance / a task missing its files is a hard ERROR (exit 1);
staleness and possible redundancy are WARNINGS (exit 0) — better to lag than to wrongly prune.

Checks each tasks/<task>/:
  1. config.yaml carries _recipe.{summary, source, last_verified}.            [ERROR]
  2. last_verified parses as a date and is not in the future.                 [ERROR]
  3. a <task>.md knowledge file exists.                                       [ERROR]
  4. Freshness: last_verified older than --stale-days (default 120).          [WARN]
  5. the .md carries a 'last updated' marker.                                 [WARN]
  6. Redundancy: two tasks sharing a normalized summary or primary source.    [WARN]
  7. Consistency: every task folder is listed in tasks/tasks.md.             [WARN]
  8. Size budgets: SKILL.md <= 500 lines; other durable *.md <= 800.          [WARN]
  9. Unknown keys: _recipe fields + core-section knobs the loop never reads.  [WARN]

Usage: check_reference.py [--stale-days N] [--today YYYY-MM-DD]
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PyYAML required: pip install pyyaml")

ROOT = Path(__file__).resolve().parent.parent
TASKS = ROOT / "tasks"
INDEX = TASKS / "tasks.md"
REFS = ROOT / "references"
RULES = ROOT / "rules"
SKILL = ROOT / "SKILL.md"
TEMPLATE = ROOT / "scaffold" / "experiments" / "_template" / "config.yaml"

RECIPE_FIELDS = {"summary", "source", "last_verified", "adoption", "extra", "todo"}
# Config sections the core loop owns with a fixed schema. model/loss/optim are intentionally
# excluded — they're free-form / extended by experiment.py overrides (e.g. optim.layer_decay).
SCHEMA_SECTIONS = ("run", "logging", "data", "scheduler", "train")

errors: list[str] = []
warns: list[str] = []


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def _template_schema() -> dict:
    """{section: set(keys)} from the scaffold's _template config — the canonical core knob set.
    A task config key outside this (in a core-owned section) is read by nothing → dead/typo."""
    if not TEMPLATE.exists():
        return {}
    doc = yaml.safe_load(TEMPLATE.read_text()) or {}
    return {s: set(doc.get(s) or {}) for s in SCHEMA_SECTIONS}


def _task_dirs():
    """Real task folders (skip _template and non-dirs)."""
    return [d for d in sorted(TASKS.iterdir())
            if d.is_dir() and not d.name.startswith("_")]


def check_tasks(today: dt.date, stale_days: int):
    summaries: dict[str, str] = {}
    sources: dict[str, str] = {}
    index_text = INDEX.read_text() if INDEX.exists() else ""
    schema = _template_schema()
    for d in _task_dirs():
        name = d.name

        # config.yaml + _recipe provenance
        cfg = d / "config.yaml"
        if not cfg.exists():
            errors.append(f"{name}: no config.yaml")
            continue
        doc = yaml.safe_load(cfg.read_text()) or {}
        r = doc.get("_recipe")
        if not r:
            errors.append(f"{name}/config.yaml: missing _recipe block")
            r = {}
        for field in ("summary", "source", "last_verified"):
            if not r.get(field):
                errors.append(f"{name}/config.yaml: _recipe.{field} missing")

        # unknown keys: dead/typo'd _recipe fields, or core-section knobs the loop never reads
        for k in r:
            if k not in RECIPE_FIELDS:
                warns.append(f"{name}/config.yaml: _recipe.{k} is not a known field (typo or dead key?)")
        for section in SCHEMA_SECTIONS:
            known = schema.get(section)
            if known and isinstance(doc.get(section), dict):
                for k in doc[section]:
                    if k not in known:
                        warns.append(f"{name}/config.yaml: {section}.{k} is read by nothing in core (typo or dead key?)")

        # last_verified parses, not future, not stale
        lv = r.get("last_verified")
        if lv:
            try:
                date = lv if isinstance(lv, dt.date) else dt.date.fromisoformat(str(lv))
                if date > today:
                    errors.append(f"{name}: last_verified {date} is in the future")
                elif (today - date).days > stale_days:
                    warns.append(f"{name}: STALE — last verified {date} "
                                 f"({(today - date).days}d ago, budget {stale_days}d)")
            except ValueError:
                errors.append(f"{name}/config.yaml: last_verified '{lv}' is not an ISO date")

        # a knowledge .md must exist, carry a 'last updated' marker, and be renamed
        mds = list(d.glob("*.md"))
        if not mds:
            errors.append(f"{name}: no <task>.md knowledge file")
        else:
            if not any("last updated" in m.read_text().lower() for m in mds):
                warns.append(f"{name}: .md has no 'last updated' marker")
            if [m.name for m in mds] == ["task.md"]:
                warns.append(f"{name}: knowledge file still named task.md — rename to {name}.md")

        # redundancy (duplicate summary / shared primary source)
        s = _norm(r.get("summary", ""))
        if s and s in summaries:
            warns.append(f"{name}: duplicate summary of {summaries[s]}")
        summaries[s] = name
        src = _norm((r.get("source", "") or "").split(";")[0])
        if src and src in sources:
            warns.append(f"{name}: shares primary source with {sources[src]} (possible overlap)")
        sources[src] = name

        # consistency: listed in the index
        if index_text and name not in index_text:
            warns.append(f"{name}: not listed in tasks/tasks.md")
    if not INDEX.exists():
        warns.append("tasks/tasks.md (index) missing")


def check_sizes():
    budgets = {SKILL: 500}
    for folder in (REFS, RULES):
        for f in folder.glob("*.md"):
            budgets[f] = 800
    for d in _task_dirs():
        for f in d.glob("*.md"):
            budgets[f] = 800
    for f, budget in budgets.items():
        if f.exists() and len(f.read_text().splitlines()) > budget:
            warns.append(f"{f.relative_to(ROOT)}: exceeds budget {budget} lines — split or prune")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stale-days", type=int, default=120)
    ap.add_argument("--today", default=None, help="override today (YYYY-MM-DD) for determinism")
    a = ap.parse_args()
    today = dt.date.fromisoformat(a.today) if a.today else dt.date.today()

    check_tasks(today, a.stale_days)
    check_sizes()

    if warns:
        print("WARNINGS (review; non-blocking — conservatism favors lag over churn):")
        for w in warns:
            print(f"  - {w}")
    if errors:
        print("\nERRORS (must fix):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    print(f"\nclean: {len(_task_dirs())} tasks, {len(warns)} warning(s), 0 errors.")


if __name__ == "__main__":
    main()
