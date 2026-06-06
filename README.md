# BigDataProyect - Clasificación de Riesgo Crediticio con Spark y MLlib

Proyecto final de **Analítica y Tecnologías de Big Data** orientado a construir un flujo completo de Big Data para clasificar obligaciones financieras activas según riesgo crediticio al corte de abril de 2026.

La solución compara dos técnicas de clasificación sobre el mismo dataset:

- Regresión Logística.
- Random Forest.

El enfoque corresponde a la **Opción 2 de la rúbrica**: dos técnicas con propósito similar aplicadas a un mismo dataset para resolver un solo caso de negocio y comparar resultados.

## Caso de negocio

Clasificar obligaciones financieras activas según señales de riesgo crediticio para apoyar:

- priorización de gestión preventiva,
- segmentación de cartera,
- asignación de recursos de cobranza,
- análisis de deterioro crediticio al corte.

El dataset disponible es una fotografía de cartera al corte de abril de 2026. Por esta razón, el alcance metodológico se presenta como **clasificación de riesgo crediticio al corte**, no como predicción futura de mora.

## Tecnologías utilizadas

- Python
- PySpark
- Apache Spark
- Spark SQL
- Spark MLlib
- HDFS
- Parquet
- Docker

El procesamiento principal se realiza con Spark DataFrames, Spark SQL y MLlib. No se reemplaza el pipeline principal con pandas ni scikit-learn.

## Arquitectura del proyecto

```text
Excel .xlsm
  -> TSV/CSV
  -> HDFS raw
  -> Spark DataFrames
  -> Perfilado y limpieza distribuida
  -> Parquet trusted
  -> Spark SQL analytics
  -> MLlib
  -> Resultados y documentación
```

Zonas propuestas en HDFS:

```text
/proyecto_crediticio/raw
/proyecto_crediticio/trusted
/proyecto_crediticio/analytics
/proyecto_crediticio/modelos
/proyecto_crediticio/resultados
```

## Estructura del repositorio

```text
.
├── docs/
│   ├── DATA_DICTIONARY.md
│   ├── FINAL_TECHNICAL_REPORT.md
│   ├── MODELING_EXPERIMENT_NOTES.md
│   ├── MODEL_RESULTS_SUMMARY.md
│   ├── PROJECT_CONTEXT.md
│   ├── RUNBOOK_INGESTA_SPARK.md
│   ├── SETUP_LOCAL.md
│   └── TARGET_VALIDATION_NOTES.md
├── scripts/
│   ├── docker_terminal_check.sh
│   ├── run_local_spark_pipeline.sh
│   ├── run_model_experiment.sh
│   └── use_local_spark.sh
├── src/
│   ├── 00_inspect_xlsm.py
│   ├── 00_export_xlsm_to_tsv.py
│   ├── 01_ingest_profile.py
│   ├── 02_clean_to_parquet.py
│   ├── 03_validate_quality_target.py
│   ├── 04_train_compare_models.py
│   ├── project_config.py
│   └── xlsm_utils.py
├── tests/
│   ├── test_clean_to_parquet.py
│   └── test_xlsm_utils.py
├── .gitignore
├── README.md
└── requirements.txt
```

## Datos requeridos

El archivo real de datos debe colocarse localmente en:

```text
data/raw/ConvertidorEstructura - DATA.xlsm
```

Ese archivo no se incluye en GitHub porque contiene información sensible. También se excluyen archivos `.xlsm`, `.xlsx`, `.csv`, `.tsv`, `.parquet` y toda la carpeta `data/`.

## Protección de datos

El dataset contiene información personal. No se imprimen ni se suben a GitHub las siguientes columnas:

- `NombreCompleto`
- `Identificacion6`
- `Identificacion2`
- `NumeroDeObligacion`

Las pruebas usan datos sintéticos anonimizados.

## Instalación local

Desde la raíz del proyecto:

```bash
cd ~/Downloads/proyecto_big_data_codex
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

El proyecto usa Java 17 para Spark. En el ambiente local se configuró mediante:

```bash
source scripts/use_local_spark.sh
```

Validar ambiente:

```bash
python --version
python -c "import pyspark; print(pyspark.__version__)"
python -m pytest -q
```

Resultado validado:

```text
2 passed
```

## Ejecución paso a paso en consola

### 1. Verificar Docker

```bash
cd ~/Downloads/proyecto_big_data_codex
bash scripts/docker_terminal_check.sh
```

Resultado obtenido:

```text
Docker:
  Client=29.1.5 Server=29.1.5
Contenedores activos:
CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES
Compose:
Docker Compose version v5.0.1
```

### 2. Activar ambiente Spark local

```bash
cd ~/Downloads/proyecto_big_data_codex
source scripts/use_local_spark.sh
```

### 3. Inspeccionar el Excel sin cargar toda la hoja

```bash
python src/00_inspect_xlsm.py
```

Resultado obtenido:

```text
Hojas: ['Sheet1']
Dimension: A1:AF1006882
Filas incluyendo encabezado: 1006882
Columnas: 32
Encabezados coinciden: True
```

### 4. Exportar Excel a TSV

```bash
python src/00_export_xlsm_to_tsv.py \
  --input "data/raw/ConvertidorEstructura - DATA.xlsm" \
  --output "data/raw/creditos_raw.tsv"
```

Resultado obtenido:

```text
TSV generado: data/raw/creditos_raw.tsv
Filas escritas incluyendo encabezado: 1006882
```

### 5. Ejecutar perfilado con Spark

```bash
python src/01_ingest_profile.py \
  --input data/raw/creditos_raw.tsv \
  --output data/results/profiling_raw
```

Este paso genera métricas de registros, columnas, particiones, nulos, duplicados, cardinalidad categórica y distribución de `Estado`, `SubEstado` y `Calificacion`.

### 6. Construir zona trusted en Parquet

```bash
python src/02_clean_to_parquet.py \
  --input data/raw/creditos_raw.tsv \
  --output data/trusted/obligaciones
```

Resultado validado:

```text
trusted_rows= 1006881
trusted_columns= 39
has_riesgo_crediticio= False
```

Variables derivadas creadas:

- `fecha_corte`
- `credito_cerrado`
- `edad_cliente`
- `antiguedad_credito_meses`
- `meses_hasta_vencimiento`
- `ratio_utilizacion`
- `ratio_cuota_saldo`

### 7. Validar calidad y señales candidatas del target

```bash
python src/03_validate_quality_target.py \
  --input data/trusted/obligaciones \
  --output data/analytics/target_validation
```

Este paso genera agregados seguros para analizar activos vs cerrados, distribución de mora, relación entre calificación y mora, valores especiales como `NumeroDiasMora = 999` y controles de calidad.

### 8. Ejecutar pipeline local completo

```bash
bash scripts/run_local_spark_pipeline.sh
```

Resultado obtenido:

```text
trusted_rows= 1006881
trusted_columns= 39
has_riesgo_crediticio= False
Pipeline local Spark completado.
```

### 9. Entrenar y comparar modelos MLlib

```bash
bash scripts/run_model_experiment.sh
```

Comando equivalente:

```bash
SPARK_LOCAL_IP=127.0.0.1 python src/04_train_compare_models.py \
  --input data/trusted/obligaciones \
  --output data/results/model_experiment \
  --rf-trees 40 \
  --lr-max-iter 30
```

## Ejecución en HDFS/Spark tipo clase

Cuando se use el contenedor Hadoop/Spark de clase, el flujo esperado es:

```bash
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

Subir archivo raw:

```bash
hdfs dfs -put -f data/raw/creditos_raw.tsv /proyecto_crediticio/raw/creditos_raw.tsv
hdfs dfs -ls -h /proyecto_crediticio/raw
```

Ejecutar scripts con `spark-submit`:

```bash
spark-submit src/01_ingest_profile.py \
  --input hdfs:///proyecto_crediticio/raw/creditos_raw.tsv \
  --output hdfs:///proyecto_crediticio/resultados/profiling_raw

spark-submit src/02_clean_to_parquet.py \
  --input hdfs:///proyecto_crediticio/raw/creditos_raw.tsv \
  --output hdfs:///proyecto_crediticio/trusted/obligaciones

spark-submit src/03_validate_quality_target.py \
  --input hdfs:///proyecto_crediticio/trusted/obligaciones \
  --output hdfs:///proyecto_crediticio/analytics/target_validation

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

## Resultados obtenidos

### Perfilado inicial

- Registros procesados: 1,006,881.
- Columnas: 32.
- Particiones Spark iniciales: 8.
- Duplicados agregados detectados: 284.
- `Estado`: `VIG` 973,350; `CAN` 33,531.
- `SubEstado`: `VIG` 755,516; `CAS` 191,266; `VOL` 33,531; `MOR` 26,122; `CJU` 446.
- `Calificacion`: `A1` 742,368; `E` 201,243; `A2` 26,157; `B` 13,033; `C1` 8,420; `C2` 7,373; `D1` 4,438; `D2` 3,848.

### Universo activo

Regla utilizada:

```text
Credito cerrado: FechaDeCancelacion <= 2026-04-30
Credito activo: FechaDeCancelacion nula o posterior a 2026-04-30
```

Resultado:

- Obligaciones activas: 973,350.
- Obligaciones cerradas: 33,531.
- Saldo total en activas: 3,173,079,995.81.
- Mora total en activas: 30,876,513.15.

### Target experimental

Se creó `riesgo_crediticio_exp` como target experimental:

```text
1 si NumeroDiasMora >= 30 OR ValorMoraTotal > 0
0 en caso contrario
excluyendo NumeroDiasMora = 999
```

`NumeroDiasMora = 999` aparece 43,530 veces y se trató como código especial pendiente de validación de negocio.

### Dataset de modelado

- Total modelado: 929,820 registros.
- Entrenamiento: 650,462 registros.
- Prueba: 279,358 registros.
- Clase 0: 782,476 registros (84.15 %).
- Clase 1: 147,344 registros (15.85 %).

### Comparación de modelos

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

## Interpretación

Random Forest obtuvo el mejor desempeño general en el escenario experimental. Presentó mayor accuracy, precisión positiva, recall positivo, F1, AUC-ROC y AUC-PR. La principal ventaja fue la reducción de falsos positivos y el aumento del F1 de la clase positiva.

Regresión Logística funciona como línea base interpretable y robusta, pero generó más falsos positivos que Random Forest. Esto sugiere que las relaciones entre variables financieras, características del crédito y señales de riesgo pueden ser no lineales.

## Limitaciones

- El dataset representa una sola fotografía al corte de abril de 2026.
- El resultado debe interpretarse como clasificación al corte, no predicción futura.
- `NumeroDiasMora = 999` requiere validación de negocio.
- `SubEstado = CAS`, `MOR` y `CJU` requieren interpretación documental.
- La semántica completa de `Calificacion` debe confirmarse.
- El target usado en modelado es experimental.

## Documentación adicional

- `docs/FINAL_TECHNICAL_REPORT.md`: reporte técnico consolidado.
- `docs/RUNBOOK_INGESTA_SPARK.md`: comandos de ingesta, HDFS y Spark.
- `docs/TARGET_VALIDATION_NOTES.md`: evidencia para validación del target.
- `docs/MODEL_RESULTS_SUMMARY.md`: resumen de resultados de modelos.
- `docs/DATA_DICTIONARY.md`: diccionario preliminar de datos.

## Estado final

El proyecto deja implementado y documentado el ciclo completo de Big Data: inspección segura del Excel, exportación a TSV, procesamiento con Spark, construcción de Parquet trusted, validación de target, entrenamiento MLlib, evaluación comparativa y documentación reproducible.
