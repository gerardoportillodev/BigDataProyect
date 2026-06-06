#!/usr/bin/env bash

set -euo pipefail

cd /workspace
RUN_ID="${RUN_ID:?RUN_ID is required}"

export SPARK_SUBMIT_OPTS="-Dlog4j.configurationFile=file:/workspace/docker/spark/log4j2.properties"

spark_submit() {
  spark-submit \
    --master spark://spark-master:7077 \
    --deploy-mode client \
    --conf spark.ui.showConsoleProgress=false \
    --conf spark.cores.max=4 \
    --conf spark.executor.cores=1 \
    --conf spark.executor.memory=1g \
    --conf spark.driver.host=spark-client \
    --conf spark.driver.bindAddress=0.0.0.0 \
    --conf spark.driver.port=4045 \
    --conf spark.blockManager.port=4046 \
    "$@"
}

mkdir -p data/results/cluster_evidence

echo "== Versiones =="
hadoop version | head -1
spark-submit --version 2>&1 | head -6
python3 --version

echo "== Evidencia HDFS =="
hdfs dfsadmin -report | tee data/results/cluster_evidence/hdfs_report.txt

echo "== Evidencia Spark =="
curl -fsS http://spark-master:8080/json/ | tee data/results/cluster_evidence/spark_master.json
python3 scripts/verify_cluster.py \
  --spark-master-json data/results/cluster_evidence/spark_master.json \
  --minimum-workers 2

echo "== Crear zonas HDFS =="
hdfs dfs -mkdir -p /proyecto_crediticio/raw
hdfs dfs -mkdir -p /proyecto_crediticio/trusted
hdfs dfs -mkdir -p /proyecto_crediticio/analytics
hdfs dfs -mkdir -p /proyecto_crediticio/modelos
hdfs dfs -mkdir -p /proyecto_crediticio/resultados

echo "== Subir TSV a HDFS =="
hdfs dfs -put -f data/raw/creditos_raw.tsv /proyecto_crediticio/raw/creditos_raw.tsv
hdfs dfs -setrep -w 2 /proyecto_crediticio/raw/creditos_raw.tsv
hdfs dfs -ls -h /proyecto_crediticio/raw
hdfs fsck /proyecto_crediticio/raw/creditos_raw.tsv -files -blocks -locations \
  | tee data/results/cluster_evidence/hdfs_block_locations.txt

echo "== Perfilado raw distribuido =="
spark_submit src/01_ingest_profile.py \
  --input hdfs:///proyecto_crediticio/raw/creditos_raw.tsv \
  --output hdfs:///proyecto_crediticio/resultados/profiling_raw

echo "== Trusted Parquet distribuido =="
spark_submit src/02_clean_to_parquet.py \
  --input hdfs:///proyecto_crediticio/raw/creditos_raw.tsv \
  --output hdfs:///proyecto_crediticio/trusted/obligaciones

echo "== Validación calidad y target =="
spark_submit src/03_validate_quality_target.py \
  --input hdfs:///proyecto_crediticio/trusted/obligaciones \
  --output hdfs:///proyecto_crediticio/analytics/target_validation

echo "== Modelado MLlib distribuido =="
spark_submit src/04_train_compare_models.py \
  --input hdfs:///proyecto_crediticio/trusted/obligaciones \
  --output hdfs:///proyecto_crediticio/resultados/model_experiment \
  --models-output hdfs:///proyecto_crediticio/modelos \
  --scores-output hdfs:///proyecto_crediticio/resultados/scores \
  --run-id "$RUN_ID" \
  --rf-trees 40 \
  --rf-max-depth 8 \
  --lr-max-iter 30

echo "== Salidas HDFS =="
hdfs dfs -du -h /proyecto_crediticio/raw
hdfs dfs -du -h /proyecto_crediticio/trusted
hdfs dfs -du -h /proyecto_crediticio/analytics
hdfs dfs -du -h /proyecto_crediticio/modelos
hdfs dfs -du -h /proyecto_crediticio/resultados

hdfs dfsadmin -report > data/results/cluster_evidence/hdfs_report_after.txt
curl -fsS http://spark-master:8080/json/ > data/results/cluster_evidence/spark_master_after.json

echo "Pipeline distribuido finalizado: $RUN_ID"
