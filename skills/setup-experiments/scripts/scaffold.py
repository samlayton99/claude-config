#!/usr/bin/env python3
"""scaffold.py — deterministic repo emitter for the setup-experiments skill.

Copies the scaffold template into a destination directory and substitutes a few mechanical
placeholders (project name, the experiment-grouping term). The folder structure is laid down by
CODE here so it is identical every time — the model does NOT hand-build the skeleton. After
scaffolding, the model fills the `<FILL: ...>` placeholders in CLAUDE.md / docs/roadmap.md /
results/results.md from the interview (see SKILL.md).

Safe on existing repos: skips any file that already exists unless --force. It never silently
overwrites real work.

Usage:
    scaffold.py --dest PATH --project "Project Name" [--group checkpoint] [--force]
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL_ROOT / "assets" / "template"
SKIP = {"__pycache__", ".git", ".DS_Store", ".ipynb_checkpoints"}
# files we substitute placeholders into (everything else is copied byte-for-byte)
TEXT_SUFFIXES = {".md", ".yaml", ".yml", ".py", ".txt", ".gitignore", ""}


def substitute(text: str, project: str, group: str) -> str:
    return (text
            .replace("{{project}}", project)
            .replace("{{Group}}", group.capitalize())
            .replace("{{group}}", group))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", required=True, help="destination repo directory")
    ap.add_argument("--project", required=True, help="project name (title of CLAUDE.md)")
    ap.add_argument("--group", default="checkpoint",
                    help="experiment-grouping term (default: checkpoint)")
    ap.add_argument("--force", action="store_true", help="overwrite existing files")
    args = ap.parse_args()

    dest = Path(args.dest).expanduser().resolve()
    dest.mkdir(parents=True, exist_ok=True)

    copied, skipped = [], []
    for src in sorted(TEMPLATE.rglob("*")):
        rel = src.relative_to(TEMPLATE)
        if any(p in SKIP for p in rel.parts) or src.suffix == ".pyc":
            continue
        target = dest / rel
        if src.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        if target.exists() and not args.force:
            skipped.append(str(rel)); continue
        target.parent.mkdir(parents=True, exist_ok=True)
        # substitute placeholders in text files; copy others verbatim
        if src.suffix in TEXT_SUFFIXES:
            try:
                target.write_text(substitute(src.read_text(), args.project, args.group))
            except UnicodeDecodeError:
                shutil.copy2(src, target)
        else:
            shutil.copy2(src, target)
        copied.append(str(rel))

    print(f"scaffolded {len(copied)} file(s) into {dest}")
    for r in copied:
        print(f"  + {r}")
    if skipped:
        print(f"\nskipped {len(skipped)} existing file(s) [use --force to overwrite]:")
        for r in skipped:
            print(f"  = {r}")
    print("\nNEXT: fill the `<FILL: ...>` placeholders from the interview, in this order —")
    print("  1. CLAUDE.md         — research question, key abstractions, success criterion, conventions")
    print("  2. docs/roadmap.md   — central question, success criterion, the decisive arc")
    print("  3. results/results.md — the story so far (stub until experiments exist)")
    print("  Then `git init` if this is a new repo. See the skill's SKILL.md for the full workflow.")


if __name__ == "__main__":
    main()
