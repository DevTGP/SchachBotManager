#!/usr/bin/env bash
# Runs the negative suite in the runner image with the rights the runner has in compose.yaml
# (sandbox.md, E86). Needs Docker on a Linux host with cgroup v2; run it from the repository root.
# The image is built first unless SBM_RUNNER_IMAGE names one that exists.
set -euo pipefail

image=${SBM_RUNNER_IMAGE:-sbm-runner}
if [ -z "${SBM_RUNNER_IMAGE:-}" ]; then
  docker build -f deploy/python.Dockerfile --target runner -t "$image" .
fi
# The runner image has no test tools; this layer adds pytest on top.
docker build -t sbm-runner-suite - <<DOCKERFILE
FROM $image
RUN pip install --no-cache-dir pytest==9.1.1
DOCKERFILE

# Keep these options in line with the runner service in deploy/compose.yaml.
docker run --rm \
  --read-only --tmpfs /tmp \
  --cap-drop ALL --cap-add SYS_ADMIN --cap-add SETUID --cap-add SETGID \
  --security-opt no-new-privileges:true \
  --security-opt seccomp=unconfined --security-opt apparmor=unconfined \
  --cgroupns private --network none \
  --volume "$PWD/services/runner/tests/sandbox:/suite:ro" --workdir /suite \
  --env SBM_REQUIRE_SANDBOX=1 --env PYTHONDONTWRITEBYTECODE=1 \
  --env GITHUB_ACTIONS --env PYTEST_RUN_PATH=services/runner/tests/sandbox \
  sbm-runner-suite \
  python -m pytest -p no:cacheprovider -v "$@" .
