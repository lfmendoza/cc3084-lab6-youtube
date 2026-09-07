#!/usr/bin/env bash
#
# Reproduce el Laboratorio 6 completo desde cero.
#
#   ./scripts/run_analysis.sh            pipeline completo + tests
#   ./scripts/run_analysis.sh --no-tests solo el pipeline
#   ./scripts/run_analysis.sh --clean    borra las salidas y vuelve a generarlas
#
# Requisitos: uv (https://docs.astral.sh/uv/). Si no esta disponible, el script
# recurre a python3 -m venv y pip; vease el README.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

RUN_TESTS=1
CLEAN=0
for arg in "$@"; do
  case "$arg" in
    --no-tests) RUN_TESTS=0 ;;
    --clean)    CLEAN=1 ;;
    -h|--help)  sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Opcion desconocida: $arg" >&2; exit 2 ;;
  esac
done

say() { printf '\n\033[1;34m==>\033[0m %s\n' "$1"; }
die() { printf '\n\033[1;31mERROR:\033[0m %s\n' "$1" >&2; exit 1; }

# ---------------------------------------------------------------- entorno ----
if command -v uv >/dev/null 2>&1; then
  RUNNER=(uv run)
  say "Sincronizando el entorno con uv (pyproject.toml + uv.lock)"
  UV_TORCH_BACKEND=cpu uv sync --frozen || UV_TORCH_BACKEND=cpu uv sync
else
  say "uv no esta disponible: se usa python3 -m venv y pip"
  [ -d .venv ] || python3 -m venv .venv
  # shellcheck disable=SC1091
  . .venv/bin/activate
  RUNNER=()
  python -m pip install --quiet --upgrade pip
  python -m pip install --quiet -r requirements.txt
fi

# ------------------------------------------------------- datos de entrada ----
say "Verificando los datos de entrada"
for f in data/raw/youtube_videos.csv data/raw/youtube_comments.csv; do
  [ -s "$f" ] || die "falta $f (los datos crudos son parte del repositorio)"
done
md5sum data/raw/*.csv 2>/dev/null || true

# -------------------------------------------------- modelos y recursos NLP ---
say "Asegurando el modelo de espanol de spaCy y los recursos de NLTK"
"${RUNNER[@]}" python - <<'PY'
import subprocess, sys
try:
    import spacy; spacy.load("es_core_news_sm")
    print("      es_core_news_sm ya instalado")
except Exception:
    print("      descargando es_core_news_sm...")
    subprocess.run([sys.executable, "-m", "spacy", "download", "es_core_news_sm"],
                   check=True)
import nltk
for pkg in ("stopwords", "punkt", "punkt_tab"):
    try:
        nltk.data.find(f"corpora/{pkg}") if pkg == "stopwords" else nltk.data.find(f"tokenizers/{pkg}")
        print(f"      nltk:{pkg} ya disponible")
    except LookupError:
        print(f"      descargando nltk:{pkg}...")
        nltk.download(pkg, quiet=True)
PY

# ------------------------------------------------------ limpieza opcional ----
if [ "$CLEAN" -eq 1 ]; then
  say "Borrando salidas generadas (los datos de data/raw NO se tocan)"
  rm -rf results/figures/*.png results/figures/_captions.jsonl \
         results/tables/*.csv results/networks/* results/metrics/*.json \
         results/model/* data/processed/*.csv \
         report/laboratorio_6_reporte.md \
         "report/Laboratorio_6_Analisis_Redes_Sociales_YouTube.pdf"
  find . -type d -name __pycache__ -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null || true
  rm -rf .pytest_cache
fi

# ---------------------------------------------------------------- pipeline ---
say "Ejecutando el pipeline completo"
"${RUNNER[@]}" python -m src.run_all

# ------------------------------------------------------------------- tests ---
if [ "$RUN_TESTS" -eq 1 ]; then
  say "Ejecutando las validaciones"
  "${RUNNER[@]}" pytest -q
fi

say "Listo. Entregables:"
echo "  Informe PDF : report/Laboratorio_6_Analisis_Redes_Sociales_YouTube.pdf"
echo "  Informe MD  : report/laboratorio_6_reporte.md"
echo "  Modelo      : results/model/sentiment_model_report.md"
echo "  Figuras     : results/figures/  ($(ls -1 results/figures/*.png 2>/dev/null | wc -l) PNG)"
echo "  Tablas      : results/tables/   ($(ls -1 results/tables/*.csv 2>/dev/null | wc -l) CSV)"
echo "  Redes       : results/networks/ ($(ls -1 results/networks/* 2>/dev/null | wc -l) archivos)"
