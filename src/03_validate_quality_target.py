"""Generate safe quality and target-validation analytics from trusted Parquet.

This step does not define the final target. It produces aggregate evidence to
validate the business meaning of mora, Estado, SubEstado and Calificacion.
"""

from __future__ import annotations

import argparse


def parse_args():
    parser = argparse.ArgumentParser(description="Validate data quality and candidate target signals.")
    parser.add_argument("--input", default="data/trusted/obligaciones")
    parser.add_argument("--output", default="data/analytics/target_validation")
    return parser.parse_args()


def main() -> None:
    from pyspark.sql import SparkSession

    args = parse_args()
    spark = (
        SparkSession.builder.appName("proyecto-crediticio-quality-target-validation")
        .config("spark.sql.shuffle.partitions", "48")
        .getOrCreate()
    )

    df = spark.read.parquet(args.input)
    write_validation_outputs(df, args.output)
    spark.stop()


def write_validation_outputs(df, output_path: str) -> None:
    from pyspark.sql import functions as F

    total_rows = df.count()

    active_status = (
        df.groupBy("credito_cerrado")
        .agg(
            F.count("*").alias("registros"),
            F.sum("ValorSaldoTotal").alias("saldo_total"),
            F.sum("ValorMoraTotal").alias("mora_total"),
        )
        .withColumn("pct_registros", F.col("registros") / F.lit(total_rows))
        .orderBy("credito_cerrado")
    )
    write_csv(active_status, f"{output_path}/active_status")

    active = df.where(~F.col("credito_cerrado"))

    for column in ["Estado", "SubEstado", "Calificacion", "NumeroDiasMora"]:
        distribution = active.groupBy(column).count().orderBy(F.desc("count"), F.asc(column))
        write_csv(distribution, f"{output_path}/active_distribution_{column}")

    estado_subestado = (
        active.groupBy("Estado", "SubEstado")
        .agg(
            F.count("*").alias("registros"),
            F.sum("ValorSaldoTotal").alias("saldo_total"),
            F.sum("ValorMoraTotal").alias("mora_total"),
            F.avg("NumeroDiasMora").alias("avg_dias_mora"),
        )
        .orderBy(F.desc("registros"))
    )
    write_csv(estado_subestado, f"{output_path}/active_estado_subestado")

    calificacion_mora = (
        active.groupBy("Calificacion")
        .agg(
            F.count("*").alias("registros"),
            F.avg("NumeroDiasMora").alias("avg_dias_mora"),
            F.expr("percentile_approx(NumeroDiasMora, 0.5)").alias("p50_dias_mora"),
            F.expr("percentile_approx(NumeroDiasMora, 0.95)").alias("p95_dias_mora"),
            F.sum("ValorMoraTotal").alias("mora_total"),
        )
        .orderBy("Calificacion")
    )
    write_csv(calificacion_mora, f"{output_path}/active_calificacion_mora")

    mora_buckets = (
        active.withColumn(
            "bucket_dias_mora",
            F.when(F.col("NumeroDiasMora") == 999, "999_especial")
            .when(F.col("NumeroDiasMora") <= 0, "000")
            .when(F.col("NumeroDiasMora") <= 30, "001_030")
            .when(F.col("NumeroDiasMora") <= 60, "031_060")
            .when(F.col("NumeroDiasMora") <= 90, "061_090")
            .when(F.col("NumeroDiasMora") <= 180, "091_180")
            .otherwise("181_mas"),
        )
        .groupBy("bucket_dias_mora")
        .agg(
            F.count("*").alias("registros"),
            F.sum("ValorSaldoTotal").alias("saldo_total"),
            F.sum("ValorMoraTotal").alias("mora_total"),
        )
        .orderBy("bucket_dias_mora")
    )
    write_csv(mora_buckets, f"{output_path}/active_mora_buckets")

    quality_checks = df.select(
        F.count("*").alias("total_rows"),
        F.sum(F.when(F.col("ValorLimite") < 0, 1).otherwise(0)).alias("valor_limite_negativo"),
        F.sum(F.when(F.col("ValorSaldoTotal") < 0, 1).otherwise(0)).alias("saldo_negativo"),
        F.sum(F.when(F.col("ValorMoraTotal") < 0, 1).otherwise(0)).alias("mora_negativa"),
        F.sum(F.when(F.col("ValorCuota") < 0, 1).otherwise(0)).alias("cuota_negativa"),
        F.sum(F.when(F.col("FechaDeOtorgamiento") > F.col("FechaDeVencimiento"), 1).otherwise(0)).alias(
            "otorgamiento_posterior_vencimiento"
        ),
        F.sum(F.when(F.col("FechaDeCancelacion") < F.col("FechaDeOtorgamiento"), 1).otherwise(0)).alias(
            "cancelacion_anterior_otorgamiento"
        ),
        F.sum(F.when((F.col("edad_cliente") < 18) | (F.col("edad_cliente") > 100), 1).otherwise(0)).alias(
            "edad_fuera_rango_18_100"
        ),
        F.sum(F.when(F.col("NumeroDiasMora") == 999, 1).otherwise(0)).alias("numero_dias_mora_999"),
    )
    write_csv(quality_checks, f"{output_path}/quality_checks")


def write_csv(df, path: str) -> None:
    df.coalesce(1).write.mode("overwrite").option("header", True).csv(path)


if __name__ == "__main__":
    main()
