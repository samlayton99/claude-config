#!/usr/bin/env bash
# Sourceable helpers for /update-index.
# Pure repo helpers live in _shared/lib-repos.sh; this file adds
# update-index-specific state-management and discovery helpers.

# Resolve _shared/lib-repos.sh via $HOME instead of ${BASH_SOURCE[0]} so that
# sourcing this file works under zsh (where BASH_SOURCE is empty) as well as bash.
. "$HOME/.claude/skills/_shared/lib-repos.sh"

# init_state_dir <workspace_root>
# Creates .update-index/scratch/ and writes .update-index/.gitignore containing "*".
init_state_dir() {
    local ws="$1"
    mkdir -p "$ws/.update-index/scratch"
    if [[ ! -f "$ws/.update-index/.gitignore" ]]; then
        echo "*" > "$ws/.update-index/.gitignore"
    fi
}

# index_exists <workspace_root>
# INDEX.md lives inside the repos/ folder when present; otherwise at the workspace root.
index_exists() {
    local ws="$1"
    if [[ -d "$ws/repos" ]]; then
        [[ -f "$ws/repos/INDEX.md" ]]
    else
        [[ -f "$ws/INDEX.md" ]]
    fi
}

# meta_path <workspace_root>
meta_path() {
    echo "$1/.update-index/meta.json"
}

# load_index_meta <workspace_root>
# Echoes contents of meta.json, or "{}" if missing.
load_index_meta() {
    local f; f="$(meta_path "$1")"
    if [[ -f "$f" ]]; then
        cat "$f"
    else
        echo "{}"
    fi
}

# save_index_meta <workspace_root> <json_blob>
# Atomic write (write-then-rename).
save_index_meta() {
    local ws="$1"
    local blob="$2"
    local f; f="$(meta_path "$ws")"
    mkdir -p "$(dirname "$f")"
    local tmp="$f.tmp.$$"
    printf '%s\n' "$blob" > "$tmp"
    mv "$tmp" "$f"
}

# get_last_scanned_sha <workspace_root> <repo_name>
# Reads meta.json via python3; echoes sha or empty.
get_last_scanned_sha() {
    local ws="$1"; local name="$2"
    local f; f="$(meta_path "$ws")"
    [[ -f "$f" ]] || { echo ""; return; }
    python3 -c '
import json, sys
path, name = sys.argv[1], sys.argv[2]
try:
    with open(path) as fp:
        data = json.load(fp)
    print(data.get("repos", {}).get(name, {}).get("last_sha", ""))
except Exception:
    print("")
' "$f" "$name"
}

# set_last_scanned_sha <workspace_root> <repo_name> <sha>
# Reads meta.json, sets repos[name].last_sha and last_scanned_at, writes back.
set_last_scanned_sha() {
    local ws="$1"; local name="$2"; local sha="$3"
    local f; f="$(meta_path "$ws")"
    local now; now="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
    local updated
    updated="$(load_index_meta "$ws" | python3 -c '
import json, sys
try:
    data = json.load(sys.stdin)
except Exception:
    data = {}
data.setdefault("repos", {})[sys.argv[1]] = {"last_sha": sys.argv[2], "last_scanned_at": sys.argv[3]}
data.setdefault("schema_version", 1)
print(json.dumps(data, indent=2, sort_keys=True))
' "$name" "$sha" "$now")"
    save_index_meta "$ws" "$updated"
}

# remove_repo_from_meta <workspace_root> <repo_name>
remove_repo_from_meta() {
    local ws="$1"; local name="$2"
    local updated
    updated="$(load_index_meta "$ws" | python3 -c '
import json, sys
try:
    data = json.load(sys.stdin)
except Exception:
    data = {}
data.get("repos", {}).pop(sys.argv[1], None)
print(json.dumps(data, indent=2, sort_keys=True))
' "$name")"
    save_index_meta "$ws" "$updated"
}
