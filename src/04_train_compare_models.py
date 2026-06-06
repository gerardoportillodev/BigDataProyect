"""Train and compare MLlib models using an experimental target definition.

The target created here is not the final business target. It is an explicit
experimental scenario for academic comparison and must remain documented as
pending business validation.
"""

from __future__ import annotations

import argparse

from project_config import PREDICTOR_CANDIDATE_COLUMNS


CATEGORICAL_FEATURES = [
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
]

NUMERIC_FEATURES = [
    "ValorLimite",
    "ValorSaldoTotal",
    "ValorCuota",
    "edad_cliente",
    "antiguedad_credito_meses",
    "meses_hasta_vencimiento",
    "ratio_utilizacion",
    "ratio_cuota_saldo",
]

LABEL_COLUMN = "riesgo_crediticio_exp"
SEED = 20260430


def parse_args():
    parser = argparse.ArgumentParser(description="Train Logistic Regression and Random Forest with MLlib.")
    parser.add_argument("--input", default="data/trusted/obligaciones")
    parser.add_argument("--output", default="data/results/model_experiment")
    parser.add_argument("--test-size", type=float, default=0.30)
    parser.add_argument("--sample-fraction", type=float, default=1.0)
    parser.add_argument("--rf-trees", type=int, default=40)
    parser.add_argument("--lr-max-iter", type=int, default=30)
    return parser.parse_args()


def main() -> None:
    from pyspark.sql import SparkSession

    args = parse_args()
    spark = (
        SparkSession.builder.appName("proyecto-crediticio-train-compare-models")
        .config("spark.sql.shuffle.partitions", "48")
        .getOrCreate()
    )

    trusted = spark.read.parquet(args.input)
    model_df = build_model_frame(trusted)

    if args.sample_fraction < 1.0:
        model_df = model_df.sampleBy(LABEL_COLUMN, fractions={0: args.sample_fraction, 1: args.sample_fraction}, seed=SEED)

    train_df, test_df = model_df.randomSplit([1.0 - args.test_size, args.test_size], seed=SEED)
    train_df = add_class_weights(train_df)
    test_df = add_class_weights(test_df)

    write_basic_outputs(model_df, train_df, test_df, args.output)
    train_and_evaluate(train_df, test_df, args.output, args.lr_max_iter, args.rf_trees)

    spark.stop()


def build_model_frame(df):
    from pyspark.sql import functions as F

    missing = sorted(set(PREDICTOR_CANDIDATE_COLUMNS) - set(df.columns))
    if missing:
        raise ValueError(f"Missing predictor columns: {missing}")

    active = df.where(~F.col("credito_cerrado"))

    target = (
        F.when(F.col("NumeroDiasMora") == 999, None)
        .when((F.col("NumeroDiasMora") >= 30) | (F.col("ValorMoraTotal") > 0), 1)
        .otherwise(0)
    )

    selected = active.withColumn(LABEL_COLUMN, target).where(F.col(LABEL_COLUMN).isNotNull())

    for column in NUMERIC_FEATURES:
        selected = selected.withColumn(column, F.coalesce(F.col(column).cast("double"), F.lit(0.0)))

    for column in CATEGORICAL_FEATURES:
        selected = selected.withColumn(column, F.coalesce(F.col(column), F.lit("__MISSING__")))

    return selected.select([LABEL_COLUMN, *CATEGORICAL_FEATURES, *NUMERIC_FEATURES])


def add_class_weights(df):
    from pyspark.sql import functions as F

    counts = {row[LABEL_COLUMN]: row["count"] for row in df.groupBy(LABEL_COLUMN).count().collect()}
    total = sum(counts.values())
    classes = max(len(counts), 1)
    weights = {label: total / (classes * count) for label, count in counts.items() if count}

    return df.withColumn(
        "class_weight",
        F.when(F.col(LABEL_COLUMN) == 1, F.lit(float(weights.get(1, 1.0)))).otherwise(F.lit(float(weights.get(0, 1.0)))),
    )


def train_and_evaluate(train_df, test_df, output_path: str, lr_max_iter: int, rf_trees: int) -> None:
    from pyspark.ml import Pipeline
    from pyspark.ml.classification import LogisticRegression, RandomForestClassifier
    from pyspark.ml.evaluation import BinaryClassificationEvaluator
    from pyspark.ml.feature import Imputer, OneHotEncoder, StringIndexer, VectorAssembler
    from pyspark.sql import functions as F

    indexers = [
        StringIndexer(inputCol=column, outputCol=f"{column}_idx", handleInvalid="keep")
        for column in CATEGORICAL_FEATURES
    ]
    encoder = OneHotEncoder(
        inputCols=[f"{column}_idx" for column in CATEGORICAL_FEATURES],
        outputCols=[f"{column}_ohe" for column in CATEGORICAL_FEATURES],
        handleInvalid="keep",
    )
    imputer = Imputer(inputCols=NUMERIC_FEATURES, outputCols=[f"{column}_imp" for column in NUMERIC_FEATURES])
    assembler = VectorAssembler(
        inputCols=[f"{column}_ohe" for column in CATEGORICAL_FEATURES] + [f"{column}_imp" for column in NUMERIC_FEATURES],
        outputCol="features",
        handleInvalid="keep",
    )

    models = {
        "logistic_regression": LogisticRegression(
            featuresCol="features",
            labelCol=LABEL_COLUMN,
            weightCol="class_weight",
            maxIter=lr_max_iter,
            regParam=0.01,
            elasticNetParam=0.0,
        ),
        "random_forest": RandomForestClassifier(
            featuresCol="features",
            labelCol=LABEL_COLUMN,
            weightCol="class_weight",
            numTrees=rf_trees,
            maxDepth=8,
            seed=SEED,
        ),
    }

    evaluator_roc = BinaryClassificationEvaluator(
        labelCol=LABEL_COLUMN, rawPredictionCol="rawPrediction", metricName="areaUnderROC"
    )
    evaluator_pr = BinaryClassificationEvaluator(
        labelCol=LABEL_COLUMN, rawPredictionCol="rawPrediction", metricName="areaUnderPR"
    )

    metrics_rows = []
    confusion_outputs = []

    for model_name, estimator in models.items():
        pipeline = Pipeline(stages=[*indexers, encoder, imputer, assembler, estimator])
        fitted = pipeline.fit(train_df)
        predictions = fitted.transform(test_df).select(LABEL_COLUMN, "prediction", "rawPrediction", "probability")

        confusion = (
            predictions.groupBy(LABEL_COLUMN, "prediction")
            .count()
            .withColumn("model", F.lit(model_name))
            .select("model", LABEL_COLUMN, "prediction", "count")
        )
        confusion_outputs.append(confusion)

        counts = {
            (int(row[LABEL_COLUMN]), int(row["prediction"])): row["count"]
            for row in confusion.select(LABEL_COLUMN, "prediction", "count").collect()
        }
        tn = counts.get((0, 0), 0)
        fp = counts.get((0, 1), 0)
        fn = counts.get((1, 0), 0)
        tp = counts.get((1, 1), 0)
        total = tn + fp + fn + tp

        precision_pos = safe_div(tp, tp + fp)
        recall_pos = safe_div(tp, tp + fn)
        f1_pos = safe_div(2 * precision_pos * recall_pos, precision_pos + recall_pos)

        metrics_rows.append(
            (
                model_name,
                total,
                safe_div(tp + tn, total),
                precision_pos,
                recall_pos,
                f1_pos,
                evaluator_roc.evaluate(predictions),
                evaluator_pr.evaluate(predictions),
            )
        )

    spark = train_df.sparkSession
    metrics_df = spark.createDataFrame(
        metrics_rows,
        ["model", "test_rows", "accuracy", "precision_positive", "recall_positive", "f1_positive", "auc_roc", "auc_pr"],
    )
    write_csv(metrics_df, f"{output_path}/metrics")

    confusion_df = confusion_outputs[0]
    for extra in confusion_outputs[1:]:
        confusion_df = confusion_df.unionByName(extra)
    write_csv(confusion_df, f"{output_path}/confusion_matrix")


def write_basic_outputs(model_df, train_df, test_df, output_path: str) -> None:
    from pyspark.sql import functions as F

    label_distribution = (
        model_df.groupBy(LABEL_COLUMN)
        .count()
        .withColumn("pct", F.col("count") / F.lit(model_df.count()))
        .orderBy(LABEL_COLUMN)
    )
    split_summary = model_df.sparkSession.createDataFrame(
        [
            ("total_model_rows", str(model_df.count())),
            ("train_rows", str(train_df.count())),
            ("test_rows", str(test_df.count())),
            ("excluded_numero_dias_mora_999", "true"),
            ("target_rule", "NumeroDiasMora >= 30 OR ValorMoraTotal > 0; excludes NumeroDiasMora = 999"),
            ("target_status", "experimental_pending_business_validation"),
        ],
        ["metric", "value"],
    )

    write_csv(label_distribution, f"{output_path}/label_distribution")
    write_csv(split_summary, f"{output_path}/split_summary")


def safe_div(numerator: float, denominator: float) -> float:
    return float(numerator / denominator) if denominator else 0.0


def write_csv(df, path: str) -> None:
    df.coalesce(1).write.mode("overwrite").option("header", True).csv(path)


if __name__ == "__main__":
    main()
