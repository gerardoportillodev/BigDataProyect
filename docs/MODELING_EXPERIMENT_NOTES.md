# Experimento de modelado MLlib

Este experimento compara Regresión Logística y Random Forest sobre el mismo dataset, split y target experimental.

## Target experimental

Nombre: `riesgo_crediticio_exp`.

Regla usada:

```text
1 si NumeroDiasMora >= 30 OR ValorMoraTotal > 0
0 en caso contrario
excluir registros con NumeroDiasMora = 999
```

La regla queda pendiente de validación de negocio. Se excluyen los `999` porque la fase de validación mostró que son un código especial, no necesariamente 999 días reales de mora.

## Variables predictoras

Categóricas:

- `Sexo`
- `TipoDeRegistro`
- `TipoDeSujeto`
- `TipoDeObligacion`
- `Moneda`
- `PeriodoDePago`
- `TipoDeDeudor`
- `Cod_Activo`
- `Destino`
- `tipo_prestamo`

Numéricas:

- `ValorLimite`
- `ValorSaldoTotal`
- `ValorCuota`
- `edad_cliente`
- `antiguedad_credito_meses`
- `meses_hasta_vencimiento`
- `ratio_utilizacion`
- `ratio_cuota_saldo`

## Variables excluidas por leakage o sensibilidad

No se usan como predictoras:

- `Estado`
- `SubEstado`
- `Calificacion`
- `NumeroDiasMora`
- `ValorMoraTotal`
- Fechas de inicio de mora
- Fechas de último pago
- `FechaDeCancelacion`
- `NombreCompleto`
- `Identificacion6`
- `Identificacion2`
- `NumeroDeObligacion`

## Ejecutar

```bash
cd ~/Downloads/proyecto_big_data_riesgo_crediticio
source scripts/use_local_spark.sh
SPARK_LOCAL_IP=127.0.0.1 python src/04_train_compare_models.py \
  --input data/trusted/obligaciones \
  --output data/results/model_experiment \
  --rf-trees 40 \
  --lr-max-iter 30
```

## Salidas

- `data/results/model_experiment/label_distribution`
- `data/results/model_experiment/split_summary`
- `data/results/model_experiment/metrics`
- `data/results/model_experiment/confusion_matrix`

Las métricas deben interpretarse como resultado de una clasificación al corte, no como predicción futura de mora.
