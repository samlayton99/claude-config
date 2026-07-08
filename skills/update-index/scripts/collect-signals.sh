#!/usr/bin/env bash
# collect-signals.sh <repo_path> <last_sha>
# Prints a signal block the update-evaluator subagent can consume.
#
# Blocks emitted (in order, only if non-empty):
#   ---DIR_DIFF---       top-level dirs added/removed between last_sha and HEAD
#   ---COMMIT_SUBJECTS---  up to 50 commit subjects in last_sha..HEAD
#   ---README_DIFF---    git diff --stat for README/ARCHITECTURE/DESIGN/docs
#
# Exit 0 always. If all blocks are empty, prints nothing — caller treats
# this as "no meaningful signal, skip the subagent dispatch".
#
# Special cases:
#   - If last_sha is empty, prints a single line "NEW_REPO" and exits 0.
#   - If last_sha is unreachable (e.g., history rewritten), prints
#     "UNREACHABLE_SHA <sha>" and exits 0 — caller may treat as NEW_REPO.
set -euo pipefail

main() {
    local repo="${1:-}"
    local last_sha="${2:-}"

    if [[ -z "$repo" ]]; then
        echo "usage: collect-signals.sh <repo_path> <last_sha>" >&2
        return 2
    fi
    if [[ ! -d "$repo/.git" && ! -f "$repo/.git" ]]; then
        echo "error: not a git repo: $repo" >&2
        return 2
    fi

    if [[ -z "$last_sha" ]]; then
        echo "NEW_REPO"
        return 0
    fi

    if ! git -C "$repo" cat-file -e "$last_sha" 2>/dev/null; then
        echo "UNREACHABLE_SHA $last_sha"
        return 0
    fi

    # Top-level dirs whose presence changed (added, removed, or became present/absent).
    # A dir "changed" if any file under it was added or deleted in the range.
    local dir_diff
    dir_diff="$(git -C "$repo" diff --name-only --diff-filter=AD "$last_sha" HEAD 2>/dev/null \
        | awk -F/ 'NF>1 {print $1}' \
        | sort -u)"

    # Further narrow to dirs that appeared or disappeared entirely
    local refined_dirs=""
    if [[ -n "$dir_diff" ]]; then
        while IFS= read -r d; do
            [[ -z "$d" ]] && continue
            local existed_before existed_after
            if git -C "$repo" ls-tree --name-only "$last_sha" -- "$d" 2>/dev/null | grep -q .; then
                existed_before="yes"
            else
                existed_before="no"
            fi
            if [[ -d "$repo/$d" ]]; then
                existed_after="yes"
            else
                existed_after="no"
            fi
            if [[ "$existed_before" == "no" && "$existed_after" == "yes" ]]; then
                refined_dirs+="$d/ (added)"$'\n'
            elif [[ "$existed_before" == "yes" && "$existed_after" == "no" ]]; then
                refined_dirs+="$d/ (removed)"$'\n'
            fi
        done <<< "$dir_diff"
        refined_dirs="${refined_dirs%$'\n'}"
    fi

    local commit_subjects
    commit_subjects="$(git -C "$repo" log --format='%s' "$last_sha..HEAD" 2>/dev/null | head -50 || true)"

    local readme_diff
    readme_diff="$(git -C "$repo" diff --stat "$last_sha" HEAD \
        -- 'README*' 'ARCHITECTURE*' 'DESIGN*' 'CLAUDE*' 'AGENTS*' 'docs/**' 2>/dev/null \
        | head -20 || true)"
    # Trim the summary footer if only it remained
    if [[ -n "$readme_diff" ]]; then
        # If first (and only) line is the "N files changed" summary and shows 0 changes, drop it
        local line_count
        line_count=$(printf '%s\n' "$readme_diff" | grep -c . || true)
        if [[ "$line_count" -le 1 ]]; then
            readme_diff=""
        fi
    fi

    # Short-circuit: if all three are empty, produce nothing
    if [[ -z "$refined_dirs" && -z "$commit_subjects" && -z "$readme_diff" ]]; then
        return 0
    fi

    if [[ -n "$refined_dirs" ]]; then
        echo "---DIR_DIFF---"
        printf '%s\n' "$refined_dirs"
    fi
    if [[ -n "$commit_subjects" ]]; then
        echo "---COMMIT_SUBJECTS---"
        printf '%s\n' "$commit_subjects"
    fi
    if [[ -n "$readme_diff" ]]; then
        echo "---README_DIFF---"
        printf '%s\n' "$readme_diff"
    fi
}

main "$@"
