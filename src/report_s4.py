"""Secciones 6 y 7 del informe: preguntas obligatorias (3.5) y adicionales (3.6)."""
from __future__ import annotations

from .report_text import Ctx, fmt, pct, trunc


def preguntas_obligatorias(c: Ctx) -> list:
    q = c.m("questions_mandatory")
    cen = c.m("centrality_summary")
    cs = c.t("community_summary")

    els: list = [
        ("h1", "6. Preguntas obligatorias del inciso 3.5"),
        ("p",
         "Las seis preguntas se responden por separado y con evidencia cuantitativa. "
         "Algunas requieren resultados de las secciones 8 a 12 (redes, comunidades, "
         "centralidad y sentimiento); en esos casos se anticipa la cifra y se remite a la "
         "seccion donde se deriva."),
        ("h2", "6.1 ¿Que videos y canales concentran la mayor participacion observada?"),
    ]
    q1 = q["q1"]
    els += [
        ("p",
         f"**Videos.** «{q1['video_top1']['title']}» del canal "
         f"{q1['video_top1']['channel_name']} concentra "
         f"{fmt(q1['video_top1']['n_comentarios'])} comentarios de "
         f"{fmt(q1['video_top1']['n_autores'])} autores, es decir "
         f"{pct(q1['video_top1']['pct_de_comentarios'])} de todos los comentarios del "
         f"conjunto. Los tres videos mas comentados suman "
         f"{pct(q1['top3_videos_pct'])} y los cinco primeros "
         f"{pct(q1['top5_videos_pct'])}. Bastan "
         f"{fmt(q1['n_videos_para_50pct'])} videos para acumular la mitad de la "
         f"participacion (Gini = {fmt(q1['gini_por_video'], 4)})."),
        ("p",
         f"**Canales.** {q1['canal_top1']['channel_name']} reune "
         f"{fmt(q1['canal_top1']['n_comentarios'])} comentarios "
         f"({pct(q1['canal_top1']['pct_de_comentarios'])}) de "
         f"{fmt(q1['canal_top1']['n_autores'])} autores distintos, repartidos en "
         f"{fmt(q1['canal_top1']['n_videos_con_comentarios'])} videos. Los tres primeros "
         f"canales acumulan {pct(q1['top3_canales_pct'])} y bastan "
         f"{fmt(q1['n_canales_para_80pct'])} canales para el 80 % "
         f"(Gini = {fmt(q1['gini_por_canal'], 4)})."),
        ("p",
         f"**Matiz necesario.** La concentracion por contenido conviene contrastarla con la "
         f"del autor: el Gini por autor es de solo {fmt(q1['gini_por_autor'], 4)}. La "
         "participacion se concentra en pocos videos y pocos canales, pero se reparte entre "
         "muchisimas personas. Ademas, parte de esta concentracion es un artefacto del "
         "muestreo: el canal lider fue objeto de un barrido especifico de canal "
         "(`@quorumgt/videos`), lo que garantiza que aporte muchos comentarios "
         "independientemente de su volumen real de conversacion."),
        ("h2", "6.2 ¿Existen audiencias compartidas entre videos, canales o temas?"),
    ]
    q2 = q["q2"]
    els += [
        ("p", f"**Si, pero de forma marginal.** " + q2["respuesta"].split("Si, pero de forma marginal. ")[-1]),
        ("table", "Tabla 27. Magnitud de la audiencia compartida observada",
         ["Metrica", "Valor"],
         [["Autores totales", fmt(q2["n_autores_totales"])],
          ["Autores que comentaron en mas de un video",
           f"{fmt(q2['n_autores_en_mas_de_un_video'])} "
           f"({pct(q2['pct_autores_en_mas_de_un_video'])})"],
          ["Autores que comentaron en mas de un canal",
           fmt(q2["n_autores_en_mas_de_un_canal"])],
          ["Aristas en la proyeccion video-video",
           f"{fmt(q2['aristas_en_proyeccion_video'])} de "
           f"{fmt(q2['aristas_posibles_proyeccion_video'])} posibles"],
          ["Densidad de la proyeccion video-video", fmt(q2["densidad_proyeccion_video"], 4)],
          ["Peso maximo de una arista (autores compartidos)",
           fmt(q2["peso_max_proyeccion_video"])],
          ["Aristas con mas de un autor compartido", fmt(q2["aristas_con_peso_mayor_1"])],
          ["Videos sin audiencia compartida observada",
           f"{fmt(q2['videos_aislados'])} ({pct(q2['pct_videos_aislados'])})"],
          ["Aristas en la proyeccion autor-autor", fmt(q2["aristas_proyeccion_autor"])],
          ["Componentes de la proyeccion video-video",
           ", ".join(fmt(x) for x in q2["componentes_proyeccion_video"])]]),
        ("p",
         f"El contraste entre las dos proyecciones es ilustrativo. La de autores tiene "
         f"{fmt(q2['aristas_proyeccion_autor'])} aristas, un numero enorme, pero eso no "
         "indica audiencias entrelazadas: son las cliques que la proyeccion crea "
         "mecanicamente dentro de cada video (si 128 personas comentan el mismo video, la "
         "proyeccion las une a todas entre si). La cifra que si informa sobre audiencia "
         f"compartida es la de la proyeccion video-video: {fmt(q2['aristas_en_proyeccion_video'])} "
         f"aristas, todas de peso 1 o {fmt(q2['peso_max_proyeccion_video'])}, y "
         f"{fmt(q2['videos_aislados'])} videos sin ninguna conexion."),
        ("p",
         "En cuanto a temas, la audiencia compartida se da casi enteramente **dentro** del "
         "mismo campo tematico. Las tres comunidades detectadas (seccion 11) agrupan videos "
         "de politica nacional, comunicacion de gobierno y regulacion economica; los cruces "
         "entre esos bloques son los que sostienen los 7 autores puente."),
        ("h2", "6.3 ¿Que autores funcionan como puentes entre contenidos que de otra forma "
                "permanecerian separados?"),
    ]
    q3 = q["q3"]
    els += [
        ("p", f"**Criterio.** {q3['criterio']}"),
        ("p",
         f"De los {fmt(q2['n_autores_totales'])} autores, "
         f"{fmt(q3['n_autores_multivideo'])} comentaron en mas de un video, "
         f"{fmt(q3['n_autores_multicanal'])} en mas de un canal, "
         f"{fmt(q3['n_autores_multicomunidad'])} en mas de una comunidad, y "
         f"**{fmt(q3['n_autores_puente_verificados'])} superan la prueba de eliminacion**. "
         f"Solo {fmt(q3['autores_con_betweenness_positiva'])} autores "
         f"({pct(q3['pct_autores_con_betweenness_positiva'])}) tienen intermediacion "
         "positiva en la proyeccion autor-autor: el resto pertenece a una unica clique de "
         "video y no esta en el camino entre nada."),
        ("table", "Tabla 28. Autores puente verificados por prueba de eliminacion",
         ["Handle", "Com.", "Videos", "Canales", "Comunidades", "Δ componentes",
          "Aristas perdidas", "Canales que conecta"],
         [[r["author_handle"], fmt(r["n_comentarios"]), fmt(r["n_videos_distintos"]),
           fmt(r["n_canales_distintos"]), fmt(r["n_comunidades_video_tocadas"]),
           f"+{fmt(r['delta_componentes_al_eliminar'])}",
           fmt(r["aristas_video_perdidas_al_eliminar"]), trunc(r["canales"], 46)]
          for r in q3["autores_puente"]]),
        ("p",
         "La tabla se lee asi: al retirar a ese autor de la red bipartita y recalcular la "
         "proyeccion video-video, el numero de componentes conexas **aumenta** en la "
         "cantidad indicada. Es decir, esa persona era el unico vinculo observado entre dos "
         "grupos de contenido. Es una propiedad estructural verificada, no una lectura de "
         "un ranking."),
        ("callout",
         "**Que significa y que no significa ser «puente» aqui.** Significa que esa cuenta "
         "publico comentarios observados en videos que ninguna otra cuenta recolectada "
         "comento a la vez. No significa que difunda informacion entre comunidades, ni que "
         "tenga influencia, ni que conozca a nadie. Y su condicion de puente es fragil por "
         "construccion: depende de que no se hayan recolectado otros comentarios que "
         "sostendrian la misma conexion. Con una recoleccion mas completa, es probable que "
         "varios de estos puentes dejaran de ser unicos."),
        ("pagebreak",),
        ("h2", "6.4 ¿Que temas y sentimientos caracterizan a las principales comunidades "
                "de participacion?"),
    ]
    q4 = q["q4"]
    nt = cs[~cs.es_singleton].nlargest(3, "n_comentarios_observados")
    els += [
        ("p",
         f"Louvain ponderado sobre la proyeccion video-video devuelve "
         f"{fmt(q4['n_comunidades'])} comunidades (Q = {q4['modularidad']}), de las cuales "
         f"{fmt(q4['n_singletons'])} son singletons. Las tres no triviales, que son todas "
         "las que existen, se caracterizan asi:"),
        ("table", "Tabla 29. Caracterizacion tematica y afectiva de las tres comunidades",
         ["Com.", "Videos", "Com. obs.", "Autores", "Canales", "Terminos TF-IDF distintivos",
          "% NEG", "% NEU", "% POS", "Polaridad neta"],
         [[r.comunidad_id, fmt(r.n_videos), fmt(r.n_comentarios_observados),
           fmt(r.n_autores_unicos), trunc(r.canales, 30),
           trunc(r.top_terminos_tfidf, 44), pct(r.pct_NEG), pct(r.pct_NEU),
           pct(r.pct_POS), f"{r.polaridad_neta:+.1f}"] for r in nt.itertuples()]),
        ("p",
         f"**C0 — Critica al Congreso y a la corrupcion institucional** "
         f"({fmt(nt.n_videos.iloc[0])} videos, {fmt(nt.n_comentarios_observados.iloc[0])} "
         f"comentarios, {fmt(nt.n_autores_unicos.iloc[0])} autores). Sus terminos "
         f"distintivos son *{nt.top_terminos_tfidf.iloc[0]}* y sus bigramas incluyen "
         f"«pueblo pagar», «pagar sueldo» y «pacto corrupto». Es la comunidad mas negativa "
         f"del conjunto ({pct(nt.pct_NEG.iloc[0])} NEG, polaridad neta "
         f"{nt.polaridad_neta.iloc[0]:+.1f}) y agrupa periodismo de investigacion con "
         "noticias de sucesos."),
        ("p",
         f"**C1 — Comunicacion del Ejecutivo** ({fmt(nt.n_videos.iloc[1])} videos, "
         f"{fmt(nt.n_comentarios_observados.iloc[1])} comentarios, "
         f"{fmt(nt.n_autores_unicos.iloc[1])} autores). Terminos distintivos: "
         f"*{nt.top_terminos_tfidf.iloc[1]}*, con «presidente bernardo» y «bernardo "
         f"arevalo» como bigramas dominantes. Es la menos negativa de las tres "
         f"({pct(nt.pct_NEG.iloc[1])} NEG frente a {pct(nt.pct_POS.iloc[1])} POS, polaridad "
         f"neta {nt.polaridad_neta.iloc[1]:+.1f}): conviven el apoyo explicito («apoyo "
         "presidente») con la impaciencia («bla bla»)."),
        ("p",
         f"**C2 — Regulacion economica y movilidad urbana** ({fmt(nt.n_videos.iloc[2])} "
         f"videos, {fmt(nt.n_comentarios_observados.iloc[2])} comentarios, "
         f"{fmt(nt.n_autores_unicos.iloc[2])} autores). Terminos distintivos: "
         f"*{nt.top_terminos_tfidf.iloc[2]}*, con «ley competencia» y «libre mercado». Es "
         f"la comunidad mas pequena y la de vocabulario mas especifico; su polaridad neta es "
         f"{nt.polaridad_neta.iloc[2]:+.1f} con {pct(nt.pct_POS.iloc[2])} de comentarios "
         "positivos, la proporcion mas alta de las tres."),
        ("p",
         f"La diferencia de composicion de sentimiento entre comunidades es "
         f"estadisticamente significativa: chi-cuadrado = "
         f"{q4['chi2_sentimiento_por_comunidad']['chi2']}, "
         f"gl = {q4['chi2_sentimiento_por_comunidad']['gl']}, "
         f"p = {q4['chi2_sentimiento_por_comunidad']['p_valor']}, V de Cramer = "
         f"{q4['chi2_sentimiento_por_comunidad']['v_de_cramer']}, sobre las "
         f"{fmt(q4['chi2_sentimiento_por_comunidad']['grupos_incluidos'])} comunidades con "
         f"n ≥ 10. "
         f"{q4['chi2_sentimiento_por_comunidad']['advertencia_validez']}"),
        ("h2", "6.5 ¿La visibilidad medida mediante visualizaciones coincide con la "
                "participacion observada?"),
        ("p", q["q5"]["respuesta"]),
        ("p",
         f"Hay que anadir dos precisiones. Primera: el Gini de visualizaciones del catalogo "
         f"({fmt(q['q5']['gini_visualizaciones_catalogo'], 4)}) es mucho mayor que el de "
         f"comentarios por video ({fmt(q['q5']['gini_comentarios_por_video'], 4)}), es "
         "decir, la visibilidad esta mas concentrada que la participacion. Segunda: los "
         "videos con comentarios recolectados no son los mas vistos del catalogo "
         f"(Mann-Whitney p = {q['q5']['sesgo_de_cobertura']['mannwhitney_p']}), de modo que "
         "la relacion observada entre visibilidad y participacion se estima sobre un "
         "subconjunto que no fue elegido por popularidad. Eso es bueno para la validez "
         "interna de la comparacion y malo para su generalizacion."),
        ("h2", "6.6 ¿Que conclusiones estan limitadas por el procedimiento de recoleccion "
                "y la cobertura de los datos?"),
        ("p",
         "Esta pregunta se responde en detalle en la seccion 16. En terminos de las "
         "conclusiones concretas de este informe, las mas afectadas son:"),
        ("bullets", [
            f"**Cualquier afirmacion sobre volumen de participacion.** Solo "
            f"{pct(q['q6']['cobertura_videos_pct'])} de los videos tiene comentarios "
            f"recolectados y no necesariamente todos los de cada video. La frase «este "
            "video recibio 161 comentarios» debe leerse siempre como «se recolectaron 161 "
            "comentarios de este video».",
            f"**La estructura de la red.** Una sola consulta "
            f"(`{q['q6']['consulta_dominante']['grupo']}`) aporta "
            f"{fmt(q['q6']['consulta_dominante']['n'])} de los 406 comentarios. La "
            "fragmentacion medida, el numero de componentes y la identidad de los puentes "
            "son propiedades de la muestra tanto como del fenomeno.",
            "**Todo aislamiento.** Un video sin audiencia compartida en estos datos puede "
            "tenerla en YouTube; solo se sabe que no se observo.",
            f"**Cualquier reconstruccion de conversacion.** {q['q6']['solo_comentarios_principales']}",
            "**Toda comparacion temporal.** `published_text` y `published_time` son "
            "relativos y redondeados por YouTube; no hay fecha absoluta de comentario.",
            "**Toda cifra de popularidad o aprobacion.** `view_count`, `like_count` y "
            "`reply_count` son cortes al momento de la recoleccion, no totales finales.",
        ]),
        ("pagebreak",),
    ]
    return els


def preguntas_adicionales(c: Ctx) -> list:
    a = c.m("questions_additional")
    els: list = [
        ("h1", "7. Preguntas adicionales del inciso 3.6"),
        ("p",
         "Las cinco preguntas de esta seccion surgieron de hallazgos concretos del analisis "
         "exploratorio y de la red, no de una lista generica. Cada una se motiva con el "
         "hallazgo que la origina y se responde con una prueba estadistica."),
    ]
    titles = {
        "p1": "7.1", "p2": "7.2", "p3": "7.3", "p4": "7.4", "p5": "7.5",
    }
    for key, num in titles.items():
        v = a[key]
        els.append(("h2", f"{num} {v['pregunta']}"))
        els.append(("p", f"*Por que surge:* {v['motivacion']}"))
        els.append(("p", f"**Respuesta.** {v['respuesta']}"))
        els.append(("table", f"Evidencia de la pregunta {num}", ["Metrica", "Valor"],
                    _evidence_rows(v)))
    els.append(("pagebreak",))
    return els


def _evidence_rows(v: dict) -> list:
    skip = {"pregunta", "motivacion", "respuesta", "tabla", "tabla_cruzada",
            "nota_metricas", "consultas_en_varias_comunidades"}
    rows = []
    for k, val in v.items():
        if k in skip:
            continue
        if isinstance(val, dict):
            if {"rho", "p"} <= set(val):
                rows.append([_lab(k),
                             f"rho = {val['rho']}, p = {val['p']}, "
                             f"{'significativo' if val['significativo'] else 'no significativo'}"])
            elif {"H", "p"} <= set(val):
                rows.append([_lab(k),
                             f"H = {val['H']}, p = {val['p']}, "
                             f"{'significativo' if val['significativo'] else 'no significativo'}"])
            else:
                rows.append([_lab(k), ", ".join(f"{kk}: {fmt(vv, 1)}"
                                                for kk, vv in val.items())])
        elif isinstance(val, list):
            if val and isinstance(val[0], dict):
                continue
            rows.append([_lab(k), ", ".join(str(x) for x in val)])
        else:
            rows.append([_lab(k), fmt(val, 3) if isinstance(val, float) else fmt(val)])
    return rows[:14]


def _lab(k: str) -> str:
    return k.replace("_", " ").replace("spearman", "Spearman").replace(
        "kruskal", "Kruskal-Wallis").replace("pct", "%").capitalize()
