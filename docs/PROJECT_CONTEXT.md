# Contexto del proyecto

## Rúbrica
El proyecto debe integrar el ciclo de vida completo de Big Data para resolver un problema empresarial real.

Requisitos: datos reales, volumen masivo, Python/PySpark/MLlib, marco teórico, problema empresarial, justificación de técnicas, origen/calidad/volumen/diccionario, código reproducible, interpretación de resultados, recursos y conclusiones.

Pesos:
- Desarrollo de la solución: 45 %.
- Análisis de resultados: 25 %.
- Introducción, marco teórico y objetivos: 10 %.
- Descripción del problema: 10 %.
- Recursos y conclusiones: 10 %.

## Opción seleccionada
Opción 2: mismo dataset, dos algoritmos comparables.
- Regresión Logística.
- Random Forest.

## Problema
Clasificar obligaciones activas según riesgo crediticio para priorizar gestión preventiva, segmentar cartera y asignar recursos de cobranza.

## Arquitectura
Excel -> TSV/CSV -> HDFS raw -> PySpark -> Parquet trusted -> Spark SQL analytics -> MLlib -> resultados.

## Zonas HDFS
- `/proyecto_crediticio/raw`
- `/proyecto_crediticio/trusted`
- `/proyecto_crediticio/analytics`
- `/proyecto_crediticio/modelos`
- `/proyecto_crediticio/resultados`

## Fases
1. Ingesta y perfilado.
2. Limpieza y trusted.
3. Analítica descriptiva.
4. Validación del target.
5. Modelado y evaluación.
6. Interpretación y documentación.

## Limitación actual
Solo existe una fotografía al corte de abril de 2026. Sin históricos, el alcance inicial es clasificación de riesgo al corte, no predicción futura a 30/60/90 días.
