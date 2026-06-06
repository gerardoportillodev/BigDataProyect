#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

source scripts/use_local_spark.sh >/dev/null

python src/01_ingest_profile.py \
  --input data/raw/creditos_raw.tsv \
  --output data/results/profiling_raw

python src/02_clean_to_parquet.py \
  --input data/raw/creditos_raw.tsv \
  --output data/trusted/obligaciones

python src/03_validate_quality_target.py \
  --input data/trusted/obligaciones \
  --output data/analytics/target_validation

python - <<'PY'
from pyspark.sql import SparkSession

spark = SparkSession.builder.master("local[*]").appName("validate-local-pipeline").getOrCreate()
df = spark.read.parquet("data/trusted/obligaciones")
print("trusted_rows=", df.count())
print("trusted_columns=", len(df.columns))
print("has_riesgo_crediticio=", "riesgo_crediticio" in df.columns)
spark.stop()
PY

echo "Pipeline local Spark completado."
