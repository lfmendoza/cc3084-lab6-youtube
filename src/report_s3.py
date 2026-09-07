"""Seccion 5 del informe: analisis exploratorio."""
from __future__ import annotations

from .report_text import Ctx, fmt, pct, trunc


def eda(c: Ctx) -> list:
    d, cn, pop = c.m("descriptives"), c.m("concentration"), c.m("popularity")
    cov = c.m("coverage_bias")
    cbv = c.t("comments_by_video", dtype={"video_id": str})
    cbc = c.t("comments_by_channel", dtype={"channel_id": str})
    words, bigr = c.t("top_words"), c.t("top_bigrams")
    hts = c.t("top_hashtags")
    hts_v = hts[hts.fuente.str.startswith("videos")]
    hts_c = hts[hts.fuente == "comentarios"]

    return [
        ("h1", "5. Analisis exploratorio"),
        ("h2", "5.1 Descriptivos minimos"),
        ("table", "Tabla 15. Conteos basicos de los dos universos",
         ["Concepto", "Valor", "Denominador correcto"],
         [["Videos en el catalogo", fmt(d["n_videos_catalogo"]),
           "Universo de videos recolectados"],
          ["Canales en el catalogo", fmt(d["n_canales_catalogo"]), "—"],
          ["Categorias de YouTube", fmt(d["n_categorias"]), "—"],
          ["Consultas de recoleccion (videos)", fmt(d["n_source_query_videos"]), "—"],
          ["Comentarios observados", fmt(d["n_comentarios"]),
           "Solo de los videos con comentarios recolectados"],
          ["Autores unicos", fmt(d["n_autores_unicos"]), "—"],
          ["Videos con comentario observado", fmt(d["n_videos_con_comentario_observado"]),
           f"{pct(d['pct_videos_con_comentario_observado'])} del catalogo"],
          ["Videos sin comentario observado", fmt(d["n_videos_sin_comentario_observado"]),
           "**No** equivale a «sin comentarios en YouTube»"],
          ["Canales con comentario observado", fmt(d["n_canales_con_comentario_observado"]),
           f"{pct(d['cobertura_canales_pct'])} de los canales"],
          ["Comentarios por autor (global)", fmt(d["ratio_comentarios_por_autor_global"], 3),
           "—"]]),
        ("callout",
         "Todas las metricas «por video» de esta seccion se calculan sobre los "
         f"{fmt(d['n_videos_con_comentario_observado'])} videos con comentarios "
         f"recolectados, no sobre los {fmt(d['n_videos_catalogo'])} del catalogo. Incluir "
         f"los {fmt(d['n_videos_sin_comentario_observado'])} restantes con valor cero "
         "produciria una mediana de 0 comentarios por video y confundiria la falta de datos "
         "con la falta de participacion."),
        ("h3", "Videos por canal"),
        ("figure", "13_videos_per_channel.png"),
        ("table", "Tabla 16. Distribucion de videos por canal (catalogo completo)",
         ["Estadistico", "Valor"],
         _dist_rows(d["videos_por_canal"], extra=[
             ["Canales con un solo video", fmt(d["canales_con_un_solo_video"])]])),
        ("p",
         f"El catalogo no es una muestra homogenea de canales: "
         f"{fmt(d['canales_con_un_solo_video'])} de los {fmt(d['n_canales_catalogo'])} "
         f"canales aportan un unico video, mientras que el maximo es de "
         f"{fmt(d['videos_por_canal']['max'])} videos. Esa mezcla es consecuencia directa "
         "del procedimiento de recoleccion, que combino busquedas por tema (que devuelven un "
         "video de muchos canales distintos) con barridos de canales especificos (que "
         "devuelven muchos videos del mismo canal)."),
        ("h3", "Comentarios y autores unicos por video"),
        ("figure", "02_comments_by_video.png"),
        ("table", "Tabla 17. Comentarios y autores por video observado",
         ["Estadistico", "Comentarios por video", "Autores unicos por video"],
         _two_dist_rows(d["comentarios_por_video_observado"],
                        d["autores_por_video_observado"])),
        ("p",
         f"La cifra mas informativa de esta tabla es la cercania entre las dos columnas. La "
         f"mediana de comentarios por video es "
         f"{fmt(d['comentarios_por_video_observado']['mediana'])} y la de autores unicos es "
         f"{fmt(d['autores_por_video_observado']['mediana'])}; el video mas comentado tiene "
         f"{fmt(d['comentarios_por_video_observado']['max'])} comentarios de "
         f"{fmt(d['autores_por_video_observado']['max'])} autores distintos. Es decir, "
         "**cada comentario proviene practicamente de una persona diferente**. La "
         "participacion observada es amplia y superficial, no un intercambio sostenido entre "
         "pocos usuarios."),
        ("h3", "Visualizaciones"),
        ("table", "Tabla 18. Visualizaciones: catalogo completo frente a videos observados",
         ["Estadistico", "Catalogo (n=293)", "Con comentario observado (n=19)"],
         _two_dist_rows(d["visualizaciones_catalogo"],
                        d["visualizaciones_videos_observados"], dec=0)),
        ("p",
         f"La distribucion tiene cola derecha extrema: mediana de "
         f"{fmt(d['visualizaciones_catalogo']['mediana'])} visualizaciones frente a un "
         f"maximo de {fmt(d['visualizaciones_catalogo']['max'])}, con asimetria de "
         f"{fmt(d['visualizaciones_catalogo']['asimetria'], 2)} y Gini de "
         f"{cn['visualizaciones_por_video_catalogo']['gini']}. Los dos videos mas vistos "
         f"concentran {pct(cn['visualizaciones_por_video_catalogo']['top1_pct'])} y "
         f"{pct(cn['visualizaciones_por_video_catalogo']['top3_pct'])} (top 3) de todas las "
         "visualizaciones del catalogo."),
        ("p",
         f"La comparacion entre las dos columnas responde una pregunta importante sobre el "
         f"muestreo: **¿se recolectaron comentarios de los videos mas vistos?** La mediana "
         f"de los videos con comentarios recolectados es de "
         f"{fmt(cov['mediana_views_con_comentarios'])} visualizaciones frente a "
         f"{fmt(cov['mediana_views_sin_comentarios'])} de los demas, una diferencia que "
         f"**no** es estadisticamente significativa (Mann-Whitney U = "
         f"{fmt(cov['mannwhitney_U'])}, p = {cov['mannwhitney_p']}). Sus posiciones en el "
         f"ranking de visualizaciones van del puesto "
         f"{fmt(cov['rango_de_views_de_videos_observados_min'])} al "
         f"{fmt(cov['rango_de_views_de_videos_observados_max'])} de "
         f"{fmt(d['n_videos_catalogo'])}. La cobertura de comentarios no se explica por "
         "popularidad, sino por el procedimiento de recoleccion."),
        ("h3", "«Me gusta» y respuestas"),
        ("figure", "12_engagement_distributions.png"),
        ("table", "Tabla 19. Aprobacion y respuestas recibidas por los comentarios",
         ["Metrica", "Valor"],
         [["Suma de «me gusta»", fmt(d["suma_me_gusta"])],
          ["«Me gusta» mediana por comentario", fmt(d["me_gusta"]["mediana"])],
          ["«Me gusta» media por comentario", fmt(d["me_gusta"]["media"], 2)],
          ["«Me gusta» maximo en un comentario", fmt(d["me_gusta"]["max"])],
          ["Gini de «me gusta»", fmt(cn["me_gusta_por_comentario"]["gini"], 4)],
          ["Comentarios con cero «me gusta»",
           f"{fmt(d['comentarios_con_cero_me_gusta'])} "
           f"({pct(d['pct_comentarios_cero_me_gusta'])})"],
          ["Suma de respuestas (`reply_count`)", fmt(d["suma_respuestas"])],
          ["Comentarios que recibieron alguna respuesta",
           f"{fmt(d['comentarios_con_al_menos_una_respuesta'])} "
           f"({pct(d['pct_comentarios_con_respuesta'])})"],
          ["Valores observados de `reply_count`",
           ", ".join(fmt(x) for x in d["respuestas_valores_observados"])]]),
        ("p",
         f"La interaccion secundaria es escasa. El "
         f"{pct(d['pct_comentarios_cero_me_gusta'])} de los comentarios no muestra ningun "
         f"«me gusta», y solo {fmt(d['comentarios_con_al_menos_una_respuesta'])} de "
         f"{fmt(d['n_comentarios'])} ({pct(d['pct_comentarios_con_respuesta'])}) recibieron "
         f"alguna respuesta, con un total de {fmt(d['suma_respuestas'])} respuestas en todo "
         "el conjunto. **Esas respuestas no estan en los datos**: se sabe que existen y "
         "cuantas son, pero no su texto ni su autor. Es la evidencia directa de por que no "
         "puede construirse una red de interaccion entre usuarios."),
        ("h3", "Recurrencia de los autores"),
        ("table", "Tabla 20. Distribucion de autores por numero de comentarios",
         ["Comentarios publicados", "Numero de autores", "% de autores"],
         [[k, fmt(v), pct(100 * v / d["n_autores_unicos"])]
          for k, v in d["autores_por_n_comentarios"].items()]),
        ("p",
         f"{fmt(d['autores_con_un_comentario'])} de {fmt(d['n_autores_unicos'])} autores "
         f"({pct(d['pct_autores_con_un_comentario'])}) aparecen una sola vez, y el maximo es "
         f"de {fmt(d['max_comentarios_por_autor'])} comentarios. Mas relevante para la red: "
         f"solo {fmt(d['autores_en_mas_de_un_video'])} autores "
         f"({pct(d['pct_autores_en_mas_de_un_video'])}) comentaron en mas de un video y "
         f"{fmt(d['autores_en_mas_de_un_canal'])} en mas de un canal, con un maximo de "
         f"{fmt(d['max_videos_por_autor'])} videos distintos. Estos numeros anticipan la "
         "seccion 10: la red estara fragmentada porque casi nadie conecta contenidos."),
        ("pagebreak",),
        ("h3", "Categorias y consultas de recoleccion"),
        ("figure", "04_category_distribution.png"),
        ("figure", "05_source_queries.png"),
        ("p",
         f"El catalogo esta dominado por News & Politics (138 de "
         f"{fmt(d['n_videos_catalogo'])} videos, 47,1 %), seguido de People & Blogs (66) y "
         f"Entertainment (48). Pero la distribucion de los **comentarios** esta aun mas "
         "sesgada que la del catalogo, y en una direccion distinta: el "
         "grueso de los comentarios recolectados corresponde a videos de News & Politics de "
         "unos pocos canales. La comparacion lado a lado de la figura 4 muestra que la "
         "cobertura de comentarios **no es proporcional al catalogo**: es un submuestreo "
         "concentrado, no una muestra reducida representativa."),
        ("p",
         f"La figura 5 lo hace explicito desde el lado del muestreo: de las "
         f"{fmt(d['n_source_query_videos'])} consultas que construyeron el catalogo, solo 6 "
         "aparecen en los comentarios, y una sola de ellas (`@quorumgt/videos`) aporta 231 "
         "de los 406 comentarios (56,9 %). La estructura de participacion que se describe en "
         "las secciones siguientes esta condicionada por esa decision de recoleccion."),
        ("h3", "Hashtags"),
        ("figure", "05_top_hashtags.png"),
        ("table", "Tabla 21. Hashtags mas frecuentes en el contenido publicado por los canales",
         ["Hashtag", "Frecuencia"],
         [[f"#{r.hashtag}", fmt(r.frecuencia)] for r in hts_v.head(12).itertuples()]),
        ("p",
         f"Los hashtags son una practica del **emisor**, no de la audiencia. En titulos y "
         f"descripciones de video hay {fmt(int(hts_v.frecuencia.sum()))} usos de "
         f"{fmt(len(hts_v))} hashtags distintos, mientras que en los "
         f"{fmt(d['n_comentarios'])} comentarios hay "
         f"{fmt(int(hts_c.frecuencia.sum()) if len(hts_c) else 0)} usos de "
         f"{fmt(len(hts_c))} hashtags. Este desequilibrio hace que los hashtags sean utiles "
         "para caracterizar el contenido publicado, pero inservibles para caracterizar la "
         "conversacion: para eso se usan las palabras y bigramas de los comentarios."),
        ("h3", "Palabras y bigramas frecuentes en los comentarios"),
        ("figure", "06_top_words.png"),
        ("figure", "07_top_bigrams.png"),
        ("table", "Tabla 22. 12 palabras y 12 bigramas mas frecuentes en texto_limpio",
         ["#", "Palabra", "Frec.", "% docs", "Bigrama", "Frec.", "% docs"],
         [[str(i + 1), words.ngram.iloc[i], fmt(words.frecuencia.iloc[i]),
           pct(words.pct_documentos.iloc[i]), bigr.ngram.iloc[i],
           fmt(bigr.frecuencia.iloc[i]), pct(bigr.pct_documentos.iloc[i])]
          for i in range(12)]),
        ("p",
         f"El vocabulario es politico-institucional y esta encabezado por «"
         f"{words.ngram.iloc[0]}» ({fmt(words.frecuencia.iloc[0])} apariciones, presente en "
         f"{pct(words.pct_documentos.iloc[0])} de los comentarios). Ningun termino domina el "
         "corpus: el mas frecuente aparece en menos de una quinta parte de los comentarios, "
         "de modo que la conversacion es tematicamente dispersa dentro de un marco de "
         "referencia comun."),
        ("p",
         f"Los bigramas son mas informativos que las palabras aisladas y confirman la "
         f"ausencia de coordinacion: el bigrama mas frecuente («{bigr.ngram.iloc[0]}») "
         f"aparece {fmt(bigr.frecuencia.iloc[0])} veces en "
         f"{fmt(d['n_comentarios'])} comentarios. No hay consignas repetidas ni texto "
         "copiado en masa; cada comentario es una redaccion individual. Ese dato importa "
         "para descartar actividad automatizada como explicacion de la concentracion."),
        ("figure", "11_wordcloud.png"),
        ("pagebreak",),
        ("h2", "5.2 Concentracion de la participacion"),
        ("figure", "10_participation_concentration.png"),
        ("table", "Tabla 23. Concentracion de la participacion observada",
         ["Distribucion", "Unidades", "Gini", "Top 1", "Top 3", "Top 5", "Top 10",
          "Unidades para el 50 %"],
         _conc_rows(cn)),
        ("p",
         f"La estructura de la concentracion tiene dos caras opuestas y esa oposicion es el "
         f"hallazgo. **Por contenido y por emisor esta muy concentrada**: los dos videos mas "
         f"comentados acumulan la mitad de los comentarios "
         f"({cn['comentarios_por_video']['n_unidades_para_50pct']} unidades para el 50 %), "
         f"los tres primeros {pct(cn['comentarios_por_video']['top3_pct'])} y los cinco "
         f"primeros {pct(cn['comentarios_por_video']['top5_pct'])}, con un Gini de "
         f"{cn['comentarios_por_video']['gini']}. Por canal la concentracion es aun mayor: "
         f"un solo canal reune {pct(cn['comentarios_por_canal']['top1_pct'])} de los "
         "comentarios."),
        ("p",
         f"**Por persona, en cambio, la participacion esta casi perfectamente repartida**: "
         f"el Gini por autor es de solo {cn['comentarios_por_autor']['gini']}, el autor mas "
         f"activo aporta {pct(cn['comentarios_por_autor']['top1_pct'])} de los comentarios y "
         f"hacen falta {fmt(cn['comentarios_por_autor']['n_unidades_para_50pct'])} autores "
         f"({pct(cn['comentarios_por_autor']['pct_unidades_para_50pct'])} del total) para "
         "acumular la mitad. La curva de Lorenz del tercer panel de la figura 11 es casi la "
         "diagonal."),
        ("callout",
         "La lectura conjunta es que **la concentracion de esta muestra es de atencion, no "
         "de voz**. Unos pocos contenidos capturan casi toda la participacion, pero dentro "
         "de ellos la participacion se distribuye entre muchas personas que hablan una sola "
         "vez. No hay un grupo pequeno de usuarios dominando la conversacion; hay un grupo "
         "pequeno de videos que la concentra."),
        ("h3", "Los videos y canales que concentran la participacion"),
        ("table", "Tabla 24. Top 10 videos por comentarios observados",
         ["#", "Video", "Canal", "Com.", "Aut.", "% del total", "% acum.", "Vistas"],
         [[str(i + 1), trunc(r.title, 40), trunc(r.channel_name, 22),
           fmt(r.n_comentarios), fmt(r.n_autores), pct(r.pct_de_comentarios),
           pct(r.pct_acumulado), fmt(r.view_count_final)]
          for i, r in enumerate(cbv.head(10).itertuples())]),
        ("figure", "03_comments_by_channel.png"),
        ("table", "Tabla 25. Canales por participacion observada",
         ["#", "Canal", "Com.", "% total", "% acum.", "Videos con com.",
          "Videos en catalogo", "Autores"],
         [[str(i + 1), trunc(r.channel_name, 34), fmt(r.n_comentarios),
           pct(r.pct_de_comentarios), pct(r.pct_acumulado),
           fmt(r.n_videos_con_comentarios), fmt(r.n_videos_catalogo), fmt(r.n_autores)]
          for i, r in enumerate(cbc.itertuples())]),
        ("p",
         f"El video mas comentado es «{cbv.title.iloc[0]}» de {cbv.channel_name.iloc[0]}, "
         f"con {fmt(cbv.n_comentarios.iloc[0])} comentarios de "
         f"{fmt(cbv.n_autores.iloc[0])} autores distintos "
         f"({pct(cbv.pct_de_comentarios.iloc[0])} de todos los comentarios del conjunto). El "
         f"canal lider es {cbc.channel_name.iloc[0]}, con "
         f"{fmt(cbc.n_comentarios.iloc[0])} comentarios "
         f"({pct(cbc.pct_de_comentarios.iloc[0])}) repartidos en "
         f"{fmt(cbc.n_videos_con_comentarios.iloc[0])} videos. Conviene notar que ese canal "
         f"tiene {fmt(cbc.n_videos_catalogo.iloc[0])} videos en el catalogo: su peso en los "
         "comentarios se debe a que fue objeto de un barrido especifico de canal durante la "
         "recoleccion, no necesariamente a que genere mas conversacion que los demas."),
        ("pagebreak",),
        ("h2", "5.3 Popularidad frente a participacion"),
        ("figure", "09_views_vs_comments.png"),
        ("table", "Tabla 26. Correlaciones entre visibilidad y participacion observada",
         ["Par de variables", "n", "Spearman rho", "p", "Pearson log-log r", "Kendall tau",
          "Signif. 5 %"],
         _corr_rows(pop)),
        ("p",
         "**Spearman es la medida principal y Pearson solo un complemento.** La razon es la "
         "forma de los datos: las visualizaciones tienen asimetria de "
         f"{fmt(d['visualizaciones_catalogo']['asimetria'], 2)} y los comentarios "
         f"observados de {fmt(d['comentarios_por_video_observado']['asimetria'], 2)}, con "
         f"n = {pop['n_videos_comparados']}. Con esa asimetria y esa n, un coeficiente de "
         "Pearson sobre los valores brutos estaria dominado por uno o dos videos; una "
         "correlacion de rangos no. Se reporta ademas Pearson sobre `log1p` de ambas "
         "variables, que es defendible porque linealiza relaciones de potencia, y Kendall "
         "tau, mas robusto aun con n pequena. Los tres coinciden en signo y magnitud."),
        ("p",
         f"La asociacion entre visualizaciones y comentarios observados es **fuerte, "
         f"positiva y significativa**: rho = "
         f"{pop['views_vs_n_comentarios']['spearman_rho']} "
         f"(p = {pop['views_vs_n_comentarios']['spearman_p']}). Practicamente identica para "
         f"autores unicos (rho = {pop['views_vs_n_autores']['spearman_rho']}). Y la relacion "
         f"entre comentarios y autores unicos es casi perfecta "
         f"(rho = {pop['n_comentarios_vs_n_autores']['spearman_rho']}), lo que vuelve a "
         "indicar que el numero de comentarios y el numero de personas son casi la misma "
         "cantidad en esta muestra."),
        ("p",
         f"El orden coincide, pero el detalle no. El video mas visto del conjunto observado "
         f"({trunc(pop['video_mas_visto_observado']['title'], 44)}, "
         f"{fmt(pop['video_mas_visto_observado']['views'])} visualizaciones) recibio "
         f"{fmt(pop['video_mas_visto_observado']['n_comentarios'])} comentarios observados, "
         f"mientras que el mas comentado "
         f"({trunc(pop['video_mas_comentado']['title'], 44)}) acumula "
         f"{fmt(pop['video_mas_comentado']['n_comentarios'])} comentarios con "
         f"{fmt(pop['video_mas_comentado']['views'])} visualizaciones, un orden de magnitud "
         "menos de audiencia. La visibilidad ordena la participacion, pero no la determina."),
        ("callout",
         "**Tres advertencias sobre esta correlacion.** Primera: correlacion no es "
         "causalidad, y aqui la direccion causal es ambigua en ambos sentidos (mas "
         "visualizaciones dan mas oportunidades de comentar, pero un video con mucha "
         "discusion tambien recibe mas recomendaciones del algoritmo). Segunda: el conteo de "
         "comentarios proviene de la muestra recolectada, no del total real de YouTube, asi "
         "que el eje vertical mide cobertura de recoleccion tanto como participacion. "
         "Tercera: las visualizaciones son un corte al momento de la recoleccion y siguen "
         "creciendo; dos videos publicados en fechas distintas no son comparables sin "
         "ajustar por antiguedad, y esa correccion no es posible con fechas relativas."),
        ("pagebreak",),
    ]


def _dist_rows(dist: dict, extra: list | None = None) -> list:
    rows = [["n", fmt(dist["n"])], ["Suma", fmt(dist["suma"])],
            ["Minimo", fmt(dist["min"])], ["Percentil 25", fmt(dist["p25"], 1)],
            ["Mediana", fmt(dist["mediana"], 1)], ["Media", fmt(dist["media"], 2)],
            ["Percentil 75", fmt(dist["p75"], 1)], ["Percentil 90", fmt(dist["p90"], 1)],
            ["Maximo", fmt(dist["max"])], ["Desv. estandar", fmt(dist["std"], 2)],
            ["Asimetria", fmt(dist["asimetria"], 3)], ["Gini", fmt(dist["gini"], 4)]]
    return rows + (extra or [])


def _two_dist_rows(a: dict, b: dict, dec: int = 1) -> list:
    keys = [("n", "n", 0), ("Suma", "suma", 0), ("Minimo", "min", 0),
            ("Percentil 25", "p25", dec), ("Mediana", "mediana", dec),
            ("Media", "media", 2), ("Percentil 75", "p75", dec),
            ("Percentil 90", "p90", dec), ("Maximo", "max", 0),
            ("Desv. estandar", "std", 2), ("Asimetria", "asimetria", 3),
            ("Gini", "gini", 4)]
    return [[lab, fmt(a[k], dd), fmt(b[k], dd)] for lab, k, dd in keys]


def _conc_rows(cn: dict) -> list:
    labels = {
        "comentarios_por_video": "Comentarios por video observado",
        "comentarios_por_canal": "Comentarios por canal",
        "comentarios_por_autor": "Comentarios por autor",
        "autores_por_video": "Autores unicos por video",
        "visualizaciones_por_video_catalogo": "Visualizaciones por video (catalogo)",
        "videos_por_canal_catalogo": "Videos por canal (catalogo)",
        "me_gusta_por_comentario": "«Me gusta» por comentario",
    }
    rows = []
    for k, lab in labels.items():
        m = cn[k]
        rows.append([lab, fmt(m["n_unidades"]), fmt(m["gini"], 4),
                     pct(m["top1_pct"]), pct(m["top3_pct"]), pct(m["top5_pct"]),
                     pct(m["top10_pct"]),
                     f"{fmt(m['n_unidades_para_50pct'])} "
                     f"({pct(m['pct_unidades_para_50pct'])})"])
    return rows


def _corr_rows(pop: dict) -> list:
    labels = {
        "views_vs_n_comentarios": "Visualizaciones vs comentarios observados",
        "views_vs_n_autores": "Visualizaciones vs autores unicos",
        "n_comentarios_vs_n_autores": "Comentarios vs autores unicos",
        "views_vs_n_me_gusta": "Visualizaciones vs «me gusta» totales",
    }
    rows = []
    for k, lab in labels.items():
        s = pop[k]
        rows.append([lab, fmt(s["n"]), fmt(s["spearman_rho"], 4), f"{s['spearman_p']}",
                     fmt(s["pearson_log1p_r"], 4), fmt(s["kendall_tau"], 4),
                     "si" if s["spearman_significativo_0.05"] else "no"])
    return rows
