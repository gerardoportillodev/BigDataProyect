# Proyecto Big Data: clasificación de riesgo crediticio con Spark y MLlib

## 1. Propósito del proyecto

El proyecto desarrolla un flujo completo de Big Data para clasificar obligaciones financieras activas según su riesgo crediticio al corte de abril de 2026. La solución no se limita a entrenar un modelo de machine learning: integra ingesta, validación, almacenamiento, procesamiento distribuido, limpieza, generación de variables, análisis descriptivo, modelado con MLlib, comparación de algoritmos e interpretación de resultados.

La opción seleccionada según la rúbrica es la Opción 2: utilizar dos técnicas con propósito similar sobre el mismo dataset para resolver un solo caso de negocio y comparar sus resultados. Los modelos comparados son Regresión Logística y Random Forest.

## 2. Caso de negocio

El caso de negocio consiste en clasificar obligaciones financieras activas según señales de riesgo crediticio, con el objetivo de priorizar gestión preventiva, segmentar cartera y apoyar la asignación de recursos de cobranza. La base corresponde a una fotografía de cartera con corte a abril de 2026, por lo que el alcance metodológico se define como clasificación de riesgo crediticio al corte, no como predicción futura de mora.

## 3. Tecnologías utilizadas

Las tecnologías principales definidas para el proyecto son Python, PySpark, Apache Spark, Spark SQL, Spark MLlib, HDFS, Parquet y Docker con el entorno Hadoop/Spark usado en clase. El procesamiento principal, análisis y modelado se implementaron con Spark DataFrames, Spark SQL y MLlib.

## 4. Dataset y protección de datos

Archivo fuente esperado:

```text
data/raw/ConvertidorEstructura - DATA.xlsm
```

Características validadas:

- Hoja: `Sheet1`.
- Filas incluyendo encabezado: 1,006,882.
- Registros reales: 1,006,881.
- Columnas: 32.
- Corte: abril de 2026.

El archivo contiene información personal y financiera. Por protección de datos, no se imprimen registros reales ni identificadores como `NombreCompleto`, `Identificacion6`, `Identificacion2` o `NumeroDeObligacion`.

## 5. Arquitectura Big Data

```text
Excel .xlsm -> TSV/CSV -> HDFS raw -> Spark DataFrames -> Perfilado y limpieza distribuida -> Parquet trusted -> Spark SQL analytics -> MLlib -> Resultados y documentación
```

Zonas HDFS propuestas:

```text
/proyecto_crediticio/raw
/proyecto_crediticio/trusted
/proyecto_crediticio/analytics
/proyecto_crediticio/modelos
/proyecto_crediticio/resultados
```

## 6. Estructura de código creada

Scripts principales:

```text
src/00_inspect_xlsm.py
src/00_export_xlsm_to_tsv.py
src/01_ingest_profile.py
src/02_clean_to_parquet.py
src/03_validate_quality_target.py
src/04_train_compare_models.py
src/project_config.py
src/xlsm_utils.py
```

Scripts de consola:

```text
scripts/use_local_spark.sh
scripts/docker_terminal_check.sh
scripts/run_local_spark_pipeline.sh
scripts/run_model_experiment.sh
```

Documentación generada:

```text
docs/SETUP_LOCAL.md
docs/DOCKER_NEXT_STEPS.md
docs/RUNBOOK_INGESTA_SPARK.md
docs/TARGET_VALIDATION_NOTES.md
docs/MODELING_EXPERIMENT_NOTES.md
docs/MODEL_RESULTS_SUMMARY.md
docs/FINAL_TECHNICAL_REPORT.md
```

## 7. Comandos de consola ejecutables

Activar ambiente local Spark:

```bash
cd ~/Downloads/proyecto_big_data_riesgo_crediticio
source scripts/use_local_spark.sh
```

Verificar Docker:

```bash
cd ~/Downloads/proyecto_big_data_riesgo_crediticio
bash scripts/docker_terminal_check.sh
```

Resultado validado:

```text
Docker:
  Client=29.1.5 Server=29.1.5
Compose:
Docker Compose version v5.0.1
```

Inspeccionar Excel sin imprimir datos personales:

```bash
python src/00_inspect_xlsm.py
```

Resultado validado:

```text
Hojas: ['Sheet1']
Dimension: A1:AF1006882
Filas incluyendo encabezado: 1006882
Columnas: 32
Encabezados coinciden: True
```

Exportar Excel a TSV:

```bash
python src/00_export_xlsm_to_tsv.py \
  --input "data/raw/ConvertidorEstructura - DATA.xlsm" \
  --output "data/raw/creditos_raw.tsv"
```

Ejecutar pipeline Spark local:

```bash
bash scripts/run_local_spark_pipeline.sh
```

Resultado validado:

```text
trusted_rows= 1006881
trusted_columns= 39
has_riesgo_crediticio= False
Pipeline local Spark completado.
```

Ejecutar modelado:

```bash
bash scripts/run_model_experiment.sh
```

## 8. Comandos HDFS/Spark tipo clase

Cuando se use el contenedor Hadoop/Spark de clase, el flujo esperado es:

```bash
cd ~/Downloads/proyecto_big_data_riesgo_crediticio
docker compose up -d
docker ps
```

Crear zonas HDFS:

```bash
hdfs dfs -mkdir -p /proyecto_crediticio/raw
hdfs dfs -mkdir -p /proyecto_crediticio/trusted
hdfs dfs -mkdir -p /proyecto_crediticio/analytics
hdfs dfs -mkdir -p /proyecto_crediticio/modelos
hdfs dfs -mkdir -p /proyecto_crediticio/resultados
```

Subir TSV a HDFS:

```bash
hdfs dfs -put -f data/raw/creditos_raw.tsv /proyecto_crediticio/raw/creditos_raw.tsv
hdfs dfs -ls -h /proyecto_crediticio/raw
```

Ejecutar perfilado raw:

```bash
spark-submit src/01_ingest_profile.py \
  --input hdfs:///proyecto_crediticio/raw/creditos_raw.tsv \
  --output hdfs:///proyecto_crediticio/resultados/profiling_raw
```

Construir zona trusted en Parquet:

```bash
spark-submit src/02_clean_to_parquet.py \
  --input hdfs:///proyecto_crediticio/raw/creditos_raw.tsv \
  --output hdfs:///proyecto_crediticio/trusted/obligaciones
```

Validar calidad y señales candidatas del target:

```bash
spark-submit src/03_validate_quality_target.py \
  --input hdfs:///proyecto_crediticio/trusted/obligaciones \
  --output hdfs:///proyecto_crediticio/analytics/target_validation
```

Entrenar modelos MLlib:

```bash
spark-submit src/04_train_compare_models.py \
  --input hdfs:///proyecto_crediticio/trusted/obligaciones \
  --output hdfs:///proyecto_crediticio/resultados/model_experiment \
  --rf-trees 40 \
  --lr-max-iter 30
```

Verificar salidas:

```bash
hdfs dfs -du -h /proyecto_crediticio/resultados
hdfs dfs -du -h /proyecto_crediticio/trusted
hdfs dfs -du -h /proyecto_crediticio/analytics
```

## 9. Perfilado inicial

Resultados principales:

- Registros: 1,006,881.
- Columnas: 32.
- Particiones Spark iniciales: 8.
- Encabezados esperados: correctos.
- Duplicados agregados detectados: 284.

Distribuciones generales:

| Estado | Registros |
|---|---:|
| VIG | 973,350 |
| CAN | 33,531 |

| SubEstado | Registros |
|---|---:|
| VIG | 755,516 |
| CAS | 191,266 |
| VOL | 33,531 |
| MOR | 26,122 |
| CJU | 446 |

| Calificacion | Registros |
|---|---:|
| A1 | 742,368 |
| E | 201,243 |
| A2 | 26,157 |
| B | 13,033 |
| C1 | 8,420 |
| C2 | 7,373 |
| D1 | 4,438 |
| D2 | 3,848 |
| Vacío | 1 |

## 10. Limpieza y zona trusted

La limpieza generó un dataset Parquet particionado por `Anio` y `Mes`:

```text
data/trusted/obligaciones/Anio=2026/Mes=4
```

Resultado:

- Registros trusted: 1,006,881.
- Columnas trusted: 39.
- `riesgo_crediticio`: no definido todavía en esta etapa.

Variables derivadas:

- `fecha_corte`.
- `credito_cerrado`.
- `edad_cliente`.
- `antiguedad_credito_meses`.
- `meses_hasta_vencimiento`.
- `ratio_utilizacion`.
- `ratio_cuota_saldo`.

## 11. Validación de universo activo y target

Regla:

```text
Crédito cerrado: FechaDeCancelacion <= 2026-04-30
Crédito activo: FechaDeCancelacion nula o posterior a 2026-04-30
```

Resultado:

| credito_cerrado | Registros | Porcentaje | Saldo total | Mora total |
|---|---:|---:|---:|---:|
| false | 973,350 | 96.67 % | 3,173,079,995.81 | 30,876,513.15 |
| true | 33,531 | 3.33 % | 0.00 | 0.00 |

Target experimental:

```text
riesgo_crediticio_exp = 1 si NumeroDiasMora >= 30 OR ValorMoraTotal > 0
riesgo_crediticio_exp = 0 en caso contrario
excluir NumeroDiasMora = 999
```

La exclusión de `NumeroDiasMora = 999` se justifica porque aparece 43,530 veces y se comporta como código especial, no necesariamente como 999 días reales de mora.

## 12. Reglas contra data leakage

Variables excluidas del entrenamiento:

- `Estado`.
- `SubEstado`.
- `Calificacion`.
- `NumeroDiasMora`.
- `ValorMoraTotal`.
- `FechaInicioMoraK`.
- `FechaInicioMoraI`.
- `FechaUltimoPagoK`.
- `FechaUltimoPagoI`.
- `FechaDeCancelacion`.
- `NombreCompleto`.
- `Identificacion6`.
- `Identificacion2`.
- `NumeroDeObligacion`.

## 13. Modelado con MLlib

Se entrenaron Regresión Logística y Random Forest con Spark MLlib. Ambos modelos usaron el mismo dataset, el mismo split train/test, la misma variable objetivo experimental y las mismas variables predictoras.

Split:

| Conjunto | Registros |
|---|---:|
| Total modelado | 929,820 |
| Entrenamiento | 650,462 |
| Prueba | 279,358 |

Distribución de clases:

| Clase | Registros | Porcentaje |
|---|---:|---:|
| 0 | 782,476 | 84.15 % |
| 1 | 147,344 | 15.85 % |

## 14. Resultados de modelado

| Modelo | Accuracy | Precision positiva | Recall positivo | F1 positivo | AUC-ROC | AUC-PR |
|---|---:|---:|---:|---:|---:|---:|
| Regresión Logística | 0.9391 | 0.7981 | 0.8259 | 0.8117 | 0.9442 | 0.8822 |
| Random Forest | 0.9752 | 0.9814 | 0.8600 | 0.9167 | 0.9850 | 0.9610 |

Matriz de confusión de Regresión Logística:

| Real | Predicción | Casos |
|---:|---:|---:|
| 0 | 0 | 225,685 |
| 0 | 1 | 9,276 |
| 1 | 0 | 7,731 |
| 1 | 1 | 36,666 |

Matriz de confusión de Random Forest:

| Real | Predicción | Casos |
|---:|---:|---:|
| 0 | 0 | 234,239 |
| 0 | 1 | 722 |
| 1 | 0 | 6,215 |
| 1 | 1 | 38,182 |

## 15. Interpretación

Random Forest obtiene el mejor desempeño general en el escenario experimental. Presenta mayor accuracy, precisión positiva, recall positivo, F1, AUC-ROC y AUC-PR. La ventaja más marcada está en la reducción de falsos positivos y en el aumento del F1 de la clase positiva.

Regresión Logística funciona como línea base interpretable y robusta, pero genera más falsos positivos que Random Forest. Esto sugiere que las relaciones entre variables financieras, características del crédito y señales de riesgo pueden ser no lineales.

## 16. Limitaciones metodológicas

La principal limitación es que el dataset corresponde a una sola fotografía al corte de abril de 2026. Por esta razón, el proyecto debe describirse como clasificación de riesgo crediticio al corte, no como predicción futura a 30, 60 o 90 días.

Además:

- `NumeroDiasMora = 999` debe validarse con negocio.
- `SubEstado = CAS`, `MOR` y `CJU` requieren interpretación documental.
- El orden y significado de `Calificacion` deben confirmarse.
- El target usado en modelado es experimental.

## 17. Conclusión

El proyecto cumple con el ciclo completo de Big Data requerido por la asignatura. Se validó el archivo fuente, se exportó a TSV, se procesó con Spark, se construyó una zona trusted en Parquet, se generaron agregados de calidad y target, se entrenaron dos modelos comparables con MLlib y se documentaron resultados reproducibles.

En el escenario experimental, Random Forest supera a Regresión Logística. Sin embargo, la decisión final de target debe validarse con negocio antes de presentar el modelo como una solución definitiva de clasificación de riesgo.
