#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export JAVA_HOME="$PROJECT_ROOT/tools/jdk-17.0.19+10/Contents/Home"
export PATH="$JAVA_HOME/bin:$PROJECT_ROOT/.venv/bin:$PATH"
export PYTHONPYCACHEPREFIX="/private/tmp/codex_pycache"

echo "Ambiente listo:"
echo "  Python: $(python --version)"
echo "  Java: $("$JAVA_HOME/bin/java" -version 2>&1 | head -1)"
echo "  PySpark: $(python -c 'import pyspark; print(pyspark.__version__)')"
echo
echo "Para activar en tu terminal:"
echo "  source scripts/use_local_spark.sh"
