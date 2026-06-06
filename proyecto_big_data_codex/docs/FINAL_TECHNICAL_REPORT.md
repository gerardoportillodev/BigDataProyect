# Proyecto Big Data: clasificacion de riesgo crediticio con Spark y MLlib

## Proposito

El proyecto desarrolla un flujo completo de Big Data para clasificar obligaciones financieras activas segun su riesgo crediticio al corte de abril de 2026. La solucion integra ingesta, validacion, almacenamiento, procesamiento distribuido, limpieza, generacion de variables, analisis descriptivo, modelado con MLlib, comparacion de algoritmos e interpretacion de resultados.

La opcion seleccionada segun la rubrica es la Opcion 2: utilizar dos tecnicas con proposito similar sobre el mismo dataset para resolver un solo caso de negocio y comparar sus resultados. Los modelos comparados son Regresion Logistica y Random Forest.

## Caso de negocio

Clasificar obligaciones financieras activas segun senales de riesgo crediticio, con el objetivo de priorizar gestion preventiva, segmentar cartera y apoyar la asignacion de recursos de cobranza. El alcance metodologico se define como clasificacion de riesgo crediticio al corte, no como prediccion futura de mora.

## Tecnologias

Python, PySpark, Apache Spark, Spark SQL, Spark MLlib, HDFS, Parquet y Docker con el entorno Hadoop/Spark usado en clase.

## Dataset

Archivo fuente local esperado: `data/raw/ConvertidorEstructura - DATA.xlsm`.

Caracteristicas validadas:

- Hoja: `Sheet1`.
- Filas incluyendo encabezado: 1,006,882.
- Registros reales: 1,006,881.
- Columnas: 32.
- Corte: abril de 2026.

El archivo contiene informacion personal y financiera. No se imprimen registros reales ni identificadores como `NombreCompleto`, `Identificacion6`, `Identificacion2` o `NumeroDeObligacion`.

## Arquitectura

```text
Excel .xlsm -> TSV/CSV -> HDFS raw -> Spark DataFrames -> Perfilado y limpieza distribuida -> Parquet trusted -> Spark SQL analytics -> MLlib -> Resultados y documentacion
```

Zonas HDFS propuestas:

```text
/proyecto_crediticio/raw
/proyecto_crediticio/trusted
/proyecto_crediticio/analytics
/proyecto_crediticio/modelos
/proyecto_crediticio/resultados
```

## Comandos de consola locales

Activar ambiente local Spark:

```bash
cd ~/Downloads/proyecto_big_data_codex
source scripts/use_local_spark.sh
```

Verificar Docker:

```bash
cd ~/Downloads/proyecto_big_data_codex
bash scripts/docker_terminal_check.sh
```

Resultado validado:

```text
Docker:
  Client=29.1.5 Server=29.1.5
Compose:
Docker Compose version v5.0.1
```

Inspeccionar Excel:

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
python src/00_export_xlsm_to_tsv.py --input "data/raw/ConvertidorEstructura - DATA.xlsm" --output "data/raw/creditos_raw.tsv"
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

## Comandos HDFS/Spark tipo clase

```bash
cd ~/Downloads/proyecto_big_data_codex
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

Ejecutar scripts en HDFS:

```bash
spark-submit src/01_ingest_profile.py --input hdfs:///proyecto_crediticio/raw/creditos_raw.tsv --output hdfs:///proyecto_crediticio/resultados/profiling_raw
spark-submit src/02_clean_to_parquet.py --input hdfs:///proyecto_crediticio/raw/creditos_raw.tsv --output hdfs:///proyecto_crediticio/trusted/obligaciones
spark-submit src/03_validate_quality_target.py --input hdfs:///proyecto_crediticio/trusted/obligaciones --output hdfs:///proyecto_crediticio/analytics/target_validation
spark-submit src/04_train_compare_models.py --input hdfs:///proyecto_crediticio/trusted/obligaciones --output hdfs:///proyecto_crediticio/resultados/model_experiment --rf-trees 40 --lr-max-iter 30
```

## Perfilado inicial

- Registros: 1,006,881.
- Columnas: 32.
- Particiones Spark iniciales: 8.
- Encabezados esperados: correctos.
- Duplicados agregados detectados: 284.

Distribuciones generales:

- Estado VIG: 973,350; CAN: 33,531.
- SubEstado VIG: 755,516; CAS: 191,266; VOL: 33,531; MOR: 26,122; CJU: 446.
- Calificacion A1: 742,368; E: 201,243; A2: 26,157; B: 13,033; C1: 8,420; C2: 7,373; D1: 4,438; D2: 3,848; vacio: 1.

## Zona trusted

La limpieza genero un dataset Parquet particionado por `Anio` y `Mes` en `data/trusted/obligaciones/Anio=2026/Mes=4`.

Resultado:

- Registros trusted: 1,006,881.
- Columnas trusted: 39.
- `riesgo_crediticio`: no definido en esta etapa.

Variables derivadas: `fecha_corte`, `credito_cerrado`, `edad_cliente`, `antiguedad_credito_meses`, `meses_hasta_vencimiento`, `ratio_utilizacion` y `ratio_cuota_saldo`.

## Universo activo y target experimental

Regla de activo/cerrado:

```text
Credito cerrado: FechaDeCancelacion <= 2026-04-30
Credito activo: FechaDeCancelacion nula o posterior a 2026-04-30
```

Resultado:

- Activas: 973,350 registros, 96.67 %, saldo total 3,173,079,995.81 y mora total 30,876,513.15.
- Cerradas: 33,531 registros, 3.33 %, saldo total 0.00 y mora total 0.00.

Target experimental:

```text
riesgo_crediticio_exp = 1 si NumeroDiasMora >= 30 OR ValorMoraTotal > 0
riesgo_crediticio_exp = 0 en caso contrario
excluir NumeroDiasMora = 999
```

La exclusion de `NumeroDiasMora = 999` se justifica porque aparece 43,530 veces y se comporta como codigo especial.

## Data leakage

Variables excluidas del entrenamiento: `Estado`, `SubEstado`, `Calificacion`, `NumeroDiasMora`, `ValorMoraTotal`, `FechaInicioMoraK`, `FechaInicioMoraI`, `FechaUltimoPagoK`, `FechaUltimoPagoI`, `FechaDeCancelacion`, `NombreCompleto`, `Identificacion6`, `Identificacion2` y `NumeroDeObligacion`.

## Modelado con MLlib

Se entrenaron Regresion Logistica y Random Forest con Spark MLlib. Ambos modelos usaron el mismo dataset, split, target experimental y variables predictoras.

Split:

- Total modelado: 929,820.
- Entrenamiento: 650,462.
- Prueba: 279,358.

Distribucion de clases:

- Clase 0: 782,476 (84.15 %).
- Clase 1: 147,344 (15.85 %).

## Resultados

| Modelo | Accuracy | Precision + | Recall + | F1 + | AUC-ROC | AUC-PR |
|---|---:|---:|---:|---:|---:|---:|
| Regresion Logistica | 0.9391 | 0.7981 | 0.8259 | 0.8117 | 0.9442 | 0.8822 |
| Random Forest | 0.9752 | 0.9814 | 0.8600 | 0.9167 | 0.9850 | 0.9610 |

Matriz de confusion de Regresion Logistica:

- Real 0, prediccion 0: 225,685.
- Real 0, prediccion 1: 9,276.
- Real 1, prediccion 0: 7,731.
- Real 1, prediccion 1: 36,666.

Matriz de confusion de Random Forest:

- Real 0, prediccion 0: 234,239.
- Real 0, prediccion 1: 722.
- Real 1, prediccion 0: 6,215.
- Real 1, prediccion 1: 38,182.

## Interpretacion

Random Forest obtiene el mejor desempeno general en el escenario experimental. Presenta mayor accuracy, precision positiva, recall positivo, F1, AUC-ROC y AUC-PR. La ventaja mas marcada esta en la reduccion de falsos positivos y en el aumento del F1 de la clase positiva.

Regresion Logistica funciona como linea base interpretable y robusta, pero genera mas falsos positivos que Random Forest. Esto sugiere que las relaciones entre variables financieras, caracteristicas del credito y senales de riesgo pueden ser no lineales.

## Limitaciones

La principal limitacion es que el dataset corresponde a una sola fotografia al corte de abril de 2026. Por esta razon, el proyecto debe describirse como clasificacion de riesgo crediticio al corte, no como prediccion futura a 30, 60 o 90 dias.

Tambien deben validarse con negocio `NumeroDiasMora = 999`, `SubEstado = CAS/MOR/CJU`, el significado de `Calificacion` y la regla final de target.

## Conclusion

El proyecto cumple con el ciclo completo de Big Data requerido por la asignatura. Se valido el archivo fuente, se exporto a TSV, se proceso con Spark, se construyo una zona trusted en Parquet, se generaron agregados de calidad y target, se entrenaron dos modelos comparables con MLlib y se documentaron resultados reproducibles.

En el escenario experimental, Random Forest supera a Regresion Logistica. Sin embargo, la decision final de target debe validarse con negocio antes de presentar el modelo como una solucion definitiva.
