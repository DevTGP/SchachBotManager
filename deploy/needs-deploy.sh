#!/usr/bin/env bash
# Prints "yes" when the checked-out commit changes anything the stack is built from, compared
# with the commit deploy.sh last brought up (deploy/.deployed-commit), otherwise "no" (E79).
# Run it from the repository root; the deploy workflow skips the build on "no".
set -euo pipefail

# Everything the images and deploy.sh are made of, see the Dockerfiles and compose.yaml.
paths=(deploy sandbox sdk/core sdk/python services/store services/runner services/gateway backend frontend)

last=$(cat deploy/.deployed-commit 2>/dev/null || true)
if [ -z "$last" ] || ! git cat-file -e "$last^{commit}" 2>/dev/null; then
  echo "no deployed commit recorded" >&2
  echo yes
elif git diff --quiet "$last" HEAD -- "${paths[@]}"; then
  echo "nothing the stack is built from changed since $(git rev-parse --short "$last")" >&2
  echo no
else
  echo "changed since $(git rev-parse --short "$last"):" >&2
  git diff --name-only "$last" HEAD -- "${paths[@]}" | sed -n '1,20p' >&2
  echo yes
fi
