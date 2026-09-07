"""Secciones 10-12 del informe: topologia, comunidades y centralidad."""
from __future__ import annotations

from .report_text import Ctx, fmt, pct, trunc


def topologia(c: Ctx) -> list:
    t = c.m("network_topology")
    per = c.m("network_peripheral")
    b, ap, vp = (t["bipartita_autor_video"], t["proyeccion_autor_autor"],
                 t["proyeccion_video_video"])

    return [
        ("h1", "10. Topologia y fragmentacion"),
        ("h2", "10.1 Metricas estructurales de las tres redes"),
        ("table", "Tabla 39. Metricas topologicas comparadas",
         ["Metrica", "Bipartita autor-video", "Proy. autor-autor", "Proy. video-video"],
         _topo_rows(b, ap, vp)),
        ("h3", "Densidad: por que la bipartita necesita su propia formula"),
        ("p",
         f"La densidad estandar de un grafo compara las aristas observadas con "
         f"n(n−1)/2, que es el maximo en un grafo simple. **En una red bipartita ese maximo "
         f"es imposible de alcanzar** porque no puede haber aristas dentro de un mismo "
         f"conjunto: el maximo real es |A|·|B| = {fmt(b['n_nodos_tipo_autor'])} · "
         f"{fmt(b['n_nodos_tipo_video'])} = {fmt(b['max_aristas_bipartita'])}. Por eso la densidad "
         f"estandar de {fmt(b['densidad'], 5)} subestima gravemente la conectividad, y la "
         f"cifra correcta es la densidad bipartita de {fmt(b['densidad_bipartita'], 5)}. Aun "
         "asi es baja: se materializa poco mas del 5 % de los emparejamientos "
         "autor-video posibles."),
        ("h3", "Transitividad: cero por construccion en la bipartita"),
        ("p",
         f"La transitividad global de la red bipartita es exactamente "
         f"{fmt(b['transitividad_global'], 1)}, y eso **no es un hallazgo empirico sino una "
         "propiedad matematica**: un triangulo exige tres nodos mutuamente adyacentes, y en "
         "una red bipartita toda arista cruza de un conjunto al otro, asi que el tercer "
         "vertice nunca puede cerrarse. Reportar ese cero como «falta de cohesion local» "
         "seria un error de interpretacion."),
        ("p",
         f"La metrica interpretable para una red bipartita es el **clustering bipartito de "
         f"Latapy**, que mide el solapamiento de vecindarios en lugar de triangulos. Su "
         f"valor medio es {fmt(b['clustering_bipartito_latapy_medio'], 4)}, un valor alto: "
         "los autores que comparten un video tienden a compartir tambien su vecindario "
         "completo, que es exactamente lo que se espera de una estructura de estrellas."),
        ("p",
         f"En las proyecciones la transitividad si es informativa. La de autores tiene "
         f"{fmt(ap['transitividad_global'], 4)}, practicamente 1, porque esta compuesta de "
         f"cliques. La de videos tiene {fmt(vp['transitividad_global'], 4)}: hay algunos "
         "triangulos de videos que comparten audiencia entre si, pero la mayoria de las "
         "conexiones son cadenas abiertas."),
        ("h2", "10.2 Cohesion: definicion operacional"),
        ("callout",
         "**Definicion.** En este informe *cohesion* significa **conectividad por nodos "
         "(κ)**: el numero minimo de nodos que hay que eliminar para desconectar el grafo. "
         "Si el grafo ya esta desconectado, κ = 0 por definicion. Como las tres redes lo "
         "estan, se reporta ademas κ calculada **sobre la componente conexa mayor**, que es "
         "la cifra interpretable en una red fragmentada, junto con la conectividad por "
         "aristas (teorema de Menger) y el clustering medio como medida de cohesion local."),
        ("table", "Tabla 40. Medidas de cohesion de las tres redes",
         ["Medida", "Bipartita", "Proy. autor-autor", "Proy. video-video"],
         [["Grafo conexo",
           "no" if not b["grafo_conexo"] else "si",
           "no" if not ap["grafo_conexo"] else "si",
           "no" if not vp["grafo_conexo"] else "si"],
          ["κ global (conectividad por nodos)", fmt(b["conectividad_por_nodos_global"]),
           fmt(ap["conectividad_por_nodos_global"]), fmt(vp["conectividad_por_nodos_global"])],
          ["κ en la componente mayor", fmt(b["conectividad_por_nodos_componente_mayor"]),
           fmt(ap["conectividad_por_nodos_componente_mayor"]),
           fmt(vp["conectividad_por_nodos_componente_mayor"])],
          ["Conectividad por aristas en la componente mayor",
           fmt(b["conectividad_por_aristas_componente_mayor"]),
           fmt(ap["conectividad_por_aristas_componente_mayor"]),
           fmt(vp["conectividad_por_aristas_componente_mayor"])],
          ["Puntos de articulacion en la componente mayor",
           fmt(b["n_puntos_articulacion_componente_mayor"]),
           fmt(ap["n_puntos_articulacion_componente_mayor"]),
           fmt(vp["n_puntos_articulacion_componente_mayor"])],
          ["Puentes (aristas) en la componente mayor",
           fmt(b["n_puentes_componente_mayor"]), fmt(ap["n_puentes_componente_mayor"]),
           fmt(vp["n_puentes_componente_mayor"])],
          ["Clustering medio (cohesion local)", fmt(b["clustering_medio"], 4),
           fmt(ap["clustering_medio"], 4), fmt(vp["clustering_medio"], 4)],
          ["Diametro de la componente mayor", fmt(b["diametro_componente_mayor"]),
           fmt(ap["diametro_componente_mayor"]), fmt(vp["diametro_componente_mayor"])],
          ["Longitud media de camino en la componente mayor",
           fmt(b["longitud_media_camino_componente_mayor"], 3),
           fmt(ap["longitud_media_camino_componente_mayor"], 3),
           fmt(vp["longitud_media_camino_componente_mayor"], 3)]]),
        ("p",
         f"**La cohesion es minima en las tres redes.** κ global es 0 porque ninguna es "
         f"conexa, y κ en la componente mayor es "
         f"{fmt(b['conectividad_por_nodos_componente_mayor'])} en las tres: existe **un "
         f"solo nodo** cuya eliminacion parte la componente principal. La componente mayor "
         f"de la bipartita tiene {fmt(b['n_puntos_articulacion_componente_mayor'])} nodos "
         f"con esa propiedad, la de autores {fmt(ap['n_puntos_articulacion_componente_mayor'])} "
         f"y la de videos {fmt(vp['n_puntos_articulacion_componente_mayor'])}."),
        ("p",
         f"Un contraste ilustrativo: en la proyeccion de autores, κ por nodos es "
         f"{fmt(ap['conectividad_por_nodos_componente_mayor'])} pero la conectividad por "
         f"aristas es {fmt(ap['conectividad_por_aristas_componente_mayor'])}. Es decir, hay "
         "que cortar cinco vinculos para partirla, pero basta retirar a una persona. Esa "
         "asimetria es la firma de una red sostenida por individuos concretos y no por una "
         "malla redundante de relaciones."),
        ("h2", "10.3 Distribucion de grados"),
        ("figure", "13_degree_distribution_bipartite.png"),
        ("figure", "18_degree_distribution_authors.png"),
        ("figure", "19_degree_distribution_videos.png"),
        ("table", "Tabla 41. Distribucion de grados: mediana frente a maximo",
         ["Red", "Grado medio", "Mediana", "p75", "p90", "p99", "Max", "Gini del grado",
          "% con grado 1", "% con grado ≤ 2"],
         [["Bipartita", fmt(b["grado_medio"], 2), fmt(b["grado_mediano"]),
           fmt(b["grado_p75"]), fmt(b["grado_p90"]), fmt(b["grado_p99"], 1),
           fmt(b["grado_max"]), fmt(b["grado_gini"], 4), pct(b["pct_nodos_grado_1"]),
           pct(b["pct_nodos_grado_menor_igual_2"])],
          ["Proy. autor-autor", fmt(ap["grado_medio"], 2), fmt(ap["grado_mediano"]),
           fmt(ap["grado_p75"]), fmt(ap["grado_p90"]), fmt(ap["grado_p99"], 1),
           fmt(ap["grado_max"]), fmt(ap["grado_gini"], 4), pct(ap["pct_nodos_grado_1"]),
           pct(ap["pct_nodos_grado_menor_igual_2"])],
          ["Proy. video-video", fmt(vp["grado_medio"], 2), fmt(vp["grado_mediano"]),
           fmt(vp["grado_p75"]), fmt(vp["grado_p90"]), fmt(vp["grado_p99"], 1),
           fmt(vp["grado_max"]), fmt(vp["grado_gini"], 4), pct(vp["pct_nodos_grado_1"]),
           pct(vp["pct_nodos_grado_menor_igual_2"])]]),
        ("p",
         f"**El promedio de la red bipartita miente.** Su grado medio es "
         f"{fmt(b['grado_medio'], 2)}, un numero que sugiere que un nodo tipico tiene dos "
         f"vecinos. La mediana es {fmt(b['grado_mediano'])} y el "
         f"{pct(b['pct_nodos_grado_1'])} de los nodos tiene grado exactamente 1, mientras "
         f"que el maximo es {fmt(b['grado_max'])}. La media esta arrastrada por los "
         "nodos de video, que tienen un grado promedio de "
         f"{fmt(b['grado_medio_videos'], 1)} frente a {fmt(b['grado_medio_autores'], 2)} de "
         "los autores. Por eso el histograma y la ECDF de la figura 19 son necesarios: "
         "muestran una distribucion en L, no una campana."),
        ("p",
         f"La respuesta a la pregunta del inciso 6.1 («¿la mayoria tiene pocas conexiones o "
         f"estan concentradas en unos pocos?») es inequivoca: **estan concentradas**. El "
         f"Gini del grado en la bipartita es {fmt(b['grado_gini'], 4)} y en la proyeccion de "
         f"videos {fmt(vp['grado_gini'], 4)}. La asortatividad de grado de la bipartita es "
         f"{fmt(b['assortatividad_de_grado'], 4)}, claramente negativa, lo que confirma la "
         "estructura de estrella: los nodos de grado alto (videos) se conectan con nodos de "
         "grado bajo (autores de un solo comentario), no entre si."),
        ("p",
         f"En la proyeccion de autores el patron se invierte: la asortatividad es "
         f"{fmt(ap['assortatividad_de_grado'], 4)}, fuertemente positiva. Tambien es un "
         "artefacto de las cliques: todos los miembros de la audiencia de un video tienen el "
         "mismo grado, asi que se conectan con nodos de grado identico al propio."),
        ("h2", "10.4 Fragmentacion, nodos perifericos y aislados"),
        ("table", "Tabla 42. Componentes conexas de las tres redes",
         ["Red", "N.º de componentes", "Tamano de la mayor", "% de nodos en la mayor",
          "Tamanos de todas las componentes"],
         [["Bipartita", fmt(b["n_componentes"]), fmt(b["tamano_componente_mayor"]),
           pct(b["pct_nodos_en_componente_mayor"]),
           ", ".join(fmt(x) for x in b["tamanos_componentes"])],
          ["Proy. autor-autor", fmt(ap["n_componentes"]), fmt(ap["tamano_componente_mayor"]),
           pct(ap["pct_nodos_en_componente_mayor"]),
           ", ".join(fmt(x) for x in ap["tamanos_componentes"])],
          ["Proy. video-video", fmt(vp["n_componentes"]), fmt(vp["tamano_componente_mayor"]),
           pct(vp["pct_nodos_en_componente_mayor"]),
           ", ".join(fmt(x) for x in vp["tamanos_componentes"])]]),
        ("p",
         f"Las tres redes tienen el mismo numero de componentes ({fmt(b['n_componentes'])}), "
         "y no es coincidencia: la particion en componentes de la bipartita determina la de "
         "sus proyecciones. La componente mayor de la bipartita reune "
         f"{fmt(b['tamano_componente_mayor'])} nodos "
         f"({pct(b['pct_nodos_en_componente_mayor'])}), y las nueve restantes son estrellas "
         "aisladas de entre 2 y 26 nodos, es decir, videos cuya audiencia recolectada no "
         "coincide con la de ningun otro video de la muestra."),
        ("table", "Tabla 43. Nodos perifericos y aislados",
         ["Metrica", "Valor"],
         [["Autores con grado 1 en la bipartita (comentaron un solo video)",
           f"{fmt(per['n_autores_grado_1_en_bipartita'])} "
           f"({pct(per['pct_autores_grado_1_en_bipartita'])})"],
          ["Videos aislados en la proyeccion video-video",
           f"{fmt(per['n_videos_aislados_proyeccion'])} "
           f"({pct(per['pct_videos_aislados_proyeccion'])})"],
          ["Autores aislados en la proyeccion autor-autor",
           fmt(per["n_autores_aislados_proyeccion"])],
          ["Componentes pequenas (≤ 5 nodos) en la proyeccion de autores",
           fmt(per["n_componentes_pequenas_author_projection"])],
          ["Nodos aislados en la bipartita", fmt(b["n_nodos_aislados"])]]),
        ("p",
         f"Los {fmt(per['n_autores_aislados_proyeccion'])} autores aislados en la "
         "proyeccion de autores son un caso interesante: son personas que comentaron un "
         "video del que **son el unico comentarista recolectado**, de modo que no comparten "
         "audiencia con nadie. En la bipartita no estan aislados (tienen su arista al "
         "video); en la proyeccion si."),
        ("table", "Tabla 44. Videos sin audiencia compartida observada",
         ["Video", "Canal", "Comentarios obs.", "Autores obs."],
         [[trunc(v["titulo"], 44), trunc(v["canal"], 24),
           fmt(v["n_comentarios_observados"]), fmt(v["n_autores_observados"])]
          for v in per["videos_aislados_en_proyeccion_video"]]),
        ("callout",
         f"**Aislamiento observado no es aislamiento real.** {per['distincion_aislamiento']}\n\n"
         "El caso mas claro de la tabla 44 es «Plan 2032 Ciudad de Guatemala»: tiene 25 "
         "comentarios de 25 autores distintos y 304 089 visualizaciones, es el video mas "
         "visto de toda la muestra, y sin embargo aparece completamente aislado. La razon "
         "no es que su publico sea ajeno al resto: es que ninguno de esos 25 autores "
         "aparece tambien en otro de los 19 videos con comentarios recolectados. Con 274 "
         "videos sin comentarios recolectados, la probabilidad de detectar solapamiento es "
         "estructuralmente baja."),
        ("h2", "10.5 Interpretacion de los hallazgos estructurales"),
        ("p",
         "Los numeros de esta seccion apuntan todos en la misma direccion y admiten una "
         "lectura unica. **La participacion observada en YouTube no forma una comunidad "
         "conversacional: forma un conjunto de audiencias paralelas.**"),
        ("bullets", [
            f"**No hay red conversacional porque no hay reincidencia.** El "
            f"{pct(b['pct_nodos_grado_1'])} de los nodos tiene grado 1, y de los "
            f"{fmt(b['n_nodos_tipo_autor'])} autores solo 9 comentaron en mas de un video. Sin "
            "reincidencia entre contenidos no puede existir una estructura de red rica: la "
            "topologia esta determinada por ese hecho.",
            f"**La estructura de estrella es el hallazgo, no un defecto.** Asortatividad "
            f"{fmt(b['assortatividad_de_grado'], 3)}, transitividad 0 y clustering "
            f"bipartito {fmt(b['clustering_bipartito_latapy_medio'], 3)} describen "
            "consistentemente videos-hub rodeados de comentaristas de una sola aparicion. "
            "Es como se ve el consumo de contenido, no la sociabilidad.",
            f"**La red es extremadamente fragil.** κ = 1 en la componente mayor de las tres "
            f"redes y {fmt(b['n_puntos_articulacion_componente_mayor'])} puntos de "
            "articulacion en la bipartita significan que la conectividad depende de "
            "individuos concretos. En una red social robusta habria caminos redundantes; "
            "aqui la eliminacion de una persona parte el grafo.",
            f"**La fragmentacion es en parte real y en parte de muestreo, y hay que "
            f"separarlas.** Es real que la mayoria de la gente comenta un solo video: eso "
            "se observa directamente. Es de muestreo que 9 de 19 videos aparezcan aislados: "
            "con cobertura de comentarios en 274 videos mas, muchas de esas conexiones "
            "podrian materializarse.",
            f"**El diametro de {fmt(b['diametro_componente_mayor'])} y la longitud media de "
            f"camino de {fmt(b['longitud_media_camino_componente_mayor'], 2)} en la "
            "bipartita describen una cadena larga, no un mundo pequeno.** En redes sociales "
            "densas la longitud media de camino es de 4 a 6 con millones de nodos; aqui es "
            "casi 5 con 286. La informacion, si circulara por estos vinculos, tendria que "
            "recorrer muchos pasos.",
        ]),
        ("pagebreak",),
    ]


def _topo_rows(b: dict, ap: dict, vp: dict) -> list:
    keys = [
        ("Tipo de red", "tipo", None), ("Nodos", "n_nodos", 0),
        ("Aristas", "n_aristas", 0), ("Suma de pesos", "suma_pesos", 0),
        ("Densidad", "densidad", 5), ("Grado medio", "grado_medio", 3),
        ("Grado mediano", "grado_mediano", 0), ("Grado maximo", "grado_max", 0),
        ("Fuerza media", "fuerza_media", 3), ("Fuerza maxima", "fuerza_max", 0),
        ("Componentes conexas", "n_componentes", 0),
        ("Tamano de la componente mayor", "tamano_componente_mayor", 0),
        ("% de nodos en la componente mayor", "pct_nodos_en_componente_mayor", 2),
        ("Nodos aislados", "n_nodos_aislados", 0),
        ("Transitividad global", "transitividad_global", 6),
        ("Clustering medio", "clustering_medio", 6),
        ("Clustering medio ponderado", "clustering_medio_ponderado", 6),
        ("Asortatividad de grado", "assortatividad_de_grado", 4),
        ("Diametro (componente mayor)", "diametro_componente_mayor", 0),
        ("Longitud media de camino (comp. mayor)",
         "longitud_media_camino_componente_mayor", 4),
        ("κ global (cohesion)", "conectividad_por_nodos_global", 0),
        ("κ en la componente mayor", "conectividad_por_nodos_componente_mayor", 0),
    ]
    rows = []
    for lab, k, dec in keys:
        vals = []
        for d in (b, ap, vp):
            v = d.get(k)
            vals.append(str(v) if dec is None else fmt(v, dec))
        rows.append([lab] + vals)
    rows.append(["Densidad bipartita (|A|·|B|)",
                 fmt(b["densidad_bipartita"], 5), "no aplica", "no aplica"])
    rows.append(["Clustering bipartito de Latapy",
                 fmt(b["clustering_bipartito_latapy_medio"], 4), "no aplica", "no aplica"])
    return rows


def comunidades(c: Ctx) -> list:
    cm = c.m("communities")
    vpm, apm = cm["video_projection"], cm["author_projection"]
    rob = cm["robustez_video_projection"]
    cmp_ = cm["author_projection_vs_particion_por_video"]
    cs = c.t("community_summary")
    tf = c.t("community_tfidf_terms")
    det = c.m("community_characterization")
    nt = cs[~cs.es_singleton].nlargest(3, "n_comentarios_observados")

    els: list = [
        ("h1", "11. Comunidades"),
        ("h2", "11.1 Eleccion de la red y justificacion"),
        ("p",
         "**La deteccion de comunidades se hace sobre la proyeccion video-video "
         "ponderada.** Las tres razones son:"),
        ("bullets", [
            "**Es la unica red cuyas comunidades tienen una interpretacion sustantiva.** "
            "Una comunidad en esta red es un grupo de videos que comparten publico, y puede "
            "caracterizarse simultaneamente por titulo, canal, categoria, consulta de "
            "recoleccion, palabras de sus comentarios y distribucion de sentimiento.",
            "**La red bipartita no admite modularidad estandar.** La formulacion clasica "
            "de modularidad compara las aristas dentro de una comunidad con las esperadas "
            "bajo un modelo de configuracion que asume que cualquier par de nodos puede "
            "conectarse. En una red bipartita eso es falso, y aplicar la formula sin "
            "adaptarla produce un numero sin significado.",
            "**Las comunidades de la proyeccion autor-autor no aportan informacion nueva.** "
            "Esto no se afirma por intuicion: se comprobo. Ver el contraste mas abajo.",
        ]),
        ("table", "Tabla 45. Comprobacion de que las comunidades de autores son triviales",
         ["Metrica", "Valor", "Lectura"],
         [["Comunidades de Louvain en la proyeccion autor-autor",
           fmt(cmp_["n_comunidades_louvain"]), "—"],
          ["Grupos de la etiqueta trivial «en que video comento»",
           fmt(cmp_["n_grupos_de_la_etiqueta_trivial"]), "—"],
          ["NMI entre ambas particiones", fmt(cmp_["nmi_con_particion_por_video"], 4),
           "Muy alto"],
          ["ARI entre ambas particiones", fmt(cmp_["ari_con_particion_por_video"], 4),
           "Muy alto (corregido por azar)"],
          ["Modularidad ponderada de la particion de autores",
           fmt(apm["modularidad_ponderada"], 4), "—"]]),
        ("p",
         f"Con NMI = {fmt(cmp_['nmi_con_particion_por_video'], 3)} y "
         f"ARI = {fmt(cmp_['ari_con_particion_por_video'], 3)} respecto de la etiqueta "
         "trivial «en que video comento este autor», las comunidades de la proyeccion de "
         "autores son esencialmente una relectura de la particion por video. Es lo esperado, "
         "porque la proyeccion crea una clique por video: Louvain no puede sino recuperarlas. "
         "Se reportan de todos modos como analisis complementario, pero el analisis principal "
         "es el de la proyeccion de videos."),
        ("h2", "11.2 Algoritmo, supuestos y tratamiento de los pesos"),
        ("table", "Tabla 46. Configuracion del algoritmo de comunidades",
         ["Parametro", "Valor"],
         [["Algoritmo", vpm["algoritmo"]],
          ["Libreria y version", vpm["libreria"]],
          ["Atributo de peso", f"`{vpm['peso_usado']}` = {vpm['significado_peso']}"],
          ["Resolucion", fmt(vpm["resolucion"], 1)],
          ["Semilla", fmt(vpm["semilla"])]]),
        ("p",
         "**Supuestos de Louvain que conviene tener presentes.** Optimiza modularidad "
         "mediante agregacion voraz en dos fases, lo que implica: (a) las comunidades son "
         "**no solapadas**, cada video pertenece a exactamente una, supuesto discutible para "
         "audiencias que podrian solaparse; (b) el resultado depende del orden de "
         "recorrido, por lo que la semilla se fija en 42; (c) sufre el **limite de "
         "resolucion**, es decir, no detecta comunidades sustancialmente menores que "
         "√(2m), lo que en una red de 11 aristas es una limitacion severa; (d) la "
         "modularidad tiene un maximo alto por azar en redes dispersas, asi que su valor "
         "absoluto no debe leerse como evidencia de estructura fuerte."),
        ("p",
         f"**Tratamiento de los pesos.** El peso de la proyeccion video-video es el numero "
         f"de autores compartidos, es decir, una **intensidad**: mas peso significa vinculo "
         f"mas fuerte. Esa es precisamente la semantica que la modularidad ponderada espera, "
         f"asi que el peso se pasa directamente sin transformar. (En el analisis de "
         f"centralidad de la seccion 12 la situacion es distinta y si requiere invertirlo.) "
         f"Se reportan las dos modularidades: ponderada Q = "
         f"{fmt(vpm['modularidad_ponderada'], 4)} y no ponderada "
         f"Q = {fmt(vpm['modularidad_no_ponderada'], 4)}."),
        ("h2", "11.3 Resultado: numero, tamanos y calidad"),
        ("table", "Tabla 47. Resultado de la deteccion de comunidades",
         ["Metrica", "Proy. video-video (principal)", "Proy. autor-autor (complementaria)"],
         [["Comunidades detectadas", fmt(vpm["n_comunidades"]), fmt(apm["n_comunidades"])],
          ["Tamanos", ", ".join(fmt(x) for x in vpm["tamanos"]),
           ", ".join(fmt(x) for x in apm["tamanos"])],
          ["Modularidad ponderada", fmt(vpm["modularidad_ponderada"], 4),
           fmt(apm["modularidad_ponderada"], 4)],
          ["Modularidad no ponderada", fmt(vpm["modularidad_no_ponderada"], 4),
           fmt(apm["modularidad_no_ponderada"], 4)],
          ["Comunidades singleton", fmt(vpm["n_singletons"]), fmt(apm["n_singletons"])],
          ["% de nodos en singletons", pct(vpm["pct_nodos_en_singletons"]),
           pct(apm["pct_nodos_en_singletons"])],
          ["Comunidades no triviales (> 1 nodo)", fmt(vpm["n_comunidades_no_triviales"]),
           fmt(apm["n_comunidades_no_triviales"])],
          ["Comunidad mayor", fmt(vpm["tamano_comunidad_mayor"]),
           fmt(apm["tamano_comunidad_mayor"])],
          ["Tamano medio", fmt(vpm["tamano_medio_comunidad"], 2),
           fmt(apm["tamano_medio_comunidad"], 2)]]),
        ("callout",
         f"**Los {fmt(vpm['n_singletons'])} singletons se reportan explicitamente y no se "
         f"descartan.** Representan el {pct(vpm['pct_nodos_en_singletons'])} de los videos: "
         "contenidos cuya audiencia recolectada no coincide con la de ningun otro video de "
         "la muestra. Ocultarlos inflaria artificialmente la cobertura de las comunidades "
         f"«reales», que es del {pct(vpm['cobertura_comunidades_no_triviales_pct'])}. "
         "Aparecen en la figura 22, en la tabla 49 y en "
         "`results/tables/community_summary.csv`."),
        ("h3", "Robustez de la particion"),
        ("table", "Tabla 48. Comparacion con otros algoritmos de deteccion",
         ["Algoritmo", "Comunidades", "Tamanos", "Q ponderada", "NMI con Louvain"],
         [["Louvain (principal)", fmt(vpm["n_comunidades"]),
           ", ".join(fmt(x) for x in vpm["tamanos"]),
           fmt(vpm["modularidad_ponderada"], 4), "1.0 (referencia)"],
          ["Greedy modularity (CNM)", fmt(rob["greedy_modularity_n_comunidades"]),
           ", ".join(fmt(x) for x in rob["greedy_modularity_tamanos"]),
           fmt(rob["greedy_modularity_Q"], 4), fmt(rob["nmi_louvain_vs_greedy"], 4)],
          ["Label propagation asincrona", fmt(rob["label_propagation_n_comunidades"]),
           ", ".join(fmt(x) for x in rob["label_propagation_tamanos"]),
           "no aplica", fmt(rob["nmi_louvain_vs_label_propagation"], 4)],
          ["Componentes conexas (referencia estructural)",
           fmt(len(rob["componentes_conexas"])),
           ", ".join(fmt(x) for x in rob["componentes_conexas"]), "no aplica", "—"]]),
        ("p",
         f"Louvain y greedy modularity devuelven **exactamente la misma particion** "
         f"(NMI = {fmt(rob['nmi_louvain_vs_greedy'], 2)}), y label propagation coincide en "
         f"gran medida (NMI = {fmt(rob['nmi_louvain_vs_label_propagation'], 4)}), "
         "diferenciandose solo en que fusiona la componente conexa entera en un unico "
         "grupo. La coincidencia entre dos algoritmos independientes indica que la particion "
         "no es un artefacto de Louvain. La comparacion con las componentes conexas es igual "
         "de informativa: la componente mayor de 10 videos se subdivide en tres comunidades, "
         "de modo que Louvain **si** encuentra estructura interna y no se limita a devolver "
         "las componentes."),
        ("h2", "11.4 Visualizacion de todas las comunidades"),
        ("figure", "20_video_communities.png"),
        ("figure", "21_community_sizes.png"),
        ("p",
         f"La figura 22 muestra las {fmt(vpm['n_comunidades'])} comunidades, singletons "
         "incluidos, con el numero de autores compartidos sobre cada arista. La figura 23 "
         "contrasta tamano con intensidad y revela que **no son la misma cosa**: la "
         f"comunidad con mas videos ({fmt(nt.n_videos.iloc[0])}) es tambien la de mas "
         f"comentarios ({fmt(nt.n_comentarios_observados.iloc[0])}), pero varias comunidades "
         "singleton acumulan mas comentarios que C2, que tiene tres videos."),
        ("h2", "11.5 Caracterizacion de las tres comunidades principales"),
        ("p", det["justificacion_top3"]),
    ]

    for i, r in enumerate(nt.itertuples()):
        terms = tf[tf.grupo == r.comunidad_id].nsmallest(10, "rango")
        els += [
            ("h3", f"Comunidad {r.comunidad_id}"),
            ("table", f"Tabla {49 + i}. Perfil completo de {r.comunidad_id}",
             ["Dimension", "Valor"],
             [["Videos", fmt(r.n_videos)],
              ["Titulos", r.titulos],
              ["Canales", f"{fmt(r.n_canales)} — {r.canales}"],
              ["Categorias de YouTube", r.categorias],
              ["Consultas de recoleccion", r.source_queries],
              ["Comentarios observados",
               f"{fmt(r.n_comentarios_observados)} ({pct(r.pct_de_comentarios)} del total)"],
              ["Autores unicos", fmt(r.n_autores_unicos)],
              ["Autores en mas de un video de la comunidad",
               fmt(r.n_autores_en_mas_de_un_video_de_la_comunidad)],
              ["Intensidad: comentarios por video", fmt(r.comentarios_por_video, 2)],
              ["Intensidad: comentarios por autor", fmt(r.comentarios_por_autor, 3)],
              ["«Me gusta» acumulados / medianos",
               f"{fmt(r.n_me_gusta)} / {fmt(r.me_gusta_medianos)}"],
              ["Respuestas acumuladas", fmt(r.n_respuestas)],
              ["Visualizaciones totales / medianas",
               f"{fmt(r.views_totales)} / {fmt(r.views_medianas)}"],
              ["Aristas internas / peso interno",
               f"{fmt(r.aristas_internas)} / {fmt(r.peso_interno_total)}"],
              ["Densidad interna", fmt(r.densidad_interna, 4)],
              ["Longitud mediana del comentario",
               f"{fmt(r.longitud_mediana_comentario)} caracteres"],
              ["Terminos distintivos (TF-IDF de los comentarios)",
               ", ".join(terms.termino.tolist())],
              ["Keywords y titulos distintivos (TF-IDF del contenido publicado)",
               r.top_keywords_tfidf],
              ["Palabras mas frecuentes", r.top_palabras],
              ["Bigramas mas frecuentes", r.top_bigramas],
              ["Hashtags en los comentarios", r.hashtags_en_comentarios],
              ["Sentimiento",
               f"NEG {pct(r.pct_NEG)} · NEU {pct(r.pct_NEU)} · POS {pct(r.pct_POS)} "
               f"(n = {fmt(r.n_sentimiento)}, polaridad neta {r.polaridad_neta:+.1f}, "
               f"confianza media {fmt(r.confianza_media_sentimiento, 3)})"],
              ["Comparable estadisticamente (n ≥ 10)",
               "si" if r.comparable_n_mayor_igual_10 else "NO"]]),
        ]

    els += [
        ("h3", "Lectura conjunta de las tres comunidades"),
        ("p",
         "Las tres comunidades se ordenan a lo largo de un eje reconocible: **la relacion "
         "del comentarista con el poder institucional**. C0 agrupa contenido que fiscaliza "
         "al Congreso y a la justicia, y es la mas negativa; C1 agrupa la comunicacion "
         "directa del Ejecutivo y es la mas mixta, con apoyo explicito conviviendo con "
         "impaciencia; C2 agrupa contenido sobre regulacion economica y movilidad urbana, "
         "temas donde la critica se dirige a empresas mas que a funcionarios, y es la de "
         "mayor proporcion de comentarios positivos."),
        ("p",
         "La etiqueta tematica de cada comunidad se sostiene en evidencia convergente y no "
         "en una impresion: los terminos TF-IDF de los comentarios, los bigramas, las "
         "keywords del contenido publicado y los titulos de los videos apuntan al mismo "
         "campo semantico en los tres casos. Cuando esa convergencia no existe, la etiqueta "
         "no se pone: los nueve singletons se describen por su contenido individual, sin "
         "asignarles un tema de comunidad que no puede sostenerse con un solo video."),
        ("h2", "11.6 Las comunidades singleton"),
        ("table", "Tabla 52. Los nueve videos que forman comunidades de un solo elemento",
         ["Com.", "Video", "Canal", "Com. obs.", "Autores", "% NEG", "% NEU", "% POS"],
         [[s["comunidad_id"], trunc(s["titulos"], 38), trunc(s["canales"], 22),
           fmt(s["n_comentarios_observados"]), fmt(s["n_autores_unicos"]),
           pct(s["pct_NEG"]), pct(s["pct_NEU"]), pct(s["pct_POS"])]
          for s in det["singletons"]]),
        ("p",
         "Dos de estos singletons son notables. **«Plan 2032 Ciudad de Guatemala»** (25 "
         "comentarios, 25 autores) es el video mas visto de toda la muestra y el unico con "
         "polaridad claramente positiva; su aislamiento estructural conviviendo con su "
         "altisima visibilidad es la mejor ilustracion de que la posicion en la red no se "
         "deriva de la popularidad. **«EE.UU. envia a mexicanos deportados a Guatemala»** "
         "(25 comentarios, 18 autores, canal Noticias Telemundo) es el unico contenido de "
         "un medio internacional y tambien queda aislado, lo que es consistente con que su "
         "audiencia sea distinta de la del resto del corpus."),
        ("pagebreak",),
    ]
    return els


def centralidad(c: Ctx) -> list:
    cen = c.m("centrality_summary")
    just = cen["justificacion_medidas"]
    ac = c.t("author_centrality")
    vc = c.t("video_centrality")
    arts = c.t("articulation_points")

    return [
        ("h1", "12. Nodos centrales y participantes puente"),
        ("h2", "12.1 Medidas elegidas y por que"),
        ("table", "Tabla 53. Medidas de centralidad calculadas y su justificacion",
         ["Medida", "Que mide y por que se usa aqui"],
         [["Grado", just["degree"]],
          ["Fuerza (grado ponderado)", just["strength"]],
          ["Betweenness", just["betweenness"]],
          ["Closeness (Wasserman-Faust)", just["closeness_wf"]],
          ["Harmonic centrality", just["harmonic"]],
          ["PageRank", just["pagerank"]],
          ["Eigenvector", just["eigenvector"]],
          ["Numero de k-core", just["k_core"]],
          ["Puntos de articulacion", just["articulation_points"]]]),
        ("callout",
         f"**El punto tecnico que decide si los resultados son correctos o no.** "
         f"{just['transformacion_de_pesos']}\n\n"
         "Concretamente: dos videos que comparten 2 autores estan **mas** relacionados que "
         "dos que comparten 1, pero si se le pasa `weight=2` a un algoritmo de camino mas "
         "corto, el algoritmo entiende que estan al **doble de distancia**. El resultado "
         "seria el inverso del correcto. Por eso se construye `distance = 1/weight` y esa es "
         "la que se usa en betweenness, closeness y harmonic; el peso sin transformar se usa "
         "en fuerza, PageRank y eigenvector, donde la semantica de intensidad es la "
         "correcta."),
        ("p",
         "**Tratamiento de los grafos desconectados.** Las tres redes tienen 10 componentes, "
         "lo que rompe la definicion clasica de closeness (la distancia a un nodo "
         "inalcanzable es infinita y su inverso indefinido). Se resolvio de tres formas "
         "complementarias: betweenness de networkx suma por componente de manera nativa; "
         "closeness se calcula con la correccion de Wasserman-Faust (`wf_improved=True`), "
         "que escala por el tamano de la componente alcanzable; y se agrega harmonic "
         "centrality, que suma reciprocos de distancias y por tanto esta bien definida con "
         "distancias infinitas. Cada nodo lleva ademas su identificador de componente y el "
         "tamano de esta, para que ningun ranking se lea entre componentes distintas sin "
         "advertirlo."),
        ("figure", "23_centrality_correlation.png"),
        ("p",
         "La matriz de correlacion de rangos justifica calcular varias medidas en lugar de "
         "una. Grado, fuerza, PageRank y eigenvector correlacionan casi perfectamente entre "
         "si: en estas redes miden lo mismo, y usar una u otra no cambia el ranking. "
         "**Betweenness se separa claramente del bloque**, lo que confirma que captura una "
         "propiedad distinta —estar en el camino entre grupos— y que es la medida pertinente "
         "para identificar puentes. Es la evidencia de por que un ranking de grado no basta "
         "para llamar «puente» a un nodo."),
        ("h2", "12.2 Autores: recurrencia, diversidad e intermediacion"),
        ("figure", "22_centrality.png"),
        ("p",
         "Para los autores conviene separar cuatro cosas que suelen confundirse en un solo "
         "concepto de «usuario activo»:"),
        ("table", "Tabla 54. Cuatro dimensiones distintas de la participacion de un autor",
         ["Dimension", "Como se mide", "Valor en estos datos"],
         [["Recurrencia", "Numero de comentarios publicados",
           f"{fmt(cen['n_autores_recurrentes'])} autores con mas de uno; maximo 6"],
          ["Amplitud de contenido", "Numero de videos distintos comentados",
           f"{fmt(cen['n_autores_multivideo'])} autores en mas de un video; maximo 3"],
          ["Diversidad de emisores", "Numero de canales distintos comentados",
           f"{fmt(cen['n_autores_multicanal'])} autores en mas de un canal; maximo 2"],
          ["Papel estructural", "Betweenness y condicion de puente verificado",
           f"{fmt(cen['autores_con_betweenness_positiva'])} con betweenness > 0 "
           f"({pct(cen['pct_autores_con_betweenness_positiva'])}); "
           f"{fmt(cen['n_autores_puente_verificados'])} puentes verificados"]]),
        ("p",
         "**Las cuatro dimensiones no coinciden**, y ahi esta el hallazgo. Un autor puede "
         "ser muy recurrente y estructuralmente irrelevante: el mas activo del conjunto "
         "publico 6 comentarios, todos en el mismo video, y tiene betweenness 0. A la "
         "inversa, un autor con 2 comentarios en 2 videos de canales distintos puede ser el "
         "unico vinculo entre dos bloques de contenido. **Actividad y centralidad "
         "estructural son propiedades independientes en esta muestra.**"),
        ("table", "Tabla 55. Top 10 autores por betweenness ponderada",
         ["#", "Handle", "Com.", "Videos", "Canales", "Grado", "Fuerza", "Betweenness",
          "PageRank", "Articulacion"],
         [[str(i + 1), r["handle"], fmt(r["n_comentarios_observados"]),
           fmt(r["n_videos_comentados"]), fmt(r["n_canales_comentados"]),
           fmt(r["degree"]), fmt(r["strength"]), fmt(r["betweenness_ponderada"], 5),
           fmt(r["pagerank"], 5), "si" if r["es_punto_articulacion"] else "no"]
          for i, r in enumerate(cen["top_autores_betweenness"])]),
        ("table", "Tabla 56. Top 10 autores por recurrencia (numero de comentarios)",
         ["#", "Handle", "Com.", "Videos", "Canales", "Betweenness"],
         [[str(i + 1), r["handle"], fmt(r["n_comentarios_observados"]),
           fmt(r["n_videos_comentados"]), fmt(r["n_canales_comentados"]),
           fmt(r["betweenness_ponderada"], 5)]
          for i, r in enumerate(cen["top_autores_recurrencia"])]),
        ("p",
         "El contraste entre las tablas 55 y 56 es directo: casi ninguno de los autores mas "
         "recurrentes aparece entre los de mayor intermediacion, y varios de los "
         "intermediadores tienen apenas 2 o 3 comentarios. La fuerza en la proyeccion de "
         "autores tampoco sirve como proxy: esta dominada por el tamano de la audiencia del "
         "video comentado, no por el papel del autor (quien comento el video de 128 "
         "comentaristas tiene fuerza altisima por el simple hecho de estar en esa clique)."),
        ("h2", "12.3 Autores puente: identificacion y verificacion"),
        ("p",
         f"Un autor se declara puente **solo si pasa una prueba de eliminacion**: se lo "
         f"retira de la red bipartita, se recalcula la proyeccion video-video y se cuenta si "
         f"aumento el numero de componentes conexas. De los "
         f"{fmt(cen['n_autores_multivideo'])} autores con mas de un video, "
         f"**{fmt(cen['n_autores_puente_verificados'])} superan la prueba**."),
        ("table", "Tabla 57. Todos los autores con participacion en mas de un video",
         ["Handle", "Com.", "Videos", "Canales", "Com.-dades", "Puente verificado",
          "Δ componentes", "Videos que conecta"],
         [[r["author_handle"], fmt(r["n_comentarios"]), fmt(r["n_videos_distintos"]),
           fmt(r["n_canales_distintos"]), fmt(r["n_comunidades_video_tocadas"]),
           "SI" if r["es_puente_verificado"] else "no",
           f"+{fmt(r['delta_componentes_al_eliminar'])}"
           if r["delta_componentes_al_eliminar"] else "0",
           trunc(r["titulos_videos"], 52)]
          for r in cen["autores_multivideo"]]),
        ("p",
         f"Dos de los nueve autores multivideo **no** son puentes: su conexion entre videos "
         f"esta duplicada por otro autor, de modo que retirarlos no parte nada. Es "
         "exactamente la distincion que la prueba de eliminacion permite hacer y que un "
         "ranking de grado no. Los siete restantes son, en el sentido estricto del "
         "enunciado, los participantes cuya eliminacion segmenta la red."),
        ("h2", "12.4 Videos: alcance y capacidad de conectar audiencias"),
        ("table", "Tabla 58. Centralidad de los videos en la proyeccion video-video",
         ["Video", "Canal", "Com. obs.", "Vistas", "Grado", "Fuerza", "Betweenness",
          "PageRank", "Articulacion"],
         [[trunc(r["display_name"], 34), trunc(r["channel_name"], 18),
           fmt(r["n_comentarios_observados"]), fmt(r["view_count"]), fmt(r["degree"]),
           fmt(r["strength"]), fmt(r["betweenness_ponderada"], 4),
           fmt(r["pagerank"], 4), "si" if r["es_punto_articulacion"] else "no"]
          for r in cen["top_videos_betweenness"]]),
        ("p",
         f"El alcance de un video dentro de la red **no se deriva de su popularidad**. "
         f"Como se cuantifico en la pregunta 7.5, la correlacion entre visualizaciones y "
         f"grado en la proyeccion no es significativa, mientras que la correlacion con el "
         f"numero de comentarios observados si lo es. El video mas visto de la muestra "
         f"(«Plan 2032 Ciudad de Guatemala», 304 089 vistas) tiene grado 0 y betweenness 0: "
         "no conecta con nada. El mas central es «Que rico come tu diputado», que tiene "
         "26 veces menos visualizaciones pero 161 comentarios recolectados."),
        ("h2", "12.5 Videos articuladores"),
        ("p",
         "Igual que con los autores, la condicion de articulador se verifica eliminando el "
         "nodo y recontando componentes. La tabla registra el estado antes y despues para "
         "que la afirmacion sea auditable:"),
        ("table", "Tabla 59. Nodos articuladores verificados por red",
         ["Red", "Nodo", "Canal", "Grado", "Comp. antes", "Comp. tras",
          "Delta", "Mayor antes", "Mayor tras", "Aislados tras"],
         [[_red_corta(r["red"]), trunc(r["display_name"], 28),
           trunc(r["channel_name"], 16), fmt(r["degree"]), fmt(r["componentes_antes"]),
           fmt(r["componentes_despues"]), f"+{fmt(r['delta_componentes'])}",
           fmt(r["componente_mayor_antes"]), fmt(r["componente_mayor_despues"]),
           fmt(r["nodos_aislados_tras_eliminar"])]
          for r in cen["articuladores_verificados"]
          if r["red"] == "proyeccion_video_video"]),
        ("p",
         f"En la proyeccion video-video hay "
         f"{fmt(cen['n_articuladores_por_red'].get('proyeccion_video_video', 0))} videos "
         f"articuladores de {fmt(len(vc))}. El de mayor impacto es «Que rico come tu "
         "diputado»: al eliminarlo, la componente mayor pasa de 10 a 4 videos y se generan "
         "nodos aislados nuevos. Ese video es el punto de paso de la mayor parte de la "
         "audiencia compartida del corpus, y no por su alcance publicitario sino porque es "
         "donde mas gente recolectada comento."),
        ("table", "Tabla 60. Numero de articuladores verificados por red",
         ["Red", "Articuladores verificados", "Nodos totales"],
         [[_red_corta(k), fmt(v),
           fmt(c.m("network_topology")[k]["n_nodos"])]
          for k, v in cen["n_articuladores_por_red"].items()]),
        ("p",
         f"La red bipartita tiene "
         f"{fmt(cen['n_articuladores_por_red'].get('bipartita_autor_video', 0))} nodos "
         "articuladores, que incluyen tanto videos como los autores puente. Es coherente "
         "con κ = 1 en su componente mayor: la conectividad de esta red depende de nodos "
         "individuales, no de redundancia estructural."),
        ("callout",
         "**Advertencia sobre la fragilidad de estos resultados.** Que un nodo sea "
         "articulador es una propiedad exacta *del grafo observado*, no una propiedad "
         "robusta del fenomeno. Todos los articuladores identificados lo son porque una "
         "unica persona sostiene una unica conexion. Con una recoleccion de comentarios mas "
         "completa, casi con certeza aparecerian conexiones alternativas y varios de estos "
         "nodos dejarian de ser criticos. Se reportan porque responden a lo que el "
         "enunciado pide y porque estan correctamente verificados, no porque describan una "
         "vulnerabilidad estructural de YouTube."),
        ("pagebreak",),
    ]


def _red_corta(k: str) -> str:
    return {"bipartita_autor_video": "Bipartita",
            "proyeccion_autor_autor": "Proy. autor-autor",
            "proyeccion_video_video": "Proy. video-video"}.get(k, k)
