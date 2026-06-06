#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

source scripts/use_local_spark.sh >/dev/null
export SPARK_LOCAL_IP=127.0.0.1

python src/04_train_compare_models.py \
  --input data/trusted/obligaciones \
  --output data/results/model_experiment \
  --rf-trees "${RF_TREES:-40}" \
  --lr-max-iter "${LR_MAX_ITER:-30}"

python - <<'PY'
import csv
import glob

for section in ["label_distribution", "split_summary", "metrics", "confusion_matrix"]:
    path = glob.glob(f"data/results/model_experiment/{section}/part-*.csv")[0]
    print(f"\n## {section}")
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.reader(fh):
            print(",".join(row))
PY
