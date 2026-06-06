# Clasificación de Riesgo Crediticio con Big Data Distribuido

**Proyecto final — Analítica y Tecnologías de Big Data**

Sistema distribuido que procesa ~1 millón de obligaciones financieras y entrena dos modelos de Machine Learning (Regresión Logística y Random Forest) usando Apache Hadoop HDFS + Apache Spark sobre una arquitectura de **7 contenedores Docker**.

> **Corrida oficial completada:** `official_20260606T191340Z`  
> **Ganador:** Random Forest — AUC-ROC **98.1%**, Accuracy **97.3%**

---

## Caso de negocio

Clasificar obligaciones financieras activas al corte de abril 2026 según señales de riesgo crediticio, para apoyar la priorización de cobranza, segmentación de cartera y análisis de deterioro. El alcance es **clasificación al corte**, no predicción futura.

**Target experimental:**
```
riesgo_crediticio_exp = 1  si  NumeroDiasMora >= 30  OR  ValorMoraTotal > 0
riesgo_crediticio_exp = 0  en caso contrario
(excluye NumeroDiasMora = 999 — código especial sin validación de negocio)
```

---

## Resultados Oficiales

**Run ID:** `official_20260606T191340Z` — 279,416 registros en prueba

| Modelo | Accuracy | AUC-ROC | AUC-PR | Precisión+ | Recall+ | F1+ |
|---|---:|---:|---:|---:|---:|---:|
| Regresión Logística | 93.9% | 94.4% | 88.2% | 79.8% | 82.5% | 81.1% |
| **Random Forest** ✅ | **97.3%** | **98.1%** | **95.5%** | **98.8%** | **84.0%** | **90.8%** |

### Matrices de confusión

**Regresión Logística**

|  | Pred. Sano | Pred. Riesgo |
|---|---:|---:|
| **Real Sano** | 226,065 ✅ | 9,218 ⚠️ |
| **Real Riesgo** | 7,729 ❌ | 36,404 ✅ |

**Random Forest**

|  | Pred. Sano | Pred. Riesgo |
|---|---:|---:|
| **Real Sano** | 234,847 ✅ | 436 ⚠️ |
| **Real Riesgo** | 7,055 ❌ | 37,078 ✅ |

### Saldo expuesto

| Modelo | Saldo FN — riesgo no detectado | Saldo FP — falsa alarma |
|---|---:|---:|
| Regresión Logística | $25,948,778 | $13,994,277 |
| **Random Forest** | $26,620,081 | **$606,510** |

Random Forest reduce las falsas alarmas en **96%** ($13.4M menos), evitando rechazar créditos sanos innecesariamente.

---

## Arquitectura — 7 Contenedores Docker

```
┌─────────────────── Red: bigdata_net ───────────────────────────────┐
│                                                                     │
│  ┌──────────────── HDFS (Almacenamiento) ─────────────────────┐    │
│  │  namenode       → Directorio de bloques       :9870        │    │
│  │  datanode-1     → Almacena bloques  ─┐                     │    │
│  │  datanode-2     → Réplica de bloques ┘  replicación 2x     │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ┌──────────────── Spark (Procesamiento) ─────────────────────┐    │
│  │  spark-master   → Coordinador del clúster     :8080 :7077  │    │
│  │  spark-worker-1 → 2 cores · 2 GB RAM          :8081        │    │
│  │  spark-worker-2 → 2 cores · 2 GB RAM          :8082        │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  spark-client  → Ejecuta el pipeline (spark-submit)  :4040         │
└─────────────────────────────────────────────────────────────────────┘
```

### ¿Por qué 7 contenedores y no uno solo?

| Contenedor | Rol | Por qué es necesario |
|---|---|---|
| **namenode** | Directorio HDFS | Registra dónde vive cada bloque de datos. Sin él no hay sistema de archivos distribuido. |
| **datanode-1** | Almacén de bloques | Guarda físicamente los datos. Con dos nodos se garantiza que si uno falla, el otro tiene la copia. |
| **datanode-2** | Réplica de bloques | Hace posible la replicación 2x — la misma información en dos lugares distintos simultáneamente. |
| **spark-master** | Coordinador Spark | Recibe los jobs y decide qué worker ejecuta qué tarea. Es el "supervisor" del procesamiento. |
| **spark-worker-1** | Ejecutor de tareas | Realiza los cálculos reales en paralelo. Más workers = más velocidad de procesamiento. |
| **spark-worker-2** | Ejecutor de tareas | Trabaja en paralelo con worker-1. Juntos procesan el millón de registros en fracciones del tiempo. |
| **spark-client** | Driver del pipeline | Orquesta los 15 pasos: envía instrucciones al clúster, espera resultados, guarda en HDFS. |

---

## Pipeline de 15 Pasos

```bash
bash scripts/run_distributed_cluster.sh
```

| # | Paso | Dónde corre | Qué hace |
|---|---|---|---|
| 1 | Exportar XLSM → TSV | Local · Python | Convierte el Excel con macros a texto plano compatible con sistemas distribuidos |
| 2 | Build imágenes Docker | Docker | Construye la imagen con Hadoop 3.3.6 + Spark 3.5.3 + Python 3.11 |
| 3 | Levantar clúster | Docker Compose | Inicia los 7 contenedores en red privada `bigdata_net` |
| 4 | Esperar NameNode | healthcheck | Valida que HDFS responde en `:9870` antes de continuar |
| 5 | Esperar 2 DataNodes | `dfsadmin -report` | Confirma que ambos DataNodes están registrados y vivos |
| 6 | Esperar 2 Workers ALIVE | Spark REST API | Verifica que ambos workers están activos en el Master |
| 7 | Crear zonas HDFS | `hdfs dfs -mkdir` | Crea la estructura de carpetas: raw, trusted, analytics, modelos, resultados |
| 8 | Cargar TSV → HDFS | `hdfs dfs -put` | Sube los datos crudos con replicación automática en ambos DataNodes |
| 9 | Perfilado distribuido | `spark-submit` | Analiza nulos, tipos, distribuciones y duplicados del dataset crudo |
| 10 | Zona Trusted (Parquet) | `spark-submit` | Limpia, castea tipos, crea variables derivadas, guarda en Parquet comprimido |
| 11 | Validación de calidad | `spark-submit` | Verifica integridad: nulls, rangos, target válido, exclusión de 999 |
| 12 | Entrenar LR | `spark-submit` · MLlib | Regresión Logística con StandardScaler + Imputer(median) distribuido en workers |
| 13 | Entrenar RF | `spark-submit` · MLlib | Random Forest (20 árboles, profundidad 6) distribuido en workers |
| 14 | Evidencia post-ejecución | HDFS + Spark API | Guarda reporte del clúster, árbol HDFS y estado de Spark Master |
| 15 | Resumen y Run ID | consola | Imprime Run ID oficial y URLs de las interfaces web |

**Zonas HDFS al finalizar:**
```
/proyecto_crediticio/raw/                        ← TSV original (189 MB · replicación 2x)
/proyecto_crediticio/trusted/                    ← Parquet limpio
/proyecto_crediticio/analytics/                  ← Perfilado, métricas, confusion matrix
/proyecto_crediticio/modelos/<run_id>/           ← PipelineModel LR y RF persistidos
/proyecto_crediticio/resultados/scores/<run_id>/ ← Scores anonimizados (SHA-256)
```

---

## Demo Rápida (sin reentrenar)

El clúster y los modelos ya están entrenados y corriendo. Para demostrar el sistema en vivo:

### 1. Mostrar los 7 contenedores activos
```bash
docker compose ps
```

### 2. Abrir las interfaces web en el navegador
| UI | URL | Qué muestra |
|---|---|---|
| HDFS NameNode | http://localhost:9870 | DataNodes vivos, bloques, replicación |
| Spark Master | http://localhost:8080 | Workers ALIVE, apps completadas |
| Spark Worker 1 | http://localhost:8081 | Recursos y tareas ejecutadas |
| Spark Worker 2 | http://localhost:8082 | Recursos y tareas ejecutadas |

### 3. Verificar el clúster desde consola
```bash
# Estado de HDFS — 2 DataNodes, bloques replicados
docker compose exec -T namenode hdfs dfsadmin -report

# Árbol de archivos en HDFS
docker compose exec -T spark-client hdfs dfs -ls -R /proyecto_crediticio

# Ver métricas reales de los modelos
docker compose exec -T spark-client bash -c \
  "hdfs dfs -cat /proyecto_crediticio/analytics/model_experiment/metrics/*.csv"
```

### 4. Ver los resultados directamente
```bash
# Integridad del archivo en HDFS (replicación 2x confirmada)
docker compose exec -T namenode \
  hdfs fsck /proyecto_crediticio/raw/creditos_raw.tsv -files -blocks
```

### 5. Páginas de evidencia (abrir en navegador)
```bash
open docs/diagrama_arquitectura.html   # Diagrama visual del sistema
open docs/evidencia_ejecucion.html     # Evidencia real con métricas
```

---

## Datos del Dataset

| Métrica | Valor |
|---|---:|
| Registros totales | 1,006,881 |
| Columnas originales | 32 |
| Obligaciones activas | 973,350 |
| Obligaciones cerradas | 33,531 |
| Saldo total activo | $3,173,079,995.81 |
| Mora total activa | $30,876,513.15 |
| Registros modelados | ~929,820 |
| Registros en prueba | 279,416 |
| Clase positiva (riesgo) | ~15.85% |

---

## Tecnologías

| Tecnología | Versión | Rol |
|---|---|---|
| Apache Hadoop HDFS | 3.3.6 | Almacenamiento distribuido con replicación |
| Apache Spark | 3.5.3 | Procesamiento distribuido y MLlib |
| PySpark MLlib | 3.5.3 | Pipelines de ML: StringIndexer, Imputer, VectorAssembler, StandardScaler, LR, RF |
| Docker / Compose | 29.x / 5.x | Orquestación de los 7 contenedores |
| Python | 3.11 | Scripts de procesamiento y tests |
| Parquet + Snappy | — | Formato columnar comprimido para zona trusted |

---

## Estructura del Repositorio

```
.
├── docker/
│   ├── Dockerfile                        ← Hadoop + Spark + Python en una imagen
│   ├── hadoop/
│   │   ├── core-site.xml                 ← fs.defaultFS = hdfs://namenode:9000
│   │   └── hdfs-site.xml                 ← replication=2, sin rpc-address problemático
│   └── scripts/entrypoint.sh             ← Lógica de arranque por SERVICE_ROLE
├── docs/
│   ├── MODEL_RESULTS_SUMMARY.md          ← Métricas oficiales completas
│   ├── diagrama_arquitectura.html        ← Diagrama visual (abrir en navegador)
│   ├── evidencia_ejecucion.html          ← Evidencia real del clúster
│   ├── RUNBOOK_INGESTA_SPARK.md
│   └── ...
├── scripts/
│   ├── run_distributed_cluster.sh        ← COMANDO OFICIAL (15 pasos)
│   ├── run_distributed_inside.sh         ← Ejecutado dentro de spark-client
│   └── verify_cluster.py                 ← Validación de DataNodes y Workers
├── src/
│   ├── 00_export_xlsm_to_tsv.py          ← Paso 1: Excel → TSV
│   ├── 01_ingest_profile.py              ← Paso 9: Perfilado distribuido
│   ├── 02_clean_to_parquet.py            ← Paso 10: Zona trusted
│   ├── 03_validate_quality_target.py     ← Paso 11: Validación calidad
│   └── 04_train_compare_models.py        ← Pasos 12-13: LR + RF
├── tests/
│   └── test_train_compare_models.py      ← 28 pruebas sintéticas (sin PII)
├── docker-compose.yml                    ← 7 servicios: namenode, 2 datanodes, master, 2 workers, client
└── README.md
```

---

## Privacidad y Seguridad

- El dataset contiene información personal y **no se sube a GitHub** (`.gitignore` excluye `data/`)
- Los scores guardados usan `record_key` generado con **SHA-256** — imposible revertir a datos personales
- Columnas excluidas del modelo: `NombreCompleto`, `Identificacion6`, `Identificacion2`, `NumeroDeObligacion`
- Las pruebas usan datos sintéticos sin PII

---

## Cautelas Metodológicas

- Target pendiente de validación de negocio
- `NumeroDiasMora = 999` excluido — código especial sin interpretación confirmada (43,530 registros)
- Variables de leakage excluidas del modelo: `Estado`, `SubEstado`, `Calificacion`, `NumeroDiasMora`, `ValorMoraTotal`
- `Imputer(strategy="median")` para nulos numéricos — no reemplazados por cero
- `StandardScaler` aplicado únicamente a Regresión Logística
- Mismo split y semilla para ambos modelos (`SEED = 20260430`, `test_size = 0.30`)
- Alcance: clasificación al corte de abril 2026 — no predicción dinámica
