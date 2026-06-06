# Runbook de ingesta y perfilado Spark

## Ejecución completa con Docker/HDFS/Spark

Para ejecutar el proyecto como flujo Big Data real con HDFS, usar:

```bash
cd ~/Downloads/proyecto_big_data_riesgo_crediticio
bash scripts/run_hdfs_pipeline.sh
```

Este comando construye la imagen Docker, levanta HDFS, carga el TSV en `/proyecto_crediticio/raw` y ejecuta todos los `spark-submit` contra rutas `hdfs:///`.

La interfaz del NameNode queda disponible en `http://localhost:9870`.

Salida HDFS validada:

```text
/proyecto_crediticio/raw/creditos_raw.tsv                 189.0 M
/proyecto_crediticio/trusted/obligaciones                  69.0 M
/proyecto_crediticio/analytics/target_validation           52.9 K
/proyecto_crediticio/resultados/model_experiment             971 B
/proyecto_crediticio/resultados/profiling_raw               1.3 K
```

Este proyecto no imprime registros reales ni identificadores personales. Los comandos generan archivos intermedios dentro de `data/`, que está excluido de Git.

## 1. Validar el archivo Excel

```bash
python3 src/00_inspect_xlsm.py
```

Salida esperada:

- Hoja `Sheet1`.
- 32 columnas.
- Encabezados iguales al diccionario.
- No se imprimen filas reales.

## 2. Exportar Excel a TSV

El archivo `.xlsm` se inspecciona y exporta por streaming desde los XML internos del libro. Esto evita cargar toda la hoja en memoria.

```bash
python3 src/00_export_xlsm_to_tsv.py \
  --input "data/raw/ConvertidorEstructura - DATA.xlsm" \
  --output "data/raw/creditos_raw.tsv"
```

Las columnas de fecha conocidas se normalizan a formato ISO cuando vienen como serial numérico de Excel. El TSV preserva todas las columnas para la zona raw, pero no debe subirse a Git.

## 3. Copiar a HDFS

Dentro del contenedor o entorno Hadoop/Spark de clase:

```bash
hdfs dfs -mkdir -p /proyecto_crediticio/raw
hdfs dfs -mkdir -p /proyecto_crediticio/trusted
hdfs dfs -mkdir -p /proyecto_crediticio/analytics
hdfs dfs -mkdir -p /proyecto_crediticio/modelos
hdfs dfs -mkdir -p /proyecto_crediticio/resultados
hdfs dfs -put -f data/raw/creditos_raw.tsv /proyecto_crediticio/raw/creditos_raw.tsv
hdfs dfs -ls -h /proyecto_crediticio/raw
```

## 4. Ejecutar perfilado raw

```bash
spark-submit src/01_ingest_profile.py \
  --input hdfs:///proyecto_crediticio/raw/creditos_raw.tsv \
  --output hdfs:///proyecto_crediticio/resultados/profiling_raw
```

Este paso calcula:

- Total de registros, columnas y particiones.
- Nulos y porcentajes de nulos.
- Duplicados sin usar columnas sensibles para la llave de comparación.
- Cardinalidad categórica.
- Frecuencias de `Estado`, `SubEstado` y `Calificacion`.

## 5. Construir zona trusted en Parquet

```bash
spark-submit src/02_clean_to_parquet.py \
  --input hdfs:///proyecto_crediticio/raw/creditos_raw.tsv \
  --output hdfs:///proyecto_crediticio/trusted/obligaciones
```

Este paso:

- Convierte enteros, decimales y fechas.
- Crea `fecha_corte = 2026-04-30`.
- Crea `credito_cerrado`.
- Crea variables derivadas: `edad_cliente`, `antiguedad_credito_meses`, `meses_hasta_vencimiento`, `ratio_utilizacion` y `ratio_cuota_saldo`.
- No define todavía `riesgo_crediticio`.

## 6. Validar salidas

```bash
hdfs dfs -du -h /proyecto_crediticio/resultados/profiling_raw
hdfs dfs -du -h /proyecto_crediticio/trusted/obligaciones
```

## Nota metodológica antes de modelar

El modelado usa `riesgo_crediticio_exp` como target experimental. En un escenario productivo, negocio debe validar la interpretación final de `Estado`, `SubEstado`, `Calificacion`, `NumeroDiasMora` y `ValorMoraTotal`.

## 7. Validar calidad y señales candidatas del target

```bash
spark-submit src/03_validate_quality_target.py \
  --input hdfs:///proyecto_crediticio/trusted/obligaciones \
  --output hdfs:///proyecto_crediticio/analytics/target_validation
```

Este paso genera únicamente agregados seguros. No imprime PII y no define todavía `riesgo_crediticio`.

## 8. Entrenar comparación experimental MLlib

```bash
spark-submit src/04_train_compare_models.py \
  --input hdfs:///proyecto_crediticio/trusted/obligaciones \
  --output hdfs:///proyecto_crediticio/resultados/model_experiment \
  --rf-trees 40 \
  --lr-max-iter 30
```

Este paso usa `riesgo_crediticio_exp`, un target experimental documentado y pendiente de validación de negocio.

Resultados validados en la corrida HDFS:

| Modelo | Accuracy | Precision positiva | Recall positivo | F1 positivo | AUC-ROC | AUC-PR |
|---|---:|---:|---:|---:|---:|---:|
| Regresión Logística | 0.9391 | 0.7981 | 0.8259 | 0.8117 | 0.9442 | 0.8822 |
| Random Forest | 0.9740 | 0.9857 | 0.8490 | 0.9122 | 0.9832 | 0.9580 |
