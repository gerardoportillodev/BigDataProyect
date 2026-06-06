#!/usr/bin/env bash
# Ejecutado DENTRO del contenedor spark-client.
# Requiere: RUN_ID exportado por el script externo.

set -euo pipefail

cd /workspace
RUN_ID="${RUN_ID:?RUN_ID es requerido}"

echo "[inside] Run ID: $RUN_ID"

spark_submit() {
  spark-submit \
    --master spark://spark-master:7077 \
    --deploy-mode client \
    --driver-memory 2g \
    --conf spark.ui.showConsoleProgress=false \
    --conf spark.cores.max=2 \
    --conf spark.executor.cores=1 \
    --conf spark.executor.memory=1500m \
    --conf spark.driver.host=spark-client \
    --conf spark.driver.bindAddress=0.0.0.0 \
    --conf spark.driver.port=4045 \
    --conf spark.blockManager.port=4046 \
    "$@"
}

# ── Versiones ────────────────────────────────────────────────────────────────
echo ""
echo "== Versiones =="
hadoop version | head -1
spark-submit --version 2>&1 | head -4
python3 --version

# ── Salir de safe mode si está activo ────────────────────────────────────────
hdfs dfsadmin -safemode leave 2>/dev/null || true

# ── Paso 7: Crear zonas HDFS ─────────────────────────────────────────────────
echo ""
echo "== Paso 7: Crear zonas HDFS =="
hdfs dfs -mkdir -p /proyecto_crediticio/raw
hdfs dfs -mkdir -p /proyecto_crediticio/trusted
hdfs dfs -mkdir -p /proyecto_crediticio/analytics
hdfs dfs -mkdir -p /proyecto_crediticio/modelos
hdfs dfs -mkdir -p /proyecto_crediticio/resultados/scores
hdfs dfs -mkdir -p /proyecto_crediticio/evidencia
hdfs dfs -ls /proyecto_crediticio

# ── Paso 8: Cargar TSV con replicación 2 ────────────────────────────────────
echo ""
echo "== Paso 8: Cargar TSV a HDFS (replicación 2) =="
TSV="data/raw/creditos_raw.tsv"
if [ ! -f "$TSV" ]; then
  echo "ERROR: No existe $TSV"
  exit 1
fi
hdfs dfs -put -f "$TSV" /proyecto_crediticio/raw/creditos_raw.tsv
hdfs dfs -setrep -w 2 /proyecto_crediticio/raw/creditos_raw.tsv
hdfs dfs -ls /proyecto_crediticio/raw/

# ── Evidencia HDFS ──────────────────────────────────────────────────────────
echo ""
echo "== Evidencia HDFS =="
mkdir -p data/results/cluster_evidence
hdfs dfsadmin -report | tee data/results/cluster_evidence/hdfs_report_"${RUN_ID}".txt
hdfs fsck /proyecto_crediticio/raw/creditos_raw.tsv -blocks -locations \
  | tee data/results/cluster_evidence/hdfs_fsck_"${RUN_ID}".txt

# ── Evidencia Spark Master ──────────────────────────────────────────────────
curl -fsS http://spark-master:8080/json/ \
  | tee data/results/cluster_evidence/spark_master_"${RUN_ID}".json

python3 scripts/verify_cluster.py \
  --hdfs-report data/results/cluster_evidence/hdfs_report_"${RUN_ID}".txt \
  --spark-master-json data/results/cluster_evidence/spark_master_"${RUN_ID}".json \
  --minimum-datanodes 2 \
  --minimum-workers 2

# ── Paso 9: Perfilado distribuido ────────────────────────────────────────────
echo ""
echo "== Paso 9: Perfilado con Spark distribuido =="
spark_submit \
  --name "proyecto-crediticio-ingest-profile-${RUN_ID}" \
  src/01_ingest_profile.py \
  --input /proyecto_crediticio/raw/creditos_raw.tsv \
  --output /proyecto_crediticio/analytics/profile

# ── Paso 10: Zona trusted en Parquet ─────────────────────────────────────────
echo ""
echo "== Paso 10: Zona trusted en Parquet =="
spark_submit \
  --name "proyecto-crediticio-clean-parquet-${RUN_ID}" \
  src/02_clean_to_parquet.py \
  --input /proyecto_crediticio/raw/creditos_raw.tsv \
  --output /proyecto_crediticio/trusted/obligaciones

# ── Paso 11: Validación de calidad y target ──────────────────────────────────
echo ""
echo "== Paso 11: Validación de calidad y target =="
spark_submit \
  --name "proyecto-crediticio-validate-${RUN_ID}" \
  src/03_validate_quality_target.py \
  --input /proyecto_crediticio/trusted/obligaciones \
  --output /proyecto_crediticio/analytics/validation

# ── Pasos 12-13: Entrenamiento de modelos ────────────────────────────────────
echo ""
echo "== Pasos 12-13: Entrenamiento Regresión Logística y Random Forest =="
spark_submit \
  --name "proyecto-crediticio-train-models-${RUN_ID}" \
  --conf spark.sql.shuffle.partitions=48 \
  src/04_train_compare_models.py \
  --input /proyecto_crediticio/trusted/obligaciones \
  --output /proyecto_crediticio/analytics/model_experiment \
  --models-output /proyecto_crediticio/modelos \
  --scores-output /proyecto_crediticio/resultados/scores \
  --run-id "$RUN_ID" \
  --rf-trees 20 \
  --rf-max-depth 6 \
  --lr-max-iter 20

# ── Paso 14: Guardar evidencia HDFS post-ejecución ──────────────────────────
echo ""
echo "== Paso 14: Evidencia post-ejecución =="
hdfs dfsadmin -report | tee data/results/cluster_evidence/hdfs_report_post_"${RUN_ID}".txt
hdfs dfs -ls -R /proyecto_crediticio | tee data/results/cluster_evidence/hdfs_tree_"${RUN_ID}".txt
curl -fsS http://spark-master:8080/json/ \
  | tee data/results/cluster_evidence/spark_master_post_"${RUN_ID}".json

# ── Paso 15: Resumen ─────────────────────────────────────────────────────────
echo ""
echo "== Paso 15: Run ID y resumen =="
echo "Run ID: $RUN_ID" | tee data/results/cluster_evidence/run_id.txt
hdfs dfs -ls /proyecto_crediticio/modelos/"$RUN_ID"/ 2>/dev/null && echo "Modelos guardados en HDFS." || true
hdfs dfs -ls /proyecto_crediticio/resultados/scores/"$RUN_ID"/ 2>/dev/null && echo "Scores guardados en HDFS." || true

echo ""
echo "[inside] Pipeline distribuido completado. Run ID: $RUN_ID"
