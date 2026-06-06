# AGENTS.md — Proyecto Big Data

## Propósito
Este repositorio contiene el proyecto final de **Analítica y Tecnologías de Big Data**. Debe demostrar el ciclo completo de Big Data y no limitarse a entrenar un modelo.

## Decisión metodológica
- Opción de la rúbrica: **Opción 2**.
- Un mismo dataset masivo y dos técnicas comparables.
- Caso: clasificación del riesgo crediticio de obligaciones activas.
- Modelos: Regresión Logística y Random Forest.
- Fecha de corte: **2026-04-30**.

## Tecnologías
Python, PySpark, Apache Spark, Spark SQL, Spark MLlib, HDFS, Parquet y Docker.
No reemplazar el pipeline principal por pandas o scikit-learn. pandas solo puede utilizarse en muestras pequeñas o visualizaciones finales.

## Arquitectura
1. Fuente Excel `.xlsm`.
2. Exportación a TSV/CSV.
3. Carga en HDFS (`raw`).
4. Lectura con Spark DataFrames.
5. Perfilado y limpieza distribuida.
6. Persistencia en Parquet (`trusted`).
7. Análisis descriptivo (`analytics`).
8. Pipelines de MLlib.
9. Entrenamiento y evaluación.
10. Resultados, modelos y documentación.

## Dataset
Archivo esperado: `data/raw/ConvertidorEstructura - DATA.xlsm`.
- Hoja: `Sheet1`.
- Aproximadamente 1,006,881 registros.
- 32 columnas.

Columnas:
Anio, Mes, TipoDeRegistro, TipoDeSujeto, NombreCompleto, Identificacion6, Identificacion2, FechaDeNacimiento, Sexo, TipoDeObligacion, Moneda, NumeroDeObligacion, FechaDeOtorgamiento, FechaDeVencimiento, PeriodoDePago, Estado, SubEstado, Calificacion, NumeroDiasMora, ValorLimite, ValorSaldoTotal, ValorMoraTotal, ValorCuota, TipoDeDeudor, Cod_Activo, FechaInicioMoraK, FechaInicioMoraI, Destino, tipo_prestamo, FechaUltimoPagoK, FechaUltimoPagoI, FechaDeCancelacion.

## Interpretación conocida
`FechaDeCancelacion` es la fecha en que el crédito cerró o fue liquidado; no representa mora ni castigo.
- Cerrado: fecha de cancelación menor o igual al corte.
- Activo: fecha nula o posterior al corte.
El modelo principal debe usar obligaciones activas.

## Variable objetivo
Nombre tentativo: `riesgo_crediticio`.
- 1: señales de mora o deterioro.
- 0: sin señales de mora o deterioro.

Variables candidatas para construir la etiqueta: NumeroDiasMora, ValorMoraTotal, SubEstado, Calificacion y, solo si la semántica lo justifica, Estado.
No asumir el significado de códigos como CAS, MOR, VIG, A1, B, D1 o E sin validación.
Como solo existe un corte de abril de 2026, describir el alcance inicial como **clasificación de riesgo al corte**, no predicción futura.

## Data leakage
Excluir del entrenamiento:
- Estado, SubEstado, Calificacion, NumeroDiasMora, ValorMoraTotal.
- FechaInicioMoraK, FechaInicioMoraI, FechaUltimoPagoK, FechaUltimoPagoI.
- FechaDeCancelacion.
- NombreCompleto, Identificacion6, Identificacion2, NumeroDeObligacion.

## Predictoras iniciales
Categóricas: Sexo, TipoDeRegistro, TipoDeSujeto, TipoDeObligacion, Moneda, PeriodoDePago, TipoDeDeudor, Cod_Activo, Destino y tipo_prestamo.

Numéricas: ValorLimite, ValorSaldoTotal, ValorCuota, edad_cliente, antiguedad_credito_meses, meses_hasta_vencimiento, ratio_utilizacion y ratio_cuota_saldo.

Derivadas:
- edad_cliente.
- antiguedad_credito_meses.
- meses_hasta_vencimiento.
- ratio_utilizacion = ValorSaldoTotal / ValorLimite.
- ratio_cuota_saldo = ValorCuota / ValorSaldoTotal.

Aplicar controles para divisiones por cero, valores negativos, fechas imposibles e infinitos.

## Perfilado requerido
- Total de registros, columnas y particiones.
- Esquema.
- Nulos y porcentaje de nulos.
- Duplicados.
- Cardinalidad categórica.
- Distribuciones de Estado, SubEstado y Calificacion.
- Activos vs cerrados.
- Saldo y mora total.
- Riesgo por segmentos.
- Distribuciones de días en mora y ratio de utilización.

Usar Spark DataFrames o Spark SQL.

## MLlib
Usar Pipelines con StringIndexer, OneHotEncoder, VectorAssembler, LogisticRegression y RandomForestClassifier. StandardScaler solo cuando sea pertinente.
Ambos modelos deben usar exactamente el mismo split de entrenamiento y prueba.

## Evaluación
Reportar accuracy, precision de clase positiva, recall de clase positiva, F1, AUC-ROC, AUC-PR, matriz de confusión, distribución de clases y, si es viable, tiempo de entrenamiento.
No depender solo de métricas ponderadas.

## Calidad académica
- Código reproducible, limpio y comentado.
- No inventar resultados ni significados.
- Justificar decisiones técnicas y de negocio.
- Documentar origen, volumen, calidad y diccionario.
- Incluir evidencia de HDFS, Spark, particiones, planes de ejecución y MLlib.

## Protección de datos
- No subir `data/raw/` a GitHub.
- No imprimir PII en logs.
- No incluir registros reales en tests o documentación.
- Usar muestras anonimizadas.
- No enviar el archivo completo a servicios externos sin autorización.

## Forma de trabajo de Codex
Antes de modificar código:
1. Leer este archivo.
2. Leer `docs/PROJECT_CONTEXT.md` y `docs/DATA_DICTIONARY.md`.
3. Inspeccionar el repositorio.
4. Proponer un plan breve.
5. Trabajar por fases pequeñas.
6. Ejecutar validaciones.
7. Explicar lo hecho y lo pendiente.

No cambiar la definición del target sin señalarlo. No entrenar modelos antes de completar perfilado, calidad y validación del universo activo.
