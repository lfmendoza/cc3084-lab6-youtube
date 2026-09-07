"""Configuracion central del laboratorio: rutas, semillas y constantes.

Todo modulo del pipeline importa desde aqui para que las rutas y la semilla
sean unicas y el analisis sea reproducible.
"""
from __future__ import annotations

import json
import os
import random
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------- rutas -----
ROOT = Path(__file__).resolve().parent.parent

DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
DOCS = ROOT / "docs"
RESULTS = ROOT / "results"
TABLES = RESULTS / "tables"
FIGURES = RESULTS / "figures"
NETWORKS = RESULTS / "networks"
MODEL_DIR = RESULTS / "model"
METRICS = RESULTS / "metrics"
REPORT = ROOT / "report"

VIDEOS_CSV = DATA_RAW / "youtube_videos.csv"
COMMENTS_CSV = DATA_RAW / "youtube_comments.csv"

VIDEOS_CLEAN = DATA_PROCESSED / "videos_clean.csv"
COMMENTS_CLEAN = DATA_PROCESSED / "comments_clean.csv"
JOINED_CLEAN = DATA_PROCESSED / "comments_videos_joined.csv"

for _d in (DATA_PROCESSED, TABLES, FIGURES, NETWORKS, MODEL_DIR, METRICS, REPORT):
    _d.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------- semillas -----
SEED = 42


def set_seeds(seed: int = SEED) -> None:
    """Fija las semillas de los generadores usados en el pipeline."""
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    try:  # torch solo se usa en el modulo de sentimiento
        import torch

        torch.manual_seed(seed)
        torch.use_deterministic_algorithms(False)
    except Exception:  # pragma: no cover - torch opcional en tests
        pass


# ------------------------------------------------- constantes de analisis ---
#: Modelo de sentimiento en espanol (RoBERTuito afinado en TASS 2020).
SENTIMENT_MODEL_ID = "pysentimiento/robertuito-sentiment-analysis"
SENTIMENT_MAX_LEN = 128
SENTIMENT_BATCH_SIZE = 32

#: Resolucion de Louvain. 1.0 = formulacion estandar de modularidad.
LOUVAIN_RESOLUTION = 1.0

#: N de elementos mostrados en rankings del cuerpo del informe.
TOP_N = 10

#: Dimensiones y columnas esperadas segun el enunciado del laboratorio (se
#: validan contra los archivos reales; si difieren, gana el archivo real).
EXPECTED_VIDEOS_SHAPE = (293, 20)
EXPECTED_COMMENTS_SHAPE = (406, 17)

ID_COLUMNS = {
    "videos": ["video_id", "channel_id"],
    "comments": ["video_id", "comment_id", "channel_id", "author_channel_id"],
}

FIG_DPI = 300


# --------------------------------------------------------------- metricas ---
def write_metrics(name: str, payload: dict) -> Path:
    """Persiste un bloque de metricas como JSON en ``results/metrics``."""
    path = METRICS / f"{name}.json"
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=_json_default),
        encoding="utf-8",
    )
    return path


def read_metrics(name: str) -> dict:
    """Lee un bloque de metricas previamente persistido."""
    return json.loads((METRICS / f"{name}.json").read_text(encoding="utf-8"))


def _json_default(obj):
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, (np.ndarray,)):
        return obj.tolist()
    if isinstance(obj, Path):
        return str(obj)
    raise TypeError(f"No serializable: {type(obj)}")
