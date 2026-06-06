# Setup local del proyecto

Este setup deja PySpark funcionando en la Mac sin cambiar el Java del sistema.

## Activar ambiente

```bash
cd ~/Downloads/proyecto_big_data_riesgo_crediticio
source scripts/use_local_spark.sh
```

El proyecto usa:

- Python virtualenv en `.venv/`.
- Java 17 local en `tools/jdk-17.0.19+10/Contents/Home`.
- PySpark instalado desde `requirements.txt`.

## Validar

```bash
python -m pytest -q
python src/00_inspect_xlsm.py
```

## Ejecutar Spark local sin HDFS

Mientras Docker/HDFS no esté activo, estos comandos permiten avanzar localmente:

```bash
python src/01_ingest_profile.py \
  --input data/raw/creditos_raw.tsv \
  --output data/results/profiling_raw

python src/02_clean_to_parquet.py \
  --input data/raw/creditos_raw.tsv \
  --output data/trusted/obligaciones

python src/03_validate_quality_target.py \
  --input data/trusted/obligaciones \
  --output data/analytics/target_validation
```

## Pendiente para el entorno Big Data completo

Para usar HDFS real falta abrir Docker Desktop o compartir el `docker-compose.yml` usado en clase. Cuando Docker esté encendido, se pueden ejecutar los comandos de `docs/RUNBOOK_INGESTA_SPARK.md`.
