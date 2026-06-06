# Manifiesto de archivos seguros para GitHub

Este manifiesto documenta los archivos del proyecto que deben subirse a GitHub y los archivos que deben excluirse por seguridad, peso o sensibilidad.

## Archivos subidos por Codex al repo privado

Repositorio: `gerardoportillodev/KodigoPythonAnalyst`

Carpeta: `proyecto_big_data_codex/`

- `README.md`
- `docs/FINAL_TECHNICAL_REPORT.md`
- `PROJECT_FILE_MANIFEST.md`

## Archivos seguros que deben quedar versionados

Raiz del proyecto:

- `AGENTS.md`
- `README.md`
- `.gitignore`
- `requirements.txt`
- `prompts/FIRST_CODEX_PROMPT.txt`

Codigo fuente:

- `src/00_inspect_xlsm.py`
- `src/00_export_xlsm_to_tsv.py`
- `src/01_ingest_profile.py`
- `src/02_clean_to_parquet.py`
- `src/03_validate_quality_target.py`
- `src/04_train_compare_models.py`
- `src/project_config.py`
- `src/xlsm_utils.py`

Scripts:

- `scripts/use_local_spark.sh`
- `scripts/docker_terminal_check.sh`
- `scripts/run_local_spark_pipeline.sh`
- `scripts/run_model_experiment.sh`

Tests:

- `tests/test_clean_to_parquet.py`
- `tests/test_xlsm_utils.py`

Documentacion:

- `docs/DATA_DICTIONARY.md`
- `docs/PROJECT_CONTEXT.md`
- `docs/SETUP_LOCAL.md`
- `docs/DOCKER_NEXT_STEPS.md`
- `docs/RUNBOOK_INGESTA_SPARK.md`
- `docs/TARGET_VALIDATION_NOTES.md`
- `docs/MODELING_EXPERIMENT_NOTES.md`
- `docs/MODEL_RESULTS_SUMMARY.md`
- `docs/FINAL_TECHNICAL_REPORT.md`

## Archivos que NO deben subirse

Datos reales y derivados:

- `data/raw/ConvertidorEstructura - DATA.xlsm`
- `data/raw/creditos_raw.tsv`
- `data/trusted/`
- `data/analytics/`
- `data/results/`
- Cualquier `*.xlsm`, `*.xlsx`, `*.csv`, `*.tsv`, `*.parquet`

Ambientes y herramientas locales:

- `.venv/`
- `tools/`
- `__pycache__/`
- `.pytest_cache/`
- `spark-warehouse/`
- `metastore_db/`

Referencias pesadas o sensibles:

- PDFs de clase en `docs/reference/`
- Copias accidentales del Excel dentro de `docs/reference/`

## Comandos recomendados para subir el proyecto completo desde Terminal

Ejecutar en la Terminal normal del usuario, no desde Codex:

```bash
cd ~/Downloads/proyecto_big_data_codex

# Eliminar copia sensible si existe en docs/reference
rm -f "docs/reference/ConvertidorEstructura - DATA.xlsm"

# Inicializar Git local
git init
git branch -M main

# Confirmar que los datos estan excluidos
git status --short

# Agregar solo codigo/documentacion segura
git add AGENTS.md README.md .gitignore requirements.txt prompts src scripts tests docs/*.md

git commit -m "Add Big Data credit risk Spark project"

# Usar el repo privado existente
git remote add origin https://github.com/gerardoportillodev/KodigoPythonAnalyst.git

# Subir a main
git push -u origin main
```

Antes de ejecutar `git push`, revisar que `git status --short` no muestre archivos dentro de `data/`, `.venv/`, `tools/` ni `docs/reference/`.
