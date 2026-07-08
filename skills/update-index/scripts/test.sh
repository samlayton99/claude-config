#!/usr/bin/env bash
# Tests for update-index helpers and scripts.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
. "$SCRIPT_DIR/lib.sh"

FAILED=0
PASSED=0

assert_eq() {
    local expected="$1"
    local actual="$2"
    local msg="${3:-}"
    if [[ "$expected" == "$actual" ]]; then
        PASSED=$((PASSED+1))
    else
        FAILED=$((FAILED+1))
        echo "FAIL: $msg" >&2
        echo "  expected: $expected" >&2
        echo "  actual:   $actual" >&2
    fi
}

assert_true() {
    local cmd="$1"
    local msg="${2:-}"
    if eval "$cmd"; then
        PASSED=$((PASSED+1))
    else
        FAILED=$((FAILED+1))
        echo "FAIL: $msg (cmd: $cmd)" >&2
    fi
}

# -----------------------------------------------------------------------------
# init_state_dir
# -----------------------------------------------------------------------------
t=$(mktemp -d)
init_state_dir "$t"
assert_true "[[ -d '$t/.update-index/scratch' ]]" "init_state_dir creates scratch"
assert_true "[[ -f '$t/.update-index/.gitignore' ]]" "init_state_dir creates .gitignore"
assert_eq "*" "$(cat "$t/.update-index/.gitignore")" "gitignore content"
rm -rf "$t"

# -----------------------------------------------------------------------------
# index_exists
# -----------------------------------------------------------------------------
t=$(mktemp -d)
assert_true "! index_exists '$t'" "index_exists false when missing"
touch "$t/INDEX.md"
assert_true "index_exists '$t'" "index_exists true when present"
rm -rf "$t"

# -----------------------------------------------------------------------------
# load_index_meta default
# -----------------------------------------------------------------------------
t=$(mktemp -d)
assert_eq "{}" "$(load_index_meta "$t")" "load_index_meta default"
rm -rf "$t"

# -----------------------------------------------------------------------------
# save/load round-trip + sha helpers
# -----------------------------------------------------------------------------
t=$(mktemp -d)
init_state_dir "$t"
set_last_scanned_sha "$t" "alkonos" "abc123"
assert_eq "abc123" "$(get_last_scanned_sha "$t" "alkonos")" "set/get sha roundtrip"
set_last_scanned_sha "$t" "backend" "def456"
assert_eq "def456" "$(get_last_scanned_sha "$t" "backend")" "second repo sha"
assert_eq "abc123" "$(get_last_scanned_sha "$t" "alkonos")" "first sha unchanged by second write"
assert_eq "" "$(get_last_scanned_sha "$t" "nonexistent")" "missing repo returns empty"
remove_repo_from_meta "$t" "alkonos"
assert_eq "" "$(get_last_scanned_sha "$t" "alkonos")" "remove_repo_from_meta"
assert_eq "def456" "$(get_last_scanned_sha "$t" "backend")" "other repos preserved after removal"
rm -rf "$t"

# -----------------------------------------------------------------------------
# discover.sh: point at a temp workspace with two git children
# -----------------------------------------------------------------------------
t=$(mktemp -d)
mkdir -p "$t/repos/alpha" "$t/repos/beta" "$t/repos/notarepo"
git -C "$t/repos/alpha" init -q
git -C "$t/repos/alpha" commit -q --allow-empty -m init
git -C "$t/repos/beta" init -q
git -C "$t/repos/beta" commit -q --allow-empty -m init
out="$(bash "$SCRIPT_DIR/discover.sh" "$t" 2>/dev/null | sort)"
expected_lines=2
actual_lines=$(printf '%s\n' "$out" | grep -c . || true)
assert_eq "$expected_lines" "$actual_lines" "discover.sh finds 2 repos"
assert_true "printf '%s\n' \"\$out\" | grep -q '^alpha	'" "discover includes alpha"
assert_true "printf '%s\n' \"\$out\" | grep -q '^beta	'" "discover includes beta"
rm -rf "$t"

# -----------------------------------------------------------------------------
# assemble-index.sh: build from one scratch entry + concept map
# -----------------------------------------------------------------------------
t=$(mktemp -d)
init_state_dir "$t"
mkdir -p "$SCRIPT_DIR/../templates"
# Use a minimal preamble (write if missing so test works on first run)
if [[ ! -f "$SCRIPT_DIR/../templates/preamble.md" ]]; then
    printf '# Workspace Index\n\n_Last regenerated: <TIMESTAMP>_\n\n---\n' > "$SCRIPT_DIR/../templates/preamble.md"
fi
printf '## alpha\n**Purpose:** demo.\n' > "$t/.update-index/scratch/alpha.entry.md"
printf '# Concept Map\n\n## demo\n- alpha — primary\n' > "$t/.update-index/scratch/concept-map.md"
bash "$SCRIPT_DIR/assemble-index.sh" "$t" 2>/dev/null
assert_true "[[ -f '$t/INDEX.md' ]]" "INDEX.md written"
assert_true "grep -q '## alpha' '$t/INDEX.md'" "INDEX contains per-repo block"
assert_true "grep -q '# Concept Map' '$t/INDEX.md'" "INDEX contains concept map"
assert_true "grep -q 'Last regenerated' '$t/INDEX.md'" "timestamp substituted"
rm -rf "$t"

# -----------------------------------------------------------------------------
# collect-signals.sh
# -----------------------------------------------------------------------------
# Empty last_sha -> NEW_REPO marker
t=$(mktemp -d)
git -C "$t" init -q
git -C "$t" commit -q --allow-empty -m init
out="$(bash "$SCRIPT_DIR/collect-signals.sh" "$t" "" 2>/dev/null)"
assert_eq "NEW_REPO" "$out" "empty last_sha -> NEW_REPO"
rm -rf "$t"

# Unreachable sha
t=$(mktemp -d)
git -C "$t" init -q
git -C "$t" commit -q --allow-empty -m init
out="$(bash "$SCRIPT_DIR/collect-signals.sh" "$t" "0000000000000000000000000000000000000000" 2>/dev/null)"
assert_true "[[ '$out' == UNREACHABLE_SHA* ]]" "unreachable sha reported"
rm -rf "$t"

# No diff between SHAs -> empty output
t=$(mktemp -d)
git -C "$t" init -q
git -C "$t" commit -q --allow-empty -m init
sha=$(git -C "$t" rev-parse HEAD)
out="$(bash "$SCRIPT_DIR/collect-signals.sh" "$t" "$sha" 2>/dev/null)"
assert_eq "" "$out" "no diff -> empty output"
rm -rf "$t"

# New top-level dir + commit subject
t=$(mktemp -d)
git -C "$t" init -q
git -C "$t" commit -q --allow-empty -m init
sha=$(git -C "$t" rev-parse HEAD)
mkdir -p "$t/billing"
echo "x" > "$t/billing/file.txt"
git -C "$t" add billing
git -C "$t" commit -q -m "feat: initial billing module"
out="$(bash "$SCRIPT_DIR/collect-signals.sh" "$t" "$sha" 2>/dev/null)"
assert_true "printf '%s' \"\$out\" | grep -q 'billing/ (added)'" "dir added detected"
assert_true "printf '%s' \"\$out\" | grep -q 'feat: initial billing module'" "commit subject present"
rm -rf "$t"

# README change detected
t=$(mktemp -d)
git -C "$t" init -q
echo "old" > "$t/README.md"
git -C "$t" add README.md
git -C "$t" commit -q -m init
sha=$(git -C "$t" rev-parse HEAD)
printf 'new content line1\nnew content line2\nnew content line3\n' > "$t/README.md"
git -C "$t" commit -q -am "docs: rewrite README"
out="$(bash "$SCRIPT_DIR/collect-signals.sh" "$t" "$sha" 2>/dev/null)"
assert_true "printf '%s' \"\$out\" | grep -q 'README_DIFF'" "README diff section present"
rm -rf "$t"

# -----------------------------------------------------------------------------
echo "-----"
echo "$PASSED passed, $FAILED failed"
[[ "$FAILED" -eq 0 ]]
