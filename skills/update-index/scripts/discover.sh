#!/usr/bin/env bash
# discover.sh [path]
# Prints a TSV line per repo found under the resolved repos folder:
#   <name>\t<abs_path>\t<current_head_sha>\t<has_remote>\t<state>
# Fields:
#   name         — repo directory name
#   abs_path     — absolute path to repo
#   head_sha     — current HEAD SHA (or "-" if no commits)
#   has_remote   — "yes" or "no" (origin configured?)
#   state        — classify_repo output (CLEAN_ON_DEFAULT, EMPTY_REMOTE, etc.)
# Also prints one header line to stderr: WORKSPACE <path> REPOS_FOLDER <path>
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
. "$SCRIPT_DIR/lib.sh"

main() {
    local ws="${1:-$PWD}"
    if [[ ! -d "$ws" ]]; then
        echo "error: path does not exist: $ws" >&2
        return 2
    fi
    local repos_folder
    repos_folder="$(find_repos_folder "$ws")"
    echo "WORKSPACE $ws REPOS_FOLDER $repos_folder" >&2

    local repo name path head has_remote state
    while IFS= read -r path; do
        [[ -z "$path" ]] && continue
        name="$(basename "$path")"
        head="$(git -C "$path" rev-parse --verify HEAD 2>/dev/null || echo '-')"
        if git -C "$path" remote get-url origin >/dev/null 2>&1; then
            has_remote="yes"
        else
            has_remote="no"
        fi
        state="$(classify_repo "$path" 2>/dev/null || echo 'UNKNOWN')"
        printf '%s\t%s\t%s\t%s\t%s\n' "$name" "$path" "$head" "$has_remote" "$state"
    done < <(list_git_children "$repos_folder")
}

main "$@"
