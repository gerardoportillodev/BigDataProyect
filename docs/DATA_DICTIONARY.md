# Diccionario preliminar

| Variable | Tipo esperado | Uso |
|---|---|---|
| Anio | entero | partición/descriptivo |
| Mes | entero | partición/descriptivo |
| TipoDeRegistro | cadena | predictor candidato |
| TipoDeSujeto | cadena | predictor candidato |
| NombreCompleto | cadena | excluir, sensible |
| Identificacion6 | cadena | excluir, sensible |
| Identificacion2 | cadena | excluir, sensible |
| FechaDeNacimiento | fecha | derivar edad |
| Sexo | cadena | predictor candidato |
| TipoDeObligacion | cadena | predictor candidato |
| Moneda | cadena | predictor candidato |
| NumeroDeObligacion | cadena | excluir, identificador |
| FechaDeOtorgamiento | fecha | derivar antigüedad |
| FechaDeVencimiento | fecha | derivar meses restantes |
| PeriodoDePago | cadena | predictor candidato |
| Estado | cadena | etiqueta/EDA; excluir del modelo |
| SubEstado | cadena | etiqueta/EDA; excluir del modelo |
| Calificacion | cadena | etiqueta/EDA; excluir del modelo |
| NumeroDiasMora | numérico | etiqueta/EDA; excluir del modelo |
| ValorLimite | decimal | predictor candidato |
| ValorSaldoTotal | decimal | predictor candidato |
| ValorMoraTotal | decimal | etiqueta/EDA; excluir del modelo |
| ValorCuota | decimal | predictor candidato |
| TipoDeDeudor | cadena | predictor candidato |
| Cod_Activo | cadena | predictor candidato |
| FechaInicioMoraK | fecha | excluir del modelo |
| FechaInicioMoraI | fecha | excluir del modelo |
| Destino | cadena | predictor candidato |
| tipo_prestamo | cadena | predictor candidato |
| FechaUltimoPagoK | fecha | excluir del modelo |
| FechaUltimoPagoI | fecha | excluir del modelo |
| FechaDeCancelacion | fecha | filtrar activo/cerrado; excluir |

## Derivadas
- fecha_corte = 2026-04-30.
- edad_cliente.
- antiguedad_credito_meses.
- meses_hasta_vencimiento.
- credito_cerrado.
- ratio_utilizacion.
- ratio_cuota_saldo.
- riesgo_crediticio, pendiente de validación.

## Validaciones
Fechas imposibles, edad fuera de rango, otorgamiento posterior a vencimiento, cancelación anterior a otorgamiento, valores negativos, división por cero, duplicados por obligación/corte, códigos desconocidos y valores especiales como 999 en mora.
