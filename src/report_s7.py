"""Secciones 13-18 del informe: contenido, sentimiento, interpretacion,
limitaciones, conclusiones y reproducibilidad."""
from __future__ import annotations

from . import config as C
from .report_text import Ctx, fmt, pct, trunc


def contenido(c: Ctx) -> list:
    words, bigr = c.t("top_words"), c.t("top_bigrams")
    tri = c.t("top_trigrams")
    kw = c.t("top_video_keywords")
    emo = c.t("top_emojis")
    tf = c.t("community_tfidf_terms")
    tfk = c.t("community_tfidf_keywords")
    cl = c.m("cleaning")

    return [
        ("h1", "13. Analisis de contenido"),
        ("h2", "13.1 Enfoque elegido y por que no un modelo de topicos"),
        ("p",
         f"La caracterizacion de contenido se hace con **TF-IDF por comunidad, frecuencias, "
         f"bigramas y las keywords del contenido publicado**, no con un modelo de topicos "
         f"probabilistico. La decision es de adecuacion al tamano del corpus: hay "
         f"{fmt(cl['n_comentarios'])} comentarios con una mediana de "
         f"{fmt(cl['tokens_medios_despues'], 1)} tokens utiles tras la limpieza, repartidos "
         "en comunidades de entre 6 y 225 documentos. Un LDA o un BERTopic estarian "
         "estimando muchos parametros sobre muy pocos datos, sus topicos no serian estables "
         "entre corridas y su interpretacion exigiria mas supuestos de los que los datos "
         "sostienen."),
        ("p",
         "TF-IDF, en cambio, responde exactamente la pregunta pertinente —**que terminos "
         "distinguen a esta comunidad del resto del corpus**— con una sola decision de "
         "diseno explicita: el IDF se calcula tomando cada comunidad como un documento, de "
         "modo que un termino frecuente en todas ellas (como «guatemala») queda penalizado "
         "y emergen los terminos diferenciadores. Se complementa con las keywords y titulos "
         "de los videos, que provienen del emisor y no del comentarista, lo que permite "
         "cruzar dos fuentes independientes de senal tematica."),
        ("h2", "13.2 Terminos distintivos por comunidad"),
        ("table", "Tabla 61. Terminos TF-IDF de los comentarios por comunidad (top 6)",
         ["Comunidad", "1.º", "2.º", "3.º", "4.º", "5.º", "6.º"],
         _tf_rows(tf, 6)),
        ("table", "Tabla 62. Keywords y titulos TF-IDF del contenido publicado (top 5)",
         ["Comunidad", "1.º", "2.º", "3.º", "4.º", "5.º"],
         _tf_rows(tfk, 5)),
        ("p",
         "Las dos tablas convergen en las tres comunidades no triviales, y esa convergencia "
         "es lo que autoriza a ponerles una etiqueta tematica. En C0 los comentarios hablan "
         "de *diputado, pueblo, sueldo, almuerzo, corrupto* y las keywords del contenido "
         "dicen *usac, mazariegos, combustibles*: el mismo campo de fiscalizacion del poder "
         "publico visto desde los dos lados. En C1 los comentarios dicen *presidente, "
         "bernardo arevalo, puente* y las keywords *belice, disfrazados*. En C2 los "
         "comentarios dicen *empresa, internet, tigo, competencia* y las keywords "
         "*internet, telefonia, caminar*."),
        ("callout",
         "**Cuando la convergencia no existe, no se pone etiqueta.** Los nueve singletons no "
         "reciben nombre tematico de comunidad: con un solo video no hay forma de distinguir "
         "el tema del video del tema de una supuesta comunidad. Se describen por su "
         "contenido individual en la tabla 52."),
        ("h2", "13.3 Vocabulario global de los comentarios"),
        ("table", "Tabla 63. 20 palabras, 15 bigramas y 10 trigramas mas frecuentes",
         ["#", "Palabra", "Frec.", "Bigrama", "Frec.", "Trigrama", "Frec."],
         [[str(i + 1),
           words.ngram.iloc[i] if i < len(words) else "",
           fmt(words.frecuencia.iloc[i]) if i < len(words) else "",
           bigr.ngram.iloc[i] if i < len(bigr) else "",
           fmt(bigr.frecuencia.iloc[i]) if i < len(bigr) else "",
           tri.ngram.iloc[i] if i < len(tri) else "",
           fmt(tri.frecuencia.iloc[i]) if i < len(tri) else ""]
          for i in range(20)]),
        ("p",
         f"La caida de frecuencias entre los tres niveles de n-grama es la firma de un "
         f"corpus sin coordinacion: la palabra mas frecuente aparece "
         f"{fmt(words.frecuencia.iloc[0])} veces, el bigrama mas frecuente "
         f"{fmt(bigr.frecuencia.iloc[0])} y el trigrama mas frecuente "
         f"{fmt(tri.frecuencia.iloc[0])}. Si hubiera consignas repetidas, campanas "
         "coordinadas o texto copiado, los trigramas mantendrian frecuencias altas. No lo "
         "hacen: cada comentario es una redaccion individual. Esto es relevante para "
         "descartar automatizacion como explicacion de la concentracion documentada en la "
         "seccion 5.2."),
        ("h2", "13.4 Contenido desde el lado del emisor"),
        ("table", "Tabla 64. 15 keywords mas frecuentes en el catalogo de videos",
         ["#", "Keyword", "Frecuencia"],
         [[str(i + 1), r.keyword, fmt(r.frecuencia)]
          for i, r in enumerate(kw.head(15).itertuples())]),
        ("p",
         "Las keywords las escribe el canal para posicionar su contenido, no la audiencia. "
         "Su comparacion con el vocabulario de los comentarios muestra un desajuste "
         "sistematico: los canales etiquetan con terminos de identificacion institucional "
         "y geografica, mientras que los comentaristas escriben sobre personas concretas y "
         "dinero. Es una diferencia entre el marco que propone el emisor y el marco con el "
         "que responde la audiencia."),
        ("h2", "13.5 Emojis"),
        ("table", "Tabla 65. 12 emojis mas frecuentes en los comentarios",
         ["Emoji (descripcion)", "Frecuencia"],
         [[_emoji_desc(r.emoji), fmt(r.frecuencia)]
          for r in emo.head(12).itertuples()]),
        ("p",
         f"Hay {fmt(cl['total_emojis'])} emojis en {fmt(cl['comentarios_con_emoji'])} de "
         f"{fmt(cl['n_comentarios'])} comentarios "
         f"({pct(100 * cl['comentarios_con_emoji'] / cl['n_comentarios'])}). Se eliminan de "
         "`texto_limpio` porque en una bolsa de palabras no son terminos, pero **se "
         "conservan y se traducen a texto en la entrada del modelo de sentimiento**, donde "
         "si aportan senal. La tabla se incluye porque el uso de emojis resulta ser "
         "informativo por si mismo: como se ve en la seccion 14, la proporcion de "
         "comentarios con emoji es el doble en los positivos que en los negativos."),
        ("pagebreak",),
    ]


def sentimiento(c: Ctx) -> list:
    st = c.m("sentiment")
    m = st["modelo"]
    cs = c.t("community_summary")

    def ex(items, n=2):
        out = []
        for e in items[:n]:
            t = str(e["texto_original"]).replace("\n", " ").strip()
            out.append(f"«{trunc(t, 190)}» — predicho **{e['predicted_label']}** con "
                       f"confianza {e['confidence']:.3f}")
        return out

    return [
        ("h1", "14. Modelo y analisis de sentimiento"),
        ("h2", "14.1 Modelo utilizado y justificacion"),
        ("table", "Tabla 66. Identificacion del modelo",
         ["Campo", "Valor"],
         [["Identificador", m["model_id"]],
          ["Arquitectura", f"{', '.join(m['arquitectura'])} (`{m['model_type']}`)"],
          ["Parametros", fmt(m["n_parametros"])],
          ["Capas / hidden size", f"{fmt(m['n_capas'])} / {fmt(m['hidden_size'])}"],
          ["Tokenizer", f"{m['tokenizer_class']}, {fmt(m['tokenizer_vocab_size'])} tokens"],
          ["Framework", f"{m['framework']}, transformers {m['transformers_version']}, "
                        f"torch {m['torch_version']}"],
          ["Clases", " / ".join(m["clases"])],
          ["max_length / truncation / batch",
           f"{fmt(m['max_length_usado'])} / {m['truncation']} / {fmt(m['batch_size'])}"],
          ["Dispositivo", f"{m['device']} ({m['plataforma']})"],
          ["Semilla", fmt(m["seed"])],
          ["Fecha de ejecucion (UTC)", m["fecha_ejecucion_utc"]],
          ["Tiempo de inferencia",
           f"{m['segundos_de_inferencia']} s ({m['comentarios_por_segundo']} com./s)"]]),
        ("p",
         "**Por que este modelo y no un lexico.** RoBERTuito es un RoBERTa preentrenado "
         "desde cero sobre aproximadamente 500 millones de tweets en espanol y afinado para "
         "polaridad con el corpus TASS 2020. Cumple tres condiciones que los comentarios de "
         "este conjunto exigen: es un modelo **de espanol**, no multilingue, de modo que su "
         "vocabulario no compite con otras cien lenguas; su dominio de preentrenamiento es "
         "**texto informal de redes sociales**, que comparte con los comentarios de YouTube "
         "la brevedad, los emojis y la ortografia libre; y devuelve **tres clases con "
         "probabilidades**, lo que permite reportar distribucion y confianza sin inventar "
         "umbrales."),
        ("p",
         "**Por que se descartaron TextBlob y VADER.** Los dos son herramientas razonables "
         "para ingles y las dos fallarian aqui por la misma razon: sus lexicos son de "
         "ingles. Aplicados a texto espanol, la mayoria de los tokens quedaria fuera de "
         "diccionario y el resultado seria una masa de polaridad cero producida por "
         "ausencia de vocabulario, no por neutralidad de los textos. Eso no es una medicion "
         "con sesgo: es una no-medicion. Un lexico de sentimiento en espanol seria mejor, "
         "pero seguiria sin modelar la negacion («no me gusta») ni el contexto de la "
         "oracion, que un transformer si captura."),
        ("h2", "14.2 Texto de entrada y preprocesamiento"),
        ("p",
         "**La inferencia se hace sobre `texto_original`, no sobre `texto_limpio`.** La "
         "razon es que la version tematica elimina precisamente lo que porta polaridad: "
         "mayusculas, signos de exclamacion, emojis y stopwords. «NO me gusta» y «me gusta» "
         "son identicos tras quitar stopwords, y opuestos en sentimiento."),
        ("p",
         "Sobre el texto original se aplica la normalizacion que el modelo vio en "
         "entrenamiento (menciones a `@usuario`, URL a `url`, hashtags sin `#`, emojis "
         "traducidos a su descripcion en espanol entre delimitadores, repeticiones "
         "acortadas y risa normalizada). El detalle completo esta en la seccion 4 del "
         "reporte del modelo (`results/model/sentiment_model_report.md`)."),
        ("h2", "14.3 Resultados globales"),
        ("figure", "24_sentiment_distribution.png"),
        ("table", "Tabla 67. Distribucion de clases y confianza",
         ["Clase", "Significado", "n", "%", "Confianza media", "Confianza mediana"],
         [[k, st["significado_clases"][k], fmt(v), pct(st["pct_por_clase"][k]),
           fmt(st["confianza_media_por_clase"].get(k), 4),
           fmt(st["confianza_mediana_por_clase"].get(k), 4)]
          for k, v in st["conteo_por_clase"].items()]),
        ("p",
         f"**{pct(st['pct_por_clase']['NEG'])} de los comentarios se clasifica como "
         f"negativo**, frente a {pct(st['pct_por_clase']['NEU'])} neutro y "
         f"{pct(st['pct_por_clase']['POS'])} positivo, lo que da una polaridad neta de "
         f"{st['polaridad_neta_global']:+.1f} puntos porcentuales. La cobertura es total: "
         f"los {fmt(st['n_comentarios_evaluados'])} comentarios recibieron prediccion "
         f"({pct(st['cobertura_pct'])}), sin fallos ni exclusiones."),
        ("p",
         f"La confianza mediana es {fmt(st['confianza_mediana'], 4)} y solo "
         f"{fmt(st['n_confianza_menor_0.5'])} predicciones "
         f"({pct(st['pct_confianza_menor_0.5'])}) quedan por debajo de 0,5. Es un perfil de "
         f"confianza alto, aunque {fmt(st['n_margen_menor_0.2'])} predicciones "
         f"({pct(st['pct_margen_menor_0.2'])}) tienen un margen menor a 0,2 entre la primera "
         "y la segunda clase, es decir, son casos donde el modelo esta dividido."),
        ("callout",
         f"**Confianza no es polaridad.** {st['advertencia_confianza']}"),
        ("h2", "14.4 Comparaciones por grupo"),
        ("figure", "25_sentiment_by_video_channel.png"),
        ("p",
         f"Las comparaciones formales se limitan a los grupos con n ≥ 10 y el n de cada uno "
         f"aparece siempre visible. De {fmt(st['grupos_comparables']['videos_totales'])} "
         f"videos, {fmt(st['grupos_comparables']['videos_con_n_mayor_igual_10'])} son "
         f"comparables; de {fmt(st['grupos_comparables']['canales_totales'])} canales, "
         f"{fmt(st['grupos_comparables']['canales_con_n_mayor_igual_10'])}; de "
         f"{fmt(st['grupos_comparables']['comunidades_totales'])} comunidades, "
         f"{fmt(st['grupos_comparables']['comunidades_con_n_mayor_igual_10'])}."),
        ("table", "Tabla 68. Pruebas de independencia entre grupo y clase de sentimiento",
         ["Agrupacion", "Grupos incl.", "n", "chi-cuadrado", "gl", "p", "V de Cramer",
          "Signif. 5 %"],
         _chi_rows(st)),
        ("table", "Tabla 69. Composicion de sentimiento por canal (n ≥ 10)",
         ["Canal", "n", "% NEG", "% NEU", "% POS", "Polaridad neta", "Mayoritaria"],
         [[trunc(r["grupo_label"], 34), fmt(r["n"]), pct(r["pct_NEG"]), pct(r["pct_NEU"]),
           pct(r["pct_POS"]), f"{r['polaridad_neta']:+.1f}", r["etiqueta_mayoritaria"]]
          for r in sorted(st["comparacion_por_canal"], key=lambda d: -d["n"])
          if r["comparable_n_mayor_igual_10"]]),
        ("p",
         f"La composicion difiere entre canales de forma significativa (chi-cuadrado = "
         f"{st['chi2_por_canal']['chi2']}, gl = {st['chi2_por_canal']['gl']}, "
         f"p = {st['chi2_por_canal']['p_valor']}, V de Cramer = "
         f"{st['chi2_por_canal']['v_de_cramer']}), y la direccion del efecto es clara: "
         "**el contraste mas fuerte del conjunto no es entre temas sino entre tipos de "
         "emisor**. La Municipalidad de Guatemala es el unico canal con mayoria de "
         "comentarios positivos (80,0 %), mientras que el periodismo de investigacion y los "
         "noticieros concentran entre 50 % y 86 % de comentarios negativos."),
        ("figure", "26_sentiment_by_community.png"),
        ("table", "Tabla 70. Composicion de sentimiento por comunidad",
         ["Comunidad", "Videos", "n comentarios", "% NEG", "% NEU", "% POS",
          "Polaridad neta", "Comparable"],
         [[r.comunidad_id, fmt(r.n_videos), fmt(r.n_sentimiento), pct(r.pct_NEG),
           pct(r.pct_NEU), pct(r.pct_POS), f"{r.polaridad_neta:+.1f}",
           "si" if r.comparable_n_mayor_igual_10 else "NO"]
          for r in cs.sort_values("n_sentimiento", ascending=False).itertuples()]),
        ("p",
         f"Entre comunidades la diferencia tambien es significativa (chi-cuadrado = "
         f"{st['chi2_por_comunidad']['chi2']}, p = {st['chi2_por_comunidad']['p_valor']}, "
         f"V de Cramer = {st['chi2_por_comunidad']['v_de_cramer']}). El orden es el descrito "
         "en la seccion 11: C0 (fiscalizacion del poder publico) es la mas negativa, C1 "
         "(comunicacion del Ejecutivo) la mas mixta, y C2 (regulacion economica) la de "
         "mayor proporcion positiva. Siete de las doce comunidades tienen n < 10 y se "
         "marcan como no comparables."),
        ("h2", "14.5 Sentimiento y metricas de interaccion"),
        ("figure", "27_sentiment_vs_engagement.png"),
        ("table", "Tabla 71. Asociacion entre clase de sentimiento y metricas observadas",
         ["Clase", "«Me gusta» mediana", "«Me gusta» media",
          "Longitud mediana (car.)", "% con emoji"],
         [[k, fmt(st["me_gusta_mediana_por_clase"][k]),
           fmt(st["me_gusta_medio_por_clase"][k], 2),
           fmt(st["longitud_mediana_por_clase"][k]),
           pct(st["pct_con_emoji_por_clase"][k])]
          for k in ["NEG", "NEU", "POS"]]),
        ("p",
         f"El patron es consistente y se cuantifico formalmente en la pregunta 7.4: los "
         f"comentarios negativos son los **mas largos** "
         f"(mediana {fmt(st['longitud_mediana_por_clase']['NEG'])} caracteres frente a "
         f"{fmt(st['longitud_mediana_por_clase']['POS'])} de los positivos) y los que "
         f"reciben **menos aprobacion** "
         f"(mediana {fmt(st['me_gusta_mediana_por_clase']['NEG'])} «me gusta» frente a "
         f"{fmt(st['me_gusta_mediana_por_clase']['POS'])}), y los positivos son los que mas "
         f"usan emojis ({pct(st['pct_con_emoji_por_clase']['POS'])} frente a "
         f"{pct(st['pct_con_emoji_por_clase']['NEG'])}). En esta muestra la critica se "
         "argumenta mas y se premia menos."),
        ("callout",
         "Esta asociacion es **descriptiva**. No permite concluir que la negatividad reduzca "
         "los «me gusta»: los conteos son parciales y tomados en un momento, los "
         "comentarios positivos podrian ser mas breves por ser formulas de apoyo faciles de "
         "aprobar, y la seleccion de videos condiciona ambos lados de la relacion."),
        ("h2", "14.6 Ejemplos y casos ambiguos"),
        ("p", "Los ejemplos se eligen por posicion en la distribucion de confianza (maxima, "
              "mediana y minima de cada clase), no a mano. Dos por clase:"),
        ("bullets", ex(st["ejemplos"]["NEG"]) + ex(st["ejemplos"]["NEU"])
                    + ex(st["ejemplos"]["POS"])),
        ("p", "Los seis comentarios de menor confianza de todo el corpus:"),
        ("bullets", ex(st["ejemplos"]["casos_ambiguos_global"], 6)),
        ("p",
         "La inspeccion de estos casos muestra exactamente donde falla el modelo: la ironia "
         "(«Ay ricos shucos en la calle jajaja» es una burla y recibe NEG con 0,435 de "
         "confianza), el sarcasmo citado entre comillas, las expresiones de una palabra sin "
         "contexto («Mantenidos») y el lexico guatemalteco ausente del corpus de "
         "entrenamiento («shucos», «tambo», «moronga»). El reporte completo del modelo, con "
         "las trece limitaciones documentadas y la referencia a la model card, esta en "
         "`results/model/sentiment_model_report.md`."),
        ("callout",
         f"**{st['advertencia_intencion']}** Ademas, no se dispone de un conjunto etiquetado "
         "a mano de este dominio, por lo que **no se puede reportar exactitud ni F1 sobre "
         "estos datos**. Las cifras de esta seccion describen la distribucion de las "
         "predicciones, no su correccion."),
        ("pagebreak",),
    ]


def _tf_rows(tf, n: int) -> list:
    rows = []
    for g in sorted(tf.grupo.unique(), key=lambda x: int(str(x).lstrip("C"))):
        t = tf[tf.grupo == g].nsmallest(n, "rango").termino.tolist()
        t += [""] * (n - len(t))
        rows.append([g] + t[:n])
    return rows


def _chi_rows(st: dict) -> list:
    labels = {"chi2_por_canal": "Por canal", "chi2_por_video": "Por video",
              "chi2_por_comunidad": "Por comunidad", "chi2_por_categoria": "Por categoria"}
    rows = []
    for k, lab in labels.items():
        d = st[k]
        if not d.get("aplicable"):
            rows.append([lab, "—", "—", "no aplicable", "—", "—", "—", d.get("razon", "")])
            continue
        rows.append([lab, fmt(d["grupos_incluidos"]), fmt(d["n_incluido"]),
                     fmt(d["chi2"], 4), fmt(d["gl"]), f"{d['p_valor']}",
                     fmt(d["v_de_cramer"], 4),
                     "si" if d["significativo_0.05"] else "no"])
    return rows


def _emoji_desc(e: str) -> str:
    """Describe un emoji por nombre y punto de codigo.

    No se imprime el glifo: ninguna fuente incrustable en el PDF contiene los
    emojis de los planos suplementarios de Unicode, y hacerlo produciria
    cuadros vacios. El punto de codigo permite identificarlo sin ambiguedad.
    """
    e = str(e)
    cps = " ".join(f"U+{ord(ch):04X}" for ch in e)
    try:
        import emoji as em

        name = em.demojize(e, language="es").strip(":").replace("_", " ")
        if name and name != e:
            return f"{name} ({cps})"
    except Exception:
        pass
    return cps


def interpretacion(c: Ctx) -> list:
    d, cn = c.m("descriptives"), c.m("concentration")
    b = c.m("network_topology")["bipartita_autor_video"]
    vp = c.m("network_topology")["proyeccion_video_video"]
    cen, st = c.m("centrality_summary"), c.m("sentiment")
    cm = c.m("communities")["video_projection"]
    pop, cov = c.m("popularity"), c.m("coverage_bias")

    return [
        ("h1", "15. Interpretacion integrada"),
        ("p",
         "Esta seccion cruza los tres bloques de resultados —estructura de red, contenido y "
         "sentimiento— para responder que se observo sobre la participacion y el consumo de "
         "contenido en esta muestra de YouTube. Cada afirmacion se etiqueta segun su estatus "
         "epistemico, siguiendo la distincion que el inciso 10.3 exige."),
        ("h2", "15.1 Hallazgo 1: consumo paralelo, no conversacion"),
        ("p",
         f"**Descripcion.** El {pct(b['pct_nodos_grado_1'])} de los nodos de la red bipartita "
         f"tiene grado 1. {fmt(d['autores_con_un_comentario'])} de "
         f"{fmt(d['n_autores_unicos'])} autores ({pct(d['pct_autores_con_un_comentario'])}) "
         f"publicaron un unico comentario y solo {fmt(d['autores_en_mas_de_un_video'])} "
         f"({pct(d['pct_autores_en_mas_de_un_video'])}) comentaron en mas de un video. La "
         f"asortatividad de grado es {fmt(b['assortatividad_de_grado'], 3)} y la "
         f"transitividad es 0 por construccion; el clustering bipartito de Latapy es "
         f"{fmt(b['clustering_bipartito_latapy_medio'], 3)}. Solo "
         f"{fmt(d['comentarios_con_al_menos_una_respuesta'])} comentarios "
         f"({pct(d['pct_comentarios_con_respuesta'])}) recibieron alguna respuesta."),
        ("p",
         "**Que significa en esta muestra.** La estructura observada es la de audiencias "
         "paralelas: videos-hub rodeados de comentaristas que aparecen una sola vez y no "
         "vuelven. El acto tipico no es participar en una discusion sino dejar una opinion "
         "y salir. Es coherente con el analisis de contenido: la caida abrupta de "
         "frecuencias entre palabras, bigramas y trigramas indica redacciones individuales "
         "sin consignas repetidas ni coordinacion."),
        ("p",
         "**Que no puede concluirse.** No puede concluirse que los usuarios de YouTube no "
         "conversen. Los datos contienen **solo comentarios principales**: las respuestas "
         "existen (se sabe que hubo 51) pero no estan en el conjunto, y sin ellas cualquier "
         "medida de conversacion esta truncada por construccion. Tampoco puede concluirse "
         "que un autor «solo comento una vez»: comento una vez *en los videos "
         "recolectados*."),
        ("h2", "15.2 Hallazgo 2: la concentracion es de atencion, no de voz"),
        ("p",
         f"**Descripcion.** Gini de {cn['comentarios_por_video']['gini']} por video y "
         f"{cn['comentarios_por_canal']['gini']} por canal, frente a un Gini de solo "
         f"{cn['comentarios_por_autor']['gini']} por autor. Los tres videos mas comentados "
         f"acumulan {pct(cn['comentarios_por_video']['top3_pct'])} de los comentarios y el "
         f"canal lider {pct(cn['comentarios_por_canal']['top1_pct'])}; el autor mas activo, "
         f"{pct(cn['comentarios_por_autor']['top1_pct'])}."),
        ("p",
         "**Que significa.** Unos pocos contenidos capturan casi toda la participacion, pero "
         "dentro de ellos la palabra se reparte entre cientos de personas distintas. No hay "
         "un grupo reducido de usuarios dominando la conversacion —el escenario que suele "
         "preocupar en analisis de redes sociales— sino un grupo reducido de videos que "
         "concentra la atencion. Es una asimetria de agenda, no de voz."),
        ("p",
         f"**Que no puede concluirse.** Parte de esta concentracion es artefacto del "
         f"muestreo: el canal lider fue objeto de un barrido especifico "
         f"(`@quorumgt/videos`, que aporta 231 de {fmt(d['n_comentarios'])} comentarios), "
         "lo que garantiza su peso independientemente de su volumen real de conversacion."),
        ("h2", "15.3 Hallazgo 3: la audiencia compartida es minima y fragil"),
        ("p",
         f"**Descripcion.** La proyeccion video-video tiene {fmt(vp['n_aristas'])} aristas "
         f"de {fmt(int(vp['n_nodos'] * (vp['n_nodos'] - 1) / 2))} posibles "
         f"(densidad {fmt(vp['densidad'], 4)}), con pesos de 1 o 2, y "
         f"{fmt(vp['n_nodos_aislados'])} de {fmt(vp['n_nodos'])} videos aislados. κ global "
         f"es 0 en las tres redes y κ en la componente mayor es 1. De "
         f"{fmt(d['n_autores_unicos'])} autores, "
         f"{fmt(cen['n_autores_puente_verificados'])} son puentes verificados por prueba de "
         f"eliminacion y solo {fmt(cen['autores_con_betweenness_positiva'])} "
         f"({pct(cen['pct_autores_con_betweenness_positiva'])}) tienen betweenness "
         "positiva."),
        ("p",
         "**Que significa.** Los contenidos de esta muestra tienen publicos casi disjuntos, "
         "y las conexiones que existen las sostienen individuos concretos, no una malla "
         "redundante. La asimetria entre κ por nodos (1) y por aristas (5) en la proyeccion "
         "de autores lo resume: hay que cortar cinco vinculos para partirla, pero basta "
         "retirar a una persona."),
        ("p",
         "**Que no puede concluirse.** Ninguna de estas cifras describe aislamiento real en "
         f"YouTube. Con comentarios recolectados en solo {fmt(d['n_videos_con_comentario_observado'])} "
         f"de {fmt(d['n_videos_catalogo'])} videos, la probabilidad de **detectar** "
         "solapamiento es estructuralmente baja. El caso ilustrativo es «Plan 2032 Ciudad de "
         "Guatemala»: 304 089 visualizaciones, el video mas visto del corpus, y grado 0 en "
         "la proyeccion. Su aislamiento es un dato sobre la cobertura del muestreo, no sobre "
         "su publico."),
        ("h2", "15.4 Hallazgo 4: la estructura de audiencia coincide con la estructura tematica"),
        ("p",
         f"**Descripcion.** Louvain sobre la proyeccion video-video devuelve "
         f"{fmt(cm['n_comunidades'])} comunidades (Q ponderada = "
         f"{fmt(cm['modularidad_ponderada'], 4)}), de las cuales "
         f"{fmt(cm['n_comunidades_no_triviales'])} son no triviales. La particion coincide "
         "exactamente con la de greedy modularity (NMI = 1,0). Las tres comunidades tienen "
         "terminos TF-IDF de comentarios y keywords de contenido publicado que convergen en "
         "el mismo campo semantico, y difieren en composicion de sentimiento de forma "
         f"significativa (chi-cuadrado = {st['chi2_por_comunidad']['chi2']}, "
         f"p = {st['chi2_por_comunidad']['p_valor']}, V de Cramer = "
         f"{st['chi2_por_comunidad']['v_de_cramer']})."),
        ("p",
         "**Que significa.** Las comunidades detectadas por **audiencia compartida** "
         "resultan interpretables por **tema** y por **polaridad**, aunque ni el tema ni la "
         "polaridad entraron en el algoritmo: Louvain solo vio numeros de autores "
         "compartidos. Que tres senales independientes converjan es lo que autoriza a poner "
         "una etiqueta tematica a cada comunidad. Y el eje que las ordena es reconocible: la "
         "relacion del comentarista con el poder institucional, de la fiscalizacion "
         "(C0, la mas negativa) a la comunicacion gubernamental (C1, mixta) y a la "
         "regulacion economica (C2, la mas positiva)."),
        ("p",
         f"**Que no puede concluirse.** La modularidad de "
         f"{fmt(cm['modularidad_ponderada'], 4)} no debe leerse como evidencia de "
         "estructura comunitaria fuerte: en un grafo de 11 aristas y 10 componentes, un "
         "valor asi se obtiene con facilidad. Ademas "
         f"{fmt(cm['n_singletons'])} de las {fmt(cm['n_comunidades'])} comunidades son "
         "singletons, de modo que la particion cubre solo el "
         f"{pct(cm['cobertura_comunidades_no_triviales_pct'])} de los videos. La "
         "correspondencia con la consulta de recoleccion, medida con ARI corregido por azar, "
         "es baja (0,083), lo que descarta que las comunidades sean una relectura del "
         "muestreo, pero el muestreo si determina que agrupamientos pueden llegar a "
         "observarse."),
        ("h2", "15.5 Hallazgo 5: la critica se argumenta mas y se premia menos"),
        ("p",
         f"**Descripcion.** {pct(st['pct_por_clase']['NEG'])} de los comentarios se clasifica "
         f"como negativo (polaridad neta {st['polaridad_neta_global']:+.1f} p. p.). Los "
         f"negativos tienen la longitud mediana mas alta "
         f"({fmt(st['longitud_mediana_por_clase']['NEG'])} caracteres frente a "
         f"{fmt(st['longitud_mediana_por_clase']['POS'])} de los positivos; Kruskal-Wallis "
         f"p < 0,001) y la mediana de «me gusta» mas baja "
         f"({fmt(st['me_gusta_mediana_por_clase']['NEG'])} frente a "
         f"{fmt(st['me_gusta_mediana_por_clase']['POS'])}; p ≈ 1e-06). Los positivos usan "
         f"emojis con el doble de frecuencia ({pct(st['pct_con_emoji_por_clase']['POS'])} "
         f"frente a {pct(st['pct_con_emoji_por_clase']['NEG'])})."),
        ("p",
         "**Que significa.** Hay dos registros distintos de participacion en la misma "
         "muestra: uno critico, extenso y argumentado, y otro de apoyo, breve y con emojis. "
         "El primero es mayoritario en volumen y el segundo en aprobacion recibida por "
         "comentario. El contraste mas fuerte no se da entre temas sino entre **tipos de "
         "emisor**: el unico canal con mayoria de comentarios positivos es una institucion "
         "municipal presentando un plan urbano, mientras que el periodismo de investigacion "
         "y los noticieros concentran la critica."),
        ("p",
         "**Que no puede concluirse.** Nada causal. No se puede afirmar que la negatividad "
         "reduzca los «me gusta»: los conteos son parciales y de un momento dado, y los "
         "comentarios de apoyo podrian ser breves precisamente por ser formulas faciles de "
         "aprobar. Tampoco se puede afirmar que el publico guatemalteco sea mayoritariamente "
         "critico: el corpus esta dominado por videos de politica y de sucesos recuperados "
         "por consultas como `guatemala politica` y `guatemala seguridad`, que atraen ese "
         "registro por construccion. Y las etiquetas son predicciones de un modelo, no la "
         "intencion de los autores."),
        ("h2", "15.6 Hallazgo 6: la visibilidad ordena la participacion pero no la determina"),
        ("p",
         f"**Descripcion.** Entre los {pop['n_videos_comparados']} videos con comentarios "
         f"recolectados, rho de Spearman entre visualizaciones y comentarios observados es "
         f"{pop['views_vs_n_comentarios']['spearman_rho']} "
         f"(p = {pop['views_vs_n_comentarios']['spearman_p']}). Pero el video mas visto "
         f"({fmt(pop['video_mas_visto_observado']['views'])} vistas) tiene "
         f"{fmt(pop['video_mas_visto_observado']['n_comentarios'])} comentarios observados y "
         f"grado 0 en la red, mientras que el mas comentado "
         f"({fmt(pop['video_mas_comentado']['n_comentarios'])} comentarios, "
         f"{fmt(pop['video_mas_comentado']['views'])} vistas) es el nodo mas central. La "
         "correlacion entre visualizaciones y grado en la proyeccion no es significativa "
         "(rho = 0,289, p = 0,231), mientras que la de comentarios observados con grado si "
         "(rho = 0,678, p = 0,001)."),
        ("p",
         "**Que significa.** La visibilidad y la participacion se ordenan de forma "
         "parecida, pero el **papel estructural** de un video en la red de audiencia "
         "compartida depende de la participacion recolectada y no de su alcance. Ser muy "
         "visto no convierte a un video en punto de encuentro de publicos distintos."),
        ("p",
         f"**Que no puede concluirse.** Ni causalidad ni generalizacion. La direccion causal "
         f"es ambigua en ambos sentidos (mas vistas dan mas oportunidades de comentar, pero "
         f"mas discusion tambien atrae mas recomendaciones del algoritmo). El eje de "
         f"comentarios mide cobertura de recoleccion tanto como participacion. Y las "
         f"visualizaciones son un corte temporal: dos videos publicados en fechas distintas "
         f"no son comparables sin ajustar por antiguedad, correccion imposible con fechas "
         f"relativas. Ademas los videos observados no son los mas vistos del catalogo "
         f"(Mann-Whitney p = {cov['mannwhitney_p']}), asi que la relacion se estima sobre un "
         "subconjunto no elegido por popularidad."),
        ("pagebreak",),
    ]


def limitaciones(c: Ctx) -> list:
    d = c.m("descriptives")
    q6 = c.m("questions_mandatory")["q6"]
    st = c.m("sentiment")
    return [
        ("h1", "16. Limitaciones"),
        ("p",
         "Las limitaciones se ordenan por su capacidad de invalidar conclusiones, de mayor a "
         "menor, y cada una indica **que afirmacion concreta de este informe restringe**."),
        ("h2", "16.1 Cobertura incompleta de comentarios"),
        ("p",
         f"Solo {fmt(d['n_videos_con_comentario_observado'])} de "
         f"{fmt(d['n_videos_catalogo'])} videos "
         f"({pct(d['pct_videos_con_comentario_observado'])}) tienen comentarios en el "
         f"conjunto, y no hay garantia de que se hayan recolectado todos los comentarios de "
         f"esos {fmt(d['n_videos_con_comentario_observado'])}. **Restringe:** toda cifra de "
         "volumen de participacion, la densidad y la fragmentacion de las redes, el numero "
         "de componentes, la identidad de los puentes y los articuladores, y la existencia "
         "de videos aislados. Es la limitacion dominante del trabajo."),
        ("h2", "16.2 Seleccion de videos por consultas de busqueda"),
        ("p",
         f"El catalogo se construyo con {fmt(d['n_source_query_videos'])} consultas que "
         f"mezclan busquedas tematicas (`guatemala lluvias`, `guatemala noticias`), canales "
         f"oficiales de gobierno y barridos de canales especificos. En los comentarios solo "
         f"sobreviven {fmt(len(st['comparacion_por_consulta']))} consultas y una sola "
         f"(`{q6['consulta_dominante']['grupo']}`) aporta "
         f"{fmt(q6['consulta_dominante']['n'])} de {fmt(d['n_comentarios'])} comentarios "
         f"({pct(100 * q6['consulta_dominante']['n'] / d['n_comentarios'])}). **Restringe:** "
         "la composicion tematica observada, el predominio de News & Politics, la identidad "
         "de las comunidades y la distribucion global de sentimiento. Un corpus construido "
         "con consultas sobre deporte o musica daria un retrato distinto."),
        ("h2", "16.3 Fechas relativas y sin resolucion"),
        ("p",
         "`published_text` (comentarios) y `published_time` (videos) son tiempos relativos "
         "al momento de recoleccion («hace 2 años»), redondeados por YouTube. No hay ninguna "
         "fecha absoluta de comentario en el conjunto. **Restringe:** cualquier analisis "
         "temporal, de evolucion o de causalidad temporal; la comparacion de acumulados "
         "entre videos de distinta antiguedad; y la posibilidad de normalizar "
         "visualizaciones o «me gusta» por tiempo de exposicion."),
        ("h2", "16.4 Conteos observados en el momento de la recoleccion"),
        ("p",
         "`view_count`, `like_count_text` y `reply_count` son cortes temporales, no totales "
         "finales. Un video de hace dos años y uno de hace dos dias no son comparables sin "
         "normalizar, y esa normalizacion es imposible por la limitacion anterior. "
         "**Restringe:** la comparacion de popularidad entre videos, la correlacion entre "
         "visualizaciones y participacion, y la asociacion entre sentimiento y «me gusta»."),
        ("h2", "16.5 Ausencia de relaciones explicitas entre autores"),
        ("p",
         f"{q6['solo_comentarios_principales']} `reply_count` indica el volumen de "
         "respuestas pero no su autoria, de modo que **no existe ninguna relacion "
         "autor-autor observable en los datos**. **Restringe:** toda la interpretacion de la "
         "red. Las aristas son de co-participacion, no de interaccion. No se puede "
         "reconstruir ningun hilo, medir reciprocidad, detectar discusiones ni identificar "
         "influencia. Es la limitacion que fija el marco conceptual de todo el laboratorio."),
        ("h2", "16.6 Solo comentarios principales"),
        ("p",
         f"Los {fmt(d['suma_respuestas'])} comentarios de respuesta que se sabe que existen "
         "no estan en el conjunto. **Restringe:** cualquier medida de conversacion, de "
         "profundidad de hilo o de participacion sostenida. Un usuario que respondio "
         "activamente a otros aparece en estos datos como si no hubiera participado."),
        ("h2", "16.7 Concentracion de comentarios en muy pocos videos"),
        ("p",
         f"Dos videos concentran la mitad de los comentarios y el video lider el "
         f"{pct(c.m('concentration')['comentarios_por_video']['top1_pct'])}. **Restringe:** "
         "la estabilidad de todos los agregados globales, que estan dominados por unos "
         "pocos hilos. La distribucion global de sentimiento, por ejemplo, esta determinada "
         "en un 40 % por un unico video sobre gastos de diputados. Por eso todas las "
         "comparaciones de esta seccion se hacen por grupo y con el n visible, en lugar de "
         "confiar en el promedio global."),
        ("h2", "16.8 Limites del sentimiento automatico"),
        ("p",
         f"El modelo se entreno con tweets de 2020 (TASS) y se aplica a comentarios de "
         f"YouTube de Guatemala: hay salto de dominio, de plataforma y de variedad "
         f"dialectal. Falla sistematicamente en ironia, sarcasmo, slang guatemalteco "
         f"(«shucos», «tambo», «moronga»), ortografia no normativa y comentarios muy cortos; "
         f"{fmt(st['n_margen_menor_0.2'])} predicciones "
         f"({pct(st['pct_margen_menor_0.2'])}) tienen margen menor a 0,2 entre las dos "
         f"clases principales. **No existe un conjunto etiquetado a mano de este dominio, "
         f"por lo que no se puede reportar exactitud ni F1.** **Restringe:** toda "
         "interpretacion de polaridad. Las cifras describen lo que el modelo predijo, no lo "
         "que los autores quisieron decir. El detalle completo, con dieciseis limitaciones "
         "documentadas, esta en `results/model/sentiment_model_report.md`."),
        ("h2", "16.9 Posible sesgo por seleccion de videos y canales"),
        ("p",
         f"Los canales presentes en los comentarios son "
         f"{fmt(d['n_canales_con_comentario_observado'])} de "
         f"{fmt(d['n_canales_catalogo'])} ({pct(d['cobertura_canales_pct'])}) y estan "
         "sesgados hacia periodismo de investigacion, noticieros y comunicacion "
         "institucional. **Restringe:** la comparacion de sentimiento entre tipos de emisor, "
         "que se estima sobre ocho canales y podria invertirse con otra seleccion."),
        ("h2", "16.10 Los datos no representan a los usuarios de YouTube"),
        ("p",
         f"Los {fmt(d['n_autores_unicos'])} autores son quienes **comentaron** y cuyos "
         "comentarios **fueron recolectados**. Quien ve videos sin comentar —la inmensa "
         "mayoria— no aparece. Los comentaristas son un grupo autoseleccionado que no es "
         "representativo ni de la audiencia de esos videos. **Restringe:** cualquier "
         "afirmacion sobre «los usuarios de YouTube» o «la audiencia»."),
        ("h2", "16.11 Los datos no representan a la poblacion de Guatemala"),
        ("p",
         "No hay marco muestral, ni ponderaciones, ni informacion demografica, ni "
         "verificacion de que los autores esten en Guatemala. La muestra es de conveniencia. "
         "**Restringe:** toda inferencia poblacional. Frases como «los guatemaltecos "
         "opinan…» no tienen sustento en estos datos y no aparecen en este informe."),
        ("h2", "16.12 Descripcion, asociacion e inferencia"),
        ("table", "Tabla 72. Los tres niveles de afirmacion y como se usan en este informe",
         ["Nivel", "Formulacion", "Ejemplo de este informe", "Que autoriza"],
         [["**Descripcion**", "«En los datos observados…»",
           "«El 61,6 % de los comentarios se clasifico como negativo.»",
           "Afirmar el hecho sobre la muestra. Es el nivel de la mayoria de este informe."],
          ["**Asociacion**", "«Se observa una relacion / correlacion…»",
           "«Visualizaciones y comentarios observados correlacionan con rho = 0,81 "
           "(p = 2e-05).»",
           "Afirmar que dos cantidades covarian en la muestra. **No** autoriza a hablar de "
           "efecto, causa ni mecanismo."],
          ["**Inferencia**", "«No puede inferirse…»",
           "«No puede inferirse que la negatividad reduzca los «me gusta», ni que estos "
           "resultados describan a la poblacion de Guatemala.»",
           "Nada, en este trabajo. No hay diseno muestral que sostenga inferencia "
           "poblacional ni diseno experimental que sostenga inferencia causal."]]),
        ("callout",
         "La consecuencia practica es que **todas las conclusiones de este informe son "
         "descriptivas o asociativas y estan acotadas a los 406 comentarios recolectados de "
         "19 videos**. Cuando aparece una relacion entre variables se reporta su magnitud, "
         "su valor p y su n, y se declara explicitamente que no implica causalidad."),
        ("pagebreak",),
    ]


def conclusiones(c: Ctx) -> list:
    d, cn = c.m("descriptives"), c.m("concentration")
    b = c.m("network_topology")["bipartita_autor_video"]
    vp = c.m("network_topology")["proyeccion_video_video"]
    cen, st = c.m("centrality_summary"), c.m("sentiment")
    cm = c.m("communities")["video_projection"]
    pop = c.m("popularity")

    return [
        ("h1", "17. Conclusiones"),
        ("p",
         "Las conclusiones integran los tres bloques del analisis en lugar de resumirlos por "
         "separado, porque el resultado principal solo aparece al cruzarlos."),
        ("h2", "17.1 Conclusion integrada"),
        ("p",
         f"**Lo que estos datos describen no es una red social sino un patron de consumo de "
         f"contenido con opinion adjunta.** Las tres fuentes de evidencia convergen en ese "
         f"punto. La *estructura* muestra estrellas casi disjuntas: "
         f"{pct(b['pct_nodos_grado_1'])} de los nodos con grado 1, asortatividad "
         f"{fmt(b['assortatividad_de_grado'], 3)}, κ = 1 en la componente mayor y "
         f"{fmt(vp['n_aristas'])} aristas entre {fmt(vp['n_nodos'])} videos. El *contenido* "
         f"muestra redacciones individuales sin coordinacion: el trigrama mas frecuente "
         f"aparece 3 veces en {fmt(d['n_comentarios'])} comentarios. Y el *sentimiento* "
         f"muestra opinion evaluativa densa —{pct(st['pct_por_clase']['NEG'])} de critica— "
         "pero dirigida al contenido y a sus protagonistas, no a otros comentaristas: no hay "
         "interpelacion mutua porque casi nadie coincide dos veces con nadie."),
        ("p",
         f"El mecanismo que articula las tres observaciones es la **falta de reincidencia**. "
         f"Solo {fmt(d['autores_en_mas_de_un_video'])} de {fmt(d['n_autores_unicos'])} "
         f"autores ({pct(d['pct_autores_en_mas_de_un_video'])}) comentaron en mas de un "
         f"video. Ese unico numero explica por que la red esta fragmentada en "
         f"{fmt(b['n_componentes'])} componentes, por que la audiencia compartida es minima, "
         f"por que basta retirar a una persona para partir la componente principal, y por "
         f"que solo {fmt(cen['n_autores_puente_verificados'])} personas califican como "
         "puentes. La topologia no es una propiedad emergente compleja: es la consecuencia "
         "directa de que comentar en YouTube sea, en esta muestra, un acto puntual."),
        ("h2", "17.2 Lo que si permite afirmar el analisis"),
        ("bullets", [
            f"**La concentracion observada es de atencion, no de voz.** Gini de "
            f"{cn['comentarios_por_video']['gini']} por video y "
            f"{cn['comentarios_por_canal']['gini']} por canal frente a solo "
            f"{cn['comentarios_por_autor']['gini']} por autor. Pocos contenidos capturan "
            "casi toda la participacion; dentro de ellos, cientos de personas hablan una "
            "sola vez.",
            f"**La red de co-participacion es real pero tenue y fragil.** "
            f"{fmt(vp['n_aristas'])} conexiones entre videos, pesos de 1 o 2, "
            f"{fmt(vp['n_nodos_aislados'])} videos aislados, κ global 0 y κ = 1 en la "
            f"componente mayor. Las conexiones las sostienen "
            f"{fmt(cen['n_autores_puente_verificados'])} personas verificadas por prueba de "
            "eliminacion, no una malla redundante.",
            f"**La estructura de audiencia coincide con la estructura tematica sin haberla "
            f"usado.** Louvain vio solo numeros de autores compartidos y devolvio "
            f"{fmt(cm['n_comunidades_no_triviales'])} comunidades cuyos terminos TF-IDF, "
            "keywords del emisor y distribucion de sentimiento convergen en tres campos "
            "distintos, ordenados por la relacion del comentarista con el poder "
            "institucional.",
            f"**El sentimiento distingue tipos de emisor mas que temas.** Diferencia "
            f"significativa entre canales (V de Cramer = "
            f"{st['chi2_por_canal']['v_de_cramer']}): el unico canal con mayoria positiva es "
            "una institucion municipal presentando un plan urbano; el periodismo de "
            "investigacion y los noticieros concentran la critica.",
            f"**Existen dos registros de participacion.** Los comentarios negativos son mas "
            f"largos ({fmt(st['longitud_mediana_por_clase']['NEG'])} vs "
            f"{fmt(st['longitud_mediana_por_clase']['POS'])} caracteres de mediana) y "
            f"reciben menos aprobacion ({fmt(st['me_gusta_mediana_por_clase']['NEG'])} vs "
            f"{fmt(st['me_gusta_mediana_por_clase']['POS'])} «me gusta»); los positivos usan "
            "el doble de emojis.",
            f"**La visibilidad ordena la participacion pero no el papel estructural.** "
            f"rho = {pop['views_vs_n_comentarios']['spearman_rho']} entre vistas y "
            "comentarios observados, pero el video mas visto del corpus (304 089 vistas) "
            "tiene grado 0 en la red de audiencia compartida.",
        ]),
        ("h2", "17.3 Lo que el analisis no permite afirmar"),
        ("bullets", [
            "**Nada sobre interaccion entre usuarios.** Los datos no identifican quien "
            "respondio a quien. Toda arista es co-participacion.",
            "**Nada sobre aislamiento real.** Un video sin audiencia compartida en estos "
            "datos puede tenerla en YouTube; con comentarios en solo "
            f"{pct(d['pct_videos_con_comentario_observado'])} de los videos, la "
            "no-deteccion es el resultado esperado.",
            "**Nada causal.** Ni entre visibilidad y participacion, ni entre sentimiento y "
            "aprobacion, ni entre tema y polaridad. No hay diseno que lo sostenga.",
            "**Nada poblacional.** Ni sobre los usuarios de YouTube, ni sobre la audiencia "
            "de estos videos, ni sobre la poblacion de Guatemala. La muestra es de "
            "conveniencia, sin marco muestral ni informacion demografica.",
            "**Nada sobre la intencion de los autores.** Las etiquetas de sentimiento son "
            "predicciones de un modelo entrenado en otro corpus, sin acceso al video, al "
            "hilo ni al contexto cultural.",
            "**Nada temporal.** Sin fechas absolutas de comentario no hay evolucion, "
            "tendencia ni normalizacion por antiguedad.",
        ]),
        ("h2", "17.4 Que haria falta para ir mas alla"),
        ("bullets", [
            "**Comentarios de respuesta con su autoria** (`parentId` y `authorChannelId` de "
            "la API de YouTube). Es el unico dato que convertiria una red de "
            "co-participacion en una red de interaccion, y sin el ninguna cantidad de "
            "comentarios principales alcanza.",
            "**Cobertura completa de comentarios en un subconjunto de videos**, incluso si "
            "es pequeno. Es preferible el censo de comentarios de 20 videos a una muestra "
            "parcial de 200: solo asi el aislamiento observado seria interpretable.",
            "**Marcas temporales absolutas** (`publishedAt` de la API) para normalizar "
            "acumulados por antiguedad y estudiar evolucion.",
            "**Un conjunto de validacion etiquetado a mano** de unos 300 comentarios de "
            "este dominio, para reportar exactitud y F1 del clasificador de sentimiento en "
            "lugar de describir solo su distribucion de salida.",
            "**Un diseno de muestreo declarado** (probabilistico o al menos documentado en "
            "sus criterios de inclusion) que permitiera acotar el sesgo de seleccion en "
            "lugar de solo diagnosticarlo.",
        ]),
        ("pagebreak",),
    ]


def reproducibilidad(c: Ctx) -> list:
    ld = c.m("load")
    m = c.m("sentiment")["modelo"]
    figs = sorted(C.FIGURES.glob("*.png"))
    tabs = sorted(C.TABLES.glob("*.csv"))
    nets = sorted(C.NETWORKS.glob("*"))
    mets = sorted(C.METRICS.glob("*.json"))

    return [
        ("h1", "18. Reproducibilidad"),
        ("h2", "18.1 Como reproducir el analisis completo"),
        ("p",
         "Todo el analisis se reconstruye desde cero con un unico comando desde la raiz del "
         "proyecto:"),
        ("code", "git clone <repositorio> && cd cc3084-lab6-youtube\n"
                 "uv sync\n"
                 "uv run python -m spacy download es_core_news_sm\n"
                 "uv run python -m src.run_all"),
        ("p",
         "Alternativamente, `./scripts/run_analysis.sh` encapsula los mismos pasos, "
         "incluida la descarga de los recursos de NLTK y del modelo de spaCy, y verifica el "
         "resultado. El pipeline ejecuta en orden: validacion de los datos, limpieza y "
         "preprocesamiento, analisis exploratorio, construccion de las redes, calculo de "
         "metricas topologicas, deteccion de comunidades, centralidades y articulaciones, "
         "analisis de sentimiento, generacion de todas las tablas y figuras, y produccion de "
         "este informe en Markdown y PDF. Al terminar valida que existan todos los "
         "entregables obligatorios y devuelve codigo de salida distinto de cero si falta "
         "alguno."),
        ("h2", "18.2 Semillas y determinismo"),
        ("table", "Tabla 73. Fuentes de aleatoriedad y su control",
         ["Componente", "Semilla / configuracion", "Efecto"],
         [["Global (`random`, `numpy`, `PYTHONHASHSEED`)", f"{c.m('sentiment')['modelo']['seed']}",
           "Fijada en `src/config.py::set_seeds`, invocada al inicio de cada etapa"],
          ["Louvain", "`seed=42`, `resolution=1.0`",
           "El resultado de Louvain depende del orden de recorrido; con semilla fija la "
           "particion es identica entre corridas"],
          ["Betweenness", "`seed=42`",
           "networkx acepta semilla para el muestreo de pivotes; aqui se calcula exacto"],
          ["Label propagation (control de robustez)", "`seed=42`", "Comparacion reproducible"],
          ["Trazado de las redes", "`spring_layout(seed=42)` y trazados deterministas",
           "Las figuras de red son identicas entre corridas. Los trazados de las dos "
           "proyecciones son construcciones deterministas propias (ver secciones 9.4 y 10)"],
          ["Nube de palabras", "`random_state=42`", "Imagen identica entre corridas"],
          ["Inferencia de sentimiento", f"`torch.manual_seed({m['seed']})`, `model.eval()`",
           "La inferencia es determinista por naturaleza (sin dropout ni muestreo); la "
           "semilla se fija de todos modos"],
          ["TF-IDF", "sin aleatoriedad", "Determinista"]]),
        ("h2", "18.3 Entorno y versiones"),
        ("table", "Tabla 74. Entorno de ejecucion",
         ["Componente", "Version / valor"],
         [["Python", m["python"]],
          ["Plataforma", m["plataforma"]],
          ["Gestor de dependencias", "uv (pyproject.toml + uv.lock)"],
          ["pandas / numpy / scipy", _ver("pandas") + " / " + _ver("numpy")
           + " / " + _ver("scipy")],
          ["networkx", _ver("networkx")],
          ["scikit-learn", _ver("sklearn")],
          ["matplotlib", _ver("matplotlib")],
          ["spaCy + modelo", _ver("spacy") + " + es_core_news_sm 3.8.0"],
          ["NLTK", _ver("nltk")],
          ["transformers / torch", m["transformers_version"] + " / " + m["torch_version"]],
          ["reportlab (generacion del PDF)", _ver("reportlab")],
          ["Modelo de sentimiento", m["model_id"]],
          ["Dispositivo de inferencia", m["device"]]]),
        ("h2", "18.4 Integridad de los datos de entrada"),
        ("p",
         f"Los archivos de `data/raw/` son inmutables durante el analisis y se versionan sin "
         f"conversion de fin de linea (via `.gitattributes`) para que sus sumas MD5 sigan "
         f"coincidiendo tras clonar en cualquier sistema operativo: "
         f"`{ld['md5_videos']}` (youtube_videos.csv) y "
         f"`{ld['md5_comments']}` (youtube_comments.csv). El pipeline recalcula y registra "
         "ambas sumas en cada corrida."),
        ("h2", "18.5 Inventario de salidas"),
        ("table", "Tabla 75. Salidas generadas por el pipeline",
         ["Ubicacion", "Contenido", "Cantidad"],
         [["`results/figures/`", "Figuras en PNG a 300 dpi", f"{len(figs)} archivos"],
          ["`results/tables/`", "Tablas completas en CSV", f"{len(tabs)} archivos"],
          ["`results/networks/`", "Tablas de nodos y aristas + GraphML",
           f"{len(nets)} archivos"],
          ["`results/metrics/`", "Bloques de metricas en JSON que alimentan el informe",
           f"{len(mets)} archivos"],
          ["`results/model/`", "Reporte y metadatos del modelo de sentimiento", "2 archivos"],
          ["`data/processed/`", "Datos limpios y conjunto integrado", "3 archivos"],
          ["`report/`", "Informe en Markdown y en PDF", "2 archivos"],
          ["`docs/`", "Enunciado, metodologia, checklist de rubrica y de entrega",
           "4 archivos"]]),
        ("h2", "18.6 Trazabilidad de las cifras del informe"),
        ("p",
         "Ninguna cifra de este documento esta escrita a mano. El informe se genera a partir "
         f"de los {len(mets)} bloques de metricas de `results/metrics/*.json` y de las "
         "tablas de `results/tables/*.csv`, que a su vez producen los scripts de analisis. "
         "Los pies de figura tambien se calculan en el momento de generar cada grafico y se "
         "persisten en `results/figures/_captions.jsonl`. La consecuencia practica es que si "
         "cambiaran los datos de entrada, el texto del informe cambiaria con ellos y no "
         "podria quedar inconsistente con los resultados."),
        ("h2", "18.7 Validaciones automaticas"),
        ("p",
         "El proyecto incluye una bateria de pruebas (`uv run pytest`) que valida los puntos "
         "criticos sobre los resultados **calculados**, no sobre valores fijados a mano: "
         "dimensiones de los dos archivos, unicidad de las llaves primarias, ausencia de "
         "identificadores vacios, integridad del join, comportamiento del parser numerico "
         "caso por caso, que la suma de pesos de la red bipartita sea igual al numero de "
         "comentarios, que exista una sola arista por par autor-video, que todos los "
         "extremos de las aristas existan en la tabla de nodos, que los pesos de las dos "
         "proyecciones coincidan con un recalculo independiente por interseccion de "
         "conjuntos, que `reply_count` no se haya usado para crear aristas, que ninguna "
         "metrica sea NaN sin explicacion, que cada comentario tenga salida de sentimiento y "
         "que existan todos los archivos obligatorios."),
        ("p",
         "Ademas, el propio pipeline aborta con `AssertionError` si alguna de las nueve "
         "invariantes de la red bipartita o alguna de las verificaciones de pesos de "
         "proyeccion falla, de modo que no es posible generar el informe sobre una red mal "
         "construida."),
    ]


def referencias(c: Ctx) -> list:
    m = c.m("sentiment")["modelo"]
    return [
        ("h1", "Referencias"),
        ("bullets", [
            "Blondel, V. D., Guillaume, J.-L., Lambiotte, R. y Lefebvre, E. (2008). "
            "*Fast unfolding of communities in large networks*. Journal of Statistical "
            "Mechanics: Theory and Experiment, 2008(10), P10008.",
            "Clauset, A., Newman, M. E. J. y Moore, C. (2004). *Finding community structure "
            "in very large networks*. Physical Review E, 70(6), 066111.",
            "Freeman, L. C. (1977). *A set of measures of centrality based on betweenness*. "
            "Sociometry, 40(1), 35-41.",
            "Hagberg, A., Schult, D. y Swart, P. (2008). *Exploring network structure, "
            "dynamics, and function using NetworkX*. Proceedings of the 7th Python in "
            "Science Conference (SciPy2008), 11-15. Documentacion: "
            "<https://networkx.org/documentation/stable/>",
            "Latapy, M., Magnien, C. y Del Vecchio, N. (2008). *Basic notions for the "
            "analysis of large two-mode networks*. Social Networks, 30(1), 31-48.",
            "Menger, K. (1927). *Zur allgemeinen Kurventheorie*. Fundamenta Mathematicae, "
            "10, 96-115. (Teorema que relaciona conectividad por nodos y caminos disjuntos.)",
            "Newman, M. E. J. (2003). *Mixing patterns in networks*. Physical Review E, "
            "67(2), 026126. (Asortatividad de grado.)",
            "Newman, M. E. J. (2004). *Analysis of weighted networks*. Physical Review E, "
            "70(5), 056131.",
            "Newman, M. E. J. y Girvan, M. (2004). *Finding and evaluating community "
            "structure in networks*. Physical Review E, 69(2), 026113. (Modularidad.)",
            "Perez, J. M., Furman, D. A., Alonso Alemany, L. y Luque, F. (2022). "
            "*RoBERTuito: a pre-trained language model for social media text in Spanish*. "
            "Proceedings of LREC 2022, 7235-7243. "
            "<https://aclanthology.org/2022.lrec-1.785/>",
            "Perez, J. M., Giudici, J. C. y Luque, F. (2021). *pysentimiento: A Python "
            "Toolkit for Sentiment Analysis and SocialNLP tasks*. "
            "<https://arxiv.org/abs/2106.09462>",
            f"Model card del modelo utilizado: `{m['model_id']}`. "
            "<https://huggingface.co/pysentimiento/robertuito-sentiment-analysis>",
            "TASS: Taller de Analisis Semantico de la SEPLN. Corpus de afinado del modelo "
            "de sentimiento (TASS 2020, Task 1). <http://tass.sepln.org/>",
            "Wasserman, S. y Faust, K. (1994). *Social Network Analysis: Methods and "
            "Applications*. Cambridge University Press. (Correccion de closeness en grafos "
            "desconectados; nociones de cohesion.)",
            "Honnibal, M. y Montani, I. (2017). *spaCy 2: Natural language understanding "
            "with Bloom embeddings, convolutional neural networks and incremental parsing*. "
            "Modelo `es_core_news_sm`. <https://spacy.io/models/es>",
            "Bird, S., Klein, E. y Loper, E. (2009). *Natural Language Processing with "
            "Python*. O'Reilly. (Lista de stopwords de espanol de NLTK.)",
            "Universidad del Valle de Guatemala, Departamento de Ciencias de la "
            "Computacion. *CC3084 Data Science. Laboratorio 6: Analisis de redes sociales*. "
            "Semestre II, 2026. (Enunciado en `docs/`.)",
        ]),
    ]


def _ver(mod: str) -> str:
    try:
        import importlib

        m = importlib.import_module(mod)
        return getattr(m, "__version__", "n/d")
    except Exception:
        return "n/d"
