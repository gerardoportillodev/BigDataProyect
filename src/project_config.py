"""Shared project configuration for the credit risk Big Data pipeline."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_XLSM_PATH = PROJECT_ROOT / "data" / "raw" / "ConvertidorEstructura - DATA.xlsm"
RAW_TSV_PATH = PROJECT_ROOT / "data" / "raw" / "creditos_raw.tsv"

CUT_OFF_DATE = "2026-04-30"

EXPECTED_COLUMNS = [
    "Anio",
    "Mes",
    "TipoDeRegistro",
    "TipoDeSujeto",
    "NombreCompleto",
    "Identificacion6",
    "Identificacion2",
    "FechaDeNacimiento",
    "Sexo",
    "TipoDeObligacion",
    "Moneda",
    "NumeroDeObligacion",
    "FechaDeOtorgamiento",
    "FechaDeVencimiento",
    "PeriodoDePago",
    "Estado",
    "SubEstado",
    "Calificacion",
    "NumeroDiasMora",
    "ValorLimite",
    "ValorSaldoTotal",
    "ValorMoraTotal",
    "ValorCuota",
    "TipoDeDeudor",
    "Cod_Activo",
    "FechaInicioMoraK",
    "FechaInicioMoraI",
    "Destino",
    "tipo_prestamo",
    "FechaUltimoPagoK",
    "FechaUltimoPagoI",
    "FechaDeCancelacion",
]

SENSITIVE_COLUMNS = {
    "NombreCompleto",
    "Identificacion6",
    "Identificacion2",
    "NumeroDeObligacion",
}

DATE_COLUMNS = {
    "FechaDeNacimiento",
    "FechaDeOtorgamiento",
    "FechaDeVencimiento",
    "FechaInicioMoraK",
    "FechaInicioMoraI",
    "FechaUltimoPagoK",
    "FechaUltimoPagoI",
    "FechaDeCancelacion",
}

INTEGER_COLUMNS = {"Anio", "Mes", "NumeroDiasMora"}

DECIMAL_COLUMNS = {
    "ValorLimite",
    "ValorSaldoTotal",
    "ValorMoraTotal",
    "ValorCuota",
}

CATEGORICAL_PROFILE_COLUMNS = [
    "TipoDeRegistro",
    "TipoDeSujeto",
    "Sexo",
    "TipoDeObligacion",
    "Moneda",
    "PeriodoDePago",
    "Estado",
    "SubEstado",
    "Calificacion",
    "TipoDeDeudor",
    "Cod_Activo",
    "Destino",
    "tipo_prestamo",
]

LEAKAGE_COLUMNS = {
    "Estado",
    "SubEstado",
    "Calificacion",
    "NumeroDiasMora",
    "ValorMoraTotal",
    "FechaInicioMoraK",
    "FechaInicioMoraI",
    "FechaUltimoPagoK",
    "FechaUltimoPagoI",
    "FechaDeCancelacion",
    *SENSITIVE_COLUMNS,
}

PREDICTOR_CANDIDATE_COLUMNS = [
    "Sexo",
    "TipoDeRegistro",
    "TipoDeSujeto",
    "TipoDeObligacion",
    "Moneda",
    "PeriodoDePago",
    "TipoDeDeudor",
    "Cod_Activo",
    "Destino",
    "tipo_prestamo",
    "ValorLimite",
    "ValorSaldoTotal",
    "ValorCuota",
    "edad_cliente",
    "antiguedad_credito_meses",
    "meses_hasta_vencimiento",
    "ratio_utilizacion",
    "ratio_cuota_saldo",
]


def raw_spark_schema():
    """Return the explicit raw schema, keeping source values as strings."""
    from pyspark.sql.types import StringType, StructField, StructType

    return StructType([StructField(column, StringType(), True) for column in EXPECTED_COLUMNS])
