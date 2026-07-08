#!/usr/bin/env bash
# Sourceable pure helpers for workspace repo operations.
# Shared by /update-repos and /update-index. No filesystem mutation, no network.

# parse_github_org <remote_url>
# Echoes the GitHub org with original casing, or empty string if the URL
# is not a GitHub URL.
parse_github_org() {
    local url="${1:-}"
    [[ -z "$url" ]] && { echo ""; return; }
    # Normalize: strip trailing .git
    url="${url%.git}"
    # Match https://github.com/ORG/... or git@github.com:ORG/... or ssh://git@github.com/ORG/...
    local re='github\.com[:/]+([^/]+)/'
    if [[ "$url" =~ $re ]]; then
        echo "${BASH_REMATCH[1]}"
    else
        echo ""
    fi
}

# pick_majority_org
# Reads repo directory paths from stdin (one per line), echoes the most
# common GitHub org among their origin URLs. Empty string if none.
pick_majority_org() {
    local dir org
    local -a orgs=()
    while IFS= read -r dir; do
        [[ -z "$dir" ]] && continue
        dir="${dir%/}"
        [[ -d "$dir/.git" || -f "$dir/.git" ]] || continue
        local url
        url="$(git -C "$dir" remote get-url origin 2>/dev/null || true)"
        org="$(parse_github_org "$url")"
        [[ -n "$org" ]] && orgs+=("$org")
    done
    [[ "${#orgs[@]}" -eq 0 ]] && { echo ""; return; }
    # Count, preserve first-seen order for ties
    local best="" best_count=0
    local seen=""
    for org in "${orgs[@]}"; do
        case ",$seen," in *",$org,"*) continue ;; esac
        seen="${seen},${org}"
        local count=0
        for o in "${orgs[@]}"; do [[ "$o" == "$org" ]] && count=$((count+1)); done
        if (( count > best_count )); then
            best="$org"; best_count=$count
        fi
    done
    echo "$best"
}

# find_repos_folder <path>
find_repos_folder() {
    local path="$1"
    if [[ -d "$path/repos" ]]; then
        echo "$path/repos"
    else
        echo "$path"
    fi
}

# list_git_children <path>
# Echoes full paths of immediate children that are git repositories.
list_git_children() {
    local path="$1"
    [[ -d "$path" ]] || return 0
    local child
    for child in "$path"/*/; do
        [[ -d "$child" ]] || continue
        child="${child%/}"
        if [[ -d "$child/.git" || -f "$child/.git" ]]; then
            echo "$child"
        fi
    done
}

# get_default_branch <repo>
get_default_branch() {
    local repo="$1"
    local head
    head="$(git -C "$repo" symbolic-ref --quiet refs/remotes/origin/HEAD 2>/dev/null || true)"
    if [[ -z "$head" ]]; then
        git -C "$repo" remote set-head origin -a >/dev/null 2>&1 || true
        head="$(git -C "$repo" symbolic-ref --quiet refs/remotes/origin/HEAD 2>/dev/null || true)"
    fi
    [[ -z "$head" ]] && { echo ""; return; }
    echo "${head#refs/remotes/origin/}"
}

# classify_repo <repo>
classify_repo() {
    local repo="$1"
    # no origin?
    if ! git -C "$repo" remote get-url origin >/dev/null 2>&1; then
        echo "NO_REMOTE"; return
    fi
    # detached?
    local branch
    branch="$(git -C "$repo" symbolic-ref --quiet --short HEAD 2>/dev/null || true)"
    if [[ -z "$branch" ]]; then
        echo "DETACHED"; return
    fi
    local def
    def="$(get_default_branch "$repo")"
    if [[ -z "$def" ]]; then
        echo "EMPTY_REMOTE"; return
    fi
    if [[ "$branch" != "$def" ]]; then
        echo "FEATURE_BRANCH"; return
    fi
    # on default: check dirty
    if [[ -n "$(git -C "$repo" status --porcelain 2>/dev/null)" ]]; then
        echo "BEHIND_DEFAULT_DIRTY"; return
    fi
    echo "CLEAN_ON_DEFAULT"
}
