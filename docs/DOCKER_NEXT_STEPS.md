# Docker y HDFS desde Terminal

Docker funciona en la Terminal normal del usuario, pero la sesión sandbox de Codex no tiene permiso para conectarse al socket de Docker. Por eso los comandos Docker deben ejecutarse manualmente en Terminal.

## 1. Verificar Docker

```bash
cd ~/Downloads/proyecto_big_data_codex
bash scripts/docker_terminal_check.sh
```

## 2. Ejecutar el pipeline Spark local

Este pipeline ya usa PySpark y Parquet, pero todavía no usa HDFS:

```bash
cd ~/Downloads/proyecto_big_data_codex
bash scripts/run_local_spark_pipeline.sh
```

Debe terminar con:

```text
trusted_rows= 1006881
trusted_columns= 39
has_riesgo_crediticio= False
```

## 3. Pendiente HDFS

Para HDFS necesitamos usar el entorno Hadoop/Spark de clase o un `docker-compose.yml` compatible con esa clase. Si ya existe un compose del docente, colócalo en la raíz del proyecto o compártelo aquí.

Cuando ese compose exista, los pasos serán:

```bash
docker compose up -d
hdfs dfs -mkdir -p /proyecto_crediticio/raw
hdfs dfs -put -f data/raw/creditos_raw.tsv /proyecto_crediticio/raw/creditos_raw.tsv
spark-submit src/01_ingest_profile.py \
  --input hdfs:///proyecto_crediticio/raw/creditos_raw.tsv \
  --output hdfs:///proyecto_crediticio/resultados/profiling_raw
spark-submit src/02_clean_to_parquet.py \
  --input hdfs:///proyecto_crediticio/raw/creditos_raw.tsv \
  --output hdfs:///proyecto_crediticio/trusted/obligaciones
```

No se debe entrenar modelos hasta revisar perfilado, calidad y validación del target.
