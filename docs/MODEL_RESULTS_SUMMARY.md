# Resultados del experimento de modelado

> **IMPORTANTE:** Este documento será actualizado con métricas oficiales tras ejecutar el pipeline distribuido completo.
> Las métricas previas fueron eliminadas porque no tienen un `run_id` generado por el pipeline oficial.
> Ejecuta `bash scripts/run_distributed_cluster.sh` para obtener el `run_id` oficial y poblar este documento.

---

## Arquitectura de la corrida oficial

| Componente | Detalle |
|---|---|
| Contenedores | 7 (namenode, datanode-1, datanode-2, spark-master, spark-worker-1, spark-worker-2, spark-client) |
| HDFS DataNodes | 2 |
| Spark Workers | 2 (ALIVE, Standalone) |
| Replicación HDFS | 2 |
| Spark Master URL | `spark://spark-master:7077` |
| Executors por corrida | hasta 4 cores totales (1 core / 1 g por executor) |
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
# Se asignará automáticamente por run_distributed_cluster.sh con formato:
# official_YYYYMMDDTHHMMSSZ
# Ejemplo: official_20260606T150000Z
```

El `run_id` se guarda en:

```
data/results/cluster_evidence/run_id.txt
```

## Universo de modelado

> Pendiente de corrida oficial.

## Métricas

> Pendiente de corrida oficial.

| Modelo | run_id | Accuracy | Precision+ | Recall+ | F1+ | AUC-ROC | AUC-PR | TN | FP | FN | TP |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| logistic_regression | — | — | — | — | — | — | — | — | — | — | — |
| random_forest | — | — | — | — | — | — | — | — | — | — | — |

## Saldo expuesto

| Modelo | Saldo FN (riesgo no detectado) | Saldo FP (falsa alarma) |
|---|---:|---:|
| logistic_regression | — | — |
| random_forest | — | — |

## Matriz de confusión

> Pendiente de corrida oficial.

## Importancia de variables (Random Forest)

> Pendiente de corrida oficial. Se guarda en:
> `hdfs:///proyecto_crediticio/analytics/model_experiment/feature_diagnostics`

## Coeficientes (Regresión Logística)

> Pendiente de corrida oficial.

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

## Siguientes pasos

1. Ejecutar `bash scripts/run_distributed_cluster.sh`.
2. Copiar `run_id` de `data/results/cluster_evidence/run_id.txt`.
3. Poblar métricas desde `hdfs:///proyecto_crediticio/analytics/model_experiment/metrics`.
4. Validar con negocio: significado de `NumeroDiasMora = 999`, `SubEstado`, y peso de `ValorMoraTotal`.
