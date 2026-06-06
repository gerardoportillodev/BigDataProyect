#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

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

docker compose build bigdata
docker compose up -d bigdata

docker compose exec -T bigdata bash -c '
set -euo pipefail
cd /workspace
export SPARK_SUBMIT_OPTS="-Dlog4j.configurationFile=file:/workspace/docker/spark/log4j2.properties"

spark_submit() {
  spark-submit --conf spark.ui.showConsoleProgress=false "$@"
}

echo "== Versiones =="
hadoop version | head -1
spark-submit --version 2>&1 | head -6
python3 --version

echo "== Estado HDFS =="
hdfs dfsadmin -report | sed -n "1,45p"

echo "== Crear zonas HDFS =="
hdfs dfs -mkdir -p /proyecto_crediticio/raw
hdfs dfs -mkdir -p /proyecto_crediticio/trusted
hdfs dfs -mkdir -p /proyecto_crediticio/analytics
hdfs dfs -mkdir -p /proyecto_crediticio/modelos
hdfs dfs -mkdir -p /proyecto_crediticio/resultados

echo "== Subir TSV a HDFS =="
hdfs dfs -put -f data/raw/creditos_raw.tsv /proyecto_crediticio/raw/creditos_raw.tsv
hdfs dfs -ls -h /proyecto_crediticio/raw

echo "== Perfilado raw =="
spark_submit --master local[*] src/01_ingest_profile.py \
  --input hdfs:///proyecto_crediticio/raw/creditos_raw.tsv \
  --output hdfs:///proyecto_crediticio/resultados/profiling_raw

echo "== Trusted Parquet =="
spark_submit --master local[*] src/02_clean_to_parquet.py \
  --input hdfs:///proyecto_crediticio/raw/creditos_raw.tsv \
  --output hdfs:///proyecto_crediticio/trusted/obligaciones

echo "== Validacion calidad/target =="
spark_submit --master local[*] src/03_validate_quality_target.py \
  --input hdfs:///proyecto_crediticio/trusted/obligaciones \
  --output hdfs:///proyecto_crediticio/analytics/target_validation

echo "== Modelado MLlib =="
spark_submit --master local[*] src/04_train_compare_models.py \
  --input hdfs:///proyecto_crediticio/trusted/obligaciones \
  --output hdfs:///proyecto_crediticio/resultados/model_experiment \
  --rf-trees 40 \
  --lr-max-iter 30

echo "== Salidas HDFS =="
hdfs dfs -du -h /proyecto_crediticio/raw
hdfs dfs -du -h /proyecto_crediticio/trusted
hdfs dfs -du -h /proyecto_crediticio/analytics
hdfs dfs -du -h /proyecto_crediticio/resultados
'

echo "Pipeline HDFS/Spark completado."
echo "NameNode UI: http://localhost:9870"
