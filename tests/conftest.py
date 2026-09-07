"""Fixtures compartidas. Cargan las salidas ya computadas por el pipeline.

Los tests validan lo que el pipeline calculo, no valores fijados a mano. Si
una salida no existe, el test se salta con un mensaje que indica que hay que
ejecutar el pipeline primero: fallar por ausencia de archivo confundiria un
pipeline no ejecutado con un pipeline incorrecto.
"""
from __future__ import annotations

import json

import pandas as pd
import pytest

from src import config as C

ID_DTYPES = {"video_id": str, "comment_id": str, "channel_id": str,
             "author_channel_id": str}


def _need(path):
    if not path.exists():
        pytest.skip(f"falta {path.relative_to(C.ROOT)}; ejecute 'uv run python -m src.run_all'")
    return path


@pytest.fixture(scope="session")
def videos_raw() -> pd.DataFrame:
    return pd.read_csv(C.VIDEOS_CSV, encoding="utf-8-sig", dtype=str)


@pytest.fixture(scope="session")
def comments_raw() -> pd.DataFrame:
    return pd.read_csv(C.COMMENTS_CSV, encoding="utf-8-sig", dtype=str)


@pytest.fixture(scope="session")
def videos() -> pd.DataFrame:
    return pd.read_csv(_need(C.VIDEOS_CLEAN), dtype=ID_DTYPES)


@pytest.fixture(scope="session")
def comments() -> pd.DataFrame:
    return pd.read_csv(_need(C.COMMENTS_CLEAN), dtype=ID_DTYPES,
                       keep_default_na=False, na_values=[""])


@pytest.fixture(scope="session")
def joined() -> pd.DataFrame:
    return pd.read_csv(_need(C.JOINED_CLEAN), dtype=ID_DTYPES,
                       keep_default_na=False, na_values=[""])


@pytest.fixture(scope="session")
def metrics():
    def _get(name: str) -> dict:
        return json.loads(_need(C.METRICS / f"{name}.json").read_text(encoding="utf-8"))
    return _get


@pytest.fixture(scope="session")
def table():
    def _get(name: str, **kw) -> pd.DataFrame:
        path = C.TABLES / f"{name}.csv"
        if not path.exists():
            path = C.NETWORKS / f"{name}.csv"
        return pd.read_csv(_need(path), **kw)
    return _get
