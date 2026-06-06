#!/usr/bin/env bash

set -euo pipefail

echo "Docker:"
docker version --format '  Client={{.Client.Version}} Server={{.Server.Version}}'

echo "Contenedores activos:"
docker ps

echo "Compose:"
docker compose version
