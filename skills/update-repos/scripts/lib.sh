#!/usr/bin/env bash
# Sourceable helper functions for update-repos.
# Pure cross-skill helpers live in _shared/lib-repos.sh; this file adds
# update-repos-specific helpers on top.

. "$(dirname "${BASH_SOURCE[0]}")/../../_shared/lib-repos.sh"

# update_repo <repo>
# Prints one tab-separated result line:
#   name \t branch \t status \t detail
update_repo() {
    local repo="$1"
    local name; name="$(basename "$repo")"

    # Early-exit for no origin — do not fetch.
    if ! git -C "$repo" remote get-url origin >/dev/null 2>&1; then
        printf '%s\t%s\t%s\t%s\n' "$name" "-" "NO_REMOTE" ""
        return
    fi

    git -C "$repo" fetch --prune origin >/dev/null 2>&1 || true

    local state; state="$(classify_repo "$repo")"
    local branch; branch="$(git -C "$repo" symbolic-ref --quiet --short HEAD 2>/dev/null || echo '-')"
    local def; def="$(get_default_branch "$repo")"

    case "$state" in
        CLEAN_ON_DEFAULT)
            local before after
            before="$(git -C "$repo" rev-parse HEAD)"
            if git -C "$repo" merge --ff-only "origin/$def" >/dev/null 2>&1; then
                after="$(git -C "$repo" rev-parse HEAD)"
                if [[ "$before" == "$after" ]]; then
                    printf '%s\t%s\t%s\t%s\n' "$name" "$branch" "UP_TO_DATE" ""
                else
                    local count
                    count="$(git -C "$repo" rev-list --count "$before..$after")"
                    printf '%s\t%s\t%s\t%s\n' "$name" "$branch" "PULLED" "$count"
                fi
            else
                printf '%s\t%s\t%s\t%s\n' "$name" "$branch" "DIVERGED" ""
            fi
            ;;
        FEATURE_BRANCH)
            printf '%s\t%s\t%s\t%s\n' "$name" "$branch" "FEATURE_BRANCH" "default=$def"
            ;;
        DETACHED)
            printf '%s\t%s\t%s\t%s\n' "$name" "-" "DETACHED" ""
            ;;
        BEHIND_DEFAULT_DIRTY)
            local dirty_count
            dirty_count="$(git -C "$repo" status --porcelain | wc -l | tr -d ' ')"
            printf '%s\t%s\t%s\t%s\n' "$name" "$branch" "BEHIND_DEFAULT_DIRTY" "dirty=$dirty_count"
            ;;
        NO_REMOTE)
            printf '%s\t%s\t%s\t%s\n' "$name" "-" "NO_REMOTE" ""
            ;;
        EMPTY_REMOTE)
            printf '%s\t%s\t%s\t%s\n' "$name" "$branch" "EMPTY_REMOTE" "no branches on origin"
            ;;
        *)
            printf '%s\t%s\t%s\t%s\n' "$name" "$branch" "UNKNOWN" "$state"
            ;;
    esac
}

# clone_missing_repos <repos_folder> <org>
# Echoes names of cloned repos, one per line. Warnings go to stderr.
clone_missing_repos() {
    local repos_folder="$1"
    local org="$2"

    if ! command -v gh >/dev/null 2>&1; then
        echo "warning: gh not installed, skipping clone phase" >&2
        return 0
    fi
    if ! gh auth status >/dev/null 2>&1; then
        echo "warning: gh not authenticated, skipping clone phase" >&2
        return 0
    fi

    local remote_repos
    if ! remote_repos="$(gh repo list "$org" --limit 500 --no-archived --json name --jq '.[].name' 2>/dev/null)"; then
        echo "warning: gh repo list failed for org '$org', skipping clone phase" >&2
        return 0
    fi

    local name
    while IFS= read -r name; do
        [[ -z "$name" ]] && continue
        if [[ -d "$repos_folder/$name" ]]; then
            continue
        fi
        if gh repo clone "$org/$name" "$repos_folder/$name" -- -q >/dev/null 2>&1; then
            echo "$name"
        else
            echo "warning: failed to clone $org/$name" >&2
        fi
    done <<< "$remote_repos"
}

# format_summary
# Reads update_repo lines from stdin. Env vars:
#   CLONED — newline-separated names of newly cloned repos (may be empty)
format_summary() {
    local -a lines=()
    local line
    while IFS= read -r line; do
        [[ -z "$line" ]] && continue
        lines+=("$line")
    done

    local pulled_count=0 uptodate_count=0 attention_count=0
    local -a pulled_rows=()

    for line in "${lines[@]+"${lines[@]}"}"; do
        local name branch status detail
        IFS=$'\t' read -r name branch status detail <<< "$line"
        case "$status" in
            PULLED)
                pulled_count=$((pulled_count+1))
                pulled_rows+=("$name	$branch	$detail")
                ;;
            UP_TO_DATE)
                uptodate_count=$((uptodate_count+1))
                ;;
            *)
                attention_count=$((attention_count+1))
                ;;
        esac
    done

    # Cloned section
    local cloned_count=0
    if [[ -n "${CLONED:-}" ]]; then
        # Count non-empty lines
        cloned_count=$(printf '%s' "$CLONED" | grep -c . || true)
        echo "Cloned: $(printf '%s' "$CLONED" | tr '\n' ',' | sed 's/,$//' | sed 's/,/, /g')"
        echo
    fi

    # Pulled section
    if (( pulled_count > 0 )); then
        echo "Pulled:"
        {
            printf 'Repo\tBranch\tCommits\n'
            printf -- '---\t---\t---\n'
            # Sort by commit count desc, tie-break by name asc
            printf '%s\n' "${pulled_rows[@]}" | sort -t$'\t' -k3,3nr -k1,1
        } | _format_table
        echo
    fi

    echo "$cloned_count cloned, $pulled_count pulled, $uptodate_count up-to-date, $attention_count need attention."
}

# _format_table
# Reads tab-separated rows from stdin and prints a column-aligned table.
# Row 2 is expected to be a separator using "---" per column; it is replaced
# with dashes sized to the column width.
_format_table() {
    awk -F'\t' '
    {
        for (i=1; i<=NF; i++) {
            rows[NR,i] = $i
            if (length($i) > width[i]) width[i] = length($i)
        }
        cols[NR] = NF
    }
    END {
        for (r=1; r<=NR; r++) {
            for (i=1; i<=cols[r]; i++) {
                cell = rows[r,i]
                if (r == 2) {
                    # Separator row: use dashes of column width
                    pad = ""
                    for (k=0; k<width[i]; k++) pad = pad "-"
                    cell = pad
                }
                if (i < cols[r]) {
                    printf "%-*s  ", width[i], cell
                } else {
                    printf "%s", cell
                }
            }
            printf "\n"
        }
    }'
}
