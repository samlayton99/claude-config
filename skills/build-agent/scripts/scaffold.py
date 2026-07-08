#!/usr/bin/env python3
"""
Agent Scaffold Generator

Thin wrapper around the build-worker scaffold.py with --type agent.
This exists so the build-agent skill can call its own local script,
but all actual scaffolding logic lives in build-worker/scripts/scaffold.py.

Usage:
    python scaffold.py --name <agent-name> --path <output-dir> [options]

All options are passed through to the shared scaffold.py with --type agent prepended.
See build-worker/scripts/scaffold.py for full option list.
"""
import subprocess
import sys
from pathlib import Path

SHARED_SCAFFOLD = Path(__file__).parent.parent.parent / "build-worker" / "scripts" / "scaffold.py"


def main():
    if not SHARED_SCAFFOLD.exists():
        print(f"Error: shared scaffold not found at {SHARED_SCAFFOLD}", file=sys.stderr)
        print("Ensure build-worker skill is installed at ~/.claude/skills/build-worker/", file=sys.stderr)
        sys.exit(1)

    # Prepend --type agent to the arguments
    args = [sys.executable, str(SHARED_SCAFFOLD), "--type", "agent"] + sys.argv[1:]
    result = subprocess.run(args)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
