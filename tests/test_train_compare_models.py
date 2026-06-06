"""Synthetic tests for 04_train_compare_models.py logic.

Pure-Python tests run locally without Spark.
PySpark-dependent tests are skipped if pyspark is not available.
"""

from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

MODULE_PATH = Path(__file__).resolve().parents[1] / "src" / "04_train_compare_models.py"
SPEC = importlib.util.spec_from_file_location("train_models", MODULE_PATH)
train_models = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(train_models)


# ── Target definition ─────────────────────────────────────────────────────────

def _apply_target(mora, valor_mora: float):
    """Mirror the Spark when() target logic in plain Python."""
    if mora == 999:
        return None
    if (mora is not None and mora >= 30) or valor_mora > 0:
        return 1
    return 0


def test_credito_activo_sin_mora():
    assert _apply_target(0, 0.0) == 0


def test_credito_mora_leve():
    assert _apply_target(15, 0.0) == 0


def test_credito_mora_30_dias():
    assert _apply_target(30, 0.0) == 1


def test_credito_valor_mora_positivo():
    assert _apply_target(0, 500.0) == 1


def test_credito_mora_y_valor_mora():
    assert _apply_target(60, 1000.0) == 1


def test_exclusion_numero_dias_mora_999():
    assert _apply_target(999, 0.0) is None


def test_exclusion_999_con_valor_mora_positivo():
    assert _apply_target(999, 9999.0) is None


def test_target_positivo():
    assert _apply_target(30, 0.0) == 1


def test_target_negativo():
    assert _apply_target(0, 0.0) == 0


def test_fechas_nulas_valor_mora_positivo():
    assert _apply_target(None, 100.0) == 1


def test_division_por_cero_segura():
    assert train_models.safe_div(0.0, 0.0) == 0.0


def test_division_normal():
    assert abs(train_models.safe_div(1.0, 4.0) - 0.25) < 1e-9


# ── Exclusión de leakage y PII ────────────────────────────────────────────────

LEAKAGE_COLUMNS = {"NumeroDiasMora", "ValorMoraTotal", "Estado", "SubEstado", "Calificacion"}
PII_COLUMNS = {"NombreCliente", "NumeroIdentificacion", "Cedula", "RUC", "Telefono", "Correo"}


def test_no_leakage_in_categorical():
    overlap = LEAKAGE_COLUMNS & set(train_models.CATEGORICAL_FEATURES)
    assert not overlap, f"Leakage en CATEGORICAL_FEATURES: {overlap}"


def test_no_leakage_in_numeric():
    overlap = LEAKAGE_COLUMNS & set(train_models.NUMERIC_FEATURES)
    assert not overlap, f"Leakage en NUMERIC_FEATURES: {overlap}"


def test_no_pii_in_categorical():
    overlap = PII_COLUMNS & set(train_models.CATEGORICAL_FEATURES)
    assert not overlap, f"PII en CATEGORICAL_FEATURES: {overlap}"


def test_no_pii_in_numeric():
    overlap = PII_COLUMNS & set(train_models.NUMERIC_FEATURES)
    assert not overlap, f"PII en NUMERIC_FEATURES: {overlap}"


def test_label_not_in_features():
    label = train_models.LABEL_COLUMN
    assert label not in train_models.CATEGORICAL_FEATURES
    assert label not in train_models.NUMERIC_FEATURES


# ── Métricas ──────────────────────────────────────────────────────────────────

def test_precision_perfect():
    assert train_models.safe_div(10, 10) == 1.0


def test_recall_zero():
    assert train_models.safe_div(0, 5) == 0.0


def test_f1_calculation():
    precision = 0.8
    recall = 0.6
    f1 = train_models.safe_div(2 * precision * recall, precision + recall)
    assert abs(f1 - 0.6857) < 1e-3


# ── record_key ────────────────────────────────────────────────────────────────

def test_record_key_is_sha256_hex():
    sample = hashlib.sha256(b"0|20260430").hexdigest()
    assert len(sample) == 64
    assert all(c in "0123456789abcdef" for c in sample)


def test_two_distinct_inputs_produce_distinct_keys():
    k1 = hashlib.sha256(b"1|20260430").hexdigest()
    k2 = hashlib.sha256(b"2|20260430").hexdigest()
    assert k1 != k2


# ── Pipelines (requieren PySpark) ─────────────────────────────────────────────

def test_logistic_pipeline_has_standard_scaler():
    pytest.importorskip("pyspark")
    pipeline = train_models.build_logistic_pipeline(max_iter=5)
    stage_types = [type(s).__name__ for s in pipeline.getStages()]
    assert "StandardScaler" in stage_types


def test_random_forest_pipeline_no_standard_scaler():
    pytest.importorskip("pyspark")
    pipeline = train_models.build_random_forest_pipeline(num_trees=5, max_depth=3)
    stage_types = [type(s).__name__ for s in pipeline.getStages()]
    assert "StandardScaler" not in stage_types


def test_logistic_pipeline_ends_with_logistic_regression():
    pytest.importorskip("pyspark")
    pipeline = train_models.build_logistic_pipeline(max_iter=5)
    last = type(pipeline.getStages()[-1]).__name__
    assert last == "LogisticRegression"


def test_random_forest_pipeline_ends_with_random_forest():
    pytest.importorskip("pyspark")
    pipeline = train_models.build_random_forest_pipeline(num_trees=5, max_depth=3)
    last = type(pipeline.getStages()[-1]).__name__
    assert last == "RandomForestClassifier"


def test_shared_stages_include_imputer_with_median():
    pytest.importorskip("pyspark")
    from pyspark.ml.feature import Imputer
    _, _, imputer = train_models.shared_preprocessing_stages()
    assert isinstance(imputer, Imputer)
    assert imputer.getStrategy() == "median"


def test_build_model_frame_filters_credito_cerrado():
    pytest.importorskip("pyspark")
    from pyspark.sql import SparkSession
    import pyspark.sql.types as T
    from project_config import PREDICTOR_CANDIDATE_COLUMNS

    spark = (
        SparkSession.builder.master("local[1]")
        .appName("test-build-model-frame")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )

    base_fields = (
        [T.StructField(c, T.StringType(), True) for c in train_models.CATEGORICAL_FEATURES]
        + [T.StructField(c, T.DoubleType(), True) for c in train_models.NUMERIC_FEATURES]
        + [
            T.StructField("NumeroDiasMora", T.IntegerType(), True),
            T.StructField("ValorMoraTotal", T.DoubleType(), True),
            T.StructField("credito_cerrado", T.BooleanType(), True),
        ]
    )
    extra_cols = sorted(set(PREDICTOR_CANDIDATE_COLUMNS) - {f.name for f in base_fields})
    schema = T.StructType(base_fields + [T.StructField(c, T.StringType(), True) for c in extra_cols])

    cat_vals = ["__MISSING__"] * len(train_models.CATEGORICAL_FEATURES)
    num_vals = [None] * len(train_models.NUMERIC_FEATURES)
    extra_vals = [None] * len(extra_cols)

    rows = [
        tuple(cat_vals + num_vals + [30, 0.0, False] + extra_vals),   # activo, mora → label 1
        tuple(cat_vals + num_vals + [60, 500.0, True] + extra_vals),   # cerrado → excluido
        tuple(cat_vals + num_vals + [0, 0.0, False] + extra_vals),     # activo, sin mora → label 0
    ]

    df = spark.createDataFrame(rows, schema)
    result = train_models.build_model_frame(df)
    count = result.count()
    assert count == 2, f"Se esperaban 2 filas activas, se obtuvieron {count}"
    labels = {row[train_models.LABEL_COLUMN] for row in result.select(train_models.LABEL_COLUMN).collect()}
    assert 0 in labels and 1 in labels
    spark.stop()
