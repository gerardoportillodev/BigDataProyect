# Resultados del experimento de modelado

> **Corrida oficial completada el 6 de junio de 2026.**
> Run ID: `official_20260606T191340Z`
> Pipeline ejecutado con `bash scripts/run_distributed_cluster.sh` — 15 pasos, clúster 7 contenedores.

---

## Arquitectura de la corrida oficial

| Componente | Detalle |
|---|---|
| Contenedores | 7 (namenode, datanode-1, datanode-2, spark-master, spark-worker-1, spark-worker-2, spark-client) |
| HDFS DataNodes | 2 |
| Spark Workers | 2 (ALIVE, Standalone) |
| Replicación HDFS | 2 |
| Spark Master URL | `spark://spark-master:7077` |
| Executors por corrida | 2 cores totales (1 core / 1.5 g por executor) |
| Driver | spark-client (accesible desde ambos workers) |

## Target experimental

`riesgo_crediticio_exp = 1` cuando:

```text
NumeroDiasMora >= 30 OR ValorMoraTotal > 0
```

Se excluyen registros con `NumeroDiasMora = 999` (código especial pendiente de validación de negocio).

Alcance: **clasificación al corte** — no predicción futura.

## Run ID oficial

```
official_20260606T191340Z
```

Evidencia guardada en:
- `data/results/cluster_evidence/hdfs_report_official_20260606T191340Z.txt`
- `data/results/cluster_evidence/spark_master_official_20260606T191340Z.json`
- `hdfs:///proyecto_crediticio/analytics/model_experiment/metrics/`
- `hdfs:///proyecto_crediticio/analytics/model_experiment/confusion_matrix/`

## Universo de modelado

| Partición | Registros |
|---|---:|
| Conjunto de prueba (30%) | 279,416 |
| Conjunto de entrenamiento (70%) | ~651,970 (estimado) |

## Métricas

| Modelo | Accuracy | Precision+ | Recall+ | F1+ | AUC-ROC | AUC-PR | TN | FP | FN | TP |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| logistic_regression | 93.9% | 79.8% | 82.5% | 81.1% | 94.4% | 88.2% | 226,065 | 9,218 | 7,729 | 36,404 |
| **random_forest** | **97.3%** | **98.8%** | **84.0%** | **90.8%** | **98.1%** | **95.5%** | **234,847** | **436** | **7,055** | **37,078** |

**Ganador: Random Forest** en todas las métricas excepto Recall+ (diferencia marginal: 84.0% vs 82.5%).

## Saldo expuesto

| Modelo | Saldo FN — riesgo no detectado | Saldo FP — falsa alarma |
|---|---:|---:|
| logistic_regression | $25,948,778 | $13,994,277 |
| **random_forest** | $26,620,081 | **$606,510** |

El Random Forest reduce el saldo expuesto por falsas alarmas en **$13.4M** (96% menos que LR), al costo de $671K adicionales en riesgo no detectado — un balance favorable para operaciones de cobranza.

## Matriz de confusión

### Regresión Logística

|  | Pred. 0 (Sano) | Pred. 1 (Riesgo) |
|---|---:|---:|
| **Real 0 (Sano)** | 226,065 ✅ | 9,218 ⚠️ |
| **Real 1 (Riesgo)** | 7,729 ❌ | 36,404 ✅ |

### Random Forest

|  | Pred. 0 (Sano) | Pred. 1 (Riesgo) |
|---|---:|---:|
| **Real 0 (Sano)** | 234,847 ✅ | 436 ⚠️ |
| **Real 1 (Riesgo)** | 7,055 ❌ | 37,078 ✅ |

## Importancia de variables (Random Forest)

Guardada en HDFS: `hdfs:///proyecto_crediticio/analytics/model_experiment/feature_diagnostics/random_forest/`

## Coeficientes (Regresión Logística)

Guardados en HDFS: `hdfs:///proyecto_crediticio/analytics/model_experiment/feature_diagnostics/logistic_regression/`

## Interpretación empresarial

Random Forest captura relaciones no lineales e interacciones entre variables.
Regresión Logística sirve como línea base interpretable y estable.

En clasificación crediticia al corte:
- **Recall positivo alto** → menos créditos en mora real pasan desapercibidos.
- **Precision positiva alta** → menos alertas falsas sobre créditos sanos.
- **AUC-ROC/AUC-PR** → robustez en umbrales.

## Cautelas metodológicas

- Target pendiente de validación de negocio.
- `NumeroDiasMora = 999` excluido — código especial sin interpretación confirmada.
- No se usan variables de leakage (mora, Estado, SubEstado, Calificacion) como predictoras.
- No se usan PII ni identificadores.
- Alcance: clasificación al corte de abril 2026 — no predicción dinámica.
- Nulos numéricos manejados con `Imputer(strategy="median")` — no reemplazados por cero.
- StandardScaler aplicado únicamente a Regresión Logística.
- Mismo split y seed para ambos modelos (`SEED = 20260430`, `test_size = 0.30`).

## Modelos guardados en HDFS

```
/proyecto_crediticio/modelos/official_20260606T191340Z/logistic_regression/
/proyecto_crediticio/modelos/official_20260606T191340Z/random_forest/
```

Ambos modelos se pueden cargar con `PipelineModel.load(path)`.

## Scores anonimizados

```
/proyecto_crediticio/resultados/scores/official_20260606T191340Z/logistic_regression/
/proyecto_crediticio/resultados/scores/official_20260606T191340Z/random_forest/
```

Columnas: `record_key` (SHA-256), `risk_probability`, `prediction`, `actual_label`. Sin PII.

## Siguientes pasos

1. Validar con negocio: significado de `NumeroDiasMora = 999`, `SubEstado`, y peso de `ValorMoraTotal`.
2. Evaluar si ajustar el umbral de clasificación (default 0.5) para optimizar recall vs precision según apetito de riesgo.
3. Analizar importancia de variables para interpretabilidad ante el comité.
