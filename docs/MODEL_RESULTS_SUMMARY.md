# Resultados del experimento de modelado

Fecha de ejecución: 2026-06-06.

Este experimento compara Regresión Logística y Random Forest con MLlib sobre el mismo dataset, mismo split y mismo target experimental. Los resultados corresponden a una clasificación de riesgo al corte, no a predicción futura.

## Target experimental

`riesgo_crediticio_exp = 1` cuando:

```text
NumeroDiasMora >= 30 OR ValorMoraTotal > 0
```

Se excluyeron registros con `NumeroDiasMora = 999` porque el perfilado mostró que es un código especial pendiente de interpretación de negocio.

## Universo de modelado

| Concepto | Valor |
|---|---:|
| Registros activos elegibles | 929,820 |
| Entrenamiento | 650,462 |
| Prueba | 279,358 |
| Clase 0 | 782,476 |
| Clase 1 | 147,344 |
| Porcentaje clase 1 | 15.85 % |

## Métricas

| Modelo | Accuracy | Precision clase positiva | Recall clase positiva | F1 clase positiva | AUC-ROC | AUC-PR |
|---|---:|---:|---:|---:|---:|---:|
| Regresión Logística | 0.9391 | 0.7981 | 0.8259 | 0.8117 | 0.9442 | 0.8822 |
| Random Forest | 0.9752 | 0.9814 | 0.8600 | 0.9167 | 0.9850 | 0.9610 |

## Matriz de confusión

### Regresión Logística

| Real | Predicción | Casos |
|---:|---:|---:|
| 0 | 0 | 225,685 |
| 0 | 1 | 9,276 |
| 1 | 0 | 7,731 |
| 1 | 1 | 36,666 |

### Random Forest

| Real | Predicción | Casos |
|---:|---:|---:|
| 0 | 0 | 234,239 |
| 0 | 1 | 722 |
| 1 | 0 | 6,215 |
| 1 | 1 | 38,182 |

## Interpretación

Random Forest obtiene el mejor desempeño general en este escenario experimental. Su mayor ventaja está en precisión positiva, F1 positivo, AUC-ROC y AUC-PR. Esto sugiere que captura relaciones no lineales e interacciones entre variables mejor que Regresión Logística.

Regresión Logística sigue siendo útil como línea base por su interpretabilidad, estabilidad y menor complejidad. Sin embargo, bajo esta regla experimental, genera más falsos positivos que Random Forest.

## Cautelas metodológicas

- El target sigue pendiente de validación de negocio.
- La variable `NumeroDiasMora = 999` fue excluida del experimento por posible código especial.
- No se usaron como predictoras las variables empleadas o candidatas para construir el target.
- No se usaron identificadores ni datos personales.
- Los resultados no deben presentarse como predicción futura, porque solo existe una fotografía al corte de abril de 2026.

## Siguiente paso

Antes de cerrar el informe final se recomienda validar con negocio o documentación institucional:

1. Significado de `NumeroDiasMora = 999`.
2. Significado operativo de `SubEstado = CAS`, `MOR` y `CJU`.
3. Orden y semántica de `Calificacion` desde `A1` hasta `E`.
4. Si `ValorMoraTotal > 0` debe tener el mismo peso que `NumeroDiasMora >= 30` en la etiqueta.
