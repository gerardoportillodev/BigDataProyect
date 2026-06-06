"""Clean raw credit data and write the trusted Parquet zone without defining target."""

from __future__ import annotations

import argparse

from project_config import CUT_OFF_DATE, DATE_COLUMNS, DECIMAL_COLUMNS, INTEGER_COLUMNS, raw_spark_schema


def parse_args():
    parser = argparse.ArgumentParser(description="Build trusted Parquet data from raw TSV.")
    parser.add_argument("--input", default="hdfs:///proyecto_crediticio/raw/creditos_raw.tsv")
    parser.add_argument("--output", default="hdfs:///proyecto_crediticio/trusted/obligaciones")
    return parser.parse_args()


def main() -> None:
    from pyspark.sql import SparkSession

    args = parse_args()
    spark = (
        SparkSession.builder.appName("proyecto-crediticio-clean-to-parquet")
        .config("spark.sql.shuffle.partitions", "48")
        .getOrCreate()
    )

    raw = (
        spark.read.option("header", True)
        .option("delimiter", "\t")
        .option("encoding", "UTF-8")
        .schema(raw_spark_schema())
        .csv(args.input)
    )

    trusted = build_trusted_frame(raw)

    (
        trusted.write.mode("overwrite")
        .partitionBy("Anio", "Mes")
        .parquet(args.output)
    )

    spark.stop()


def build_trusted_frame(df):
    from pyspark.sql import functions as F

    cleaned = df
    for column in df.columns:
        cleaned = cleaned.withColumn(column, F.trim(F.col(column)))

    for column in INTEGER_COLUMNS:
        cleaned = cleaned.withColumn(column, F.col(column).cast("int"))

    for column in DECIMAL_COLUMNS:
        cleaned = cleaned.withColumn(column, F.regexp_replace(F.col(column), ",", "").cast("double"))

    for column in DATE_COLUMNS:
        cleaned = cleaned.withColumn(
            column,
            F.coalesce(
                F.to_date(F.col(column), "yyyy-MM-dd"),
                F.to_date(F.col(column), "dd/MM/yyyy"),
                F.to_date(F.col(column), "MM/dd/yyyy"),
            ),
        )

    fecha_corte = F.to_date(F.lit(CUT_OFF_DATE))
    cleaned = (
        cleaned.withColumn("fecha_corte", fecha_corte)
        .withColumn(
            "credito_cerrado",
            F.when(F.col("FechaDeCancelacion").isNotNull() & (F.col("FechaDeCancelacion") <= fecha_corte), F.lit(True))
            .otherwise(F.lit(False)),
        )
        .withColumn("edad_cliente", F.floor(F.months_between(fecha_corte, F.col("FechaDeNacimiento")) / F.lit(12)))
        .withColumn("antiguedad_credito_meses", F.floor(F.months_between(fecha_corte, F.col("FechaDeOtorgamiento"))))
        .withColumn("meses_hasta_vencimiento", F.floor(F.months_between(F.col("FechaDeVencimiento"), fecha_corte)))
        .withColumn(
            "ratio_utilizacion",
            F.when(F.col("ValorLimite") > 0, F.col("ValorSaldoTotal") / F.col("ValorLimite")),
        )
        .withColumn(
            "ratio_cuota_saldo",
            F.when(F.col("ValorSaldoTotal") > 0, F.col("ValorCuota") / F.col("ValorSaldoTotal")),
        )
    )

    return cleaned


if __name__ == "__main__":
    main()
