"""Integridad de los datos crudos, del join y de la normalizacion."""
from __future__ import annotations

import pandas as pd

from src import config as C

EXPECTED_VIDEO_COLS = [
    "video_id", "title", "channel_name", "channel_id", "source_query",
    "source_group", "dataset_sources", "channel_handle", "published_time",
    "view_count_text", "description_snippet", "video_url", "query_hits",
    "keywords", "description", "view_count", "publish_date", "upload_date",
    "category", "owner_handle",
]
EXPECTED_COMMENT_COLS = [
    "video_id", "comment_id", "video_title", "channel_name", "channel_id",
    "author_name", "author_channel_id", "text", "source_query", "source_group",
    "dataset_sources", "author_handle", "published_text", "like_count_text",
    "reply_count", "is_pinned", "viewer_rating",
]


# ------------------------------------------------------------- dimensiones ---
def test_videos_shape(videos_raw):
    assert videos_raw.shape == C.EXPECTED_VIDEOS_SHAPE


def test_comments_shape(comments_raw):
    assert comments_raw.shape == C.EXPECTED_COMMENTS_SHAPE


def test_videos_columns_exact(videos_raw):
    assert list(videos_raw.columns) == EXPECTED_VIDEO_COLS


def test_comments_columns_exact(comments_raw):
    assert list(comments_raw.columns) == EXPECTED_COMMENT_COLS


# ------------------------------------------------------------------ llaves ---
def test_video_id_unico_en_videos(videos_raw):
    assert videos_raw["video_id"].duplicated().sum() == 0
    assert videos_raw["video_id"].isna().sum() == 0
    assert videos_raw["video_id"].nunique() == len(videos_raw)


def test_comment_id_unico(comments_raw):
    assert comments_raw["comment_id"].duplicated().sum() == 0
    assert comments_raw["comment_id"].isna().sum() == 0
    assert comments_raw["comment_id"].nunique() == len(comments_raw)


def test_sin_filas_duplicadas_completas(videos_raw, comments_raw):
    assert videos_raw.duplicated().sum() == 0
    assert comments_raw.duplicated().sum() == 0


def test_sin_identificadores_vacios(comments):
    for col in ("video_id", "comment_id", "channel_id", "author_channel_id"):
        s = comments[col].astype(str)
        assert (s.str.strip() == "").sum() == 0, f"{col} tiene valores vacios"
        assert s.isna().sum() == 0, f"{col} tiene nulos"
        assert (s.str.lower() == "nan").sum() == 0, f"{col} tiene 'nan' literal"


def test_ids_no_se_bajaron_a_minusculas(comments, videos):
    """Los IDs de YouTube distinguen mayusculas: no deben normalizarse a lower."""
    assert (videos["channel_id"].str.startswith("UC")).all()
    assert (comments["author_channel_id"].str.startswith("UC")).all()
    assert (comments["channel_id"].str.startswith("UC")).all()
    assert videos["video_id"].str.lower().nunique() <= videos["video_id"].nunique()
    assert (videos["channel_id"] != videos["channel_id"].str.lower()).any()


def test_channel_id_distinto_de_author_channel_id(comments):
    """Confundirlos colapsaria autores con canales duenos del video."""
    assert (comments["channel_id"] == comments["author_channel_id"]).sum() == 0


# -------------------------------------------------------------------- join ---
def test_join_no_pierde_ni_duplica_comentarios(joined, comments_raw):
    assert len(joined) == len(comments_raw)
    assert joined["comment_id"].nunique() == len(comments_raw)


def test_todos_los_comentarios_encuentran_su_video(metrics, comments_raw):
    j = metrics("join")
    assert j["comentarios_con_video"] == len(comments_raw)
    assert j["comentarios_sin_video"] == 0
    assert j["pct_comentarios_con_video"] == 100.0
    assert j["video_ids_de_comentarios_ausentes_en_videos"] == []


def test_video_ids_de_comentarios_son_subconjunto(videos_raw, comments_raw):
    assert set(comments_raw["video_id"]) <= set(videos_raw["video_id"])


def test_join_es_uno_a_muchos(joined):
    """Cada comentario debe tener exactamente un video; nunca mas de uno."""
    assert joined.groupby("comment_id")["video_id"].nunique().max() == 1


def test_columnas_redundantes_son_consistentes_tras_el_join(joined):
    for a, b in [("video_title", "title"),
                 ("channel_id_c", "channel_id_v"),
                 ("channel_name_c", "channel_name_v")]:
        if a in joined.columns and b in joined.columns:
            diff = (joined[a].fillna("").str.strip()
                    != joined[b].fillna("").str.strip()).sum()
            assert diff == 0, f"{a} y {b} difieren en {diff} filas"


# ------------------------------------------------------------ consistencia ---
def test_relaciones_uno_a_uno_id_etiqueta(comments, videos):
    assert comments.groupby("author_channel_id")["author_name"].nunique().max() == 1
    assert comments.groupby("author_name")["author_channel_id"].nunique().max() == 1
    assert videos.groupby("channel_id")["channel_name"].nunique().max() == 1
    assert videos.groupby("channel_name")["channel_id"].nunique().max() == 1


def test_handles_percent_encoded_quedan_decodificados(comments, videos):
    """La anomalia detectada debe estar corregida en las columnas *_norm."""
    assert not comments["author_handle_norm"].str.contains("%", na=False).any()
    assert not videos["channel_handle_norm"].str.contains("%", na=False).any()
    # y el campo original debe conservarse intacto
    assert comments["author_handle"].str.contains("%", na=False).sum() > 0


def test_variables_constantes_detectadas(metrics):
    q = metrics("quality")
    assert "is_pinned" in q["variables_constantes_comentarios"]
    assert "viewer_rating" in q["variables_constantes_comentarios"]
    assert "viewer_rating" in q["variables_totalmente_vacias_comentarios"]


def test_redundancias_confirmadas(videos_raw):
    assert (videos_raw["publish_date"] == videos_raw["upload_date"]).all()
    assert (videos_raw["owner_handle"] == videos_raw["channel_handle"]).all()


def test_no_se_eliminaron_filas_en_la_limpieza(comments, comments_raw, metrics):
    assert len(comments) == len(comments_raw)
    assert metrics("cleaning")["registros_eliminados"] == 0
