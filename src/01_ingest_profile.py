"""Read raw credit data with Spark and write safe profiling outputs."""

from __future__ import annotations

import argparse

from project_config import (
    CATEGORICAL_PROFILE_COLUMNS,
    CUT_OFF_DATE,
    EXPECTED_COLUMNS,
    SENSITIVE_COLUMNS,
    raw_spark_schema,
)


def parse_args():
    parser = argparse.ArgumentParser(description="Profile raw credit data from HDFS/TSV.")
    parser.add_argument("--input", default="hdfs:///proyecto_crediticio/raw/creditos_raw.tsv")
    parser.add_argument("--output", default="hdfs:///proyecto_crediticio/resultados/profiling_raw")
    parser.add_argument("--format", choices=["csv", "parquet"], default="csv")
    return parser.parse_args()


def main() -> None:
    from pyspark.sql import SparkSession
    from pyspark.sql import functions as F

    args = parse_args()
    spark = (
        SparkSession.builder.appName("proyecto-crediticio-ingest-profile")
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

    total_rows = raw.count()
    summary = spark.createDataFrame(
        [
            ("rows", str(total_rows)),
            ("columns", str(len(raw.columns))),
            ("partitions", str(raw.rdd.getNumPartitions())),
            ("expected_columns_match", str(raw.columns == EXPECTED_COLUMNS)),
            ("cut_off_date", CUT_OFF_DATE),
        ],
        ["metric", "value"],
    )

    null_exprs = [
        F.sum(F.when(F.col(column).isNull() | (F.trim(F.col(column)) == ""), 1).otherwise(0)).alias(column)
        for column in raw.columns
    ]
    null_counts = raw.agg(*null_exprs)
    null_profile = null_counts.select(
        F.explode(
            F.array(
                *[
                    F.struct(
                        F.lit(column).alias("column"),
                        F.col(column).cast("long").alias("null_count"),
                        (F.col(column).cast("double") / F.lit(total_rows)).alias("null_pct"),
                    )
                    for column in raw.columns
                ]
            )
        ).alias("profile")
    ).select("profile.*")

    safe_duplicate_columns = [column for column in raw.columns if column not in SENSITIVE_COLUMNS]
    duplicate_count = (
        raw.groupBy(*safe_duplicate_columns)
        .count()
        .where(F.col("count") > 1)
        .agg(F.sum(F.col("count") - 1).alias("duplicate_rows"))
        .fillna(0)
    )

    cardinality = raw.agg(
        *[
            F.approx_count_distinct(F.col(column)).alias(column)
            for column in CATEGORICAL_PROFILE_COLUMNS
            if column in raw.columns
        ]
    ).select(
        F.explode(
            F.array(
                *[
                    F.struct(F.lit(column).alias("column"), F.col(column).cast("long").alias("approx_distinct"))
                    for column in CATEGORICAL_PROFILE_COLUMNS
                    if column in raw.columns
                ]
            )
        ).alias("profile")
    ).select("profile.*")

    write_table(summary, f"{args.output}/summary")
    write_table(null_profile, f"{args.output}/nulls")
    write_table(duplicate_count, f"{args.output}/duplicates")
    write_table(cardinality, f"{args.output}/cardinality")

    for column in ["Estado", "SubEstado", "Calificacion"]:
        if column in raw.columns:
            distribution = raw.groupBy(column).count().orderBy(F.desc("count"))
            write_table(distribution, f"{args.output}/distribution_{column}")

    spark.stop()


def write_table(df, path: str) -> None:
    df.coalesce(1).write.mode("overwrite").option("header", True).csv(path)


if __name__ == "__main__":
    main()
