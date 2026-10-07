#!/usr/bin/env bash
# Builds and (re)starts the stack on the server (E78). Run it from the repository root after the
# wanted commit is checked out and deploy/.env is in place; the deploy workflow does both.
set -euo pipefail

compose() {
  docker compose -f deploy/compose.yaml "$@"
}

test -f deploy/.env || { echo "deploy/.env is missing, see deploy/.env.example" >&2; exit 1; }

echo "== build"
compose build --pull

# The runner hands a running game back to the queue on SIGTERM (E75), so no game is lost.
echo "== stop runner"
compose stop runner

echo "== database"
compose up -d --wait mongo
compose run --rm mongo-users
compose run --rm migrate

echo "== services"
compose up -d --wait --remove-orphans api runner frontend

echo "== health"
compose exec -T frontend wget -q -O - http://127.0.0.1:8080/api/v1/health
echo

docker image prune -f >/dev/null
echo "== done"
