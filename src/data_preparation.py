"""Ejercicios 1 y 2: carga, integracion, diagnostico de calidad y limpieza.

Salidas
-------
``data/processed/videos_clean.csv``
``data/processed/comments_clean.csv``
``data/processed/comments_videos_joined.csv``
``results/tables/data_quality_{videos,comments}.csv``
``results/tables/consistency_checks.csv``
``results/tables/cleaning_effect.csv``
``results/metrics/{load,quality,join,cleaning}.json``
"""
from __future__ import annotations

import ast
import json
import warnings

import numpy as np
import pandas as pd

from . import config as C
from .text_processing import (
    clean_text,
    extract_hashtags,
    is_percent_encoded,
    normalize_display,
    normalize_handle,
    normalize_id,
    normalize_key,
    parse_count,
    preprocess_for_sentiment,
)

warnings.filterwarnings("ignore", category=FutureWarning)


# ============================================================== 1. carga ====
def load_raw() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Ejercicio 1.1. Carga ambos CSV como texto para no perder informacion.

    Se lee todo con ``dtype=str`` deliberadamente: si pandas infiere tipos,
    convierte los IDs con apariencia numerica y recorta ceros a la izquierda.
    La conversion a numerico se hace despues, de forma explicita y auditada.
    ``encoding="utf-8-sig"`` elimina la marca BOM presente en ambos archivos.
    """
    videos = pd.read_csv(C.VIDEOS_CSV, encoding="utf-8-sig", dtype=str, keep_default_na=True)
    comments = pd.read_csv(C.COMMENTS_CSV, encoding="utf-8-sig", dtype=str, keep_default_na=True)
    return videos, comments


def _parse_listish(value) -> list[str]:
    """Convierte las columnas ``query_hits`` y ``keywords`` de texto a lista."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return []
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return []
    try:
        parsed = ast.literal_eval(text)
        if isinstance(parsed, (list, tuple)):
            return [str(x).strip() for x in parsed if str(x).strip()]
        return [str(parsed).strip()]
    except (ValueError, SyntaxError):
        return [p.strip() for p in text.split("|") if p.strip()]


# ================================================= 2.1 diagnostico calidad ==
def quality_profile(df: pd.DataFrame, name: str, keys: list[str]) -> pd.DataFrame:
    """Perfil por variable: tipo, faltantes, cardinalidad, constancia.

    El "tipo inferido" reporta lo que la columna *podria* ser (entero,
    fecha ISO, booleano, lista serializada) para justificar despues cada
    conversion, sin que la carga haya alterado el valor original.
    """
    rows = []
    n = len(df)
    for col in df.columns:
        s = df[col]
        non_null = s.dropna()
        blanks = int((non_null.astype(str).str.strip() == "").sum())
        n_missing = int(s.isna().sum())
        n_unique = int(non_null.nunique())
        rows.append(
            {
                "dataset": name,
                "variable": col,
                "dtype_cargado": str(s.dtype),
                "tipo_inferido": _infer_type(non_null),
                "n_total": n,
                "n_no_nulos": int(non_null.shape[0]),
                "n_nulos": n_missing,
                "pct_nulos": round(100 * n_missing / n, 2) if n else 0.0,
                "n_vacios_o_espacios": blanks,
                "pct_vacios_o_espacios": round(100 * blanks / n, 2) if n else 0.0,
                "n_unicos": n_unique,
                "cardinalidad_rel": round(n_unique / n, 4) if n else 0.0,
                "es_constante": bool(n_unique <= 1),
                "es_totalmente_vacia": bool(n_missing == n),
                "es_llave_candidata": bool(col in keys),
                "es_pk": bool(n_unique == n and n_missing == 0 and col in keys),
                "ejemplo": _example(non_null),
            }
        )
    return pd.DataFrame(rows)


def _infer_type(s: pd.Series) -> str:
    if s.empty:
        return "vacia"
    sample = s.astype(str).str.strip()
    sample = sample[sample != ""]
    if sample.empty:
        return "solo_espacios"
    if sample.str.fullmatch(r"-?\d+").all():
        return "entero"
    if sample.str.fullmatch(r"-?\d+\.\d+").all():
        return "decimal"
    if sample.str.fullmatch(r"(?i)true|false").all():
        return "booleano"
    if sample.str.match(r"^\d{4}-\d{2}-\d{2}T").all():
        return "fecha_iso8601"
    if sample.str.match(r"^\s*\[").all():
        return "lista_serializada"
    if sample.str.contains(r"^\s*hace ").all():
        return "tiempo_relativo"
    if sample.str.fullmatch(r"[\d,\. ]+ ?(vistas|views)?").all():
        return "conteo_como_texto"
    return "texto"


def _example(s: pd.Series) -> str:
    if s.empty:
        return ""
    val = str(s.iloc[0])
    return val[:80] + ("..." if len(val) > 80 else "")


def duplicate_report(df: pd.DataFrame, name: str, keys: list[str]) -> dict:
    out = {
        "dataset": name,
        "n_filas": int(len(df)),
        "n_columnas": int(df.shape[1]),
        "filas_duplicadas_completas": int(df.duplicated().sum()),
        "llaves": {},
    }
    for k in keys:
        if k in df.columns:
            out["llaves"][k] = {
                "duplicados": int(df[k].duplicated().sum()),
                "nulos": int(df[k].isna().sum()),
                "vacios": int((df[k].fillna("").astype(str).str.strip() == "").sum()),
                "unicos": int(df[k].nunique()),
                "es_unica": bool(df[k].duplicated().sum() == 0 and df[k].isna().sum() == 0),
            }
    return out


def outlier_report(df: pd.DataFrame, cols: list[str], name: str) -> pd.DataFrame:
    """Atipicos por IQR y por z-score robusto, sin eliminarlos.

    Los conteos de popularidad en redes sociales tienen cola derecha pesada:
    un valor extremo es normalmente un video viral real, no un error. Se
    reportan para discutir plausibilidad, no para filtrar.
    """
    rows = []
    for col in cols:
        s = pd.to_numeric(df[col], errors="coerce").dropna()
        if s.empty:
            continue
        q1, q3 = s.quantile([0.25, 0.75])
        iqr = q3 - q1
        lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        mad = (s - s.median()).abs().median()
        rmz = 0.6745 * (s - s.median()) / mad if mad > 0 else pd.Series(0.0, index=s.index)
        rows.append(
            {
                "dataset": name,
                "variable": col,
                "n": int(s.shape[0]),
                "min": float(s.min()),
                "p25": float(q1),
                "mediana": float(s.median()),
                "media": round(float(s.mean()), 2),
                "p75": float(q3),
                "p90": float(s.quantile(0.90)),
                "p99": float(s.quantile(0.99)),
                "max": float(s.max()),
                "std": round(float(s.std(ddof=1)), 2) if s.shape[0] > 1 else 0.0,
                "asimetria": round(float(s.skew()), 3) if s.shape[0] > 2 else 0.0,
                "curtosis": round(float(s.kurtosis()), 3) if s.shape[0] > 3 else 0.0,
                "limite_iqr_inf": float(lo),
                "limite_iqr_sup": float(hi),
                "n_atipicos_iqr": int(((s < lo) | (s > hi)).sum()),
                "pct_atipicos_iqr": round(100 * float(((s < lo) | (s > hi)).mean()), 2),
                "n_atipicos_z_robusto_3.5": int((rmz.abs() > 3.5).sum()),
                "ratio_max_mediana": round(float(s.max() / s.median()), 1) if s.median() else np.nan,
            }
        )
    return pd.DataFrame(rows)


def consistency_checks(videos: pd.DataFrame, comments: pd.DataFrame,
                       joined: pd.DataFrame) -> pd.DataFrame:
    """Ejercicio 2.1: consistencia entre IDs, nombres y handles."""
    checks: list[dict] = []

    def add(ambito, chequeo, esperado, obtenido, ok, nota=""):
        checks.append(
            {
                "ambito": ambito,
                "chequeo": chequeo,
                "esperado": esperado,
                "obtenido": obtenido,
                "cumple": bool(ok),
                "nota": nota,
            }
        )

    # --- videos: relacion 1:1 entre identificador y etiquetas visibles ---
    for idc, lab in [("channel_id", "channel_name"), ("channel_id", "channel_handle")]:
        a = int(videos.groupby(idc)[lab].nunique().max())
        b = int(videos.groupby(lab)[idc].nunique().max())
        add("videos", f"{idc} <-> {lab} es 1:1", "1 y 1", f"{a} y {b}", a == 1 and b == 1,
            "Un ID por nombre visible y viceversa; no hay colisiones de nombre.")

    n_diff = int((videos["owner_handle"].fillna("") != videos["channel_handle"].fillna("")).sum())
    add("videos", "owner_handle == channel_handle", "0 diferencias", f"{n_diff} diferencias",
        n_diff == 0, "owner_handle es redundante: se conserva pero no se usa.")

    n_diff = int((videos["publish_date"].fillna("") != videos["upload_date"].fillna("")).sum())
    add("videos", "publish_date == upload_date", "0 diferencias", f"{n_diff} diferencias",
        n_diff == 0, "upload_date es redundante en este conjunto.")

    bad_url = int((~videos.apply(
        lambda r: str(r["video_id"]) in str(r["video_url"]), axis=1)).sum())
    add("videos", "video_url contiene video_id", "0 inconsistencias", f"{bad_url}",
        bad_url == 0, "Confirma que video_url y video_id refieren al mismo recurso.")

    # --- comentarios ---
    for idc, lab in [("author_channel_id", "author_name"),
                     ("author_channel_id", "author_handle"),
                     ("channel_id", "channel_name")]:
        a = int(comments.groupby(idc)[lab].nunique().max())
        b = int(comments.groupby(lab)[idc].nunique().max())
        add("comentarios", f"{idc} <-> {lab} es 1:1", "1 y 1", f"{a} y {b}",
            a == 1 and b == 1, "Sin alias ni homonimos en la ventana observada.")

    same = int((comments["channel_id"] == comments["author_channel_id"]).sum())
    add("comentarios", "channel_id != author_channel_id", "0 coincidencias", f"{same}",
        same == 0, "Ningun comentario observado fue escrito por el canal dueno del video.")

    # --- join: redundancia de las columnas duplicadas ---
    for col_c, col_v, label in [
        ("video_title", "title", "video_title == title"),
        ("channel_id_c", "channel_id_v", "channel_id (comments) == channel_id (videos)"),
        ("channel_name_c", "channel_name_v", "channel_name (comments) == channel_name (videos)"),
    ]:
        if col_c in joined.columns and col_v in joined.columns:
            d = int((joined[col_c].fillna("").map(normalize_key)
                     != joined[col_v].fillna("").map(normalize_key)).sum())
            add("join", label, "0 diferencias", f"{d} diferencias", d == 0,
                "Variable redundante tras el join; se conserva solo la de videos.")

    for col_c, col_v, label in [
        ("source_query_c", "source_query_v", "source_query (comments) == source_query (videos)"),
        ("source_group_c", "source_group_v", "source_group (comments) == source_group (videos)"),
    ]:
        if col_c in joined.columns and col_v in joined.columns:
            d = int((joined[col_c].fillna("") != joined[col_v].fillna("")).sum())
            add("join", label, "no necesariamente igual", f"{d} de {len(joined)} difieren",
                True,
                "Difieren por diseno: la del comentario describe como se "
                "recolecto el comentario y la del video como se encontro el "
                "video. Se conservan ambas con sufijo explicito.")

    n_pct = int(comments["author_handle"].map(is_percent_encoded).sum())
    add("comentarios", "author_handle sin percent-encoding", "0 registros",
        f"{n_pct} registros codificados", n_pct == 0,
        "ANOMALIA DETECTADA: author_handle guarda los caracteres no ASCII "
        "codificados para URL (/@ErmeP%C3%A9rez-q4s) mientras author_name los "
        "guarda literales. Se corrige decodificando en author_handle_norm; el "
        "campo original se conserva intacto.")

    handles_c = comments["author_handle"].map(normalize_handle)
    handles_n = comments["author_name"].map(normalize_handle)
    d = int((handles_c != handles_n).sum())
    add("comentarios", "author_handle_norm == author_name normalizado",
        "0 diferencias", f"{d} diferencias", d == 0,
        "Tras decodificar, las dos etiquetas visibles de cada autor coinciden, "
        "lo que confirma que describen la misma cuenta.")

    n_pct_v = int(videos["channel_handle"].map(is_percent_encoded).sum())
    add("videos", "channel_handle sin percent-encoding", "0 registros",
        f"{n_pct_v} registros codificados", n_pct_v == 0,
        "Los handles de canal no presentan la anomalia de codificacion.")

    return pd.DataFrame(checks)


# ===================================================== 2.3-2.4 normalizacion =
def normalize_videos(videos: pd.DataFrame) -> pd.DataFrame:
    df = videos.copy()

    for col in ("video_id", "channel_id"):
        df[col] = df[col].map(normalize_id)

    for col in ("title", "channel_name", "description", "description_snippet",
                "category", "source_query", "source_group"):
        df[col + "_norm"] = df[col].map(normalize_display)

    df["channel_handle_norm"] = df["channel_handle"].map(normalize_handle)
    df["owner_handle_norm"] = df["owner_handle"].map(normalize_handle)
    df["channel_name_key"] = df["channel_name"].map(normalize_key)

    # Conteos: se conserva el texto y se agrega la version numerica.
    df["view_count_num"] = pd.to_numeric(df["view_count"], errors="coerce")
    df["view_count_text_num"] = df["view_count_text"].map(parse_count)
    df["view_count_final"] = df["view_count_num"].fillna(df["view_count_text_num"])

    df["publish_date_dt"] = pd.to_datetime(df["publish_date"], errors="coerce", utc=True)
    df["upload_date_dt"] = pd.to_datetime(df["upload_date"], errors="coerce", utc=True)

    df["query_hits_list"] = df["query_hits"].map(_parse_listish)
    df["keywords_list"] = df["keywords"].map(_parse_listish)
    df["dataset_sources_list"] = df["dataset_sources"].map(
        lambda x: [p.strip() for p in str(x).split("|") if p.strip()] if pd.notna(x) else []
    )
    df["n_query_hits"] = df["query_hits_list"].map(len)
    df["n_keywords"] = df["keywords_list"].map(len)
    df["n_dataset_sources"] = df["dataset_sources_list"].map(len)
    df["title_len"] = df["title"].fillna("").str.len()
    df["description_len"] = df["description"].fillna("").str.len()
    df["description_hashtags"] = df["description"].fillna("").map(extract_hashtags)
    df["title_hashtags"] = df["title"].fillna("").map(extract_hashtags)
    return df


def normalize_comments(comments: pd.DataFrame) -> pd.DataFrame:
    df = comments.copy()

    for col in ("video_id", "comment_id", "channel_id", "author_channel_id"):
        df[col] = df[col].map(normalize_id)

    for col in ("author_name", "channel_name", "video_title", "source_query", "source_group"):
        df[col + "_norm"] = df[col].map(normalize_display)
    df["author_handle_norm"] = df["author_handle"].map(normalize_handle)
    df["author_name_key"] = df["author_name"].map(normalize_key)

    # "me gusta": el parser devuelve None para el blanco de YouTube; la
    # imputacion a 0 se hace aqui, explicita y con bandera de auditoria.
    df["like_count_parsed"] = df["like_count_text"].map(parse_count)
    df["like_count_blank"] = df["like_count_parsed"].isna()
    df["like_count"] = df["like_count_parsed"].fillna(0).astype("int64")

    df["reply_count_num"] = pd.to_numeric(df["reply_count"], errors="coerce").astype("Int64")
    df["is_pinned_bool"] = df["is_pinned"].map(
        {"True": True, "False": False, "true": True, "false": False}
    )
    df["published_text_edited"] = df["published_text"].fillna("").str.contains("editado")
    df["published_text_norm"] = (
        df["published_text"].fillna("").str.replace(r"\s*\(editado\)", "", regex=True).str.strip()
    )
    df["published_bucket"] = df["published_text_norm"].map(_relative_bucket)
    df["published_days_approx"] = df["published_text_norm"].map(_relative_days)
    return df


_UNIT_DAYS = {
    "segundo": 1 / 86400, "segundos": 1 / 86400,
    "minuto": 1 / 1440, "minutos": 1 / 1440,
    "hora": 1 / 24, "horas": 1 / 24,
    "dia": 1.0, "dias": 1.0, "día": 1.0, "días": 1.0,
    "semana": 7.0, "semanas": 7.0,
    "mes": 30.44, "meses": 30.44,
    "ano": 365.25, "anos": 365.25, "año": 365.25, "años": 365.25,
}


def _relative_days(text: str) -> float | None:
    """Traduce "hace 2 semanas" a dias APROXIMADOS.

    Es una aproximacion deliberadamente burda: la variable original es
    relativa al momento de recoleccion y YouTube la redondea. Solo se usa
    para ordenar por antiguedad, nunca como fecha.
    """
    import re

    m = re.match(r"hace\s+(\d+)\s+([a-zá-úñ]+)", str(text).strip(), re.IGNORECASE)
    if not m:
        return None
    qty, unit = int(m.group(1)), m.group(2).lower()
    factor = _UNIT_DAYS.get(unit) or _UNIT_DAYS.get(normalize_key(unit))
    return round(qty * factor, 3) if factor else None


def _relative_bucket(text: str) -> str:
    d = _relative_days(text)
    if d is None:
        return "desconocido"
    if d < 7:
        return "<1 semana"
    if d < 31:
        return "1 sem - 1 mes"
    if d < 366:
        return "1 mes - 1 ano"
    if d < 731:
        return "1 - 2 anos"
    return ">2 anos"


# ============================================================ 2.5-2.7 texto ==
def build_text_versions(comments: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Crea ``texto_original`` y ``texto_limpio`` y cuantifica el efecto."""
    df = comments.copy()
    df["texto_original"] = df["text"].fillna("").astype(str)

    before = {
        "n_comentarios": int(len(df)),
        "vacios_antes": int((df["texto_original"].str.strip() == "").sum()),
        "duplicados_exactos_antes": int(df["texto_original"].duplicated().sum()),
        "n_textos_duplicados_unicos_antes": int(
            df["texto_original"].value_counts().gt(1).sum()
        ),
        "longitud_media_antes": round(float(df["texto_original"].str.len().mean()), 2),
        "longitud_mediana_antes": float(df["texto_original"].str.len().median()),
        "tokens_medios_antes": round(
            float(df["texto_original"].str.split().map(len).mean()), 2
        ),
    }

    parsed = df["texto_original"].map(clean_text)
    df["texto_limpio"] = parsed.map(lambda d: d["texto_limpio"])
    df["texto_sin_lema"] = parsed.map(lambda d: d["texto_sin_lema"])
    df["hashtags"] = parsed.map(lambda d: d["hashtags"])
    df["mentions"] = parsed.map(lambda d: d["mentions"])
    df["urls"] = parsed.map(lambda d: d["urls"])
    df["emojis"] = parsed.map(lambda d: d["emojis"])
    df["emoji_shortcodes"] = parsed.map(lambda d: d["emoji_shortcodes"])
    df["n_emoji_shortcodes"] = df["emoji_shortcodes"].map(len)
    df["n_hashtags"] = df["hashtags"].map(len)
    df["n_mentions"] = df["mentions"].map(len)
    df["n_urls"] = df["urls"].map(len)
    df["n_emojis"] = df["emojis"].map(len)
    df["texto_sentimiento"] = df["texto_original"].map(preprocess_for_sentiment)

    df["len_original"] = df["texto_original"].str.len()
    df["len_limpio"] = df["texto_limpio"].str.len()
    df["tokens_original"] = df["texto_original"].str.split().map(len)
    df["tokens_limpio"] = df["texto_limpio"].str.split().map(len)
    df["texto_modificado"] = df["texto_original"].str.strip() != df["texto_limpio"]
    df["quedo_vacio_tras_limpieza"] = df["texto_limpio"].str.strip() == ""

    after = {
        "vacios_despues": int(df["quedo_vacio_tras_limpieza"].sum()),
        "duplicados_texto_limpio_despues": int(df["texto_limpio"].duplicated().sum()),
        "duplicados_texto_limpio_no_vacio": int(
            df.loc[~df["quedo_vacio_tras_limpieza"], "texto_limpio"].duplicated().sum()
        ),
        "textos_modificados": int(df["texto_modificado"].sum()),
        "textos_sin_modificacion": int((~df["texto_modificado"]).sum()),
        "pct_modificados": round(100 * float(df["texto_modificado"].mean()), 2),
        "longitud_media_despues": round(float(df["len_limpio"].mean()), 2),
        "longitud_mediana_despues": float(df["len_limpio"].median()),
        "tokens_medios_despues": round(float(df["tokens_limpio"].mean()), 2),
        "reduccion_media_caracteres_pct": round(
            100 * float(1 - df["len_limpio"].sum() / max(df["len_original"].sum(), 1)), 2
        ),
        "reduccion_media_tokens_pct": round(
            100 * float(1 - df["tokens_limpio"].sum() / max(df["tokens_original"].sum(), 1)), 2
        ),
        "registros_eliminados": 0,
        "politica_eliminacion": (
            "No se elimina ningun comentario. Los textos que quedan vacios "
            "tras la limpieza tematica conservan su texto_original y siguen "
            "siendo validos para la red y para el sentimiento; excluirlos "
            "sesgaria la red de participacion."
        ),
        "comentarios_con_url": int((df["n_urls"] > 0).sum()),
        "comentarios_con_hashtag": int((df["n_hashtags"] > 0).sum()),
        "comentarios_con_mencion": int((df["n_mentions"] > 0).sum()),
        "comentarios_con_emoji": int((df["n_emojis"] > 0).sum()),
        "total_emojis": int(df["n_emojis"].sum()),
        "comentarios_con_atajo_de_emoji_textual": int((df["n_emoji_shortcodes"] > 0).sum()),
        "total_atajos_de_emoji_textual": int(df["n_emoji_shortcodes"].sum()),
        "nota_atajos_de_emoji": (
            "El CSV crudo contiene atajos de emoji ya convertidos a texto por "
            "el recolector (:hand-purple-blue-peace:, :face-blue-smiling:). Se "
            "eliminan de texto_limpio porque generarian bigramas inexistentes "
            "('hand purple', 'purple blue') atribuibles al proceso de "
            "recoleccion y no a los usuarios. Se conservan en texto_original."
        ),
    }
    return df, {**before, **after}


# ================================================================ 1.4 join ===
def integrate(comments: pd.DataFrame, videos: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Ejercicio 1.4. Une comentarios con videos por ``video_id``.

    Se usa un LEFT JOIN desde comentarios: la pregunta es cuantos comentarios
    logran asociarse a un video, asi que ninguna fila de comentarios puede
    desaparecer. Las columnas homonimas reciben sufijos ``_c`` / ``_v`` para
    poder auditar su consistencia en lugar de sobrescribir en silencio.
    """
    v_cols = [
        "video_id", "title", "channel_id", "channel_name", "channel_handle",
        "owner_handle", "category", "source_query", "source_group",
        "view_count_final", "publish_date", "publish_date_dt", "keywords",
        "keywords_list", "description", "n_keywords", "video_url",
    ]
    v_cols = [c for c in v_cols if c in videos.columns]
    joined = comments.merge(
        videos[v_cols], on="video_id", how="left", suffixes=("_c", "_v"),
        indicator="_merge",
    )
    matched = int((joined["_merge"] == "both").sum())
    unmatched = int((joined["_merge"] != "both").sum())

    ids_comments = set(comments["video_id"])
    ids_videos = set(videos["video_id"])
    metrics = {
        "n_comentarios": int(len(comments)),
        "n_videos_catalogo": int(len(videos)),
        "comentarios_con_video": matched,
        "comentarios_sin_video": unmatched,
        "pct_comentarios_con_video": round(100 * matched / max(len(comments), 1), 2),
        "video_ids_distintos_en_comentarios": len(ids_comments),
        "video_ids_de_comentarios_ausentes_en_videos": sorted(ids_comments - ids_videos),
        "videos_con_al_menos_un_comentario_observado": len(ids_comments & ids_videos),
        "videos_sin_comentario_observado": len(ids_videos - ids_comments),
        "pct_videos_con_comentario_observado": round(
            100 * len(ids_comments & ids_videos) / max(len(ids_videos), 1), 2
        ),
        "cardinalidad_join": "1 video : N comentarios (uno a muchos)",
        "tipo_join": "LEFT JOIN comentarios -> videos por video_id",
    }
    joined = joined.drop(columns=["_merge"])
    return joined, metrics


# ================================================================= pipeline ==
def run() -> dict:
    C.set_seeds()
    print("[1/6] data_preparation: carga y validacion")
    videos_raw, comments_raw = load_raw()

    load_metrics = {
        "videos_shape": list(videos_raw.shape),
        "comments_shape": list(comments_raw.shape),
        "videos_shape_esperado": list(C.EXPECTED_VIDEOS_SHAPE),
        "comments_shape_esperado": list(C.EXPECTED_COMMENTS_SHAPE),
        "videos_shape_coincide": list(videos_raw.shape) == list(C.EXPECTED_VIDEOS_SHAPE),
        "comments_shape_coincide": list(comments_raw.shape) == list(C.EXPECTED_COMMENTS_SHAPE),
        "videos_columnas": list(videos_raw.columns),
        "comments_columnas": list(comments_raw.columns),
        "encoding": "utf-8-sig (los dos archivos traen BOM)",
        "dtype_carga": "str en todas las columnas; conversion posterior explicita",
        "md5_videos": _md5(C.VIDEOS_CSV),
        "md5_comments": _md5(C.COMMENTS_CSV),
    }

    # --- diagnostico de calidad sobre los datos crudos ---
    qv = quality_profile(videos_raw, "youtube_videos", C.ID_COLUMNS["videos"])
    qc = quality_profile(comments_raw, "youtube_comments", C.ID_COLUMNS["comments"])
    qv.to_csv(C.TABLES / "data_quality_videos.csv", index=False)
    qc.to_csv(C.TABLES / "data_quality_comments.csv", index=False)

    dup_v = duplicate_report(videos_raw, "youtube_videos", C.ID_COLUMNS["videos"])
    dup_c = duplicate_report(comments_raw, "youtube_comments", C.ID_COLUMNS["comments"])

    # --- normalizacion y texto ---
    videos = normalize_videos(videos_raw)
    comments = normalize_comments(comments_raw)
    comments, cleaning_metrics = build_text_versions(comments)

    out_v = outlier_report(videos, ["view_count_num", "title_len", "description_len",
                                    "n_keywords", "n_query_hits"], "youtube_videos")
    out_c = outlier_report(comments, ["like_count", "reply_count_num", "len_original",
                                      "tokens_original", "n_emojis"], "youtube_comments")
    outliers = pd.concat([out_v, out_c], ignore_index=True)
    outliers.to_csv(C.TABLES / "outlier_diagnostics.csv", index=False)

    joined, join_metrics = integrate(comments, videos)
    checks = consistency_checks(videos, comments, joined)
    checks.to_csv(C.TABLES / "consistency_checks.csv", index=False)

    # --- variables problematicas (2.2) ---
    problem = problematic_variables(videos_raw, comments_raw, videos, comments)
    problem.to_csv(C.TABLES / "problematic_variables.csv", index=False)

    pd.DataFrame([cleaning_metrics]).T.reset_index().rename(
        columns={"index": "metrica", 0: "valor"}
    ).to_csv(C.TABLES / "cleaning_effect.csv", index=False)

    # --- persistencia ---
    _to_csv(videos, C.VIDEOS_CLEAN)
    _to_csv(comments, C.COMMENTS_CLEAN)
    _to_csv(joined, C.JOINED_CLEAN)

    quality_metrics = {
        "duplicados_videos": dup_v,
        "duplicados_comentarios": dup_c,
        "variables_constantes_videos": qv.loc[qv.es_constante, "variable"].tolist(),
        "variables_constantes_comentarios": qc.loc[qc.es_constante, "variable"].tolist(),
        "variables_totalmente_vacias_comentarios":
            qc.loc[qc.es_totalmente_vacia, "variable"].tolist(),
        "variables_con_nulos_videos": qv.loc[qv.n_nulos > 0, ["variable", "n_nulos", "pct_nulos"]]
            .to_dict("records"),
        "variables_con_nulos_comentarios":
            qc.loc[qc.n_nulos > 0, ["variable", "n_nulos", "pct_nulos"]].to_dict("records"),
        "likes_en_blanco": int(comments["like_count_blank"].sum()),
        "pct_likes_en_blanco": round(100 * float(comments["like_count_blank"].mean()), 2),
        "min_like_no_blanco": int(comments.loc[~comments.like_count_blank, "like_count"].min()),
        "chequeos_consistencia_total": int(len(checks)),
        "chequeos_consistencia_ok": int(checks["cumple"].sum()),
        "chequeos_consistencia_fallidos": checks.loc[~checks.cumple, "chequeo"].tolist(),
        "outliers": outliers.to_dict("records"),
    }

    C.write_metrics("load", load_metrics)
    C.write_metrics("quality", quality_metrics)
    C.write_metrics("join", join_metrics)
    C.write_metrics("cleaning", cleaning_metrics)

    print(f"      videos={videos_raw.shape} comments={comments_raw.shape} "
          f"join={join_metrics['comentarios_con_video']}/{join_metrics['n_comentarios']} "
          f"({join_metrics['pct_comentarios_con_video']}%)")
    return {"videos": videos, "comments": comments, "joined": joined}


def problematic_variables(videos_raw, comments_raw, videos, comments) -> pd.DataFrame:
    """Ejercicio 2.2: variables inutilizables o de uso delicado."""
    n_c = len(comments_raw)
    rows = [
        ("comments", "viewer_rating", "Inutilizable",
         f"Vacia en los {n_c} registros ({comments_raw.viewer_rating.isna().sum()} nulos).",
         "Se excluye de todo analisis. Se conserva en el archivo crudo."),
        ("comments", "is_pinned", "Inutilizable (constante)",
         f"Valor unico {sorted(comments_raw.is_pinned.dropna().unique())} en los {n_c} registros.",
         "Varianza cero: no puede explicar ni segmentar nada. Se convierte a booleano y se documenta."),
        ("comments", "reply_count", "Uso delicado",
         "Cuenta respuestas recibidas pero no identifica a quien respondio.",
         "Prohibido usarla como arista. Se usa solo como atributo de intensidad del comentario."),
        ("comments", "published_text", "Uso delicado",
         "Tiempo relativo al momento de recoleccion ('hace 2 anos'), redondeado por YouTube.",
         "No se convierte a fecha absoluta. Se deriva published_days_approx solo para ordenar."),
        ("comments", "like_count_text", "Requiere conversion",
         f"Texto; {int(comments.like_count_blank.sum())} registros en blanco (un espacio).",
         "Parser explicito; blanco -> 0 con bandera like_count_blank, porque YouTube "
         "oculta el contador cuando vale 0 (el minimo observado no blanco es "
         f"{int(comments.loc[~comments.like_count_blank,'like_count'].min())})."),
        ("comments", "video_title / channel_name / channel_id", "Redundante",
         "Derivables del join por video_id; verificadas consistentes al 100%.",
         "Se conservan con sufijo _c y se prefiere la version de videos."),
        ("comments", "author_name / author_handle", "Uso delicado",
         "Etiquetas visibles mutables; no son identificadores. Ademas "
         f"{int(comments_raw.author_handle.map(is_percent_encoded).sum())} "
         "author_handle vienen percent-encoded (/@ErmeP%C3%A9rez-q4s).",
         "Solo para etiquetas de figuras. El nodo es author_channel_id. Se "
         "decodifica el percent-encoding en author_handle_norm."),
        ("videos", "published_time", "Uso delicado",
         f"Tiempo relativo; {int(videos_raw.published_time.isna().sum())} nulos.",
         "No se usa como fecha. Se prefiere publish_date (ISO 8601, sin nulos)."),
        ("videos", "view_count_text", "Requiere conversion",
         f"Texto con separador de miles y sufijo 'vistas'; {int(videos_raw.view_count_text.isna().sum())} nulos.",
         "Se parsea a view_count_text_num y se usa solo como respaldo de view_count."),
        ("videos", "upload_date", "Redundante",
         "Identica a publish_date en el 100% de los registros.",
         "Se conserva; los analisis temporales usan publish_date."),
        ("videos", "owner_handle", "Redundante",
         "Identica a channel_handle en el 100% de los registros.",
         "Se conserva; las etiquetas usan channel_handle."),
        ("videos", "query_hits / keywords / dataset_sources", "Requiere parseo",
         "Listas serializadas como texto (JSON o separadas por '|').",
         "Se convierten a listas reales antes de contar."),
        ("videos", "source_query / source_group", "Uso delicado",
         "Describen el muestreo, no el tema del video.",
         "Se usan para caracterizar cobertura, nunca como etiqueta tematica definitiva."),
        ("videos", "description / description_snippet", "Faltantes",
         f"{int(videos_raw.description.isna().sum())} y "
         f"{int(videos_raw.description_snippet.isna().sum())} nulos respectivamente.",
         "Los conteos de texto de video se calculan sobre los no nulos y se reporta el n."),
        ("videos", "channel_name", "Uso delicado",
         "Nombre visible mutable y potencialmente repetible.",
         "El nodo de canal es channel_id; channel_name solo etiqueta."),
    ]
    return pd.DataFrame(rows, columns=["dataset", "variable", "clasificacion",
                                       "evidencia", "tratamiento"])


def _to_csv(df: pd.DataFrame, path) -> None:
    """Guarda a CSV serializando las columnas que contienen listas."""
    out = df.copy()
    for col in out.columns:
        if out[col].map(lambda x: isinstance(x, (list, tuple))).any():
            out[col] = out[col].map(
                lambda x: json.dumps(list(x), ensure_ascii=False)
                if isinstance(x, (list, tuple)) else x
            )
    out.to_csv(path, index=False, encoding="utf-8")


def _md5(path) -> str:
    import hashlib

    return hashlib.md5(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    run()
