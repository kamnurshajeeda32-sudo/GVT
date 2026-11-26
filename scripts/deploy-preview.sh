#!/usr/bin/env bash
# Install as a trusted, root-owned forced-command script; never execute from an unreviewed checkout.
set -euo pipefail
cd /opt/GRTAlgo
exec 9>/opt/GRTAlgo/.deploy.lock
flock -n 9
compose=(docker compose -p grtalgo -f /opt/GRTAlgo/compose.yaml)
archive=$(mktemp /opt/GRTAlgo/.release.XXXXXX)
trap 'rm -f "$archive"' EXIT
cat > "$archive"
# Preserve currently running image IDs, not mutable tags.
for service in frontend backend; do
  cid=$("${compose[@]}" ps -q "$service")
  test -n "$cid"
  docker tag "$(docker inspect -f '{{.Image}}' "$cid")" "grtalgo-$service:rollback"
done
check() {
  for i in $(seq 1 30); do
    if curl -fsS --max-time 3 http://127.0.0.1:3100/ | grep -q GRTAlgo && curl -fsS --max-time 3 http://127.0.0.1:8100/health | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["status"]=="ok" and d["trading_mode"]=="paper" and d["execution_enabled"] is False'; then return 0; fi
    sleep 2
  done
  return 1
}
if docker load -i "$archive" && "${compose[@]}" up -d --no-build --force-recreate && check; then
  echo "GRTAlgo preview deployed"
else
  echo "Deployment failed; restoring previous images" >&2
  for service in frontend backend; do
    docker tag "grtalgo-$service:rollback" "grtalgo-$service:latest"
  done
  "${compose[@]}" up -d --no-build --force-recreate
  check || echo "Rollback health check failed; manual intervention required" >&2
  exit 1
fi
