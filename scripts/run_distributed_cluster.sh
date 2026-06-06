#!/usr/bin/env bash
# Pipeline oficial distribuido — arquitectura 7 contenedores (2 DataNodes, 2 Spark Workers).
# Uso: bash scripts/run_distributed_cluster.sh

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

RUN_ID="${RUN_ID:-official_$(date -u +%Y%m%dT%H%M%SZ)}"
export RUN_ID
echo "============================================"
echo "  BigData Proyecto Crediticio"
echo "  Run ID: $RUN_ID"
echo "============================================"

# ── Paso 1: Exportar XLSM a TSV si no existe ──────────────────────────────────
if [ ! -f "data/raw/creditos_raw.tsv" ]; then
  echo ""
  echo "== Paso 1: Exportar XLSM a TSV =="
  XLSM="data/raw/ConvertidorEstructura - DATA.xlsm"
  if [ ! -f "$XLSM" ]; then
    echo "ERROR: No existe $XLSM"
    exit 1
  fi
  python src/00_export_xlsm_to_tsv.py \
    --input "$XLSM" \
    --output "data/raw/creditos_raw.tsv"
  echo "TSV generado: data/raw/creditos_raw.tsv"
else
  echo "== Paso 1: TSV ya existe — omitido =="
fi

# ── Paso 2: Construir imágenes ─────────────────────────────────────────────────
echo ""
echo "== Paso 2: Construir imágenes Docker =="
docker compose build

# ── Paso 3: Levantar todos los contenedores ───────────────────────────────────
echo ""
echo "== Paso 3: Levantar cluster (7 contenedores) =="
docker compose up -d

# ── Paso 4: Esperar que HDFS esté disponible ──────────────────────────────────
echo ""
echo "== Paso 4: Esperando HDFS (UI en :9870) =="
MAX_WAIT=120
ELAPSED=0
until docker compose exec -T namenode bash -c "curl -fsS http://localhost:9870/ > /dev/null 2>&1"; do
  if [ $ELAPSED -ge $MAX_WAIT ]; then
    echo "ERROR: NameNode HTTP no respondió en ${MAX_WAIT}s"
    docker compose logs namenode | tail -20
    exit 1
  fi
  echo "  Esperando NameNode... ($ELAPSED/$MAX_WAIT s)"
  sleep 5
  ELAPSED=$((ELAPSED + 5))
done
echo "  NameNode HTTP disponible."

# ── Paso 5: Esperar 2 DataNodes vivos ────────────────────────────────────────
echo ""
echo "== Paso 5: Esperando 2 DataNodes vivos =="
MAX_WAIT=90
ELAPSED=0
until docker compose exec -T namenode hdfs dfsadmin -report 2>/dev/null \
      | python3 -c "
import sys, re
text = sys.stdin.read()
m = re.search(r'Live datanodes\s*\((\d+)\)', text)
n = int(m.group(1)) if m else 0
sys.exit(0 if n >= 2 else 1)
" 2>/dev/null; do
  if [ $ELAPSED -ge $MAX_WAIT ]; then
    echo "ERROR: No se registraron 2 DataNodes en ${MAX_WAIT}s"
    docker compose exec -T namenode hdfs dfsadmin -report 2>/dev/null | head -10
    exit 1
  fi
  echo "  Esperando DataNodes... ($ELAPSED/${MAX_WAIT}s)"
  sleep 10
  ELAPSED=$((ELAPSED + 10))
done
echo "  2 DataNodes vivos."

# ── Paso 6: Esperar 2 Spark Workers ALIVE ────────────────────────────────────
echo ""
echo "== Paso 6: Esperando 2 Spark Workers ALIVE =="
MAX_WAIT=90
ELAPSED=0
until curl -fsS http://localhost:8080/json/ 2>/dev/null | python3 -c "
import sys, json
d = json.load(sys.stdin)
alive = [w for w in d.get('workers', []) if w.get('state') == 'ALIVE']
sys.exit(0 if len(alive) >= 2 else 1)
" 2>/dev/null; do
  if [ $ELAPSED -ge $MAX_WAIT ]; then
    echo "ERROR: No se registraron 2 Spark Workers ALIVE en ${MAX_WAIT}s"
    curl -fsS http://localhost:8080/json/ 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(json.dumps(d.get('workers',[]), indent=2))" || true
    exit 1
  fi
  echo "  Esperando Spark Workers... ($ELAPSED/$MAX_WAIT s)"
  sleep 10
  ELAPSED=$((ELAPSED + 10))
done
echo "  2 Spark Workers ALIVE."

# ── Evidencia pre-ejecución ───────────────────────────────────────────────────
echo ""
echo "== Evidencia del cluster ANTES de la corrida =="
docker compose ps
echo ""
docker compose exec -T namenode hdfs dfsadmin -report | tee /tmp/hdfs_report_pre.txt
echo ""
curl -fsS http://localhost:8080/json/ | python3 -c "
import sys, json
d = json.load(sys.stdin)
workers = d.get('workers', [])
alive = [w for w in workers if w.get('state') == 'ALIVE']
print(f'Spark Master: {d.get(\"status\",\"?\")}')
print(f'Workers registrados: {len(workers)}')
print(f'Workers ALIVE: {len(alive)}')
for w in alive:
    print(f'  - {w[\"host\"]}:{w[\"port\"]}  cores={w[\"cores\"]}  memory={w[\"memory\"]}MB')
"

# ── Paso 7-14: Ejecutar pipeline dentro del cluster ──────────────────────────
echo ""
echo "== Pasos 7-14: Pipeline distribuido dentro del cluster =="
docker compose exec -T \
  -e RUN_ID="$RUN_ID" \
  spark-client \
  bash scripts/run_distributed_inside.sh

# ── Evidencia post-ejecución ──────────────────────────────────────────────────
echo ""
echo "== Evidencia del cluster DESPUÉS de la corrida =="
docker compose exec -T namenode hdfs dfsadmin -report | tee /tmp/hdfs_report_post.txt
curl -fsS http://localhost:8080/json/ | python3 -c "
import sys, json
d = json.load(sys.stdin)
workers = d.get('workers', [])
alive = [w for w in workers if w.get('state') == 'ALIVE']
apps = d.get('completedApps', [])
print(f'Spark Master: {d.get(\"status\",\"?\")}')
print(f'Workers ALIVE: {len(alive)}')
print(f'Apps completadas: {len(apps)}')
for a in apps[-3:]:
    print(f'  - {a.get(\"name\",\"?\")} | {a.get(\"state\",\"?\")} | cores={a.get(\"cores\",\"?\")}')
"

echo ""
echo "============================================"
echo "  Pipeline distribuido completado."
echo "  Run ID: $RUN_ID"
echo "============================================"
echo "  NameNode UI:       http://localhost:9870"
echo "  Spark Master UI:   http://localhost:8080"
echo "  Spark Worker 1 UI: http://localhost:8081"
echo "  Spark Worker 2 UI: http://localhost:8082"
echo "  Spark App UI:      http://localhost:4040 (durante ejecución)"
echo "============================================"
