"""Secciones 8-12 del informe: redes, topologia, comunidades y centralidad."""
from __future__ import annotations

from .report_text import Ctx, fmt, pct, trunc


def red_bipartita(c: Ctx) -> list:
    bp = c.m("network_bipartite")
    nodes = c.t("bipartite_nodes")
    edges = c.t("bipartite_edges")
    inv = [(k, v) for k, v in bp.items() if k.startswith("inv_")]

    return [
        ("h1", "8. Construccion de la red bipartita autor-video"),
        ("h2", "8.1 Definicion de la red"),
        ("p",
         "La red es **bipartita y no dirigida**. Tiene dos conjuntos de nodos que no se "
         "mezclan y toda arista cruza de un conjunto al otro:"),
        ("table", "Tabla 30. Definicion formal de la red bipartita",
         ["Elemento", "Definicion"],
         [["Nodos tipo A (autor)",
           f"Un nodo por cada `author_channel_id` distinto. {fmt(bp['nodos_autor'])} nodos."],
          ["Nodos tipo B (video)",
           f"Un nodo por cada `video_id` con comentarios observados. "
           f"{fmt(bp['nodos_video'])} nodos."],
          ["Arista",
           "Existe entre un autor y un video si ese autor publico al menos un comentario "
           "observado en ese video. No dirigida."],
          ["Peso de la arista",
           "Numero de comentarios observados de ese autor en ese video. Un solo par "
           "autor-video genera **una** arista de peso k, nunca k aristas paralelas."],
          ["Prefijo de los identificadores",
           "`A:` y `V:` en el grafo, para que un `author_channel_id` y un `video_id` no "
           "puedan colisionar. Las tablas exportadas incluyen `raw_id` sin prefijo."]]),
        ("h2", "8.2 Significado preciso de una arista"),
        ("callout",
         "**Una arista autor-video significa exclusivamente que esa cuenta publico uno o "
         "mas comentarios observados en ese video, y su peso es cuantos.**\n\n"
         "No significa amistad. No significa que hubo una respuesta. No significa que hubo "
         "conversacion. No significa acuerdo con el contenido del video ni con otros "
         "comentaristas. No significa aprobacion.\n\n"
         "La co-participacion es coincidencia en un espacio de comentarios, y nada mas. Dos "
         "personas que comentaron el mismo video pueden no haberse leido nunca, y de hecho "
         "en un video con 128 comentaristas eso es lo mas probable."),
        ("p",
         "**`reply_count` no se usa en ningun momento para construir aristas.** La variable "
         "indica cuantas respuestas recibio un comentario, pero no identifica a sus autores, "
         "asi que no puede sostener un vinculo entre personas. Aparece unicamente como "
         "atributo agregado de nodos y aristas. El pipeline verifica en cada corrida que la "
         f"suma de pesos de la red sea igual al numero de comentarios "
         f"({fmt(bp['suma_pesos'])}) y no al numero de respuestas, lo que hace imposible "
         "haber usado la variable equivocada sin que la validacion falle."),
        ("h2", "8.3 Dimensiones e invariantes verificadas"),
        ("table", "Tabla 31. Dimensiones de la red bipartita",
         ["Metrica", "Valor"],
         [["Nodos totales", fmt(bp["nodos_totales"])],
          ["Nodos de tipo autor", fmt(bp["nodos_autor"])],
          ["Nodos de tipo video", fmt(bp["nodos_video"])],
          ["Aristas", fmt(bp["aristas"])],
          ["Suma de los pesos", fmt(bp["suma_pesos"])],
          ["Comentarios usados", fmt(bp["n_comentarios_usados"])],
          ["Peso maximo de una arista", fmt(bp["peso_maximo_arista"])],
          ["Aristas con peso mayor que 1", fmt(bp["aristas_con_peso_mayor_a_1"])]]),
        ("table", "Tabla 32. Invariantes comprobadas automaticamente en cada ejecucion",
         ["Invariante", "Resultado"],
         [[_inv_label(k), "CUMPLE" if v else "FALLA"] for k, v in inv]),
        ("p",
         f"Las {len(inv)} invariantes se comprueban en cada corrida y el pipeline aborta si "
         f"alguna falla, de modo que no es posible publicar resultados con una red mal "
         f"construida. La mas importante es la primera: **la suma de los pesos "
         f"({fmt(bp['suma_pesos'])}) es exactamente igual al numero de comentarios "
         f"({fmt(bp['n_comentarios_usados'])})**, lo que demuestra que ningun comentario se "
         f"perdio ni se conto dos veces. La segunda garantiza que hay una sola arista por "
         f"par autor-video. De las {fmt(bp['aristas'])} aristas, "
         f"{fmt(bp['aristas_con_peso_mayor_a_1'])} tienen peso mayor que 1, con un maximo de "
         f"{fmt(bp['peso_maximo_arista'])}: son los casos de autores que comentaron varias "
         "veces el mismo video."),
        ("h2", "8.4 Tablas de nodos y de aristas"),
        ("p",
         f"Se entregan en `results/networks/bipartite_nodes.csv` "
         f"({fmt(len(nodes))} filas, {fmt(nodes.shape[1])} columnas) y "
         f"`results/networks/bipartite_edges.csv` ({fmt(len(edges))} filas, "
         f"{fmt(edges.shape[1])} columnas), y ademas en formato GraphML "
         f"(`bipartite.graphml`) para poder abrirlas en Gephi. Los atributos son:"),
        ("table", "Tabla 33. Atributos de la tabla de nodos",
         ["Columna", "Contenido"],
         [["node_id", "Identificador en el grafo, con prefijo `A:` o `V:`"],
          ["raw_id", "`author_channel_id` o `video_id` original, sin modificar"],
          ["node_type / bipartite_set", "`author` (0) o `video` (1)"],
          ["display_name", "Nombre del autor o titulo del video (solo etiqueta)"],
          ["handle", "Handle normalizado y decodificado (solo etiqueta)"],
          ["channel_id / channel_name", "Canal dueno del video (vacio en nodos de autor)"],
          ["category / source_query / source_group", "Metadatos del video"],
          ["view_count", "Visualizaciones del video al momento de la recoleccion"],
          ["degree / strength", "Grado y grado ponderado en la red bipartita"],
          ["n_comentarios_observados", "Comentarios del autor, o recibidos por el video"],
          ["n_videos_comentados / n_canales_comentados", "Amplitud de participacion del autor"],
          ["n_autores_observados", "Autores distintos que comentaron el video"],
          ["me_gusta_recibidos / respuestas_recibidas", "Agregados de interaccion"],
          ["largo_medio_comentario", "Longitud media de los comentarios del autor"]]),
        ("table", "Tabla 34. Atributos de la tabla de aristas",
         ["Columna", "Contenido"],
         [["source / target", "Nodo autor y nodo video (el orden es convencional: la red es "
                              "no dirigida)"],
          ["source_type / target_type", "Siempre `author` y `video`"],
          ["source_raw_id / target_raw_id", "Identificadores originales"],
          ["weight", "**Numero de comentarios observados del autor en el video**"],
          ["significado_peso", "Texto que documenta la semantica del peso en el propio archivo"],
          ["me_gusta_en_esos_comentarios", "Suma de «me gusta» de esos comentarios"],
          ["respuestas_recibidas_en_esos_comentarios",
           "Suma de `reply_count` de esos comentarios (atributo, no relacion)"],
          ["comment_ids", "Los `comment_id` que sostienen la arista, para trazabilidad"],
          ["source_label / target_label", "Etiquetas legibles"]]),
        ("h2", "8.5 Visualizacion de la red completa"),
        ("figure", "14_bipartite_network.png"),
        ("p",
         f"**La figura contiene la red completa: no se elimino ningun nodo ni ninguna "
         f"arista.** Lo que se ajusto es la presentacion (transparencia de aristas, tamano "
         f"de nodos proporcional al grado, etiquetas solo en los {fmt(bp['nodos_video'])} "
         "nodos de video), pero la estructura es integra. La forma dominante es un conjunto "
         "de **estrellas casi disjuntas**: cada video aparece rodeado de una corona de "
         "autores de grado 1, y las estrellas se tocan solo a traves de unos pocos autores "
         "de grado 2 o 3. Nueve de las estrellas estan completamente separadas del resto."),
        ("figure", "15_bipartite_core_zoom.png"),
        ("p",
         "La segunda figura es una **ampliacion complementaria**, no un reemplazo: muestra "
         "solo los autores de grado mayor que 1 y los videos que conectan, para que se "
         "puedan leer las etiquetas. Deja ver con claridad que el nucleo conectado de toda "
         "la red se sostiene sobre nueve personas."),
        ("pagebreak",),
    ]


def proyecciones(c: Ctx) -> list:
    pj = c.m("network_projections")
    ap = c.m("network_topology")["proyeccion_autor_autor"]
    vp = c.m("network_topology")["proyeccion_video_video"]
    vpe = c.t("video_projection_edges")

    return [
        ("h1", "9. Proyecciones de la red"),
        ("h2", "9.1 Definicion y construccion"),
        ("p",
         "Las dos proyecciones se obtienen con `bipartite.weighted_projected_graph` de "
         "networkx, cuyo peso es el numero de vecinos comunes en la red bipartita. Eso "
         "coincide exactamente con lo que pide el enunciado:"),
        ("table", "Tabla 35. Las dos proyecciones",
         ["Proyeccion", "Nodos", "Arista entre dos nodos si...", "Peso de la arista"],
         [["Autor-autor", f"{fmt(ap['n_nodos'])} autores",
           "ambos comentaron el mismo video (al menos uno)",
           "**numero de videos compartidos**"],
          ["Video-video", f"{fmt(vp['n_nodos'])} videos",
           "comparten al menos un autor",
           "**numero de autores compartidos**"]]),
        ("p",
         "Una nota sobre el peso: la proyeccion **ignora deliberadamente** el peso de la "
         "red bipartita. Dos autores que coinciden en un video comparten *un* video, sin "
         "importar si uno comento una vez y el otro seis. Es la definicion del enunciado y "
         "es la correcta para lo que se quiere medir (solapamiento de participacion, no "
         "volumen)."),
        ("h2", "9.2 Verificacion independiente de los pesos"),
        ("p",
         "Los pesos de las dos proyecciones se recalcularon desde el dataframe de "
         "comentarios, sin usar networkx, mediante interseccion de conjuntos (los videos de "
         "cada autor y los autores de cada video), y se compararon uno por uno:"),
        ("table", "Tabla 36. Resultado de la verificacion de pesos",
         ["Chequeo", "Resultado"],
         [["Aristas en la proyeccion autor-autor", fmt(pj["aristas_author_projection"])],
          ["Pesos incorrectos en autor-autor", fmt(pj["pesos_author_projection_incorrectos"])],
          ["Aristas en la proyeccion video-video", fmt(pj["aristas_video_projection"])],
          ["Pesos incorrectos en video-video", fmt(pj["pesos_video_projection_incorrectos"])],
          ["Peso maximo en autor-autor", fmt(pj["peso_max_author_projection"])],
          ["Peso maximo en video-video", fmt(pj["peso_max_video_projection"])],
          ["Existe una clique por cada video observado",
           "si" if pj["inv_clique_por_video_presente"] else "NO"]]),
        ("p",
         f"Los {fmt(pj['aristas_author_projection'])} pesos de la proyeccion de autores y "
         f"los {fmt(pj['aristas_video_projection'])} de la de videos coinciden con el "
         "recalculo independiente. El chequeo de cliques confirma la propiedad estructural "
         "esperada: la audiencia de cada video forma un subgrafo completo en la proyeccion "
         "de autores."),
        ("h2", "9.3 Que fenomeno representa cada proyeccion"),
        ("table", "Tabla 37. Comparacion de las dos proyecciones",
         ["Dimension", "Autor-autor", "Video-video"],
         [["Nodos", fmt(ap["n_nodos"]), fmt(vp["n_nodos"])],
          ["Aristas", fmt(ap["n_aristas"]), fmt(vp["n_aristas"])],
          ["Densidad", fmt(ap["densidad"], 4), fmt(vp["densidad"], 4)],
          ["Grado medio", fmt(ap["grado_medio"], 2), fmt(vp["grado_medio"], 2)],
          ["Transitividad", fmt(ap["transitividad_global"], 4),
           fmt(vp["transitividad_global"], 4)],
          ["Componentes", fmt(ap["n_componentes"]), fmt(vp["n_componentes"])],
          ["Nodos aislados", fmt(ap["n_nodos_aislados"]), fmt(vp["n_nodos_aislados"])],
          ["Fenomeno que representa",
           "Co-participacion de audiencias **dentro** de un video",
           "Solapamiento de audiencia **entre** contenidos"],
          ["Que NO representa",
           "Amistad, conversacion, interaccion directa ni acuerdo",
           "Similitud tematica ni relacion editorial entre los videos"]]),
        ("p",
         f"La diferencia de escala es engañosa si se lee sin cuidado. La proyeccion de "
         f"autores tiene {fmt(ap['n_aristas'])} aristas y una transitividad de "
         f"{fmt(ap['transitividad_global'], 3)}, valores que sugieren una red densamente "
         "entrelazada. **No lo es.** Esa densidad es un artefacto mecanico de la "
         "proyeccion: si 128 personas comentan el mismo video, la proyeccion las une a "
         "todas entre si y genera 8 128 aristas de un solo golpe, con transitividad 1 "
         "dentro de ese bloque. Lo que la proyeccion de autores mide, entonces, es *que tan "
         "grandes son las audiencias*, no que tan conectadas estan las personas."),
        ("p",
         f"La proyeccion de videos es la que informa sobre audiencia compartida real, y su "
         f"lectura es la opuesta: {fmt(vp['n_aristas'])} aristas sobre "
         f"{fmt(int(vp['n_nodos'] * (vp['n_nodos'] - 1) / 2))} posibles, densidad "
         f"{fmt(vp['densidad'], 4)}, {fmt(vp['n_nodos_aislados'])} videos aislados y pesos "
         f"que solo llegan a {fmt(pj['peso_max_video_projection'])}. El solapamiento de "
         "publico entre contenidos es minimo."),
        ("h2", "9.4 Visualizacion de las dos proyecciones completas"),
        ("figure", "16_author_projection.png"),
        ("p",
         f"La proyeccion de autores se dispuso con un trazado construido a partir de su "
         f"estructura conocida (un disco por audiencia de video, y los autores multivideo "
         f"en un anillo interior) porque un trazado de fuerzas colapsa las "
         f"{fmt(ap['n_aristas'])} aristas de clique en una mancha ilegible. **No se elimino "
         "ningun nodo ni arista**: solo cambia la asignacion de coordenadas. Cada disco es "
         "la audiencia de un video; los nueve nodos amarillos del centro son los unicos "
         "autores que pertenecen a mas de un disco."),
        ("figure", "17_video_projection.png"),
        ("table", "Tabla 38. Todas las aristas de la proyeccion video-video",
         ["Video A", "Video B", "Autores compartidos"],
         [[trunc(r.source_label, 40), trunc(r.target_label, 40), fmt(r.weight)]
          for r in vpe.itertuples()]),
        ("p",
         f"La proyeccion de videos cabe entera en una tabla: son "
         f"{fmt(len(vpe))} aristas. Dos de ellas tienen peso 2 y el resto peso 1, es decir, "
         "**la mayoria de las conexiones entre contenidos las sostiene una sola persona**. "
         f"Los {fmt(vp['n_nodos_aislados'])} videos en gris de la figura no tienen ninguna "
         "conexion; se muestran igual, separados por una linea, porque su ausencia de "
         "vinculos es un resultado y no un motivo para excluirlos."),
        ("pagebreak",),
    ]


def _inv_label(k: str) -> str:
    labels = {
        "inv_suma_pesos_igual_comentarios":
            "La suma de los pesos es igual al numero de comentarios",
        "inv_una_arista_por_par_autor_video":
            "Hay exactamente una arista por par autor-video",
        "inv_autores_provienen_de_author_channel_id":
            "Todo nodo autor proviene de un author_channel_id",
        "inv_videos_provienen_de_video_id":
            "Todo nodo video proviene de un video_id",
        "inv_todas_las_aristas_cruzan_tipos":
            "Toda arista une un autor con un video (bipartita)",
        "inv_grafo_no_dirigido": "El grafo es no dirigido",
        "inv_sin_autoloops": "No hay bucles",
        "inv_endpoints_existen": "Todos los extremos de las aristas existen en la tabla de nodos",
        "inv_reply_count_no_usado_como_arista":
            "reply_count no se uso para crear ninguna arista",
    }
    return labels.get(k, k)
