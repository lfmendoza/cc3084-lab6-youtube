"""Ejercicio 7.5 y 9: caracterizacion de contenido y respuestas a 3.5 / 3.6.

Contenido por comunidad
-----------------------
Se usa TF-IDF a nivel de comunidad en lugar de un modelo de topicos. Con
n=406 comentarios repartidos en comunidades de 6 a 229 documentos, un LDA o
un BERTopic estarian ajustando muchos parametros sobre muy pocos datos y sus
topicos no serian estables. TF-IDF sobre ``texto_limpio``, en cambio,
responde exactamente la pregunta pertinente: que terminos distinguen a esta
comunidad del resto del corpus. Se complementa con las ``keywords`` y los
titulos de los videos, que provienen del emisor y no del comentarista.
"""
from __future__ import annotations

import json
from collections import Counter

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.feature_extraction.text import TfidfVectorizer

from . import config as C
from .exploratory_analysis import _as_list, ngrams_top

LABEL_ORDER = ["NEG", "NEU", "POS"]


def tfidf_by_group(docs: dict[str, list[str]], top: int = 12) -> pd.DataFrame:
    """Terminos distintivos por grupo mediante TF-IDF.

    Cada grupo se concatena en un unico documento. El IDF se calcula sobre el
    conjunto de grupos, de modo que un termino frecuente en todas las
    comunidades (por ejemplo "guatemala") queda penalizado y emergen los
    terminos que **distinguen** a cada comunidad.
    """
    keys = [k for k, v in docs.items() if " ".join(v).strip()]
    if len(keys) < 2:
        return pd.DataFrame(columns=["grupo", "termino", "tfidf", "rango"])
    corpus = [" ".join(docs[k]) for k in keys]
    vec = TfidfVectorizer(sublinear_tf=True, min_df=1, ngram_range=(1, 2),
                          token_pattern=r"(?u)\b\w[\w-]+\b")
    X = vec.fit_transform(corpus)
    vocab = np.array(vec.get_feature_names_out())
    rows = []
    for i, k in enumerate(keys):
        v = X[i].toarray().ravel()
        idx = np.argsort(-v)[:top]
        for rank, j in enumerate(idx, start=1):
            if v[j] > 0:
                rows.append({"grupo": k, "termino": vocab[j],
                             "tfidf": round(float(v[j]), 5), "rango": rank})
    return pd.DataFrame(rows)


def characterize_communities(pred: pd.DataFrame, comments: pd.DataFrame,
                             videos: pd.DataFrame, csummary: pd.DataFrame,
                             partition: dict) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Completa la caracterizacion de cada comunidad (7.5)."""
    video_to_comm = {v: k for k, vs in partition.items() for v in vs}
    cm = comments.copy()
    cm["comunidad"] = cm["video_id"].map(video_to_comm)
    pr = pred.copy()
    pr["comunidad"] = pr["video_id"].map(video_to_comm)

    docs = {k: g["texto_limpio"].fillna("").tolist()
            for k, g in cm.groupby("comunidad")}
    tfidf = tfidf_by_group(docs, top=12)
    tfidf.to_csv(C.TABLES / "community_tfidf_terms.csv", index=False)

    kw_docs = {}
    for k, vs in partition.items():
        vinfo = videos[videos.video_id.isin(vs)]
        kws = [str(x).lower() for lst in vinfo["keywords_list"] for x in _as_list(lst)]
        kws += [str(t).lower() for t in vinfo["title"]]
        kw_docs[k] = kws
    tfidf_kw = tfidf_by_group(kw_docs, top=10)
    tfidf_kw.to_csv(C.TABLES / "community_tfidf_keywords.csv", index=False)

    rows = []
    for _, r in csummary.iterrows():
        cid = f"C{int(r['comunidad'])}"
        sub = cm[cm.comunidad == cid]
        sp = pr[pr.comunidad == cid]
        counts = sp["predicted_label"].value_counts()
        words = ngrams_top(sub["texto_limpio"], 1, 8)
        bigr = ngrams_top(sub["texto_limpio"], 2, 6)
        hts = Counter(h for hs in sub["hashtags"].map(_as_list) for h in hs)
        row = dict(r)
        row["comunidad_id"] = cid
        row["top_terminos_tfidf"] = ", ".join(
            tfidf.loc[tfidf.grupo == cid].nsmallest(8, "rango")["termino"].tolist())
        row["top_keywords_tfidf"] = ", ".join(
            tfidf_kw.loc[tfidf_kw.grupo == cid].nsmallest(6, "rango")["termino"].tolist())
        row["top_palabras"] = ", ".join(
            f"{t} ({n})" for t, n in zip(words["ngram"], words["frecuencia"]))
        row["top_bigramas"] = ", ".join(
            f"{t} ({n})" for t, n in zip(bigr["ngram"], bigr["frecuencia"]))
        row["hashtags_en_comentarios"] = ", ".join(
            f"{k}({v})" for k, v in hts.most_common(6)) or "ninguno"
        row["n_sentimiento"] = int(len(sp))
        for lab in LABEL_ORDER:
            row[f"n_{lab}"] = int(counts.get(lab, 0))
            row[f"pct_{lab}"] = round(100 * float(counts.get(lab, 0)) / max(len(sp), 1), 2)
        row["polaridad_neta"] = round(row["pct_POS"] - row["pct_NEG"], 2)
        row["sentimiento_mayoritario"] = counts.idxmax() if len(counts) else ""
        row["confianza_media_sentimiento"] = round(float(sp["confidence"].mean()), 4) \
            if len(sp) else np.nan
        row["comparable_n_mayor_igual_10"] = bool(len(sp) >= 10)
        row["me_gusta_medianos"] = float(sub["like_count"].median()) if len(sub) else np.nan
        row["longitud_mediana_comentario"] = float(sub["len_original"].median()) \
            if len(sub) else np.nan
        rows.append(row)

    full = pd.DataFrame(rows).sort_values("n_comentarios_observados", ascending=False)
    full.to_csv(C.TABLES / "community_summary.csv", index=False)

    top3 = full[~full.es_singleton].nlargest(3, "n_comentarios_observados")
    detail = {
        "n_comunidades": int(len(full)),
        "n_no_singleton": int((~full.es_singleton).sum()),
        "n_singletons": int(full.es_singleton.sum()),
        "comunidades_analizadas_en_detalle": top3["comunidad_id"].tolist(),
        "justificacion_top3": (
            "Se analizan en detalle las tres comunidades no triviales, que son "
            "todas las que existen: las nueve restantes son singletons "
            "(videos sin audiencia compartida observada) y se reportan pero no "
            "admiten una caracterizacion de comunidad."
        ),
        "detalle": top3.to_dict("records"),
        "resumen_todas": full.to_dict("records"),
        "singletons": full[full.es_singleton][
            ["comunidad_id", "titulos", "canales", "n_comentarios_observados",
             "n_autores_unicos", "pct_NEG", "pct_NEU", "pct_POS", "n_sentimiento"]
        ].to_dict("records"),
    }
    return full, tfidf, detail


# ================================================ preguntas obligatorias 3.5
def answer_mandatory(comments: pd.DataFrame, videos: pd.DataFrame,
                     pred: pd.DataFrame, csummary: pd.DataFrame) -> dict:
    """Respuestas cuantitativas a las seis preguntas del inciso 3.5."""
    conc = C.read_metrics("concentration")
    pop = C.read_metrics("popularity")
    cov = C.read_metrics("coverage_bias")
    topo = C.read_metrics("network_topology")
    cen = C.read_metrics("centrality_summary")
    comm = C.read_metrics("communities")
    sent = C.read_metrics("sentiment")
    per = C.read_metrics("network_peripheral")
    desc = C.read_metrics("descriptives")

    cbv = pd.read_csv(C.TABLES / "comments_by_video.csv", dtype={"video_id": str})
    cbc = pd.read_csv(C.TABLES / "comments_by_channel.csv", dtype={"channel_id": str})
    vp = topo["proyeccion_video_video"]

    q1 = {
        "pregunta": "¿Que videos y canales concentran la mayor participacion observada?",
        "video_top1": cbv.iloc[0][["video_id", "title", "channel_name", "n_comentarios",
                                   "n_autores", "pct_de_comentarios"]].to_dict(),
        "top3_videos_pct": conc["comentarios_por_video"]["top3_pct"],
        "top5_videos_pct": conc["comentarios_por_video"]["top5_pct"],
        "gini_por_video": conc["comentarios_por_video"]["gini"],
        "canal_top1": cbc.iloc[0][["channel_id", "channel_name", "n_comentarios",
                                   "n_videos_con_comentarios", "n_autores",
                                   "pct_de_comentarios"]].to_dict(),
        "top3_canales_pct": conc["comentarios_por_canal"]["top3_pct"],
        "gini_por_canal": conc["comentarios_por_canal"]["gini"],
        "n_videos_para_50pct": conc["comentarios_por_video"]["n_unidades_para_50pct"],
        "n_canales_para_80pct": conc["comentarios_por_canal"]["n_unidades_para_80pct"],
        "gini_por_autor": conc["comentarios_por_autor"]["gini"],
        "top_videos": conc["top_videos_lista"],
        "top_canales": conc["top_canales_lista"],
    }

    ap = topo["proyeccion_autor_autor"]
    q2 = {
        "pregunta": "¿Existen audiencias compartidas entre videos, canales o temas?",
        "n_autores_totales": desc["n_autores_unicos"],
        "n_autores_en_mas_de_un_video": desc["autores_en_mas_de_un_video"],
        "pct_autores_en_mas_de_un_video": desc["pct_autores_en_mas_de_un_video"],
        "n_autores_en_mas_de_un_canal": desc["autores_en_mas_de_un_canal"],
        "aristas_en_proyeccion_video": vp["n_aristas"],
        "aristas_posibles_proyeccion_video": int(vp["n_nodos"] * (vp["n_nodos"] - 1) / 2),
        "densidad_proyeccion_video": vp["densidad"],
        "videos_aislados": per["n_videos_aislados_proyeccion"],
        "pct_videos_aislados": per["pct_videos_aislados_proyeccion"],
        "peso_max_proyeccion_video": C.read_metrics("network_projections")[
            "peso_max_video_projection"],
        "aristas_con_peso_mayor_1": C.read_metrics("network_projections")[
            "aristas_video_projection_peso_mayor_1"],
        "componentes_proyeccion_video": vp["tamanos_componentes"],
        "aristas_proyeccion_autor": ap["n_aristas"],
        "respuesta": (
            f"Si, pero de forma marginal. Solo "
            f"{desc['autores_en_mas_de_un_video']} de {desc['n_autores_unicos']} autores "
            f"({desc['pct_autores_en_mas_de_un_video']}%) comentaron en mas de un video, y "
            f"{desc['autores_en_mas_de_un_canal']} en mas de un canal. Esos autores generan "
            f"{vp['n_aristas']} de las {int(vp['n_nodos']*(vp['n_nodos']-1)/2)} conexiones "
            f"posibles entre videos (densidad {vp['densidad']}), y "
            f"{per['n_videos_aislados_proyeccion']} de {vp['n_nodos']} videos quedan sin "
            "ninguna audiencia compartida observada."
        ),
    }

    q3 = {
        "pregunta": ("¿Que autores funcionan como puentes entre contenidos que de otra "
                     "forma permanecerian separados?"),
        "criterio": (
            "Un autor es puente si al eliminarlo de la red bipartita aumenta el numero de "
            "componentes de la proyeccion video-video. Es una prueba de eliminacion "
            "verificada, no un ranking de grado."
        ),
        "n_autores_puente_verificados": cen["n_autores_puente_verificados"],
        "n_autores_multivideo": cen["n_autores_multivideo"],
        "n_autores_multicanal": cen["n_autores_multicanal"],
        "n_autores_multicomunidad": cen["n_autores_multicomunidad"],
        "autores_puente": cen["autores_puente_verificados"],
        "autores_multivideo_detalle": cen["autores_multivideo"],
        "autores_con_betweenness_positiva": cen["autores_con_betweenness_positiva"],
        "pct_autores_con_betweenness_positiva": cen["pct_autores_con_betweenness_positiva"],
        "top_autores_betweenness": cen["top_autores_betweenness"][:5],
    }

    q4 = {
        "pregunta": ("¿Que temas y sentimientos caracterizan a las principales "
                     "comunidades de participacion?"),
        "n_comunidades": comm["video_projection"]["n_comunidades"],
        "modularidad": comm["video_projection"]["modularidad_ponderada"],
        "n_singletons": comm["video_projection"]["n_singletons"],
        "comunidades": csummary[[
            "comunidad_id", "n_videos", "n_comentarios_observados", "n_autores_unicos",
            "canales", "categorias", "top_terminos_tfidf", "top_bigramas",
            "pct_NEG", "pct_NEU", "pct_POS", "polaridad_neta",
            "sentimiento_mayoritario", "comparable_n_mayor_igual_10",
        ]].to_dict("records"),
        "chi2_sentimiento_por_comunidad": sent["chi2_por_comunidad"],
    }

    q5 = {
        "pregunta": ("¿La visibilidad medida mediante visualizaciones coincide con la "
                     "participacion observada?"),
        "spearman_views_comentarios": pop["views_vs_n_comentarios"],
        "spearman_views_autores": pop["views_vs_n_autores"],
        "video_mas_visto": pop["video_mas_visto_observado"],
        "video_mas_comentado": pop["video_mas_comentado"],
        "sesgo_de_cobertura": cov,
        "gini_visualizaciones_catalogo": conc["visualizaciones_por_video_catalogo"]["gini"],
        "gini_comentarios_por_video": conc["comentarios_por_video"]["gini"],
        "respuesta": (
            f"Coinciden en el orden pero no en el detalle. Sobre los "
            f"{pop['n_videos_comparados']} videos con comentarios recolectados la "
            f"correlacion de rangos es rho={pop['views_vs_n_comentarios']['spearman_rho']} "
            f"(p={pop['views_vs_n_comentarios']['spearman_p']}), fuerte y significativa. "
            f"Sin embargo el video mas visto "
            f"({int(pop['video_mas_visto_observado']['views']):,} vistas) recibio solo "
            f"{int(pop['video_mas_visto_observado']['n_comentarios'])} comentarios "
            f"observados, mientras que el mas comentado "
            f"({int(pop['video_mas_comentado']['n_comentarios'])}) tiene "
            f"{int(pop['video_mas_comentado']['views']):,} vistas: la visibilidad ordena la "
            "participacion pero no la determina."
        ),
    }

    q6 = {
        "pregunta": ("¿Que conclusiones estan limitadas por el procedimiento de "
                     "recoleccion y la cobertura de los datos?"),
        "cobertura_videos_pct": desc["pct_videos_con_comentario_observado"],
        "n_videos_sin_comentario_observado": desc["n_videos_sin_comentario_observado"],
        "cobertura_canales_pct": desc["cobertura_canales_pct"],
        "n_consultas_catalogo": desc["n_source_query_videos"],
        "n_consultas_en_comentarios": len(sent["comparacion_por_consulta"]),
        "consulta_dominante": max(sent["comparacion_por_consulta"], key=lambda d: d["n"]),
        "mannwhitney_cobertura": {k: cov[k] for k in
                                  ["mannwhitney_U", "mannwhitney_p",
                                   "diferencia_significativa_0.05"]},
        "solo_comentarios_principales": (
            "El conjunto contiene unicamente comentarios principales: reply_count "
            "indica que hubo 51 respuestas en total, pero ninguna de ellas esta en "
            "los datos ni se sabe quien las escribio."
        ),
        "limitaciones_clave": [
            f"Solo {desc['n_videos_con_comentario_observado']} de "
            f"{desc['n_videos_catalogo']} videos "
            f"({desc['pct_videos_con_comentario_observado']}%) tienen comentarios "
            "recolectados, y no necesariamente todos los de cada video.",
            f"Una sola consulta ('{max(sent['comparacion_por_consulta'], key=lambda d: d['n'])['grupo']}') "
            f"aporta {max(sent['comparacion_por_consulta'], key=lambda d: d['n'])['n']} de "
            "los 406 comentarios: la estructura de la red refleja el muestreo.",
            "Ningun aislamiento observado puede leerse como aislamiento real en YouTube.",
            "No hay relaciones reply-to entre autores, asi que no se puede reconstruir "
            "ninguna conversacion.",
            "published_text y published_time son relativos al momento de recoleccion.",
            "view_count, like_count y reply_count son cortes temporales, no totales finales.",
        ],
    }
    return {"q1": q1, "q2": q2, "q3": q3, "q4": q4, "q5": q5, "q6": q6}


# ================================================= preguntas adicionales 3.6
def answer_additional(comments: pd.DataFrame, videos: pd.DataFrame,
                      pred: pd.DataFrame, csummary: pd.DataFrame) -> dict:
    """Cinco preguntas que surgen de hallazgos concretos del EDA y de la red."""
    out: dict = {}

    # --- P1: los autores recurrentes, se quedan en un canal o lo atraviesan? ---
    a = comments.groupby("author_channel_id").agg(
        n=("comment_id", "size"), nv=("video_id", "nunique"), nc=("channel_id", "nunique"))
    rec = a[a.n > 1]
    out["p1"] = {
        "pregunta": ("¿Los autores recurrentes participan dentro de un solo canal o "
                     "atraviesan canales?"),
        "motivacion": (
            "El EDA mostro que 46 autores publicaron mas de un comentario pero solo 9 "
            "lo hicieron en mas de un video. La pregunta es si la recurrencia es "
            "fidelidad a un canal o movilidad entre canales."
        ),
        "n_autores_recurrentes": int(len(rec)),
        "pct_autores_recurrentes": round(100 * len(rec) / len(a), 2),
        "recurrentes_en_un_solo_video": int((rec.nv == 1).sum()),
        "pct_recurrentes_en_un_solo_video": round(100 * float((rec.nv == 1).mean()), 2),
        "recurrentes_en_un_solo_canal": int((rec.nc == 1).sum()),
        "pct_recurrentes_en_un_solo_canal": round(100 * float((rec.nc == 1).mean()), 2),
        "recurrentes_multicanal": int((rec.nc > 1).sum()),
        "max_canales_por_autor": int(a.nc.max()),
        "respuesta": (
            f"La recurrencia es abrumadoramente intra-video. De {len(rec)} autores con "
            f"mas de un comentario, {int((rec.nv == 1).sum())} "
            f"({round(100*float((rec.nv==1).mean()),1)}%) los publicaron todos en el mismo "
            f"video y {int((rec.nc == 1).sum())} "
            f"({round(100*float((rec.nc==1).mean()),1)}%) dentro de un solo canal. Solo "
            f"{int((rec.nc > 1).sum())} autores atraviesan canales, con un maximo de "
            f"{int(a.nc.max())} canales distintos. En esta muestra 'comentar mas' significa "
            "insistir en el mismo hilo, no seguir a varios emisores."
        ),
    }

    # --- P2: mas respuestas implica mas diversidad de autores? ---
    g = comments.groupby("video_id").agg(
        n_com=("comment_id", "size"), n_aut=("author_channel_id", "nunique"),
        n_rep=("reply_count_num", "sum"), likes=("like_count", "sum")).reset_index()
    g["diversidad"] = g.n_aut / g.n_com
    r1, p1 = stats.spearmanr(g.n_rep, g.n_aut)
    r2, p2 = stats.spearmanr(g.n_rep, g.diversidad)
    r3, p3 = stats.spearmanr(g.n_com, g.diversidad)
    out["p2"] = {
        "pregunta": ("¿Los videos con mas respuestas tienen tambien mayor diversidad "
                     "de autores?"),
        "motivacion": (
            "reply_count no permite construir aristas, pero si mide cuanta conversacion "
            "genero cada comentario. Si mas respuestas vinieran con mas autores distintos, "
            "la conversacion seria colectiva; si no, seria un puado de hilos aislados."
        ),
        "n": int(len(g)),
        "spearman_respuestas_vs_autores": {"rho": round(float(r1), 4),
                                           "p": round(float(p1), 5),
                                           "significativo": bool(p1 < 0.05)},
        "spearman_respuestas_vs_diversidad": {"rho": round(float(r2), 4),
                                              "p": round(float(p2), 5),
                                              "significativo": bool(p2 < 0.05)},
        "spearman_comentarios_vs_diversidad": {"rho": round(float(r3), 4),
                                               "p": round(float(p3), 5),
                                               "significativo": bool(p3 < 0.05)},
        "total_respuestas": int(g.n_rep.sum()),
        "videos_con_respuestas": int((g.n_rep > 0).sum()),
        "diversidad_media": round(float(g.diversidad.mean()), 4),
        "diversidad_min": round(float(g.diversidad.min()), 4),
        "tabla": g.sort_values("n_rep", ascending=False).to_dict("records"),
        "respuesta": (
            f"El numero absoluto de respuestas crece con el numero de autores "
            f"(rho={round(float(r1),3)}, p={round(float(p1),5)}), pero la *diversidad* "
            f"relativa (autores unicos por comentario) se relaciona negativamente con el "
            f"volumen (rho={round(float(r3),3)}, p={round(float(p3),5)}): en los videos mas "
            "comentados hay proporcionalmente mas autores que repiten. Aun asi la "
            f"diversidad media es {round(float(g.diversidad.mean()),3)}, muy cerca de 1: "
            "casi cada comentario proviene de una persona distinta."
        ),
    }

    # --- P3: la consulta de recoleccion determina la estructura de comunidades? ---
    part = json.loads((C.NETWORKS / "video_partition.json").read_text(encoding="utf-8"))
    v2c = {v: k for k, vs in part.items() for v in vs}
    vv = videos[videos.video_id.isin(v2c)].copy()
    vv["comunidad"] = vv["video_id"].map(v2c)
    ct = pd.crosstab(vv["source_query"], vv["comunidad"])
    multi = ct.gt(0).sum(axis=1)
    from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

    labs_q = pd.factorize(vv["source_query"])[0]
    labs_c = pd.factorize(vv["comunidad"])[0]
    out["p3"] = {
        "pregunta": ("¿Que consultas de recoleccion recuperaron contenido perteneciente "
                     "a multiples comunidades, y hasta que punto la consulta determina "
                     "la comunidad?"),
        "motivacion": (
            "source_query describe el muestreo, no el tema. Si cada comunidad "
            "correspondiera exactamente a una consulta, las 'comunidades' serian un "
            "artefacto del procedimiento de recoleccion y no una estructura de audiencia."
        ),
        "n_consultas_con_videos_comentados": int(ct.shape[0]),
        "consultas_en_varias_comunidades": multi[multi > 1].to_dict(),
        "n_consultas_en_varias_comunidades": int((multi > 1).sum()),
        "nmi_consulta_vs_comunidad": round(
            float(normalized_mutual_info_score(labs_q, labs_c)), 4),
        "ari_consulta_vs_comunidad": round(float(adjusted_rand_score(labs_q, labs_c)), 4),
        "tabla_cruzada": ct.to_dict(),
        "nota_metricas": (
            "NMI y ARI miden lo mismo de forma distinta: el NMI no corrige por "
            "azar y se infla cuando una de las particiones tiene muchos grupos "
            "pequenos (aqui, 9 singletons de 12 comunidades). El ARI si corrige "
            "por azar, por lo que es la cifra a la que hay que atender."
        ),
        "respuesta": (
            f"De las {int(ct.shape[0])} consultas que recuperaron videos con comentarios, "
            f"{int((multi > 1).sum())} aparecen en mas de una comunidad. La concordancia "
            f"entre consulta y comunidad es NMI="
            f"{round(float(normalized_mutual_info_score(labs_q, labs_c)),3)} pero ARI="
            f"{round(float(adjusted_rand_score(labs_q, labs_c)),3)}. El ARI, que corrige "
            "por azar, es bajo: la particion en comunidades NO es una relectura de la "
            "consulta de recoleccion. El NMI resulta alto solo porque la particion tiene "
            "9 singletons, y una particion muy fragmentada comparte informacion con casi "
            "cualquier etiquetado. La conclusion es que las comunidades responden a "
            "audiencia compartida y no al muestreo, aunque el muestreo determina que "
            "agrupamientos pueden llegar a observarse."
        ),
    }

    # --- P4: sentimiento y longitud/aprobacion del comentario ---
    kw = {lab: pred[pred.predicted_label == lab] for lab in LABEL_ORDER}
    h_len, p_len = stats.kruskal(*[kw[l]["len_original"].dropna() for l in LABEL_ORDER])
    h_lk, p_lk = stats.kruskal(*[kw[l]["like_count"].dropna() for l in LABEL_ORDER])
    r_lk, p_rlk = stats.spearmanr(pred["prob_POS"], pred["like_count"])
    out["p4"] = {
        "pregunta": ("¿El sentimiento del comentario se asocia con su longitud y con los "
                     "'me gusta' que recibe?"),
        "motivacion": (
            "El 61.6% de los comentarios se clasifico como negativo. Vale preguntar si la "
            "negatividad viene acompanada de textos mas largos (mas argumentacion) y de "
            "mas o menos aprobacion de otros usuarios."
        ),
        "longitud_mediana_por_clase": {l: float(kw[l]["len_original"].median())
                                       for l in LABEL_ORDER},
        "kruskal_longitud": {"H": round(float(h_len), 4), "p": round(float(p_len), 6),
                             "significativo": bool(p_len < 0.05)},
        "me_gusta_mediana_por_clase": {l: float(kw[l]["like_count"].median())
                                       for l in LABEL_ORDER},
        "me_gusta_medio_por_clase": {l: round(float(kw[l]["like_count"].mean()), 2)
                                     for l in LABEL_ORDER},
        "kruskal_me_gusta": {"H": round(float(h_lk), 4), "p": round(float(p_lk), 6),
                             "significativo": bool(p_lk < 0.05)},
        "spearman_probPOS_vs_me_gusta": {"rho": round(float(r_lk), 4),
                                         "p": round(float(p_rlk), 6),
                                         "significativo": bool(p_rlk < 0.05)},
        "n_por_clase": {l: int(len(kw[l])) for l in LABEL_ORDER},
        "respuesta": (
            f"Si, en las dos direcciones. Los comentarios negativos son los mas largos "
            f"(mediana {float(kw['NEG']['len_original'].median()):.0f} caracteres frente a "
            f"{float(kw['POS']['len_original'].median()):.0f} de los positivos y "
            f"{float(kw['NEU']['len_original'].median()):.0f} de los neutros; Kruskal-Wallis "
            f"H={round(float(h_len),1)}, p={round(float(p_len),6)}), pero reciben menos "
            f"aprobacion: mediana de {float(kw['NEG']['like_count'].median()):.0f} 'me gusta' "
            f"frente a {float(kw['POS']['like_count'].median()):.0f} de los positivos "
            f"(H={round(float(h_lk),1)}, p={round(float(p_lk),6)}). La critica se argumenta "
            "mas y se premia menos en esta muestra."
        ),
    }

    # --- P5: la visibilidad predice la posicion en la red de audiencia compartida? ---
    vc = pd.read_csv(C.TABLES / "video_centrality.csv", dtype={"raw_id": str})
    vc["view_count"] = pd.to_numeric(vc["view_count"], errors="coerce")
    m = vc.dropna(subset=["view_count"])
    r_d, p_d = stats.spearmanr(m["view_count"], m["degree"])
    r_b, p_b = stats.spearmanr(m["view_count"], m["betweenness_ponderada"])
    r_s, p_s = stats.spearmanr(m["n_comentarios_observados"], m["degree"])
    out["p5"] = {
        "pregunta": ("¿Las visualizaciones de un video predicen su posicion en la red de "
                     "audiencia compartida?"),
        "motivacion": (
            "Un video muy visto podria atraer audiencia de muchos otros contenidos y "
            "quedar central en la proyeccion video-video. Si no ocurre, el papel "
            "estructural de un video no se deduce de su popularidad."
        ),
        "n": int(len(m)),
        "spearman_views_vs_degree": {"rho": round(float(r_d), 4), "p": round(float(p_d), 5),
                                     "significativo": bool(p_d < 0.05)},
        "spearman_views_vs_betweenness": {"rho": round(float(r_b), 4),
                                          "p": round(float(p_b), 5),
                                          "significativo": bool(p_b < 0.05)},
        "spearman_comentarios_vs_degree": {"rho": round(float(r_s), 4),
                                           "p": round(float(p_s), 5),
                                           "significativo": bool(p_s < 0.05)},
        "video_mas_visto": m.nlargest(1, "view_count")[
            ["raw_id", "display_name", "view_count", "degree",
             "betweenness_ponderada"]].to_dict("records"),
        "video_mas_central": m.nlargest(1, "betweenness_ponderada")[
            ["raw_id", "display_name", "view_count", "degree",
             "betweenness_ponderada"]].to_dict("records"),
        "respuesta": (
            f"No de forma significativa. Con n={len(m)}, la correlacion de rangos entre "
            f"visualizaciones y grado en la proyeccion es rho={round(float(r_d),3)} "
            f"(p={round(float(p_d),4)}) y con betweenness rho={round(float(r_b),3)} "
            f"(p={round(float(p_b),4)}). El video mas visto de la muestra "
            f"({m.nlargest(1,'view_count').display_name.iloc[0]}, "
            f"{int(m.view_count.max()):,} vistas) tiene grado "
            f"{int(m.nlargest(1,'view_count').degree.iloc[0])}, mientras que el mas central "
            f"es {m.nlargest(1,'betweenness_ponderada').display_name.iloc[0]}. El numero de "
            f"comentarios observados si predice el grado (rho={round(float(r_s),3)}, "
            f"p={round(float(p_s),4)}): la posicion estructural depende de la participacion "
            "recolectada, no de la visibilidad."
        ),
    }
    return out


# ================================================= reporte del modelo (md) ==
def write_model_report(sent: dict, csummary: pd.DataFrame) -> None:
    """Genera ``results/model/sentiment_model_report.md``."""
    m = sent["modelo"]
    pc = sent["pct_por_clase"]
    cc = sent["conteo_por_clase"]

    def ex_block(items, show_pos=True):
        out = []
        for e in items:
            txt = str(e["texto_original"]).replace("\n", " ").strip()
            txt = (txt[:300] + "...") if len(txt) > 300 else txt
            pos = f" · posicion en confianza: **{e['posicion_en_confianza']}**" \
                if show_pos and "posicion_en_confianza" in e else ""
            out.append(
                f"- **{e['predicted_label']}** (confianza {e['confidence']:.3f}; "
                f"NEG {e['prob_NEG']:.2f} / NEU {e['prob_NEU']:.2f} / "
                f"POS {e['prob_POS']:.2f}){pos}\n"
                f"  > {txt}\n"
                f"  <br>Video: *{e['video_title']}*"
            )
        return "\n".join(out)

    comp_c = sent["comparacion_por_canal"]
    comp_m = sent["comparacion_por_comunidad"]
    comp_v = sent["comparacion_por_video"]

    def table(rows, keycol, label, min_n=10):
        head = ("| Grupo | n | % NEG | % NEU | % POS | Polaridad neta | Confianza media |"
                " Comparable (n>=10) |\n|---|---:|---:|---:|---:|---:|---:|:--:|")
        body = []
        for r in sorted(rows, key=lambda d: -d["n"]):
            g = str(r.get(keycol) or r["grupo"])
            g = (g[:52] + "...") if len(g) > 55 else g
            body.append(
                f"| {g} | {r['n']} | {r['pct_NEG']} | {r['pct_NEU']} | {r['pct_POS']} | "
                f"{r['polaridad_neta']:+.1f} | {r['confianza_media']} | "
                f"{'si' if r['comparable_n_mayor_igual_10'] else 'NO'} |")
        return head + "\n" + "\n".join(body)

    chi_c, chi_m, chi_v = (sent["chi2_por_canal"], sent["chi2_por_comunidad"],
                           sent["chi2_por_video"])

    md = f"""# Reporte del modelo de analisis de sentimiento

**Laboratorio 6 — CC3084 Data Science — Analisis de redes sociales (YouTube)**
Documento generado automaticamente por `src/content_analysis.py` a partir de
`results/metrics/sentiment.json`. Fecha de ejecucion (UTC):
`{m['fecha_ejecucion_utc']}`.

---

## 1. Identificacion exacta del modelo

| Campo | Valor |
|---|---|
| Identificador en Hugging Face | `{m['model_id']}` |
| Familia / arquitectura | {', '.join(m['arquitectura'])} (`model_type = {m['model_type']}`) |
| Clase de modelo cargada | `{m['model_class']}` |
| Numero de parametros | {m['n_parametros']:,} |
| Capas ocultas / hidden size | {m['n_capas']} / {m['hidden_size']} |
| Tokenizer | `{m['tokenizer_class']}`, vocabulario de {m['tokenizer_vocab_size']:,} tokens |
| Framework | {m['framework']} |
| Version de `transformers` | {m['transformers_version']} |
| Version de `torch` | {m['torch_version']} |
| Python / plataforma | {m['python']} / {m['plataforma']} |
| Dispositivo de inferencia | `{m['device']}` (CUDA disponible: {m['cuda_disponible']}) |
| Semilla | {m['seed']} |
| Tiempo de inferencia | {m['segundos_de_inferencia']} s para {sent['n_comentarios_evaluados']} comentarios ({m['comentarios_por_segundo']} comentarios/s) |

## 2. Motivo de la seleccion

Se necesitaba clasificar polaridad en comentarios de YouTube escritos en
espanol de Guatemala: textos cortos, con ortografia libre, emojis, ironia y
lexico local. Se eligio `{m['model_id']}` por cuatro razones concretas:

1. **Es un modelo especifico de espanol.** RoBERTuito se preentreno desde cero
   sobre texto en espanol, no como una de cien lenguas dentro de un modelo
   multilingue. Su vocabulario no compite con otros idiomas.
2. **Su dominio de preentrenamiento coincide con el de los datos.** Se
   entreno sobre aproximadamente 500 millones de tweets en espanol. Los
   comentarios de YouTube comparten con los tweets la brevedad, los emojis y
   la escritura informal.
3. **Fue afinado explicitamente para polaridad** con el corpus TASS 2020,
   que es un corpus academico de sentimiento en espanol con variantes
   dialectales de America Latina y Espana.
4. **Devuelve tres clases interpretables con probabilidades**, lo que permite
   reportar distribucion, confianza y casos ambiguos sin inventar umbrales.

### 2.1 Por que es adecuado para el espanol

RoBERTuito **no es un modelo multilingue adaptado**: se preentreno desde cero
sobre un corpus exclusivamente en espanol, y su tokenizador BPE se aprendio
sobre ese mismo corpus. Tres consecuencias practicas para estos datos:

* **El vocabulario no compite con otros idiomas.** En un mBERT o un XLM-R, el
  presupuesto de subpalabras se reparte entre mas de cien lenguas, de modo que
  el espanol se segmenta en piezas mas cortas y menos informativas. Aqui las
  palabras frecuentes del corpus (*diputado*, *pueblo*, *corrupto*) tienden a
  ser tokens unicos o de pocas piezas.
* **Cubre la morfologia flexiva del espanol.** Conjugaciones, enclisis
  (*deportarlos*, *verlos*) y diminutivos (*almuercitos*, que aparece en los
  datos) estan representados en el preentrenamiento.
* **El corpus de afinado es de espanol y dialectalmente diverso.** TASS 2020
  incluye variantes de Espana, Mexico, Peru, Uruguay y Costa Rica, lo que
  reduce (sin eliminar) el desajuste con el espanol de Guatemala. Su limitacion
  para el lexico guatemalteco se documenta en la seccion 11.

### 2.2 Por que es adecuado para texto de redes sociales

Su corpus de preentrenamiento son ~500 millones de **tweets**, no noticias ni
resenas ni Wikipedia. Los comentarios de YouTube comparten con los tweets las
propiedades que rompen a un modelo entrenado en texto formal:

| Propiedad del texto | Presencia en estos datos | Por que importa |
|---|---|---|
| Brevedad | longitud mediana de 96,5 caracteres | Un modelo de documentos largos depende de contexto que aqui no existe |
| Emojis | 199 emojis en 61 de 406 comentarios | El modelo los vio en entrenamiento como texto normalizado |
| Ortografia libre | *ba* por *va*, *tube* por *tuve*, *corrpcion* | Reduce los tokens fuera de vocabulario |
| Mayusculas expresivas y puntuacion repetida | frecuentes | Se conservan como senal, no se normalizan a la baja |
| Menciones y hashtags | 5 y 1 comentarios respectivamente | Tienen token generico propio en el preentrenamiento |
| Alargamientos y risa | *jajajaja*, repeticiones de vocales | Normalizados igual que en entrenamiento |

Esto no elimina el salto de dominio: sigue habiendo diferencia entre Twitter de
2020 y YouTube, y esa limitacion se declara en la seccion 11.

### 2.3 Alternativas descartadas y por que

| Alternativa | Motivo del descarte |
|---|---|
| TextBlob | Su analizador de polaridad es un lexico de ingles. Aplicado a espanol, la mayoria de los tokens quedaria fuera de diccionario y produciria polaridad 0 por ausencia de vocabulario, no por neutralidad del texto. No es una medicion. |
| VADER (`nltk.sentiment`) | Mismo problema: el lexico y las reglas de intensificacion son de ingles. Esta bien disenado para redes sociales, pero en ingles. |
| Diccionarios de sentimiento en espanol (p. ej. ML-SentiCon) | Son lexicos de palabra aislada: no modelan negacion ("no me gusta"), ni ironia, ni el contexto de la oracion. Serviria como respaldo, no como metodo principal. |
| Modelos multilingues genericos (mBERT, XLM-R sin afinar para sentimiento) | Requeririan afinado propio y no hay datos etiquetados de este dominio para hacerlo ni para validarlo. |

## 3. Etiquetas y su significado

| Etiqueta | id interno | Significado operativo |
|---|---|---|
{chr(10).join(f"| `{lab}` | {[k for k, v in m['id2label'].items() if v == lab][0]} | {sent['significado_clases'][lab]} |" for lab in ['NEG', 'NEU', 'POS'])}

El mapeo de etiquetas se toma directamente de `model.config.id2label`
(`{json.dumps(m['id2label'], ensure_ascii=False)}`); no se reordena ni se
renombra manualmente.

## 4. Preprocesamiento y texto de entrada

**Se usa `texto_original`, no `texto_limpio`.** La razon es metodologica: la
version tematica elimina mayusculas, puntuacion, emojis y stopwords, y
precisamente esos elementos portan senal de polaridad. "NO me gusta" y "me
gusta" son identicos tras quitar stopwords, pero opuestos en sentimiento.

Sobre `texto_original` se aplica la normalizacion que el modelo vio en
entrenamiento (equivalente a `pysentimiento.preprocessing.preprocess_tweet`,
reimplementada en `src/text_processing.py::preprocess_for_sentiment` para no
fijar una version antigua de `transformers`):

| Paso | Transformacion | Motivo |
|---|---|---|
| Menciones | `@usuario` | El modelo vio ese token generico; el nombre concreto no aporta polaridad. |
| URL | `url` | Igual que arriba. |
| Hashtags | se quita el `#`, se conserva la palabra | La palabra si es contenido. |
| Emojis | descripcion en espanol entre delimitadores `emoji ... emoji` | Es la representacion vista en entrenamiento (`emoji.demojize(language="es")`). |
| Repeticiones | mas de 3 caracteres iguales se acortan a 3 | Reduce variantes fuera de vocabulario. |
| Risa | `jajajaja` -> `jaja` | Normalizacion vista en entrenamiento. |
| Case, puntuacion, negaciones | **se conservan** | Son senal de polaridad. |

## 5. Configuracion de inferencia

| Parametro | Valor |
|---|---|
| `max_length` | {m['max_length_usado']} tokens (limite del tokenizer: {m['model_max_length_tokenizer']}) |
| `truncation` | {m['truncation']} |
| `padding` | {m['padding']} |
| `batch_size` | {m['batch_size']} |
| Modo | {m['modo']} |
| Determinismo | {m['determinismo']} |

## 6. Distribucion de clases obtenida

Sobre los **{sent['n_comentarios_evaluados']} comentarios**
({sent['cobertura_pct']}% de cobertura: ningun comentario quedo sin
prediccion):

| Clase | n | % |
|---|---:|---:|
| NEG | {cc['NEG']} | {pc['NEG']} |
| NEU | {cc['NEU']} | {pc['NEU']} |
| POS | {cc['POS']} | {pc['POS']} |
| **Total** | **{sent['n_comentarios_evaluados']}** | **100.0** |

Clase mayoritaria: **{sent['clase_mayoritaria']}**. Polaridad neta global
(%POS - %NEG): **{sent['polaridad_neta_global']:+.2f} puntos porcentuales**.

## 7. Confianza de las predicciones

| Metrica | Valor |
|---|---|
| Confianza media | {sent['confianza_media']} |
| Confianza mediana | {sent['confianza_mediana']} |
| Rango intercuartil | {sent['confianza_p25']} - {sent['confianza_p75']} |
| Confianza minima | {sent['confianza_min']} |
| Predicciones con confianza < 0.5 | {sent['n_confianza_menor_0.5']} ({sent['pct_confianza_menor_0.5']}%) |
| Predicciones con margen < 0.2 | {sent['n_margen_menor_0.2']} ({sent['pct_margen_menor_0.2']}%) |
| Entropia media de la distribucion | {sent['entropia_media']} |

Confianza media por clase:
{chr(10).join(f"- `{k}`: {v}" for k, v in sent['confianza_media_por_clase'].items())}

> **Advertencia.** {sent['advertencia_confianza']}

## 8. Comparaciones por grupo

Se reporta el `n` de cada grupo y se marca explicitamente si es comparable
(n >= 10). Los grupos pequenos se muestran pero no se interpretan: un
porcentaje sobre 2 comentarios no es una estimacion.

### 8.1 Por canal

{table(comp_c, 'grupo_label', 'canal')}

Prueba chi-cuadrado de independencia (solo canales con n >= 10):
chi2 = {chi_c.get('chi2')}, gl = {chi_c.get('gl')}, p = {chi_c.get('p_valor')},
V de Cramer = {chi_c.get('v_de_cramer')}
({chi_c.get('grupos_incluidos')} canales, n = {chi_c.get('n_incluido')}).
{chi_c.get('advertencia_validez')}

### 8.2 Por comunidad de la proyeccion video-video

{table(comp_m, 'grupo_label', 'comunidad')}

Chi-cuadrado (comunidades con n >= 10): chi2 = {chi_m.get('chi2')},
gl = {chi_m.get('gl')}, p = {chi_m.get('p_valor')},
V de Cramer = {chi_m.get('v_de_cramer')}. {chi_m.get('advertencia_validez')}

### 8.3 Por video (solo los comparables)

{table([r for r in comp_v if r['comparable_n_mayor_igual_10']], 'grupo_label', 'video')}

Chi-cuadrado (videos con n >= 10): chi2 = {chi_v.get('chi2')},
gl = {chi_v.get('gl')}, p = {chi_v.get('p_valor')},
V de Cramer = {chi_v.get('v_de_cramer')}. {chi_v.get('advertencia_validez')}

### 8.4 Asociacion con metricas de interaccion

| Clase | 'Me gusta' mediana | 'Me gusta' media | Longitud mediana (car.) | % con emoji |
|---|---:|---:|---:|---:|
{chr(10).join(f"| {lab} | {sent['me_gusta_mediana_por_clase'][lab]:.0f} | {sent['me_gusta_medio_por_clase'][lab]} | {sent['longitud_mediana_por_clase'][lab]:.0f} | {sent['pct_con_emoji_por_clase'][lab]} |" for lab in ['NEG', 'NEU', 'POS'])}

## 9. Ejemplos representativos

{sent['ejemplos']['criterio']}

### Negativos
{ex_block(sent['ejemplos']['NEG'])}

### Neutros
{ex_block(sent['ejemplos']['NEU'])}

### Positivos
{ex_block(sent['ejemplos']['POS'])}

## 10. Casos ambiguos

Los seis comentarios con menor confianza del corpus. Sirven para calibrar
cuanto peso admite una prediccion individual:

{ex_block(sent['ejemplos']['casos_ambiguos_global'], show_pos=False)}

La inspeccion de estos casos muestra el patron esperado: fallan la ironia
("Ay ricos shucos en la calle jajaja", clasificado NEG con 0.44 de
confianza), el sarcasmo citado entre comillas, las expresiones de una sola
palabra sin contexto ("Mantenidos") y el lexico guatemalteco no presente en
el corpus de entrenamiento ("shucos", "tambo", "moronga", "ba" por "va").

## 11. Limitaciones

| Limitacion | Como se manifiesta en estos datos |
|---|---|
| **Sarcasmo e ironia** | El modelo clasifica la superficie lexica. "Ay ricos shucos en la calle jajaja" es una burla, pero recibe NEG con confianza 0.44. |
| **Slang y variacion dialectal** | Terminos guatemaltecos ("shucos", "moronga", "tambo", "chapin") no estan en el vocabulario de TASS ni son frecuentes en el preentrenamiento. |
| **Ortografia no normativa** | "ba" por "va", "artan" por "hartan", "tube" por "tuve", "corrpcion". Aumentan los tokens fuera de vocabulario. |
| **Lenguaje mixto** | Aparecen fragmentos en ingles dentro de comentarios en espanol; el modelo no esta entrenado para code-switching. |
| **Emojis** | Se traducen a texto, pero su valor pragmatico (un emoji de risa puede marcar burla, no alegria) no se recupera. |
| **Negacion y alcance** | Los transformers manejan la negacion mejor que un lexico, pero siguen fallando en oraciones largas con negacion distante. |
| **Nombres propios** | Nombres de politicos e instituciones aparecen en contextos criticos; el modelo puede asociar la entidad con la polaridad en lugar de la predicacion sobre ella. |
| **Contexto ausente** | Un comentario responde a un video que el modelo no ve. "Este hombre esta loco" es ininterpretable sin saber de quien se habla. |
| **Comentarios muy cortos** | La longitud minima observada es de 1 caracter. Con menos de cinco tokens la prediccion es poco informativa. |
| **Domain shift** | Entrenado en tweets (2020, TASS), aplicado a comentarios de YouTube. Comparten registro pero no plataforma ni epoca. |
| **Truncamiento** | Los comentarios de mas de {m['max_length_usado']} tokens se truncan; el comentario mas largo tiene 1 525 caracteres. |
| **Error del modelo** | No se dispone de un conjunto etiquetado a mano de este dominio, asi que **no se puede reportar exactitud ni F1 sobre estos datos**. Las cifras de esta seccion describen la distribucion de las predicciones, no su correccion. |
| **Tres clases, no intensidad** | El modelo no mide cuan negativo es un comentario. La confianza no es intensidad. |

## 12. Referencia

- Model card: <https://huggingface.co/pysentimiento/robertuito-sentiment-analysis>
- Perez, J. M., Furman, D. A., Alonso Alemany, L. y Luque, F. (2022).
  *RoBERTuito: a pre-trained language model for social media text in Spanish*.
  LREC 2022. <https://aclanthology.org/2022.lrec-1.785/>
- Perez, J. M., Giudici, J. C. y Luque, F. (2021). *pysentimiento: A Python
  Toolkit for Sentiment Analysis and SocialNLP tasks*.
  <https://arxiv.org/abs/2106.09462>
- Corpus de afinado: TASS 2020, Task 1 (polaridad a nivel de tweet en
  espanol). <http://tass.sepln.org/>

## 13. Advertencia final

> **La prediccion del modelo no equivale a la intencion real del autor.**
> {sent['advertencia_intencion']}
>
> Cada etiqueta es una inferencia estadistica sobre la superficie del texto,
> producida por un clasificador entrenado en otro corpus, sin acceso al video
> comentado, al hilo de conversacion ni al contexto cultural del autor. Las
> distribuciones agregadas de este reporte son descripciones de lo que el
> modelo predijo sobre {sent['n_comentarios_evaluados']} comentarios
> recolectados, no una medicion del estado de animo de ninguna poblacion.
"""
    path = C.MODEL_DIR / "sentiment_model_report.md"
    path.write_text(md, encoding="utf-8")
    (C.MODEL_DIR / "sentiment_model_metadata.json").write_text(
        json.dumps(m, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


# ================================================================== pipeline
def run() -> dict:
    C.set_seeds()
    print("[5/6] content_analysis: TF-IDF por comunidad, preguntas 3.5 y 3.6")
    comments = pd.read_csv(
        C.COMMENTS_CLEAN,
        dtype={"video_id": str, "comment_id": str, "channel_id": str,
               "author_channel_id": str},
        keep_default_na=False, na_values=[""])
    comments["texto_limpio"] = comments["texto_limpio"].fillna("")
    for col in ("like_count", "reply_count_num", "len_original"):
        comments[col] = pd.to_numeric(comments[col], errors="coerce")
    videos = pd.read_csv(C.VIDEOS_CLEAN, dtype={"video_id": str, "channel_id": str})
    videos["keywords_list"] = videos["keywords_list"].map(_as_list)
    pred = pd.read_csv(C.TABLES / "sentiment_predictions.csv",
                       dtype={"video_id": str, "comment_id": str, "channel_id": str})
    csummary_in = pd.read_csv(C.TABLES / "community_summary.csv")
    partition = json.loads((C.NETWORKS / "video_partition.json").read_text(encoding="utf-8"))

    csummary, tfidf, comm_detail = characterize_communities(
        pred, comments, videos, csummary_in, partition)

    mandatory = answer_mandatory(comments, videos, pred, csummary)
    additional = answer_additional(comments, videos, pred, csummary)

    C.write_metrics("community_characterization", comm_detail)
    C.write_metrics("questions_mandatory", mandatory)
    C.write_metrics("questions_additional", additional)

    sent = C.read_metrics("sentiment")
    path = write_model_report(sent, csummary)

    pd.DataFrame([{"pregunta_id": k, "pregunta": v["pregunta"],
                   "respuesta": v.get("respuesta", "ver results/metrics")}
                  for k, v in {**mandatory, **additional}.items()]).to_csv(
        C.TABLES / "questions_answers.csv", index=False)

    print(f"      comunidades caracterizadas: {len(csummary)} | "
          f"terminos TF-IDF: {len(tfidf)} | reporte del modelo: {path.name}")
    return {"community_summary": csummary, "mandatory": mandatory,
            "additional": additional, "tfidf": tfidf}


if __name__ == "__main__":
    run()
