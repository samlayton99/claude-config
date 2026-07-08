#!/usr/bin/env bash
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

# Tests appear below as the lib grows.

# parse_github_org
assert_eq "Alkonos" "$(parse_github_org 'https://github.com/Alkonos/alkonos.git')" "https .git"
assert_eq "Alkonos" "$(parse_github_org 'https://github.com/Alkonos/alkonos')"     "https no .git"
assert_eq "Alkonos" "$(parse_github_org 'git@github.com:Alkonos/alkonos.git')"     "ssh .git"
assert_eq "Alkonos" "$(parse_github_org 'ssh://git@github.com/Alkonos/alkonos.git')" "ssh:// .git"
assert_eq ""        "$(parse_github_org 'https://gitlab.com/foo/bar.git')"          "non-github returns empty"
assert_eq ""        "$(parse_github_org '')"                                         "empty input returns empty"

# pick_majority_org — fixture-based
_fixture_repos_dir() {
    local root; root="$(mktemp -d)"
    for r in "$@"; do
        local name="${r%%=*}"; local url="${r##*=}"
        mkdir -p "$root/$name"
        git -C "$root/$name" init -q
        git -C "$root/$name" remote add origin "$url"
    done
    echo "$root"
}

root=$(_fixture_repos_dir \
    "a=https://github.com/Alkonos/a.git" \
    "b=https://github.com/Alkonos/b.git" \
    "c=https://github.com/other/c.git")
assert_eq "Alkonos" "$(printf '%s\n' "$root"/*/ | pick_majority_org)" "majority wins"
rm -rf "$root"

root=$(_fixture_repos_dir \
    "a=https://github.com/First/a.git" \
    "b=https://github.com/Second/b.git")
# tie: First listed first alphabetically by dir name (a before b) → First
assert_eq "First" "$(printf '%s\n' "$root"/*/ | pick_majority_org)" "tie → first seen"
rm -rf "$root"

root=$(_fixture_repos_dir "a=https://gitlab.com/foo/a.git")
assert_eq "" "$(printf '%s\n' "$root"/*/ | pick_majority_org)" "no github repos → empty"
rm -rf "$root"

assert_eq "" "$(printf '' | pick_majority_org)" "empty stdin → empty"

# find_repos_folder
t=$(mktemp -d); mkdir -p "$t/repos"
assert_eq "$t/repos" "$(find_repos_folder "$t")" "prefers repos/ subfolder"
rm -rf "$t"

t=$(mktemp -d)
assert_eq "$t" "$(find_repos_folder "$t")" "falls back to self"
rm -rf "$t"

# list_git_children
t=$(mktemp -d)
mkdir -p "$t/a" "$t/b" "$t/notarepo"
git -C "$t/a" init -q
git -C "$t/b" init -q
got="$(list_git_children "$t" | sort | tr '\n' ' ')"
assert_eq "$t/a $t/b " "$got" "only git children listed"
rm -rf "$t"

t=$(mktemp -d)
assert_eq "" "$(list_git_children "$t")" "empty dir returns empty"
rm -rf "$t"

# Fixture: a bare repo + a working clone.
_make_paired_repos() {
    local tmp; tmp="$(mktemp -d)"
    git init -q --bare "$tmp/remote.git"
    git clone -q "$tmp/remote.git" "$tmp/work"
    git -C "$tmp/work" commit -q --allow-empty -m init
    # Ensure we're on a known default branch name
    git -C "$tmp/work" branch -M main
    git -C "$tmp/work" push -q -u origin main >/dev/null 2>&1
    # Bare repos cloned from empty state don't set HEAD; set it explicitly
    # so that remote set-head and symbolic-ref work correctly.
    git -C "$tmp/remote.git" symbolic-ref HEAD refs/heads/main
    git -C "$tmp/work" fetch -q
    git -C "$tmp/work" remote set-head origin -a >/dev/null 2>&1
    echo "$tmp"
}

# get_default_branch
t=$(_make_paired_repos)
assert_eq "main" "$(get_default_branch "$t/work")" "default branch via HEAD"
rm -rf "$t"

# classify_repo: clean on default
t=$(_make_paired_repos)
assert_eq "CLEAN_ON_DEFAULT" "$(classify_repo "$t/work")" "clean on default"
rm -rf "$t"

# classify_repo: dirty
t=$(_make_paired_repos)
echo "change" > "$t/work/file.txt"
assert_eq "BEHIND_DEFAULT_DIRTY" "$(classify_repo "$t/work")" "dirty on default"
rm -rf "$t"

# classify_repo: feature branch
t=$(_make_paired_repos)
git -C "$t/work" checkout -q -b feature
assert_eq "FEATURE_BRANCH" "$(classify_repo "$t/work")" "feature branch"
rm -rf "$t"

# classify_repo: detached
t=$(_make_paired_repos)
sha=$(git -C "$t/work" rev-parse HEAD)
git -C "$t/work" checkout -q --detach "$sha"
assert_eq "DETACHED" "$(classify_repo "$t/work")" "detached HEAD"
rm -rf "$t"

# classify_repo: no origin
t=$(mktemp -d); git -C "$t" init -q; git -C "$t" commit -q --allow-empty -m x
assert_eq "NO_REMOTE" "$(classify_repo "$t")" "no origin"
rm -rf "$t"

# classify_repo: empty remote (origin configured but has no branches/HEAD)
t=$(mktemp -d)
git init -q --bare "$t/bare.git"
git init -q "$t/work"
git -C "$t/work" commit -q --allow-empty -m init
git -C "$t/work" branch -M main
git -C "$t/work" remote add origin "$t/bare.git"
assert_eq "EMPTY_REMOTE" "$(classify_repo "$t/work")" "empty remote"
rm -rf "$t"

# update_repo: empty remote surfaces as EMPTY_REMOTE line
t=$(mktemp -d)
git init -q --bare "$t/bare.git"
git init -q "$t/work"
git -C "$t/work" commit -q --allow-empty -m init
git -C "$t/work" branch -M main
git -C "$t/work" remote add origin "$t/bare.git"
name="$(basename "$t/work")"
line="$(update_repo "$t/work")"
assert_eq "$name	main	EMPTY_REMOTE	no branches on origin" "$line" "empty remote line"
rm -rf "$t"

# update_repo: clean, fetch, ff-only pulls 2 commits
t=$(_make_paired_repos)
# Simulate remote advancement: push 2 commits via a second clone
git clone -q "$t/remote.git" "$t/advance"
git -C "$t/advance" commit -q --allow-empty -m c1
git -C "$t/advance" commit -q --allow-empty -m c2
git -C "$t/advance" push -q origin main >/dev/null 2>&1
name="$(basename "$t/work")"
line="$(update_repo "$t/work")"
assert_eq "$name	main	PULLED	2" "$line" "pulled 2 commits"
rm -rf "$t"

# update_repo: up-to-date
t=$(_make_paired_repos)
name="$(basename "$t/work")"
line="$(update_repo "$t/work")"
assert_eq "$name	main	UP_TO_DATE	" "$line" "up-to-date"
rm -rf "$t"

# update_repo: diverged (local commit not on origin while origin advanced)
t=$(_make_paired_repos)
git clone -q "$t/remote.git" "$t/advance"
git -C "$t/advance" commit -q --allow-empty -m remote_c1
git -C "$t/advance" push -q origin main >/dev/null 2>&1
git -C "$t/work" commit -q --allow-empty -m local_only
name="$(basename "$t/work")"
line="$(update_repo "$t/work")"
assert_eq "$name	main	DIVERGED	" "$line" "diverged"
rm -rf "$t"

# update_repo: feature branch
t=$(_make_paired_repos)
git -C "$t/work" checkout -q -b feature
name="$(basename "$t/work")"
line="$(update_repo "$t/work")"
assert_eq "$name	feature	FEATURE_BRANCH	default=main" "$line" "feature branch line"
rm -rf "$t"

# format_summary: basic case
input='alkonos	main	PULLED	14
platform	main	PULLED	7
backend	main	UP_TO_DATE
browser-pool	fix/foo	FEATURE_BRANCH	default=staging
crawler	main	DIVERGED	'
expected='Cloned: new-service

Pulled:
Repo      Branch  Commits
--------  ------  -------
alkonos   main    14
platform  main    7

1 cloned, 2 pulled, 1 up-to-date, 2 need attention.'
got="$(printf '%s\n' "$input" | CLONED='new-service' format_summary)"
assert_eq "$expected" "$got" "format_summary basic"

# format_summary: nothing cloned, nothing needing attention
input='a	main	PULLED	3
b	main	UP_TO_DATE	'
expected='Pulled:
Repo  Branch  Commits
----  ------  -------
a     main    3

0 cloned, 1 pulled, 1 up-to-date, 0 need attention.'
got="$(printf '%s\n' "$input" | CLONED='' format_summary)"
assert_eq "$expected" "$got" "format_summary no attention"

echo "-----"
echo "$PASSED passed, $FAILED failed"
[[ "$FAILED" -eq 0 ]]
