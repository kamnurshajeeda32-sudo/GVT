#!/usr/bin/env bash
set -euo pipefail
for i in $(seq 1 30); do
  if curl -fsS --max-time 3 http://127.0.0.1:3100/ | grep -q GRTAlgo && curl -fsS --max-time 3 http://127.0.0.1:8100/health | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["status"]=="ok" and d["trading_mode"]=="paper" and d["execution_enabled"] is False'; then
    exit 0
  fi
  sleep 2
done
exit 1
