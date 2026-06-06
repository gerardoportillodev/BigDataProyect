#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

RUN_ID="${RUN_ID:-official_$(date -u +%Y%m%dT%H%M%SZ)}"

if [ ! -f "data/raw/creditos_raw.tsv" ]; then
  echo "No existe data/raw/creditos_raw.tsv. Generando TSV desde el Excel..."
  if [ ! -f "data/raw/ConvertidorEstructura - DATA.xlsm" ]; then
    echo "Falta data/raw/ConvertidorEstructura - DATA.xlsm"
    exit 1
  fi
  source scripts/use_local_spark.sh >/dev/null
  python src/00_export_xlsm_to_tsv.py \
    --input "data/raw/ConvertidorEstructura - DATA.xlsm" \
    --output "data/raw/creditos_raw.tsv"
fi

echo "== Construir y levantar arquitectura distribuida =="
docker compose build
docker compose up -d

echo "== Esperar inicialización de servicios =="
sleep 20

docker compose ps

echo "== Ejecutar pipeline en Spark Standalone =="
docker compose exec -T spark-client bash -lc "RUN_ID='$RUN_ID' bash scripts/run_distributed_inside.sh"

echo "Pipeline distribuido completado."
echo "Run ID oficial: $RUN_ID"
echo "NameNode UI: http://localhost:9870"
echo "Spark Master UI: http://localhost:8080"
echo "Spark Worker 1 UI: http://localhost:8081"
echo "Spark Worker 2 UI: http://localhost:8082"
echo "Spark Application UI durante ejecución: http://localhost:4040"
