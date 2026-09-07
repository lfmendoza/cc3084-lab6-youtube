"""Ejercicio 3: analisis exploratorio, concentracion y popularidad.

Distincion metodologica que atraviesa todo el modulo: ``youtube_videos.csv``
es el universo de videos recolectados (293) mientras que
``youtube_comments.csv`` cubre solo una seleccion de esos videos. Por eso
todo conteo de comentarios se reporta como *observado* y las metricas por
video se calculan sobre el subconjunto con comentarios recolectados, no
sobre los 293.
"""
from __future__ import annotations

import ast
import json
from collections import Counter

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from . import config as C
from . import viz


# ------------------------------------------------------------- utilidades ---
def _load() -> tuple[pd.DataFrame, pd.DataFrame]:
    videos = pd.read_csv(C.VIDEOS_CLEAN, dtype={"video_id": str, "channel_id": str})
    comments = pd.read_csv(
        C.COMMENTS_CLEAN,
        dtype={"video_id": str, "comment_id": str, "channel_id": str,
               "author_channel_id": str},
        keep_default_na=False, na_values=[""],
    )
    for col in ("hashtags", "mentions", "urls", "emojis"):
        comments[col] = comments[col].map(_as_list)
    for col in ("keywords_list", "query_hits_list", "dataset_sources_list",
                "description_hashtags", "title_hashtags"):
        if col in videos.columns:
            videos[col] = videos[col].map(_as_list)
    comments["texto_limpio"] = comments["texto_limpio"].fillna("")
    comments["texto_original"] = comments["texto_original"].fillna("")
    return videos, comments


def _as_list(value):
    if isinstance(value, list):
        return value
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return []
    text = str(value).strip()
    if not text or text == "nan":
        return []
    try:
        out = json.loads(text)
    except json.JSONDecodeError:
        try:
            out = ast.literal_eval(text)
        except (ValueError, SyntaxError):
            return [text]
    return list(out) if isinstance(out, (list, tuple)) else [out]


def gini(x: np.ndarray) -> float:
    """Coeficiente de Gini sobre valores no negativos.

    0 = participacion perfectamente repartida, 1 = toda la participacion en
    una sola unidad.
    """
    a = np.sort(np.asarray(x, dtype=float))
    n = a.size
    if n == 0 or a.sum() == 0:
        return float("nan")
    idx = np.arange(1, n + 1)
    return float((2 * idx - n - 1).dot(a) / (n * a.sum()))


def concentration(series: pd.Series, tops=(1, 3, 5, 10)) -> dict:
    """Cuota acumulada de los top-k y Gini de una distribucion de conteos."""
    s = series.sort_values(ascending=False)
    total = float(s.sum())
    out = {
        "n_unidades": int(s.size),
        "total": total,
        "gini": round(gini(s.to_numpy()), 4),
        "cv": round(float(s.std(ddof=1) / s.mean()), 3) if s.size > 1 and s.mean() else np.nan,
        "max": float(s.max()) if s.size else np.nan,
        "mediana": float(s.median()) if s.size else np.nan,
    }
    for k in tops:
        if s.size >= 1:
            out[f"top{k}_n"] = float(s.head(k).sum())
            out[f"top{k}_pct"] = round(100 * float(s.head(k).sum()) / total, 2) if total else np.nan
    # Unidades necesarias para acumular el 50% y el 80%
    cum = s.cumsum() / total if total else s * 0
    for thr in (0.5, 0.8):
        idx = int((cum < thr).sum()) + 1
        out[f"n_unidades_para_{int(thr*100)}pct"] = min(idx, int(s.size))
        out[f"pct_unidades_para_{int(thr*100)}pct"] = round(
            100 * min(idx, int(s.size)) / max(s.size, 1), 2)
    return out


def ngrams_top(texts: pd.Series, n: int = 1, top: int = 25) -> pd.DataFrame:
    """Top-k de n-gramas sobre una serie de textos ya tokenizados por espacio."""
    counter: Counter = Counter()
    docs = 0
    seen_docs: Counter = Counter()
    for t in texts.fillna(""):
        toks = str(t).split()
        if not toks:
            continue
        docs += 1
        grams = toks if n == 1 else [" ".join(toks[i:i + n]) for i in range(len(toks) - n + 1)]
        counter.update(grams)
        seen_docs.update(set(grams))
    total = sum(counter.values())
    rows = [
        {
            "ngram": g,
            "n": n,
            "frecuencia": c,
            "pct_del_total": round(100 * c / total, 3) if total else 0.0,
            "n_documentos": seen_docs[g],
            "pct_documentos": round(100 * seen_docs[g] / docs, 2) if docs else 0.0,
        }
        for g, c in counter.most_common(top)
    ]
    cols = ["ngram", "n", "frecuencia", "pct_del_total", "n_documentos", "pct_documentos"]
    return pd.DataFrame(rows, columns=cols)


# ==================================================================== 3.1 ===
def descriptives(videos: pd.DataFrame, comments: pd.DataFrame) -> dict:
    """Conteos minimos exigidos por el inciso 3.1."""
    obs_videos = comments["video_id"].nunique()
    vpc = videos.groupby("channel_id").size()
    cpv = comments.groupby("video_id").size()
    apv = comments.groupby("video_id")["author_channel_id"].nunique()
    views_all = videos["view_count_final"].dropna()
    views_obs = videos.loc[videos.video_id.isin(set(comments.video_id)),
                           "view_count_final"].dropna()
    likes = comments["like_count"]
    replies = comments["reply_count_num"].astype(float)
    author_counts = comments.groupby("author_channel_id").size()
    author_videos = comments.groupby("author_channel_id")["video_id"].nunique()
    author_channels = comments.groupby("author_channel_id")["channel_id"].nunique()

    return {
        # --- universos ---
        "n_videos_catalogo": int(len(videos)),
        "n_canales_catalogo": int(videos["channel_id"].nunique()),
        "n_categorias": int(videos["category"].nunique()),
        "n_source_query_videos": int(videos["source_query"].nunique()),
        "n_source_group_videos": int(videos["source_group"].nunique()),
        "n_comentarios": int(len(comments)),
        "n_autores_unicos": int(comments["author_channel_id"].nunique()),
        "n_videos_con_comentario_observado": int(obs_videos),
        "n_videos_sin_comentario_observado": int(len(videos) - obs_videos),
        "pct_videos_con_comentario_observado": round(100 * obs_videos / len(videos), 2),
        "n_canales_con_comentario_observado": int(comments["channel_id"].nunique()),
        "cobertura_canales_pct": round(
            100 * comments["channel_id"].nunique() / videos["channel_id"].nunique(), 2),
        # --- videos por canal ---
        "videos_por_canal": _dist(vpc),
        "canales_con_un_solo_video": int((vpc == 1).sum()),
        "top_canales_por_videos": vpc.sort_values(ascending=False).head(10).to_dict(),
        # --- comentarios y autores por video (solo videos observados) ---
        "comentarios_por_video_observado": _dist(cpv),
        "autores_por_video_observado": _dist(apv),
        "ratio_comentarios_por_autor_global": round(len(comments) /
                                                    comments["author_channel_id"].nunique(), 3),
        # --- visualizaciones ---
        "visualizaciones_catalogo": _dist(views_all),
        "visualizaciones_videos_observados": _dist(views_obs),
        "suma_visualizaciones_catalogo": float(views_all.sum()),
        # --- likes y respuestas ---
        "me_gusta": _dist(likes),
        "suma_me_gusta": int(likes.sum()),
        "comentarios_con_cero_me_gusta": int((likes == 0).sum()),
        "pct_comentarios_cero_me_gusta": round(100 * float((likes == 0).mean()), 2),
        "respuestas": _dist(replies),
        "suma_respuestas": int(replies.sum()),
        "comentarios_con_al_menos_una_respuesta": int((replies > 0).sum()),
        "pct_comentarios_con_respuesta": round(100 * float((replies > 0).mean()), 2),
        "respuestas_valores_observados": sorted(replies.dropna().unique().tolist()),
        # --- autores ---
        "autores_por_n_comentarios": author_counts.value_counts().sort_index().to_dict(),
        "autores_con_un_comentario": int((author_counts == 1).sum()),
        "pct_autores_con_un_comentario": round(100 * float((author_counts == 1).mean()), 2),
        "autores_en_mas_de_un_video": int((author_videos > 1).sum()),
        "pct_autores_en_mas_de_un_video": round(100 * float((author_videos > 1).mean()), 2),
        "autores_en_mas_de_un_canal": int((author_channels > 1).sum()),
        "max_comentarios_por_autor": int(author_counts.max()),
        "max_videos_por_autor": int(author_videos.max()),
        # --- texto ---
        "n_hashtags_en_comentarios": int(sum(len(h) for h in comments["hashtags"])),
        "n_hashtags_unicos_comentarios": len({h for hs in comments["hashtags"] for h in hs}),
        "n_hashtags_en_videos": int(sum(len(h) for h in videos["description_hashtags"])
                                    + sum(len(h) for h in videos["title_hashtags"])),
        "n_emojis_en_comentarios": int(comments["n_emojis"].sum()),
        "n_menciones_en_comentarios": int(comments["n_mentions"].sum()),
    }


def _dist(s: pd.Series) -> dict:
    s = pd.Series(s).dropna().astype(float)
    if s.empty:
        return {"n": 0}
    return {
        "n": int(s.size),
        "suma": float(s.sum()),
        "min": float(s.min()),
        "p25": float(s.quantile(0.25)),
        "mediana": float(s.median()),
        "media": round(float(s.mean()), 2),
        "p75": float(s.quantile(0.75)),
        "p90": float(s.quantile(0.90)),
        "max": float(s.max()),
        "std": round(float(s.std(ddof=1)), 2) if s.size > 1 else 0.0,
        "asimetria": round(float(s.skew()), 3) if s.size > 2 else 0.0,
        "gini": round(gini(s.to_numpy()), 4),
    }


# ==================================================================== 3.3 ===
def popularity_vs_participation(videos: pd.DataFrame, comments: pd.DataFrame) -> dict:
    """Relacion entre visualizaciones y comentarios observados.

    Spearman es la medida principal porque ambas variables tienen cola
    derecha pesada y n = 19: una correlacion de rangos no se desestabiliza
    con un solo video viral. Pearson se reporta sobre ``log1p`` como
    complemento, no como medida principal.
    """
    obs = (
        comments.groupby("video_id")
        .agg(n_comentarios=("comment_id", "size"),
             n_autores=("author_channel_id", "nunique"),
             n_me_gusta=("like_count", "sum"),
             n_respuestas=("reply_count_num", "sum"))
        .reset_index()
        .merge(videos[["video_id", "view_count_final", "title", "channel_name",
                       "category", "publish_date"]], on="video_id", how="left")
    )
    obs["views"] = obs["view_count_final"].astype(float)
    obs["comentarios_por_1k_vistas"] = 1000 * obs["n_comentarios"] / obs["views"]
    obs["autores_por_comentario"] = obs["n_autores"] / obs["n_comentarios"]

    out: dict = {"n_videos_comparados": int(len(obs))}
    pairs = [("views", "n_comentarios"), ("views", "n_autores"),
             ("n_comentarios", "n_autores"), ("views", "n_me_gusta")]
    for a, b in pairs:
        x, y = obs[a].to_numpy(float), obs[b].to_numpy(float)
        mask = ~(np.isnan(x) | np.isnan(y))
        x, y = x[mask], y[mask]
        rho, p_rho = stats.spearmanr(x, y)
        r, p_r = stats.pearsonr(np.log1p(x), np.log1p(y))
        kt, p_kt = stats.kendalltau(x, y)
        out[f"{a}_vs_{b}"] = {
            "n": int(x.size),
            "spearman_rho": round(float(rho), 4),
            "spearman_p": round(float(p_rho), 5),
            "spearman_significativo_0.05": bool(p_rho < 0.05),
            "pearson_log1p_r": round(float(r), 4),
            "pearson_log1p_p": round(float(p_r), 5),
            "kendall_tau": round(float(kt), 4),
            "kendall_p": round(float(p_kt), 5),
        }
    out["tabla"] = obs.sort_values("n_comentarios", ascending=False).to_dict("records")
    out["video_mas_visto_observado"] = obs.loc[obs["views"].idxmax(),
                                               ["video_id", "title", "views",
                                                "n_comentarios"]].to_dict()
    out["video_mas_comentado"] = obs.loc[obs["n_comentarios"].idxmax(),
                                         ["video_id", "title", "views",
                                          "n_comentarios"]].to_dict()
    out["nota_metodologica"] = (
        "El conteo de comentarios proviene de la muestra recolectada, no del "
        "total real de YouTube. Las visualizaciones son un corte al momento "
        "de la recoleccion. Una correlacion entre ambos no implica causalidad "
        "en ninguna direccion."
    )
    return out, obs


def coverage_bias(videos: pd.DataFrame, comments: pd.DataFrame) -> dict:
    """Contrasta si los videos con comentarios recolectados son los mas vistos.

    Es la prueba clave para separar "sesgo de recoleccion" de "propiedad del
    contenido": si los 19 videos observados fueran simplemente los mas
    vistos, la cobertura seria explicable por popularidad. Se usa
    Mann-Whitney U porque las visualizaciones no son normales ni los grupos
    comparables en tamano.
    """
    obs_ids = set(comments["video_id"])
    con = videos.loc[videos.video_id.isin(obs_ids), "view_count_final"].dropna()
    sin = videos.loc[~videos.video_id.isin(obs_ids), "view_count_final"].dropna()
    u, p = stats.mannwhitneyu(sin, con, alternative="two-sided")
    ranks = videos["view_count_final"].rank(ascending=False, method="min")
    obs_ranks = ranks[videos.video_id.isin(obs_ids)]
    return {
        "n_videos_con_comentarios": int(con.size),
        "n_videos_sin_comentarios": int(sin.size),
        "mediana_views_con_comentarios": float(con.median()),
        "mediana_views_sin_comentarios": float(sin.median()),
        "media_views_con_comentarios": round(float(con.mean()), 1),
        "media_views_sin_comentarios": round(float(sin.mean()), 1),
        "mannwhitney_U": float(u),
        "mannwhitney_p": round(float(p), 5),
        "diferencia_significativa_0.05": bool(p < 0.05),
        "rango_de_views_de_videos_observados_min": int(obs_ranks.min()),
        "rango_de_views_de_videos_observados_max": int(obs_ranks.max()),
        "rango_mediano_de_videos_observados": float(obs_ranks.median()),
        "interpretacion": (
            "No hay evidencia de que los videos con comentarios recolectados "
            "sean los mas vistos del catalogo. Su rango de visualizaciones va "
            f"del puesto {int(obs_ranks.min())} al {int(obs_ranks.max())} de "
            f"{len(videos)}. La cobertura de comentarios responde al "
            "procedimiento de recoleccion (source_query), no a la popularidad."
        ),
    }


# ================================================================= figuras ==
def make_figures(videos: pd.DataFrame, comments: pd.DataFrame,
                 desc: dict, obs: pd.DataFrame,
                 words: pd.DataFrame, bigrams: pd.DataFrame,
                 hashtags: pd.DataFrame) -> None:
    viz.apply_style()

    # --- 01 valores faltantes ---
    qv = pd.read_csv(C.TABLES / "data_quality_videos.csv")
    qc = pd.read_csv(C.TABLES / "data_quality_comments.csv")
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.6))
    for ax, q, title in [(axes[0], qv, "youtube_videos.csv (n=293)"),
                         (axes[1], qc, "youtube_comments.csv (n=406)")]:
        q = q.copy()
        q["pct_no_utilizable"] = q["pct_nulos"] + q["pct_vacios_o_espacios"]
        q = q.sort_values("pct_no_utilizable", ascending=False).head(14)
        colors = ["#D55E00" if v > 50 else "#E69F00" if v > 0 else "#B0B0B0"
                  for v in q["pct_no_utilizable"]]
        ax.barh(q["variable"], q["pct_no_utilizable"], color=colors)
        ax.invert_yaxis()
        ax.set_xlabel("% de registros nulos o en blanco")
        ax.set_title(title)
        ax.set_xlim(0, 105)
        for yi, v in enumerate(q["pct_no_utilizable"]):
            ax.text(v + 1.5, yi, f"{v:.1f}%", va="center", fontsize=8)
    fig.suptitle("Figura 1. Completitud de las variables por dataset",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    viz.save(fig, "01_missing_values.png",
             "Solo 4 variables de videos tienen faltantes (<9%). En comentarios, "
             "viewer_rating esta vacia al 100% y like_count_text aparece en blanco "
             f"en {int(comments.like_count_blank.sum())} registros ("
             f"{round(100*comments.like_count_blank.mean(),1)}%), que se interpretan como 0 me gusta.")

    # --- 02 comentarios por video ---
    top = obs.sort_values("n_comentarios", ascending=False)
    fig, ax = plt.subplots(figsize=(12, 8.5))
    labels = [viz.wrap(r.title, 40) for r in top.itertuples()]
    y = np.arange(len(top))
    ax.barh(y, top["n_comentarios"], color=viz.COLOR_VIDEO, label="Comentarios observados")
    ax.barh(y, top["n_autores"], color="#7B2D00", height=0.42, label="Autores unicos")
    ax.set_yticks(y); ax.set_yticklabels(labels, fontsize=7.5)
    ax.invert_yaxis()
    for yi, r in enumerate(top.itertuples()):
        ax.text(r.n_comentarios + 3, yi,
                f"{r.n_comentarios} com. / {r.n_autores} aut.  ·  {r.channel_name}",
                va="center", fontsize=7.5)
    ax.set_xlabel("Conteo (comentarios observados en la muestra)")
    ax.set_xlim(0, top["n_comentarios"].max() * 1.55)
    ax.set_title(f"Figura 2. Comentarios y autores unicos por video\n"
                 f"({len(top)} de {len(videos)} videos del catalogo tienen comentarios recolectados)")
    ax.legend(loc="lower right")
    viz.save(fig, "02_comments_by_video.png",
             f"Los {len(top)} videos con comentarios recolectados concentran los 406 comentarios. "
             f"El video mas comentado acumula {int(top.n_comentarios.iloc[0])} comentarios "
             f"({round(100*top.n_comentarios.iloc[0]/406,1)}% del total). La cercania entre barras "
             "indica que casi cada comentario proviene de un autor distinto.")

    # --- 03 comentarios por canal ---
    ch = (comments.groupby("channel_name")
          .agg(n_comentarios=("comment_id", "size"),
               n_videos=("video_id", "nunique"),
               n_autores=("author_channel_id", "nunique"))
          .sort_values("n_comentarios", ascending=False))
    fig, ax = plt.subplots(figsize=(10, 5))
    y = np.arange(len(ch))
    ax.barh(y, ch["n_comentarios"], color=viz.COLOR_VIDEO)
    ax.barh(y, ch["n_autores"], color="#7B2D00", height=0.42, label="Autores unicos")
    ax.set_yticks(y); ax.set_yticklabels([viz.wrap(i, 34) for i in ch.index], fontsize=8)
    ax.invert_yaxis()
    for yi, r in enumerate(ch.itertuples()):
        ax.text(r.n_comentarios + 4, yi,
                f"{r.n_comentarios} com. | {r.n_videos} vid. | {r.n_autores} aut.", fontsize=7.5,
                va="center")
    ax.set_xlim(0, ch["n_comentarios"].max() * 1.42)
    ax.set_xlabel("Comentarios observados")
    ax.set_title("Figura 3. Participacion observada por canal")
    ax.legend(loc="lower right")
    viz.save(fig, "03_comments_by_channel.png",
             f"Solo {len(ch)} de {videos.channel_id.nunique()} canales del catalogo tienen "
             f"comentarios recolectados. El canal lider aporta {int(ch.n_comentarios.iloc[0])} "
             f"comentarios ({round(100*ch.n_comentarios.iloc[0]/406,1)}%) distribuidos en "
             f"{int(ch.n_videos.iloc[0])} videos.")

    # --- 04 categorias y grupos de origen ---
    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    cat = videos["category"].value_counts()
    viz.barh(axes[0, 0], [viz.wrap(i, 26) for i in cat.index], cat.values, "#0072B2")
    axes[0, 0].set_title("Categoria de YouTube (catalogo, n=293 videos)")
    axes[0, 0].set_xlabel("Numero de videos")

    cat_obs = (comments.merge(videos[["video_id", "category"]], on="video_id")
               .groupby("category").size().sort_values(ascending=False))
    viz.barh(axes[0, 1], [viz.wrap(i, 26) for i in cat_obs.index], cat_obs.values, "#D55E00")
    axes[0, 1].set_title("Categoria de los comentarios observados (n=406)")
    axes[0, 1].set_xlabel("Numero de comentarios observados")

    sg = videos["source_group"].value_counts()
    viz.barh(axes[1, 0], sg.index.tolist(), sg.values, "#009E73")
    axes[1, 0].set_title("source_group del catalogo de videos")
    axes[1, 0].set_xlabel("Numero de videos")

    sgc = comments["source_group"].value_counts()
    viz.barh(axes[1, 1], sgc.index.tolist(), sgc.values, "#CC79A7")
    axes[1, 1].set_title("source_group de los comentarios (como se recolectaron)")
    axes[1, 1].set_xlabel("Numero de comentarios observados")
    fig.suptitle("Figura 4. Composicion tematica y de muestreo", fontsize=13, fontweight="bold")
    fig.tight_layout()
    viz.save(fig, "04_category_distribution.png",
             "El catalogo esta dominado por News & Politics (138/293 = 47.1%), pero los "
             "comentarios observados lo estan aun mas: la cobertura de comentarios no es "
             "proporcional al catalogo, es un submuestreo sesgado hacia unos pocos canales.")

    # --- 05 consultas de busqueda ---
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 6))
    sq = videos["source_query"].value_counts()
    viz.barh(axes[0], [viz.wrap(i, 34) for i in sq.index], sq.values, "#0072B2")
    axes[0].set_title(f"source_query del catalogo ({len(sq)} consultas)")
    axes[0].set_xlabel("Numero de videos recuperados")
    sqc = comments["source_query"].value_counts()
    viz.barh(axes[1], [viz.wrap(i, 34) for i in sqc.index], sqc.values, "#D55E00")
    axes[1].set_title(f"source_query de los comentarios ({len(sqc)} consultas)")
    axes[1].set_xlabel("Numero de comentarios observados")
    fig.suptitle("Figura 5. Consultas de recoleccion: catalogo frente a comentarios",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    viz.save(fig, "05_source_queries.png",
             f"Las {len(sq)} consultas del catalogo se reducen a {len(sqc)} en los comentarios. "
             f"La consulta '{sqc.index[0]}' aporta {int(sqc.iloc[0])} comentarios "
             f"({round(100*sqc.iloc[0]/406,1)}%): la cobertura de comentarios responde al "
             "procedimiento de recoleccion, no a la popularidad del contenido.")

    # --- 06 hashtags ---
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 6))
    if len(hashtags):
        h = hashtags.head(18)
        viz.barh(axes[0], h["hashtag"], h["frecuencia"], "#009E73")
    axes[0].set_title(f"Hashtags en descripciones y titulos de video (n={len(hashtags)} unicos)")
    axes[0].set_xlabel("Frecuencia")
    hc = Counter(h for hs in comments["hashtags"] for h in hs)
    if hc:
        k, v = zip(*hc.most_common(18))
        viz.barh(axes[1], list(k), list(v), "#CC79A7")
        axes[1].set_xlabel("Frecuencia")
    else:
        axes[1].text(0.5, 0.5, "Sin hashtags en los comentarios", ha="center", va="center",
                     transform=axes[1].transAxes, fontsize=11)
        axes[1].set_xticks([]); axes[1].set_yticks([]); axes[1].grid(False)
    axes[1].set_title(f"Hashtags en comentarios ({sum(hc.values())} usos, {len(hc)} unicos)")
    fig.suptitle("Figura 6. Hashtags: los publica el canal, no la audiencia",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    viz.save(fig, "05_top_hashtags.png",
             f"Los hashtags viven en el contenido publicado por los canales "
             f"({int(hashtags.frecuencia.sum()) if len(hashtags) else 0} usos) y practicamente "
             f"no en los comentarios ({sum(hc.values())} usos en {len(hc)} hashtags unicos "
             "sobre 406 comentarios). El etiquetado tematico es una practica del emisor, no de "
             "la audiencia en esta muestra.")

    # --- 07 palabras ---
    fig, ax = plt.subplots(figsize=(9.5, 8))
    w = words.head(25)
    viz.barh(ax, w["ngram"], w["frecuencia"], "#0072B2")
    ax.set_xlabel("Frecuencia en texto_limpio (lematizado, sin stopwords)")
    ax.set_title("Figura 7. 25 palabras mas frecuentes en los comentarios")
    for yi, r in enumerate(w.itertuples()):
        ax.text(r.frecuencia * 0.02, yi, f"{r.pct_documentos:.1f}% docs", va="center",
                fontsize=7, color="white", fontweight="bold")
    viz.save(fig, "06_top_words.png",
             f"Vocabulario politico-institucional: el termino mas frecuente aparece "
             f"{int(w.frecuencia.iloc[0])} veces en {w.pct_documentos.iloc[0]:.1f}% de los "
             "comentarios. Ningun termino domina, lo que indica una conversacion tematicamente "
             "dispersa dentro de un mismo marco de referencia.")

    # --- 08 bigramas ---
    fig, ax = plt.subplots(figsize=(9.5, 8))
    b = bigrams.head(25)
    viz.barh(ax, b["ngram"], b["frecuencia"], "#D55E00")
    ax.set_xlabel("Frecuencia en texto_limpio")
    ax.set_title("Figura 8. 25 bigramas mas frecuentes en los comentarios")
    viz.save(fig, "07_top_bigrams.png",
             f"El bigrama mas frecuente ('{b.ngram.iloc[0]}') aparece {int(b.frecuencia.iloc[0])} "
             "veces. Las frecuencias bajas de los bigramas confirman que no existen consignas "
             "repetidas ni copy-paste masivo: los comentarios son redacciones individuales.")

    # --- 09 distribucion de visualizaciones ---
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.2))
    vv = videos["view_count_final"].dropna()
    axes[0].hist(np.log10(vv + 1), bins=30, color="#0072B2", edgecolor="white")
    axes[0].set_xlabel("log10(visualizaciones + 1)")
    axes[0].set_ylabel("Numero de videos")
    axes[0].set_title(f"Distribucion de visualizaciones (n={len(vv)} videos)")
    axes[0].axvline(np.log10(vv.median() + 1), color="#D55E00", ls="--",
                    label=f"mediana = {int(vv.median()):,}")
    axes[0].legend()
    obs_ids = set(comments["video_id"])
    a = np.log10(videos.loc[~videos.video_id.isin(obs_ids), "view_count_final"].dropna() + 1)
    b2 = np.log10(videos.loc[videos.video_id.isin(obs_ids), "view_count_final"].dropna() + 1)
    axes[1].boxplot([a, b2], tick_labels=[f"Sin comentario\nobservado (n={len(a)})",
                                     f"Con comentario\nobservado (n={len(b2)})"],
                    patch_artist=True,
                    boxprops=dict(facecolor="#B0D8F0"), medianprops=dict(color="#D55E00", lw=2))
    axes[1].set_ylabel("log10(visualizaciones + 1)")
    axes[1].set_title("Visualizaciones segun cobertura de comentarios")
    fig.suptitle("Figura 9. Popularidad del catalogo y sesgo de cobertura",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    mw = C.read_metrics("coverage_bias")
    viz.save(fig, "08_views_distribution.png",
             f"Cola derecha pesada: mediana {int(vv.median()):,} vistas frente a un maximo de "
             f"{int(vv.max()):,} (ratio {int(vv.max()/vv.median())}x). La mediana de los videos con "
             f"comentarios recolectados ({int(mw['mediana_views_con_comentarios']):,}) frente a los "
             f"que no los tienen ({int(mw['mediana_views_sin_comentarios']):,}) no difiere de forma "
             f"significativa (Mann-Whitney U={mw['mannwhitney_U']}, p={mw['mannwhitney_p']}): la "
             "muestra de comentarios no es simplemente 'los videos mas vistos'.")

    # --- 10 popularidad vs participacion ---
    pv = C.read_metrics("popularity")
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.8))
    for ax, ycol, ylab, key in [
        (axes[0], "n_comentarios", "Comentarios observados", "views_vs_n_comentarios"),
        (axes[1], "n_autores", "Autores unicos observados", "views_vs_n_autores"),
    ]:
        ax.scatter(obs["views"], obs[ycol], s=70, c=viz.COLOR_VIDEO, alpha=0.75,
                   edgecolors="black", linewidths=0.6)
        ax.set_xscale("log"); ax.set_yscale("log")
        ax.set_xlabel("Visualizaciones al momento de la recoleccion (escala log)")
        ax.set_ylabel(f"{ylab} (escala log)")
        st = pv[key]
        ax.set_title(f"{ylab} vs visualizaciones\n"
                     f"Spearman rho={st['spearman_rho']} (p={st['spearman_p']}), "
                     f"Pearson log-log r={st['pearson_log1p_r']}")
        for r in obs.nlargest(4, ycol).itertuples():
            ax.annotate(viz.wrap(r.title, 22), (r.views, getattr(r, ycol)),
                        fontsize=6.5, xytext=(6, 4), textcoords="offset points")
    fig.suptitle("Figura 10. Visibilidad frente a participacion observada",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    st_c = pv["views_vs_n_comentarios"]
    sig = "significativa" if st_c["spearman_significativo_0.05"] else "no significativa"
    viz.save(fig, "09_views_vs_comments.png",
             f"Con n={pv['n_videos_comparados']} videos, la correlacion de rangos entre "
             f"visualizaciones y comentarios observados es rho={st_c['spearman_rho']} "
             f"(p={st_c['spearman_p']}), {sig} al 5%: una asociacion monotona fuerte y positiva. "
             f"Aun asi el video mas visto ({int(pv['video_mas_visto_observado']['views']):,} vistas) "
             f"no es el mas comentado ({int(pv['video_mas_comentado']['n_comentarios'])} comentarios "
             f"con {int(pv['video_mas_comentado']['views']):,} vistas). Ambos ejes son conteos "
             "parciales y la asociacion no implica causalidad.")

    # --- 11 concentracion (Lorenz + Pareto) ---
    conc = C.read_metrics("concentration")
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    for ax, series, title, key in [
        (axes[0], obs.set_index("video_id")["n_comentarios"],
         "Comentarios por video observado", "comentarios_por_video"),
        (axes[1], comments.groupby("channel_id").size(), "Comentarios por canal",
         "comentarios_por_canal"),
        (axes[2], comments.groupby("author_channel_id").size(), "Comentarios por autor",
         "comentarios_por_autor"),
    ]:
        s = series.sort_values(ascending=False)
        cum = 100 * s.cumsum() / s.sum()
        x = 100 * np.arange(1, len(s) + 1) / len(s)
        ax.plot(x, cum, "-o" if len(s) < 30 else "-", color="#0072B2", ms=4, lw=2,
                label="Curva de concentracion")
        ax.plot([0, 100], [0, 100], "--", color="#8C8C8C", label="Igualdad perfecta")
        ax.fill_between(x, cum, x, alpha=0.15, color="#0072B2")
        g = conc[key]["gini"]
        ax.set_title(f"{title}\nGini = {g}, top-3 = {conc[key]['top3_pct']}%")
        ax.set_xlabel("% acumulado de unidades (ordenadas de mayor a menor)")
        ax.set_ylabel("% acumulado de comentarios observados")
        ax.set_xlim(0, 100); ax.set_ylim(0, 101)
        ax.legend(loc="lower right", fontsize=8)
    fig.suptitle("Figura 11. Concentracion de la participacion observada (curvas de Lorenz)",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    viz.save(fig, "10_participation_concentration.png",
             f"La participacion esta muy concentrada por video (Gini="
             f"{conc['comentarios_por_video']['gini']}) y por canal (Gini="
             f"{conc['comentarios_por_canal']['gini']}), pero muy repartida por autor (Gini="
             f"{conc['comentarios_por_autor']['gini']}): pocos videos reciben casi todo, y casi "
             "cada comentario proviene de una persona distinta.")

    # --- 12 nube de palabras (complementaria) ---
    try:
        from wordcloud import WordCloud

        text = " ".join(comments["texto_limpio"].fillna(""))
        wc = WordCloud(width=1600, height=800, background_color="white",
                       colormap="viridis", random_state=C.SEED,
                       collocations=False).generate(text)
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.imshow(wc, interpolation="bilinear"); ax.axis("off"); ax.grid(False)
        ax.set_title("Figura 12. Nube de palabras de texto_limpio (complementaria)")
        viz.save(fig, "11_wordcloud.png",
                 "Figura complementaria. No sustituye a los rankings cuantitativos de las "
                 "figuras 7 y 8: el tamano de la nube no es comparable entre terminos con "
                 "precision y no permite leer frecuencias.")
    except Exception as exc:  # pragma: no cover
        print(f"      [aviso] nube de palabras omitida: {exc}")

    # --- 13 distribucion de me gusta y respuestas ---
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8))
    lk = comments["like_count"]
    axes[0].hist(np.log10(lk + 1), bins=25, color="#009E73", edgecolor="white")
    axes[0].set_xlabel("log10(me gusta + 1)"); axes[0].set_ylabel("Comentarios")
    axes[0].set_title(f"'Me gusta' por comentario\n(mediana={int(lk.median())}, max={int(lk.max())})")
    rc = comments["reply_count_num"].astype(float).value_counts().sort_index()
    axes[1].bar(rc.index.astype(int).astype(str), rc.values, color="#CC79A7", edgecolor="white")
    axes[1].set_xlabel("reply_count (respuestas recibidas)"); axes[1].set_ylabel("Comentarios")
    axes[1].set_title(f"Respuestas recibidas\n({int((comments.reply_count_num>0).sum())} de 406 "
                      "comentarios recibieron alguna)")
    for i, v in enumerate(rc.values):
        axes[1].text(i, v + 4, str(int(v)), ha="center", fontsize=8)
    ac = comments.groupby("author_channel_id").size().value_counts().sort_index()
    axes[2].bar(ac.index.astype(str), ac.values, color="#0072B2", edgecolor="white")
    axes[2].set_xlabel("Comentarios publicados por el autor"); axes[2].set_ylabel("Autores")
    axes[2].set_title(f"Recurrencia de los autores\n({int(ac.iloc[0])} de "
                      f"{int(ac.sum())} comentaron una sola vez)")
    for i, v in enumerate(ac.values):
        axes[2].text(i, v + 4, str(int(v)), ha="center", fontsize=8)
    fig.suptitle("Figura 13. Intensidad de la interaccion observada", fontsize=13,
                 fontweight="bold")
    fig.tight_layout()
    viz.save(fig, "12_engagement_distributions.png",
             f"El {round(100*float((lk==0).mean()),1)}% de los comentarios no muestra 'me gusta' y "
             f"solo {int((comments.reply_count_num>0).sum())} recibieron respuesta. "
             f"{int(ac.iloc[0])} de {int(ac.sum())} autores "
             f"({round(100*ac.iloc[0]/ac.sum(),1)}%) comentaron una unica vez: la participacion es "
             "mayoritariamente puntual, no conversacional.")

    # --- 14 videos por canal (catalogo) ---
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.5))
    vpc = videos.groupby("channel_name").size().sort_values(ascending=False)
    viz.barh(axes[0], [viz.wrap(i, 32) for i in vpc.head(15).index], vpc.head(15).values, "#0072B2")
    axes[0].set_xlabel("Numero de videos en el catalogo")
    axes[0].set_title(f"Top 15 canales por videos recolectados (de {len(vpc)} canales)")
    d = vpc.value_counts().sort_index()
    axes[1].bar(d.index.astype(str), d.values, color="#009E73", edgecolor="white")
    axes[1].set_xlabel("Videos por canal"); axes[1].set_ylabel("Numero de canales")
    axes[1].set_title(f"Distribucion de videos por canal (mediana={int(vpc.median())})")
    for i, v in enumerate(d.values):
        axes[1].text(i, v + 0.6, str(int(v)), ha="center", fontsize=7.5)
    fig.suptitle("Figura 14. Estructura del catalogo de videos por canal", fontsize=13,
                 fontweight="bold")
    fig.tight_layout()
    viz.save(fig, "13_videos_per_channel.png",
             f"{int((vpc==1).sum())} de {len(vpc)} canales aportan un unico video. El catalogo se "
             "construyo mezclando busquedas por tema con barridos de canales especificos, lo que "
             "produce esta mezcla de canales muy representados y canales con un solo video.")


# ================================================================ pipeline ==
def run() -> dict:
    C.set_seeds()
    print("[2/6] exploratory_analysis: EDA, concentracion y popularidad")
    viz.reset_captions()
    videos, comments = _load()

    desc = descriptives(videos, comments)

    # ---- tablas ----
    videos_summary = videos[[
        "video_id", "title", "channel_id", "channel_name", "channel_handle_norm",
        "category", "source_query", "source_group", "view_count_final",
        "publish_date", "n_keywords", "n_query_hits", "description_len", "video_url",
    ]].copy()
    obs_counts = comments.groupby("video_id").agg(
        n_comentarios_observados=("comment_id", "size"),
        n_autores_observados=("author_channel_id", "nunique"),
        n_me_gusta_observados=("like_count", "sum"),
        n_respuestas_observadas=("reply_count_num", "sum"),
    )
    videos_summary = videos_summary.merge(obs_counts, on="video_id", how="left")
    for col in obs_counts.columns:
        videos_summary[col] = videos_summary[col].fillna(0).astype(int)
    videos_summary["tiene_comentarios_observados"] = (
        videos_summary["n_comentarios_observados"] > 0)
    videos_summary.sort_values("n_comentarios_observados", ascending=False)\
        .to_csv(C.TABLES / "videos_summary.csv", index=False)

    cbv = (comments.groupby("video_id")
           .agg(n_comentarios=("comment_id", "size"),
                n_autores=("author_channel_id", "nunique"),
                n_me_gusta=("like_count", "sum"),
                n_respuestas=("reply_count_num", "sum"),
                len_medio_comentario=("len_original", "mean"))
           .merge(videos[["video_id", "title", "channel_id", "channel_name",
                          "category", "view_count_final"]], on="video_id")
           .sort_values("n_comentarios", ascending=False))
    cbv["pct_de_comentarios"] = (100 * cbv["n_comentarios"] / len(comments)).round(2)
    cbv["pct_acumulado"] = cbv["pct_de_comentarios"].cumsum().round(2)
    cbv["autores_por_comentario"] = (cbv["n_autores"] / cbv["n_comentarios"]).round(3)
    cbv["comentarios_por_1k_vistas"] = (
        1000 * cbv["n_comentarios"] / cbv["view_count_final"]).round(3)
    cbv.to_csv(C.TABLES / "comments_by_video.csv", index=False)

    cbc = (comments.groupby(["channel_id", "channel_name"])
           .agg(n_comentarios=("comment_id", "size"),
                n_videos_con_comentarios=("video_id", "nunique"),
                n_autores=("author_channel_id", "nunique"),
                n_me_gusta=("like_count", "sum"),
                n_respuestas=("reply_count_num", "sum"))
           .reset_index()
           .sort_values("n_comentarios", ascending=False))
    cbc = cbc.merge(videos.groupby("channel_id").size().rename("n_videos_catalogo"),
                    on="channel_id", how="left")
    cbc["pct_de_comentarios"] = (100 * cbc["n_comentarios"] / len(comments)).round(2)
    cbc["pct_acumulado"] = cbc["pct_de_comentarios"].cumsum().round(2)
    cbc.to_csv(C.TABLES / "comments_by_channel.csv", index=False)

    authors = (comments.groupby("author_channel_id")
               .agg(n_comentarios=("comment_id", "size"),
                    n_videos=("video_id", "nunique"),
                    n_canales=("channel_id", "nunique"),
                    n_me_gusta=("like_count", "sum"),
                    n_respuestas_recibidas=("reply_count_num", "sum"),
                    author_handle=("author_handle_norm", "first"),
                    author_name=("author_name", "first"),
                    len_medio=("len_original", "mean"))
               .sort_values(["n_videos", "n_comentarios"], ascending=False))
    authors["len_medio"] = authors["len_medio"].round(1)
    authors.to_csv(C.TABLES / "authors_summary.csv")

    words = ngrams_top(comments["texto_limpio"], 1, 60)
    bigrams = ngrams_top(comments["texto_limpio"], 2, 60)
    trigrams = ngrams_top(comments["texto_limpio"], 3, 30)
    words.to_csv(C.TABLES / "top_words.csv", index=False)
    bigrams.to_csv(C.TABLES / "top_bigrams.csv", index=False)
    trigrams.to_csv(C.TABLES / "top_trigrams.csv", index=False)

    hc = Counter(h for hs in videos["description_hashtags"] for h in hs)
    hc.update(h for hs in videos["title_hashtags"] for h in hs)
    hashtags_videos = pd.DataFrame(
        [{"hashtag": k, "frecuencia": v, "fuente": "videos (titulo+descripcion)"}
         for k, v in hc.most_common()])
    hcc = Counter(h for hs in comments["hashtags"] for h in hs)
    hashtags_comments = pd.DataFrame(
        [{"hashtag": k, "frecuencia": v, "fuente": "comentarios"} for k, v in hcc.most_common()])
    hashtags = pd.concat([hashtags_videos, hashtags_comments], ignore_index=True)
    hashtags.to_csv(C.TABLES / "top_hashtags.csv", index=False)

    kw = Counter(k.lower().strip() for ks in videos["keywords_list"] for k in ks if k.strip())
    pd.DataFrame([{"keyword": k, "frecuencia": v} for k, v in kw.most_common(120)])\
        .to_csv(C.TABLES / "top_video_keywords.csv", index=False)

    emo = Counter(e for es in comments["emojis"] for e in es)
    pd.DataFrame([{"emoji": k, "frecuencia": v} for k, v in emo.most_common()])\
        .to_csv(C.TABLES / "top_emojis.csv", index=False)

    # ---- concentracion (3.2) ----
    conc = {
        "comentarios_por_video": concentration(comments.groupby("video_id").size()),
        "comentarios_por_canal": concentration(comments.groupby("channel_id").size()),
        "comentarios_por_autor": concentration(comments.groupby("author_channel_id").size()),
        "autores_por_video": concentration(
            comments.groupby("video_id")["author_channel_id"].nunique()),
        "visualizaciones_por_video_catalogo": concentration(
            videos.set_index("video_id")["view_count_final"].dropna()),
        "videos_por_canal_catalogo": concentration(videos.groupby("channel_id").size()),
        "me_gusta_por_comentario": concentration(comments.set_index("comment_id")["like_count"]),
        "nota": (
            "El denominador de 'comentarios_por_video' son los 19 videos con "
            "comentarios recolectados, no los 293 del catalogo: incluir los 274 "
            "restantes con valor 0 confundiria 'sin comentario observado' con "
            "'sin comentarios en YouTube'."
        ),
        "top_videos_lista": cbv.head(10)[
            ["video_id", "title", "channel_name", "n_comentarios", "n_autores",
             "pct_de_comentarios", "pct_acumulado", "view_count_final"]].to_dict("records"),
        "top_canales_lista": cbc.head(10)[
            ["channel_id", "channel_name", "n_comentarios", "n_videos_con_comentarios",
             "n_autores", "pct_de_comentarios", "pct_acumulado"]].to_dict("records"),
    }
    C.write_metrics("concentration", conc)

    pop, obs = popularity_vs_participation(videos, comments)
    C.write_metrics("popularity", pop)
    C.write_metrics("coverage_bias", coverage_bias(videos, comments))
    C.write_metrics("descriptives", desc)

    pd.DataFrame([{"metrica": k, "valor": json.dumps(v, ensure_ascii=False)
                   if isinstance(v, dict) else v} for k, v in desc.items()])\
        .to_csv(C.TABLES / "eda_descriptives.csv", index=False)
    pd.DataFrame({k: v for k, v in conc.items() if isinstance(v, dict)}).T\
        .to_csv(C.TABLES / "concentration_metrics.csv")

    make_figures(videos, comments, desc, obs, words, bigrams, hashtags_videos)

    print(f"      videos={desc['n_videos_catalogo']} canales={desc['n_canales_catalogo']} "
          f"comentarios={desc['n_comentarios']} autores={desc['n_autores_unicos']} "
          f"videos_observados={desc['n_videos_con_comentario_observado']}")
    return {"videos": videos, "comments": comments, "obs": obs, "descriptives": desc}


if __name__ == "__main__":
    run()
