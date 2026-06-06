# Proyecto Big Data — Riesgo Crediticio

Este repositorio contiene el proyecto final de **Analítica y Tecnologías de Big Data** para clasificar obligaciones financieras activas según riesgo crediticio al corte de abril de 2026.

## Alcance

- Opción de rúbrica: Opción 2.
- Modelos comparados: Regresión Logística y Random Forest.
- Motor principal: Spark, PySpark, Spark SQL y MLlib.
- Formato trusted: Parquet.
- Arquitectura esperada: Excel -> TSV/CSV -> HDFS raw -> Spark -> Parquet trusted -> analytics -> MLlib -> resultados.

## Seguridad

No se suben datos reales, Excel, TSV, CSV, Parquet, PDFs de referencia, ambientes virtuales ni herramientas descargadas. El dataset contiene información personal y debe permanecer fuera de Git.

## Ejecución local

```bash
cd ~/Downloads/proyecto_big_data_codex
source scripts/use_local_spark.sh
bash scripts/run_local_spark_pipeline.sh
bash scripts/run_model_experiment.sh
```

## Documentación principal

- `docs/FINAL_TECHNICAL_REPORT.md`
- `docs/RUNBOOK_INGESTA_SPARK.md`
- `docs/TARGET_VALIDATION_NOTES.md`
- `docs/MODEL_RESULTS_SUMMARY.md`
