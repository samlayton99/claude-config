#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
. "$SCRIPT_DIR/lib.sh"

usage() {
    cat <<'EOF'
Usage: update-repos [PATH] [--org ORG] [--with-index]

Keeps a workspace of local git repos in sync with a GitHub org.

If PATH is omitted, uses $PWD.
If PATH contains a child directory named "repos", that is used as the repos folder.
Otherwise PATH is treated as the repos folder itself.

If --org is omitted, the org is inferred from the majority of existing repos'
origin URLs. If no existing repos have GitHub remotes, the clone phase is
skipped.

If --with-index is set, a hint is printed after the summary suggesting the
caller invoke /update-index to refresh INDEX.md. This flag does not run the
index skill itself — the calling agent (Claude, etc.) acts on the hint.

Behavior:
  1. List non-archived repos in the org via `gh` and clone any missing.
  2. For each local repo: fetch, then fast-forward-pull if clean-on-default.
  3. Print a summary and leave everything else for interactive resolution.

The script never stashes, resets, creates merge commits, or pushes.
EOF
}

main() {
    local path="" org="" with_index="no"
    while (( $# )); do
        case "$1" in
            -h|--help) usage; return 0 ;;
            --org) shift; org="${1:-}"; shift || true ;;
            --org=*) org="${1#--org=}"; shift ;;
            --with-index) with_index="yes"; shift ;;
            --) shift; break ;;
            -*) echo "unknown flag: $1" >&2; usage >&2; return 2 ;;
            *) path="$1"; shift ;;
        esac
    done

    [[ -z "$path" ]] && path="$PWD"
    if [[ ! -d "$path" ]]; then
        echo "error: path does not exist: $path" >&2
        return 2
    fi

    local repos_folder
    repos_folder="$(find_repos_folder "$path")"

    # Enumerate existing repos
    local existing
    existing="$(list_git_children "$repos_folder")"

    # Resolve org (auto-detect if not provided)
    if [[ -z "$org" ]]; then
        org="$(printf '%s\n' "$existing" | pick_majority_org)"
    fi

    # Phase 1: clone missing
    local cloned=""
    if [[ -n "$org" ]]; then
        cloned="$(clone_missing_repos "$repos_folder" "$org")"
    else
        echo "note: no org provided and none could be inferred, skipping clone phase" >&2
    fi

    # Re-enumerate (includes newly cloned)
    existing="$(list_git_children "$repos_folder")"

    # Phase 2: update each repo
    local results=""
    if [[ -n "$existing" ]]; then
        while IFS= read -r repo; do
            [[ -z "$repo" ]] && continue
            local line
            line="$(update_repo "$repo" || true)"
            results="${results}${line}"$'\n'
        done <<< "$existing"
    fi

    # Output — NOTE bug fix: CLONED must be on the consumer side of the pipe
    printf '%s' "$results" | CLONED="$cloned" format_summary

    if [[ "$with_index" == "yes" ]]; then
        echo "hint: workspace index refresh recommended — invoke /update-index to update INDEX.md"
    fi
}

main "$@"
