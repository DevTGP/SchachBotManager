#!/usr/bin/env bash
# Prints for every CI job whether its part of the repository changed between the commit given
# as $1 and HEAD, as name=true|false lines for $GITHUB_OUTPUT (E79). The CI passes the last commit
# that passed CI, or the base of a pull request. Without a usable base commit (manual run, no green
# run yet) or when the CI itself changed, every job runs.
set -euo pipefail

base=${1:-}

# Job name → paths it builds, checks or tests (extended regular expressions on file paths).
declare -A areas=(
  [spec]='^(spec/|tools/spec-check/)'
  [testvectors]='^(spec/|tools/testvector-gen/)'
  [core_headers]='^sdk/core/(include/|tests/header_check)'
  [core]='^(sdk/core/|spec/testvectors/)'
  [python]='^(sdk/core/|sdk/python/|templates/python/|spec/)'
  [services]='^(sdk/core/|sdk/python/|services/|backend/|spec/)'
  [sandbox]='^(sandbox/|deploy/python\.Dockerfile|sdk/core/|sdk/python/|services/)'
  [frontend]='^(frontend/|spec/web/)'
  [native_format]='^(sdk/\.clang-format$|sdk/core/(include|src|tests)/|sdk/python/src/native/)'
)
everything='^(\.github/workflows/ci\.yml|\.github/scripts/changed-areas\.sh)$'

all=false
files=''
if [[ ! "$base" =~ ^[0-9a-f]{40}$ || "$base" =~ ^0+$ ]] || ! git cat-file -e "$base^{commit}" 2>/dev/null; then
  echo "no base commit, running every job" >&2
  all=true
else
  files=$(git diff --name-only "$base" HEAD)
  if grep -Eq "$everything" <<<"$files"; then
    echo "the CI changed, running every job" >&2
    all=true
  fi
fi

for name in $(printf '%s\n' "${!areas[@]}" | sort); do
  if [ "$all" = true ] || grep -Eq "${areas[$name]}" <<<"$files"; then
    echo "$name=true"
  else
    echo "$name=false"
  fi
done
