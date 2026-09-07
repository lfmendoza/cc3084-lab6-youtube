"""Secciones 1-4 del informe: introduccion, datos, integracion y limpieza."""
from __future__ import annotations

from .report_text import Ctx, fmt, pct, trunc


def resumen_ejecutivo(c: Ctx) -> list:
    d, j = c.m("descriptives"), c.m("join")
    cl, cn = c.m("cleaning"), c.m("concentration")
    bp, vp = c.m("network_bipartite"), c.m("network_topology")["proyeccion_video_video"]
    cm, cen = c.m("communities")["video_projection"], c.m("centrality_summary")
    st, pop = c.m("sentiment"), c.m("popularity")
    per = c.m("network_peripheral")

    return [
        ("h1", "Resumen ejecutivo"),
        ("p",
         f"Se analizaron {fmt(d['n_videos_catalogo'])} videos de "
         f"{fmt(d['n_canales_catalogo'])} canales de YouTube y "
         f"{fmt(d['n_comentarios'])} comentarios principales publicados por "
         f"{fmt(d['n_autores_unicos'])} autores distintos. Los "
         f"{fmt(d['n_comentarios'])} comentarios se asociaron a un video mediante "
         f"`video_id` sin excepciones ({pct(j['pct_comentarios_con_video'])}), pero "
         f"cubren solo {fmt(d['n_videos_con_comentario_observado'])} de los "
         f"{fmt(d['n_videos_catalogo'])} videos del catalogo "
         f"({pct(d['pct_videos_con_comentario_observado'])}). Esa asimetria de cobertura "
         "condiciona todo el analisis y se trata explicitamente en cada seccion: los "
         "conteos de comentarios son *observados en la muestra*, no totales de YouTube."),
        ("p",
         f"**Participacion muy concentrada por contenido y muy repartida por persona.** "
         f"Los tres videos mas comentados acumulan {pct(cn['comentarios_por_video']['top3_pct'])} "
         f"de los comentarios y el canal lider "
         f"{pct(cn['comentarios_por_canal']['top1_pct'])} (Gini de "
         f"{cn['comentarios_por_video']['gini']} por video y "
         f"{cn['comentarios_por_canal']['gini']} por canal). En el extremo opuesto, el Gini "
         f"por autor es de solo {cn['comentarios_por_autor']['gini']}: "
         f"{fmt(d['autores_con_un_comentario'])} de {fmt(d['n_autores_unicos'])} autores "
         f"({pct(d['pct_autores_con_un_comentario'])}) publicaron un unico comentario."),
        ("p",
         f"**La red de co-participacion esta fragmentada.** La red bipartita autor-video "
         f"tiene {fmt(bp['nodos_totales'])} nodos y {fmt(bp['aristas'])} aristas, con la "
         f"suma de pesos igual a los {fmt(bp['suma_pesos'])} comentarios. Solo "
         f"{fmt(d['autores_en_mas_de_un_video'])} autores "
         f"({pct(d['pct_autores_en_mas_de_un_video'])}) comentaron en mas de un video, y son "
         f"el unico mecanismo que conecta contenidos entre si: la proyeccion video-video "
         f"tiene {fmt(vp['n_aristas'])} aristas de "
         f"{fmt(int(vp['n_nodos'] * (vp['n_nodos'] - 1) / 2))} posibles "
         f"(densidad {vp['densidad']}) y deja "
         f"{fmt(per['n_videos_aislados_proyeccion'])} de {fmt(vp['n_nodos'])} videos "
         f"aislados. La cohesion global por nodos es 0 en las tres redes porque estan "
         f"desconectadas; en la componente mayor de cada una es 1, es decir, un solo nodo "
         "bien elegido las parte."),
        ("p",
         f"**Comunidades pocas pero interpretables.** Louvain ponderado sobre la proyeccion "
         f"video-video (semilla {cm['semilla']}, resolucion {cm['resolucion']}) devuelve "
         f"{cm['n_comunidades']} comunidades con modularidad ponderada "
         f"Q = {cm['modularidad_ponderada']}, de las cuales {cm['n_singletons']} son "
         f"singletons y {cm['n_comunidades_no_triviales']} tienen mas de un video. Las tres "
         "no triviales se separan por tema y por emisor: critica al Congreso y a la "
         "corrupcion, comunicacion del Ejecutivo, y regulacion de monopolios y movilidad "
         "urbana."),
        ("p",
         f"**Puentes escasos y verificados.** De los {fmt(d['n_autores_unicos'])} autores, "
         f"{cen['n_autores_puente_verificados']} son puentes en sentido estricto: al "
         "eliminarlos de la red bipartita aumenta el numero de componentes de la proyeccion "
         f"video-video. Solo {fmt(cen['autores_con_betweenness_positiva'])} autores "
         f"({pct(cen['pct_autores_con_betweenness_positiva'])}) tienen intermediacion "
         "positiva."),
        ("p",
         f"**Sentimiento predominantemente critico.** Con "
         f"`{st['modelo']['model_id']}`, {pct(st['pct_por_clase']['NEG'])} de los "
         f"comentarios se clasifica como negativo, {pct(st['pct_por_clase']['NEU'])} como "
         f"neutro y {pct(st['pct_por_clase']['POS'])} como positivo (polaridad neta "
         f"{st['polaridad_neta_global']:+.1f} puntos porcentuales, confianza mediana "
         f"{st['confianza_mediana']}). La composicion difiere entre canales de forma "
         f"significativa (chi-cuadrado = {st['chi2_por_canal']['chi2']}, "
         f"gl = {st['chi2_por_canal']['gl']}, p = {st['chi2_por_canal']['p_valor']}, "
         f"V de Cramer = {st['chi2_por_canal']['v_de_cramer']}): el video institucional mas "
         "comentado de la Municipalidad concentra respaldo, mientras que el periodismo de "
         "investigacion concentra critica."),
        ("p",
         f"**Visibilidad y participacion se ordenan igual, pero no coinciden.** Entre los "
         f"{pop['n_videos_comparados']} videos con comentarios recolectados, "
         f"visualizaciones y comentarios observados correlacionan con "
         f"rho de Spearman = {pop['views_vs_n_comentarios']['spearman_rho']} "
         f"(p = {pop['views_vs_n_comentarios']['spearman_p']}). Aun asi el video mas visto "
         f"({fmt(pop['video_mas_visto_observado']['views'])} vistas) recibio "
         f"{fmt(pop['video_mas_visto_observado']['n_comentarios'])} comentarios "
         f"observados, frente a los {fmt(pop['video_mas_comentado']['n_comentarios'])} del "
         f"mas comentado, que tiene {fmt(pop['video_mas_comentado']['views'])} vistas."),
        ("callout",
         "Ninguna cifra de este informe puede extrapolarse a YouTube ni a la poblacion de "
         "Guatemala. Los comentarios provienen de una seleccion de videos recuperados por "
         "consultas de busqueda especificas, en un momento determinado, y el conjunto no "
         "incluye respuestas ni permite saber quien respondio a quien."),
        ("pagebreak",),
    ]


def introduccion(c: Ctx) -> list:
    ld = c.m("load")
    return [
        ("h1", "1. Introduccion y objetivo"),
        ("p",
         "El laboratorio estudia la estructura de participacion de los usuarios de YouTube "
         "a partir de dos conjuntos de datos: un catalogo de videos con sus metadatos de "
         "canal, categoria y visibilidad, y un conjunto de comentarios principales "
         "publicados en una seleccion de esos videos. El objetivo es describir quien "
         "participa, en que contenidos, con que estructura de red, sobre que temas y con "
         "que polaridad, distinguiendo en todo momento lo que los datos permiten afirmar de "
         "lo que solo permiten conjeturar."),
        ("p",
         "El analisis se organiza en torno a una decision conceptual que atraviesa el "
         "informe: **los datos no contienen relaciones explicitas entre autores**. La "
         "variable `reply_count` indica cuantas respuestas recibio un comentario, pero no "
         "identifica a quien las escribio. Por lo tanto no existe una red de interaccion "
         "directa entre usuarios, y construirla seria una invencion. Lo que si puede "
         "construirse, y es lo que se construye, es una red de **co-participacion**: dos "
         "personas quedan vinculadas si comentaron el mismo video, lo que significa que "
         "coincidieron en un espacio de discusion, no que se hayan hablado."),
        ("h2", "1.1 Preguntas que guian el analisis"),
        ("bullets", [
            "Que contenidos y que emisores concentran la participacion observada.",
            "Si existe audiencia compartida entre videos y canales, y de que magnitud.",
            "Quienes sostienen las conexiones entre contenidos que de otro modo quedarian "
            "separados, y como verificarlo en lugar de suponerlo.",
            "Que agrupamientos de contenido emergen de la audiencia compartida, y como se "
            "caracterizan por tema y por polaridad.",
            "Si la visibilidad (visualizaciones) predice la participacion observada.",
            "Que conclusiones quedan limitadas por el procedimiento de recoleccion.",
        ]),
        ("h2", "1.2 Datos de partida y verificacion de integridad"),
        ("p",
         f"Los dos archivos se copiaron a `data/raw/` y se tratan como inmutables durante "
         f"todo el analisis. Sus sumas MD5 quedan registradas en "
         f"`results/metrics/load.json` para poder comprobar que no se alteraron: "
         f"`{ld['md5_videos'][:16]}…` para el catalogo de videos y "
         f"`{ld['md5_comments'][:16]}…` para los comentarios."),
        ("table", "Tabla 1. Dimensiones observadas frente a las declaradas en el enunciado",
         ["Archivo", "Filas obs.", "Cols. obs.", "Filas esp.", "Cols. esp.", "Coincide"],
         [["youtube_videos.csv", fmt(ld["videos_shape"][0]), fmt(ld["videos_shape"][1]),
           fmt(ld["videos_shape_esperado"][0]), fmt(ld["videos_shape_esperado"][1]),
           "si" if ld["videos_shape_coincide"] else "NO"],
          ["youtube_comments.csv", fmt(ld["comments_shape"][0]), fmt(ld["comments_shape"][1]),
           fmt(ld["comments_shape_esperado"][0]), fmt(ld["comments_shape_esperado"][1]),
           "si" if ld["comments_shape_coincide"] else "NO"]]),
        ("p",
         f"Las dimensiones coinciden exactamente con las declaradas. Dos detalles tecnicos "
         f"de la carga que afectan el resultado: ambos archivos traen marca de orden de "
         f"bytes (BOM), por lo que se leen con `{ld['encoding']}` — sin eso, el nombre de la "
         f"primera columna quedaria como `\\ufeffvideo_id` y el join fallaria por completo; y "
         f"todas las columnas se cargan como texto ({ld['dtype_carga']}), porque si pandas "
         "infiere tipos convierte identificadores con apariencia numerica y puede recortar "
         "ceros a la izquierda."),
    ]


def datos_y_unidades(c: Ctx) -> list:
    d = c.m("descriptives")
    return [
        ("h1", "2. Datos y unidades de observacion"),
        ("h2", "2.1 Unidad de observacion y llave primaria"),
        ("table", "Tabla 2. Unidad de observacion y llaves de cada conjunto",
         ["Conjunto", "Unidad de observacion", "Llave primaria", "Verificacion"],
         [["youtube_videos.csv", "Un video de YouTube", "video_id",
           f"{fmt(c.m('quality')['duplicados_videos']['llaves']['video_id']['unicos'])} "
           "valores unicos, 0 duplicados, 0 nulos"],
          ["youtube_comments.csv", "Un comentario principal", "comment_id",
           f"{fmt(c.m('quality')['duplicados_comentarios']['llaves']['comment_id']['unicos'])} "
           "valores unicos, 0 duplicados, 0 nulos"]]),
        ("p",
         "En el conjunto de comentarios, `video_id` es llave **foranea**, no primaria: se "
         f"repite porque un video recibe muchos comentarios "
         f"({fmt(c.m('quality')['duplicados_comentarios']['llaves']['video_id']['duplicados'])} "
         f"repeticiones sobre {fmt(d['n_comentarios'])} filas). Del mismo modo, `channel_id` "
         "se repite en el catalogo de videos porque un canal publica varios videos. "
         "Confundir cualquiera de las dos con una llave primaria produciria agregados "
         "erroneos."),
        ("h2", "2.2 Relacion conceptual entre canal, video, comentario, autor, categoria y consulta"),
        ("p",
         "La jerarquia de los datos tiene cuatro niveles y dos etiquetas transversales. Es "
         "importante fijarla antes de agregar cualquier cosa, porque cada nivel tiene su "
         "propio denominador:"),
        ("bullets", [
            "**Canal** (`channel_id`): la cuenta que publica contenido. Es el emisor. "
            f"Hay {fmt(d['n_canales_catalogo'])} canales en el catalogo, de los cuales "
            f"{fmt(d['n_canales_con_comentario_observado'])} tienen comentarios "
            f"recolectados ({pct(d['cobertura_canales_pct'])}).",
            "**Video** (`video_id`): una pieza de contenido publicada por un canal. "
            "Relacion uno a muchos: un canal tiene varios videos, un video tiene un solo "
            f"canal. Hay {fmt(d['n_videos_catalogo'])} videos.",
            "**Comentario** (`comment_id`): un mensaje publicado en un video. Relacion uno "
            "a muchos con el video. Es la unidad de texto y de sentimiento. Hay "
            f"{fmt(d['n_comentarios'])} comentarios.",
            "**Autor del comentario** (`author_channel_id`): la cuenta que escribio el "
            "comentario. Relacion muchos a muchos con los videos: un autor puede comentar "
            "varios videos y un video recibe comentarios de varios autores. Es esta "
            "relacion muchos a muchos la que hace posible una red bipartita. Hay "
            f"{fmt(d['n_autores_unicos'])} autores.",
            "**Categoria** (`category`): etiqueta tematica que YouTube asigna al video. Es "
            f"un atributo del video, no del comentario. Hay {fmt(d['n_categorias'])} "
            "categorias distintas.",
            "**Consulta de busqueda** (`source_query`, `source_group`): describe **como se "
            "encontro** el registro durante la recoleccion. No es un atributo del contenido "
            "sino del muestreo, y por eso se usa para evaluar cobertura y sesgo, nunca "
            "como etiqueta tematica definitiva.",
        ]),
        ("callout",
         "**`channel_id` y `author_channel_id` no son la misma cosa y no son "
         "intercambiables.** `channel_id` identifica al canal *dueno del video comentado*; "
         "`author_channel_id` identifica a la *persona que escribio el comentario*. Ambos "
         "tienen el mismo formato (`UC…`), lo que los hace facilmente confundibles. Se "
         "verifico que ningun comentario observado fue escrito por el canal dueno del video "
         "(0 coincidencias entre las dos columnas en las 406 filas), de modo que en esta "
         "muestra los dos conjuntos de cuentas son disjuntos."),
        ("h2", "2.3 Variables relevantes por conjunto"),
        ("table", "Tabla 3. Variables usadas en el analisis y su funcion",
         ["Variable", "Conjunto", "Funcion en el analisis"],
         [["video_id", "ambos", "Llave del join; nodo de tipo video en la red bipartita"],
          ["comment_id", "comentarios", "Llave primaria; unidad de sentimiento"],
          ["channel_id", "ambos", "Nodo de canal; agregacion por emisor"],
          ["author_channel_id", "comentarios", "Nodo de tipo autor en la red bipartita"],
          ["text", "comentarios", "Fuente de texto_original y texto_limpio"],
          ["view_count", "videos", "Medida de visibilidad para el contraste con participacion"],
          ["like_count_text", "comentarios", "Aprobacion recibida por el comentario (requiere parseo)"],
          ["reply_count", "comentarios", "Intensidad de conversacion del comentario; NO una arista"],
          ["category", "videos", "Caracterizacion tematica de las comunidades"],
          ["source_query / source_group", "ambos", "Diagnostico de cobertura y sesgo de muestreo"],
          ["keywords / title / description", "videos", "Caracterizacion tematica desde el emisor"],
          ["publish_date", "videos", "Unica fecha absoluta disponible (ISO 8601)"]]),
    ]


def integracion(c: Ctx) -> list:
    j, d = c.m("join"), c.m("descriptives")
    checks = c.t("consistency_checks")
    return [
        ("h1", "3. Integracion de los datos"),
        ("p",
         f"La integracion se hizo con un **{j['tipo_join']}**, de cardinalidad "
         f"*{j['cardinalidad_join']}*. La direccion del join no es arbitraria: la pregunta "
         "del inciso 1.4 es cuantos comentarios logran asociarse a un video, asi que ninguna "
         "fila de comentarios puede desaparecer en el proceso. Un inner join habria "
         "respondido la pregunta ocultando su propia respuesta."),
        ("table", "Tabla 4. Resultado de la integracion por video_id",
         ["Metrica", "Valor"],
         [["Comentarios en el conjunto", fmt(j["n_comentarios"])],
          ["Comentarios que encontraron su video", fmt(j["comentarios_con_video"])],
          ["Comentarios sin video correspondiente", fmt(j["comentarios_sin_video"])],
          ["Porcentaje asociado", pct(j["pct_comentarios_con_video"])],
          ["video_id distintos en comentarios", fmt(j["video_ids_distintos_en_comentarios"])],
          ["Videos del catalogo con al menos un comentario observado",
           f"{fmt(j['videos_con_al_menos_un_comentario_observado'])} de "
           f"{fmt(j['n_videos_catalogo'])} ({pct(j['pct_videos_con_comentario_observado'])})"],
          ["Videos del catalogo sin comentario observado",
           fmt(j["videos_sin_comentario_observado"])]]),
        ("p",
         f"**Los {fmt(j['comentarios_con_video'])} comentarios se asociaron a un video sin "
         f"excepciones.** No hay comentarios huerfanos: el conjunto de `video_id` presentes "
         "en los comentarios es un subconjunto propio del catalogo de videos. Esto confirma "
         "que los dos archivos provienen de la misma recoleccion y que la llave esta bien "
         "formada."),
        ("callout",
         f"El hallazgo importante del join no es el {pct(j['pct_comentarios_con_video'])} de "
         f"exito, sino su contraparte: **{fmt(j['videos_sin_comentario_observado'])} de los "
         f"{fmt(j['n_videos_catalogo'])} videos del catalogo no tienen ningun comentario en "
         "este conjunto de datos.** Eso *no* significa que no recibieran comentarios en "
         "YouTube. Significa que no se recolectaron. La diferencia entre «sin comentario "
         "observado» y «sin comentarios» es la distincion metodologica mas importante de "
         "todo el laboratorio, y se mantiene explicita en cada tabla y cada figura."),
        ("h2", "3.1 Consistencia de las variables redundantes tras el join"),
        ("p",
         f"El conjunto de comentarios repite cuatro variables que tambien estan en el "
         f"catalogo de videos (`video_title`, `channel_name`, `channel_id`, y las de "
         f"muestreo). Se verificaron una por una en lugar de sobrescribirlas en silencio. "
         f"De {len(checks)} chequeos automaticos, "
         f"{int(checks['cumple'].sum())} se cumplen."),
        ("table", "Tabla 5. Chequeos de consistencia entre identificadores, nombres y handles",
         ["Ambito", "Chequeo", "Resultado", "Cumple"],
         [[r.ambito, trunc(r.chequeo, 52), trunc(r.obtenido, 26),
           "si" if r.cumple else "NO"] for r in checks.itertuples()]),
        ("p",
         "Las variables `video_title`, `channel_id` y `channel_name` del conjunto de "
         "comentarios coinciden al 100 % con las del catalogo tras el join, de modo que son "
         "estrictamente redundantes. Se conservan con sufijo `_c` y los analisis usan la "
         "version del catalogo de videos, que es la fuente autoritativa para atributos de "
         "video."),
        ("h3", "Dos hallazgos de los chequeos que no se cumplen"),
        ("p",
         "Los dos chequeos que no se cumplen no son fallos del pipeline sino **anomalias "
         "reales de los datos**, detectadas por el diagnostico y corregidas:"),
        ("bullets", [
            "**`author_handle` viene codificado para URL en 14 registros** "
            "(9 autores distintos): el archivo guarda `/@ErmeP%C3%A9rez-q4s` mientras que "
            "`author_name` guarda `@ErmePérez-q4s`. Sin decodificar el percent-encoding, el "
            "mismo autor parece tener dos etiquetas visibles distintas y cualquier "
            "comparacion entre ambas columnas falla. Se corrige en la columna derivada "
            "`author_handle_norm`; el campo original se conserva intacto. Tras decodificar, "
            "las dos etiquetas coinciden en los 406 registros.",
            "**`channel_handle` presenta la misma anomalia en 13 registros** del catalogo de "
            "videos. Se corrige igual, en `channel_handle_norm`.",
        ]),
        ("p",
         "Un tercer chequeo merece comentario porque su resultado *no* es un error. "
         f"`source_query` y `source_group` difieren entre los dos archivos en 188 de "
         f"{fmt(j['n_comentarios'])} filas. La razon es de diseno: la version del comentario "
         "describe mediante que consulta se obtuvo *el comentario*, y la del video mediante "
         "que consulta se encontro *el video*. Un video puede haberse localizado con la "
         "consulta tematica `guatemala noticias` y sus comentarios haberse extraido despues "
         "en un barrido del canal `@quorumgt/videos`. Ambas versiones se conservan con "
         "sufijos explicitos porque documentan dos etapas distintas del muestreo."),
        ("pagebreak",),
    ]
