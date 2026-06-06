#!/usr/bin/env bash
set -euo pipefail

docker compose build
docker compose up -d
sleep 20
docker compose ps

docker compose exec -T spark-client bash scripts/run_distributed_inside.sh
