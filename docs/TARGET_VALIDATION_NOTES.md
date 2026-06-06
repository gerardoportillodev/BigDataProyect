# Evidencia para validación del target

Fecha de corte: `2026-04-30`.

Este documento resume agregados generados por `src/03_validate_quality_target.py`. No contiene datos personales ni registros individuales.

## Universo activo

| credito_cerrado | registros | porcentaje | saldo_total | mora_total |
|---|---:|---:|---:|---:|
| false | 973,350 | 96.67 % | 3,173,079,995.81 | 30,876,513.15 |
| true | 33,531 | 3.33 % | 0.00 | 0.00 |

La regla de activo/cerrado es consistente con el perfilado inicial: las obligaciones activas quedan como `FechaDeCancelacion` nula o posterior al corte, y las cerradas no aportan saldo ni mora.

## Distribuciones en obligaciones activas

### Estado

| Estado | registros |
|---|---:|
| VIG | 973,350 |

En el universo activo, `Estado` queda constante en `VIG`. Por sí sola no sirve como predictor ni como etiqueta para el modelo activo.

### SubEstado

| SubEstado | registros |
|---|---:|
| VIG | 755,516 |
| CAS | 191,266 |
| MOR | 26,122 |
| CJU | 446 |

`SubEstado` muestra señales potenciales de comportamiento, pero su significado debe validarse con negocio antes de usarlo para construir `riesgo_crediticio`.

### Calificacion

| Calificacion | registros |
|---|---:|
| A1 | 710,275 |
| E | 200,726 |
| A2 | 25,899 |
| B | 12,905 |
| C1 | 8,388 |
| C2 | 7,000 |
| D1 | 4,371 |
| D2 | 3,785 |
| vacío | 1 |

`Calificacion` tiene una distribución ordenable aparente, pero no debe asumirse su semántica sin validación documental o de negocio.

## Días de mora en activas

| Bucket | registros | saldo_total | mora_total |
|---|---:|---:|---:|
| 000 | 759,432 | 2,486,205,278.97 | 0.00 |
| 001_030 | 24,254 | 140,784,364.29 | 3,153.44 |
| 031_060 | 7,981 | 27,147,014.21 | 681,504.00 |
| 061_090 | 7,121 | 23,008,309.47 | 1,819,211.72 |
| 091_180 | 10,995 | 29,972,714.10 | 27,493,443.77 |
| 181_mas | 120,037 | 414,711,090.27 | 817,892.45 |
| 999_especial | 43,530 | 51,251,224.50 | 61,307.77 |

El valor `999` aparece 43,530 veces. Debe tratarse como código especial pendiente de interpretación, no como 999 días reales de mora.

## Relación entre Calificacion y mora

| Calificacion | registros | promedio_dias_mora | p50 | p95 | mora_total |
|---|---:|---:|---:|---:|---:|
| A1 | 710,275 | 3.20 | 0 | 0 | 301,352.82 |
| A2 | 25,899 | 7.01 | 0 | 28 | 0.00 |
| B | 12,905 | 24.43 | 27 | 57 | 5,587.95 |
| C1 | 8,388 | 50.00 | 61 | 89 | 385,837.71 |
| C2 | 7,000 | 54.69 | 71 | 118 | 8,337,826.38 |
| D1 | 4,371 | 83.48 | 111 | 147 | 8,006,087.10 |
| D2 | 3,785 | 117.91 | 151 | 177 | 7,242,133.61 |
| E | 200,726 | 1,384.89 | 999 | 4,971 | 6,597,687.58 |

`Calificacion=E` está fuertemente asociada con valores especiales/extremos de `NumeroDiasMora`. Esta relación debe explicarse antes de definir la etiqueta.

## Calidad

| Check | resultado |
|---|---:|
| valor_limite_negativo | 0 |
| saldo_negativo | 0 |
| mora_negativa | 0 |
| cuota_negativa | 0 |
| otorgamiento_posterior_vencimiento | 0 |
| cancelacion_anterior_otorgamiento | 0 |
| edad_fuera_rango_18_100 | 5 |
| numero_dias_mora_999 | 43,530 |

## Recomendación metodológica

No definir todavía el target final.

Opciones candidatas para validación de negocio:

1. Target basado en mora contable: `NumeroDiasMora > 0` o `ValorMoraTotal > 0`, excluyendo o tratando por separado `NumeroDiasMora = 999`.
2. Target basado en umbral de mora: `NumeroDiasMora >= 30`, con regla explícita para `999`.
3. Target combinado: mora positiva, subestado de deterioro validado y calificación de riesgo validada.

Cuando se elija una regla, las variables usadas para construir `riesgo_crediticio` deben excluirse del set de predictores para evitar data leakage.
