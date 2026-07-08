#!/usr/bin/env bash
# assemble-index.sh <workspace_root>
# Assembles INDEX.md from:
#   - templates/preamble.md (replace <TIMESTAMP>)
#   - .update-index/scratch/<name>.entry.md (alphabetical)
#   - .update-index/scratch/concept-map.md (last section)
# Output path: <workspace_root>/repos/INDEX.md if repos/ exists, else <workspace_root>/INDEX.md.
# Writes atomically (temp file then rename).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

main() {
    local ws="${1:-}"
    if [[ -z "$ws" ]]; then
        echo "usage: assemble-index.sh <workspace_root>" >&2
        return 2
    fi
    if [[ ! -d "$ws" ]]; then
        echo "error: workspace not found: $ws" >&2
        return 2
    fi

    local scratch="$ws/.update-index/scratch"
    local preamble="$SKILL_DIR/templates/preamble.md"
    if [[ ! -f "$preamble" ]]; then
        echo "error: preamble template missing: $preamble" >&2
        return 2
    fi

    # INDEX.md lives inside repos/ when the workspace has one (so it sits next
    # to the repos it indexes); otherwise fall back to the workspace root.
    local out_dir
    if [[ -d "$ws/repos" ]]; then
        out_dir="$ws/repos"
    else
        out_dir="$ws"
    fi
    local out="$out_dir/INDEX.md"
    local tmp="$out.tmp.$$"
    local now; now="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"

    {
        # Preamble with timestamp substituted
        sed "s|<TIMESTAMP>|$now|" "$preamble"
        echo

        # Per-repo entries, alphabetical
        local any_entries="no"
        for f in "$scratch"/*.entry.md; do
            [[ -e "$f" ]] || continue
            any_entries="yes"
            cat "$f"
            echo
        done
        if [[ "$any_entries" == "no" ]]; then
            echo "_(no repos indexed yet)_"
            echo
        fi

        # Concept map, if present
        if [[ -f "$scratch/concept-map.md" ]]; then
            echo "---"
            echo
            cat "$scratch/concept-map.md"
            echo
        fi
    } > "$tmp"

    mv "$tmp" "$out"
    echo "wrote $out" >&2
}

main "$@"
