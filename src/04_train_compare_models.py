"""Train and compare MLlib models using a documented experimental target.

The dataset is a single portfolio snapshot. Therefore, outputs represent
classification at the April 2026 cut-off, not future delinquency prediction.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone

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
TARGET_RULE = "NumeroDiasMora >= 30 OR ValorMoraTotal > 0; excludes NumeroDiasMora = 999"


def parse_args():
    parser = argparse.ArgumentParser(description="Train Logistic Regression and Random Forest with MLlib.")
    parser.add_argument("--input", default="hdfs:///proyecto_crediticio/trusted/obligaciones")
    parser.add_argument("--output", default="hdfs:///proyecto_crediticio/resultados/model_experiment")
    parser.add_argument("--models-output", default="hdfs:///proyecto_crediticio/modelos")
    parser.add_argument("--scores-output", default="hdfs:///proyecto_crediticio/resultados/scores")
    parser.add_argument("--test-size", type=float, default=0.30)
    parser.add_argument("--sample-fraction", type=float, default=1.0)
    parser.add_argument("--rf-trees", type=int, default=40)
    parser.add_argument("--rf-max-depth", type=int, default=8)
    parser.add_argument("--lr-max-iter", type=int, default=30)
    parser.add_argument("--run-id", default=None)
    return parser.parse_args()


def main() -> None:
    from pyspark.sql import SparkSession

    args = parse_args()
    run_id = args.run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    spark = (
        SparkSession.builder.appName(f"proyecto-crediticio-modelos-{run_id}")
        .config("spark.sql.shuffle.partitions", "48")
        .getOrCreate()
    )

    trusted = spark.read.parquet(args.input)
    model_df = build_model_frame(trusted)

    if args.sample_fraction < 1.0:
        model_df = model_df.sampleBy(
            LABEL_COLUMN,
            fractions={0: args.sample_fraction, 1: args.sample_fraction},
            seed=SEED,
        )

    train_df, test_df = model_df.randomSplit([1.0 - args.test_size, args.test_size], seed=SEED)
    train_df = add_class_weights(train_df).cache()
    test_df = test_df.cache()

    write_basic_outputs(model_df, train_df, test_df, args.output, run_id, args)
    train_and_evaluate(
        train_df=train_df,
        test_df=test_df,
        output_path=args.output,
        models_output=args.models_output,
        scores_output=args.scores_output,
        run_id=run_id,
        lr_max_iter=args.lr_max_iter,
        rf_trees=args.rf_trees,
        rf_max_depth=args.rf_max_depth,
    )

    train_df.unpersist()
    test_df.unpersist()
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
        numeric = F.col(column).cast("double")
        selected = selected.withColumn(
            column,
            F.when(F.isnan(numeric) | numeric.isNull(), F.lit(None).cast("double")).otherwise(numeric),
        )

    for column in CATEGORICAL_FEATURES:
        selected = selected.withColumn(
            column,
            F.when(F.col(column).isNull() | (F.trim(F.col(column)) == ""), F.lit("__MISSING__"))
            .otherwise(F.trim(F.col(column))),
        )

    hash_inputs = [F.coalesce(F.col(column).cast("string"), F.lit("__NULL__")) for column in PREDICTOR_CANDIDATE_COLUMNS]
    selected = selected.withColumn("record_key", F.sha2(F.concat_ws("||", *hash_inputs), 256))

    return selected.select(["record_key", LABEL_COLUMN, *CATEGORICAL_FEATURES, *NUMERIC_FEATURES])


def add_class_weights(df):
    from pyspark.sql import functions as F

    counts = {int(row[LABEL_COLUMN]): row["count"] for row in df.groupBy(LABEL_COLUMN).count().collect()}
    total = sum(counts.values())
    classes = max(len(counts), 1)
    weights = {label: total / (classes * count) for label, count in counts.items() if count}

    return df.withColumn(
        "class_weight",
        F.when(F.col(LABEL_COLUMN) == 1, F.lit(float(weights.get(1, 1.0))))
        .otherwise(F.lit(float(weights.get(0, 1.0)))),
    )


def shared_preprocessing_stages():
    from pyspark.ml.feature import Imputer, OneHotEncoder, StringIndexer

    indexers = [
        StringIndexer(inputCol=column, outputCol=f"{column}_idx", handleInvalid="keep")
        for column in CATEGORICAL_FEATURES
    ]
    encoder = OneHotEncoder(
        inputCols=[f"{column}_idx" for column in CATEGORICAL_FEATURES],
        outputCols=[f"{column}_ohe" for column in CATEGORICAL_FEATURES],
        handleInvalid="keep",
    )
    imputer = Imputer(
        strategy="median",
        inputCols=NUMERIC_FEATURES,
        outputCols=[f"{column}_imp" for column in NUMERIC_FEATURES],
    )
    return indexers, encoder, imputer


def build_logistic_pipeline(max_iter: int):
    from pyspark.ml import Pipeline
    from pyspark.ml.classification import LogisticRegression
    from pyspark.ml.feature import StandardScaler, VectorAssembler

    indexers, encoder, imputer = shared_preprocessing_stages()
    numeric_assembler = VectorAssembler(
        inputCols=[f"{column}_imp" for column in NUMERIC_FEATURES],
        outputCol="numeric_features_raw",
        handleInvalid="keep",
    )
    scaler = StandardScaler(
        inputCol="numeric_features_raw",
        outputCol="numeric_features_scaled",
        withMean=False,
        withStd=True,
    )
    final_assembler = VectorAssembler(
        inputCols=[f"{column}_ohe" for column in CATEGORICAL_FEATURES] + ["numeric_features_scaled"],
        outputCol="features",
        handleInvalid="keep",
    )
    estimator = LogisticRegression(
        featuresCol="features",
        labelCol=LABEL_COLUMN,
        weightCol="class_weight",
        maxIter=max_iter,
        regParam=0.01,
        elasticNetParam=0.0,
    )
    return Pipeline(stages=[*indexers, encoder, imputer, numeric_assembler, scaler, final_assembler, estimator])


def build_random_forest_pipeline(num_trees: int, max_depth: int):
    from pyspark.ml import Pipeline
    from pyspark.ml.classification import RandomForestClassifier
    from pyspark.ml.feature import VectorAssembler

    indexers, encoder, imputer = shared_preprocessing_stages()
    assembler = VectorAssembler(
        inputCols=[f"{column}_ohe" for column in CATEGORICAL_FEATURES]
        + [f"{column}_imp" for column in NUMERIC_FEATURES],
        outputCol="features",
        handleInvalid="keep",
    )
    estimator = RandomForestClassifier(
        featuresCol="features",
        labelCol=LABEL_COLUMN,
        weightCol="class_weight",
        numTrees=num_trees,
        maxDepth=max_depth,
        seed=SEED,
    )
    return Pipeline(stages=[*indexers, encoder, imputer, assembler, estimator])


def train_and_evaluate(
    train_df,
    test_df,
    output_path: str,
    models_output: str,
    scores_output: str,
    run_id: str,
    lr_max_iter: int,
    rf_trees: int,
    rf_max_depth: int,
) -> None:
    from pyspark.ml.evaluation import BinaryClassificationEvaluator
    from pyspark.ml.functions import vector_to_array
    from pyspark.sql import functions as F

    evaluators = {
        "auc_roc": BinaryClassificationEvaluator(
            labelCol=LABEL_COLUMN, rawPredictionCol="rawPrediction", metricName="areaUnderROC"
        ),
        "auc_pr": BinaryClassificationEvaluator(
            labelCol=LABEL_COLUMN, rawPredictionCol="rawPrediction", metricName="areaUnderPR"
        ),
    }

    pipelines = {
        "logistic_regression": build_logistic_pipeline(lr_max_iter),
        "random_forest": build_random_forest_pipeline(rf_trees, rf_max_depth),
    }

    metrics_rows = []
    confusion_outputs = []
    diagnostics_outputs = []

    for model_name, pipeline in pipelines.items():
        fitted = pipeline.fit(train_df)
        predictions = fitted.transform(test_df).cache()

        confusion = (
            predictions.groupBy(LABEL_COLUMN, "prediction")
            .count()
            .withColumn("model", F.lit(model_name))
            .withColumn("run_id", F.lit(run_id))
            .select("run_id", "model", LABEL_COLUMN, "prediction", "count")
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
                run_id,
                model_name,
                total,
                safe_div(tp + tn, total),
                precision_pos,
                recall_pos,
                f1_pos,
                evaluators["auc_roc"].evaluate(predictions),
                evaluators["auc_pr"].evaluate(predictions),
                tn,
                fp,
                fn,
                tp,
            )
        )

        score_output = (
            predictions.withColumn("probability_array", vector_to_array("probability"))
            .withColumn("risk_probability", F.col("probability_array")[1])
            .withColumn("model", F.lit(model_name))
            .withColumn("run_id", F.lit(run_id))
            .select(
                "run_id",
                "model",
                "record_key",
                F.col(LABEL_COLUMN).alias("actual_label"),
                "prediction",
                "risk_probability",
                *CATEGORICAL_FEATURES,
                *NUMERIC_FEATURES,
            )
        )
        score_output.write.mode("overwrite").parquet(f"{scores_output}/{run_id}/{model_name}")
        fitted.write().overwrite().save(f"{models_output}/{run_id}/{model_name}")

        diagnostics = build_feature_diagnostics(predictions, fitted, model_name, run_id)
        diagnostics_outputs.append(diagnostics)
        predictions.unpersist()

    spark = train_df.sparkSession
    metrics_df = spark.createDataFrame(
        metrics_rows,
        [
            "run_id",
            "model",
            "test_rows",
            "accuracy",
            "precision_positive",
            "recall_positive",
            "f1_positive",
            "auc_roc",
            "auc_pr",
            "tn",
            "fp",
            "fn",
            "tp",
        ],
    )
    write_csv(metrics_df, f"{output_path}/metrics")

    confusion_df = union_all(confusion_outputs)
    write_csv(confusion_df, f"{output_path}/confusion_matrix")

    diagnostics_df = union_all(diagnostics_outputs)
    write_csv(diagnostics_df.orderBy("model", F.desc("absolute_value")), f"{output_path}/feature_diagnostics")


def build_feature_diagnostics(predictions, fitted_pipeline, model_name: str, run_id: str):
    from pyspark.sql import functions as F

    feature_names = feature_names_from_metadata(predictions.schema["features"].metadata)
    model = fitted_pipeline.stages[-1]

    if model_name == "random_forest":
        values = list(model.featureImportances.toArray())
        metric = "importance"
    else:
        values = list(model.coefficients.toArray())
        metric = "coefficient"

    rows = [
        (run_id, model_name, metric, index, feature_names[index] if index < len(feature_names) else f"feature_{index}", float(value))
        for index, value in enumerate(values)
    ]
    df = predictions.sparkSession.createDataFrame(
        rows,
        ["run_id", "model", "metric", "feature_index", "feature_name", "value"],
    )
    return df.withColumn("absolute_value", F.abs(F.col("value")))


def feature_names_from_metadata(metadata: dict) -> list[str]:
    attrs = metadata.get("ml_attr", {}).get("attrs", {})
    indexed = []
    for attr_type in ("binary", "nominal", "numeric"):
        for attr in attrs.get(attr_type, []):
            indexed.append((int(attr["idx"]), attr.get("name", f"feature_{attr['idx']}")))
    return [name for _, name in sorted(indexed)]


def write_basic_outputs(model_df, train_df, test_df, output_path: str, run_id: str, args) -> None:
    from pyspark.sql import functions as F

    model_count = model_df.count()
    label_distribution = (
        model_df.groupBy(LABEL_COLUMN)
        .count()
        .withColumn("pct", F.col("count") / F.lit(model_count))
        .withColumn("run_id", F.lit(run_id))
        .select("run_id", LABEL_COLUMN, "count", "pct")
        .orderBy(LABEL_COLUMN)
    )
    split_summary = model_df.sparkSession.createDataFrame(
        [
            ("run_id", run_id),
            ("total_model_rows", str(model_count)),
            ("train_rows", str(train_df.count())),
            ("test_rows", str(test_df.count())),
            ("seed", str(SEED)),
            ("test_size", str(args.test_size)),
            ("rf_trees", str(args.rf_trees)),
            ("rf_max_depth", str(args.rf_max_depth)),
            ("lr_max_iter", str(args.lr_max_iter)),
            ("excluded_numero_dias_mora_999", "true"),
            ("target_rule", TARGET_RULE),
            ("target_status", "experimental_pending_business_validation"),
            ("scope", "classification_at_cutoff_not_future_prediction"),
        ],
        ["metric", "value"],
    )

    write_csv(label_distribution, f"{output_path}/label_distribution")
    write_csv(split_summary, f"{output_path}/split_summary")


def union_all(dataframes):
    combined = dataframes[0]
    for extra in dataframes[1:]:
        combined = combined.unionByName(extra)
    return combined


def safe_div(numerator: float, denominator: float) -> float:
    return float(numerator / denominator) if denominator else 0.0


def write_csv(df, path: str) -> None:
    df.coalesce(1).write.mode("overwrite").option("header", True).csv(path)


if __name__ == "__main__":
    main()
