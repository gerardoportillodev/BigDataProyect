from pathlib import Path
import importlib.util
import sys

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from project_config import EXPECTED_COLUMNS, raw_spark_schema


MODULE_PATH = Path(__file__).resolve().parents[1] / "src" / "02_clean_to_parquet.py"
SPEC = importlib.util.spec_from_file_location("clean_to_parquet", MODULE_PATH)
clean_to_parquet = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(clean_to_parquet)


pyspark = pytest.importorskip("pyspark")


def test_build_trusted_frame_uses_synthetic_data_only():
    from pyspark.sql import SparkSession

    spark = SparkSession.builder.master("local[1]").appName("test-clean-to-parquet").getOrCreate()
    try:
        synthetic = {
            "Anio": "2026",
            "Mes": "4",
            "TipoDeRegistro": "T",
            "TipoDeSujeto": "N",
            "NombreCompleto": "PERSONA SINTETICA",
            "Identificacion6": "SYN001",
            "Identificacion2": "S1",
            "FechaDeNacimiento": "1990-01-01",
            "Sexo": "F",
            "TipoDeObligacion": "CONSUMO",
            "Moneda": "USD",
            "NumeroDeObligacion": "OBL-SYN-1",
            "FechaDeOtorgamiento": "2025-04-30",
            "FechaDeVencimiento": "2027-04-30",
            "PeriodoDePago": "M",
            "Estado": "CODIGO_SINTETICO",
            "SubEstado": "SUB_SINTETICO",
            "Calificacion": "A",
            "NumeroDiasMora": "0",
            "ValorLimite": "1000",
            "ValorSaldoTotal": "250",
            "ValorMoraTotal": "0",
            "ValorCuota": "50",
            "TipoDeDeudor": "PRINCIPAL",
            "Cod_Activo": "ACT",
            "FechaInicioMoraK": None,
            "FechaInicioMoraI": None,
            "Destino": "USO_SINTETICO",
            "tipo_prestamo": "TIPO_SINTETICO",
            "FechaUltimoPagoK": "2026-04-01",
            "FechaUltimoPagoI": "2026-04-01",
            "FechaDeCancelacion": None,
        }
        input_df = spark.createDataFrame(
            [tuple(synthetic[column] for column in EXPECTED_COLUMNS)],
            schema=raw_spark_schema(),
        )

        trusted = clean_to_parquet.build_trusted_frame(input_df)
        row = trusted.select(
            "credito_cerrado",
            "edad_cliente",
            "antiguedad_credito_meses",
            "meses_hasta_vencimiento",
            "ratio_utilizacion",
            "ratio_cuota_saldo",
        ).first()

        assert row.credito_cerrado is False
        assert row.edad_cliente == 36
        assert row.antiguedad_credito_meses == 12
        assert row.meses_hasta_vencimiento == 12
        assert row.ratio_utilizacion == 0.25
        assert row.ratio_cuota_saldo == 0.2
    finally:
        spark.stop()
