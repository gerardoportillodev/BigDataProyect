# Runbook de ingesta y pipeline distribuido Spark + HDFS

## Comando oficial

```bash
bash scripts/run_distributed_cluster.sh
```

Este comando orquesta el pipeline completo en una arquitectura distribuida de **7 contenedores Docker**.

---

## Arquitectura

| Contenedor | Rol | Puerto |
|---|---|---|
| `namenode` | HDFS NameNode | 9870 (UI), 9000 (RPC) |
| `datanode-1` | HDFS DataNode 1 | — |
| `datanode-2` | HDFS DataNode 2 | — |
| `spark-master` | Spark Standalone Master | 8080 (UI), 7077 |
| `spark-worker-1` | Spark Worker 1 | 8081 (UI) |
| `spark-worker-2` | Spark Worker 2 | 8082 (UI) |
| `spark-client` | Cliente spark-submit | 4040 (App UI) |

Todos los contenedores se comunican en la red `bigdata_net`.

HDFS usa replicación 2. Cada DataNode tiene un volumen Docker independiente.

---

## Pasos del pipeline

| # | Paso | Descripción |
|---|---|---|
| 1 | Exportar XLSM → TSV | Si no existe `data/raw/creditos_raw.tsv` |
| 2 | Build Docker | `docker compose build` |
| 3 | Levantar cluster | `docker compose up -d` |
| 4 | Esperar HDFS | Safe mode OFF |
| 5 | Esperar 2 DataNodes | `hdfs dfsadmin -report` |
| 6 | Esperar 2 Workers ALIVE | Spark Master JSON API |
| 7 | Crear zonas HDFS | raw, trusted, analytics, modelos, scores |
| 8 | Cargar TSV | `hdfs dfs -put` + `setrep 2` |
| 9 | Perfilado | `src/01_ingest_profile.py` via spark-submit |
| 10 | Trusted Parquet | `src/02_clean_to_parquet.py` |
| 11 | Validación | `src/03_validate_quality_target.py` |
| 12-13 | Modelos | `src/04_train_compare_models.py` (LR + RF) |
| 14 | Evidencia post | hdfs dfsadmin, spark master JSON |
| 15 | Run ID | Guardado en `data/results/cluster_evidence/run_id.txt` |

---

## Configuración Spark

```
--master spark://spark-master:7077
--deploy-mode client
--conf spark.cores.max=4
--conf spark.executor.cores=1
--conf spark.executor.memory=1g
--conf spark.driver.host=spark-client
--conf spark.driver.bindAddress=0.0.0.0
```

El Driver corre en `spark-client` y es accesible desde ambos workers.
No se usa `local[*]` en ningún paso del pipeline oficial.

---

## Evidencia generada

```
data/results/cluster_evidence/
  hdfs_report_<run_id>.txt        ← hdfs dfsadmin -report
  hdfs_fsck_<run_id>.txt          ← hdfs fsck con bloques y ubicaciones
  spark_master_<run_id>.json      ← Spark Master REST API (workers ALIVE)
  hdfs_report_post_<run_id>.txt   ← post-ejecución
  spark_master_post_<run_id>.json ← post-ejecución
  hdfs_tree_<run_id>.txt          ← árbol de rutas HDFS
  run_id.txt                      ← run_id oficial de la corrida
```

---

## Rutas HDFS

```
/proyecto_crediticio/raw/creditos_raw.tsv        ← TSV fuente (replicación 2)
/proyecto_crediticio/trusted/obligaciones/        ← Parquet limpio
/proyecto_crediticio/analytics/profile/           ← Perfilado
/proyecto_crediticio/analytics/validation/        ← Validación calidad
/proyecto_crediticio/analytics/model_experiment/  ← Métricas, confusión, diagnostics
/proyecto_crediticio/modelos/<run_id>/            ← PipelineModel LR y RF
/proyecto_crediticio/resultados/scores/<run_id>/  ← Scores anonimizados
```

---

## Interfaces UI

| Interfaz | URL |
|---|---|
| NameNode HDFS | http://localhost:9870 |
| Spark Master | http://localhost:8080 |
| Spark Worker 1 | http://localhost:8081 |
| Spark Worker 2 | http://localhost:8082 |
| Spark Application | http://localhost:4040 (durante ejecución) |

---

## Verificación del cluster

```bash
# Dentro del contenedor spark-client:
python3 scripts/verify_cluster.py \
  --hdfs-report data/results/cluster_evidence/hdfs_report_<run_id>.txt \
  --spark-master-json data/results/cluster_evidence/spark_master_<run_id>.json \
  --minimum-datanodes 2 \
  --minimum-workers 2
```

---

## Detener el cluster

```bash
docker compose down
```

Para limpiar también los volúmenes HDFS:

```bash
docker compose down -v
```
