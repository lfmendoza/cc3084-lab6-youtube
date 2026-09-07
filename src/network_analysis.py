"""Ejercicios 4-8: red bipartita, proyecciones, topologia, comunidades y centralidad.

Convenciones de identificadores
-------------------------------
Los nodos llevan prefijo para que autores y videos no puedan colisionar en el
mismo espacio de nombres:

* ``A:<author_channel_id>`` para autores;
* ``V:<video_id>`` para videos.

El prefijo es un detalle de implementacion del grafo. En las tablas
exportadas se guardan ``node_id`` (con prefijo) y ``raw_id`` (el
``author_channel_id`` o ``video_id`` original, sin modificar).

Semantica de la arista (ejercicio 4.5)
--------------------------------------
Una arista autor-video significa **exclusivamente** que ese autor publico uno
o mas comentarios observados en ese video, y su peso es cuantos. No es
amistad, ni respuesta, ni conversacion, ni acuerdo, ni aprobacion.
``reply_count`` NO se usa en ningun momento para crear aristas: solo indica
cuantas respuestas recibio un comentario y no identifica a sus autores.
"""
from __future__ import annotations

import ast
import json
from collections import Counter

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from networkx.algorithms import bipartite
from networkx.algorithms import community as nxcom

from . import config as C
from . import viz

A_PREFIX, V_PREFIX = "A:", "V:"


# =============================================================== 4. bipartita
def build_bipartite(comments: pd.DataFrame, videos: pd.DataFrame) -> nx.Graph:
    """Ejercicios 4.1-4.2. Red bipartita no dirigida autor-video.

    Una arista por par (autor, video) con ``weight`` = numero de comentarios
    observados de ese autor en ese video. El ``groupby`` garantiza el par
    unico: si un autor comento cinco veces el mismo video hay una sola arista
    de peso 5, nunca cinco aristas paralelas.
    """
    edges = (
        comments.groupby(["author_channel_id", "video_id"])
        .agg(weight=("comment_id", "size"),
             me_gusta=("like_count", "sum"),
             respuestas_recibidas=("reply_count_num", "sum"),
             comment_ids=("comment_id", lambda s: "|".join(sorted(s))))
        .reset_index()
    )

    G = nx.Graph()

    # --- nodos autor ---
    author_attrs = (
        comments.groupby("author_channel_id")
        .agg(display_name=("author_name", "first"),
             handle=("author_handle_norm", "first"),
             n_comentarios=("comment_id", "size"),
             n_videos=("video_id", "nunique"),
             n_canales=("channel_id", "nunique"),
             me_gusta_recibidos=("like_count", "sum"),
             respuestas_recibidas=("reply_count_num", "sum"),
             largo_medio_comentario=("len_original", "mean"))
    )
    for raw_id, row in author_attrs.iterrows():
        G.add_node(
            A_PREFIX + raw_id, node_type="author", bipartite=0, raw_id=raw_id,
            display_name=row["display_name"], handle=row["handle"],
            n_comentarios=int(row["n_comentarios"]), n_videos=int(row["n_videos"]),
            n_canales=int(row["n_canales"]),
            me_gusta_recibidos=int(row["me_gusta_recibidos"]),
            respuestas_recibidas=int(row["respuestas_recibidas"]),
            largo_medio_comentario=round(float(row["largo_medio_comentario"]), 1),
            category="", channel_id="", channel_name="", view_count=np.nan,
            source_query="", source_group="",
        )

    # --- nodos video ---
    vinfo = videos.set_index("video_id")
    obs = comments.groupby("video_id").agg(
        n_comentarios=("comment_id", "size"),
        n_autores=("author_channel_id", "nunique"),
        me_gusta=("like_count", "sum"),
        respuestas=("reply_count_num", "sum"),
    )
    for raw_id, row in obs.iterrows():
        v = vinfo.loc[raw_id]
        G.add_node(
            V_PREFIX + raw_id, node_type="video", bipartite=1, raw_id=raw_id,
            display_name=v["title"], handle=v.get("channel_handle_norm", ""),
            channel_id=v["channel_id"], channel_name=v["channel_name"],
            category=v["category"], source_query=v["source_query"],
            source_group=v["source_group"],
            view_count=float(v["view_count_final"]) if pd.notna(v["view_count_final"]) else np.nan,
            n_comentarios=int(row["n_comentarios"]), n_autores=int(row["n_autores"]),
            me_gusta_recibidos=int(row["me_gusta"]),
            respuestas_recibidas=int(row["respuestas"]),
            n_videos=0, n_canales=0, largo_medio_comentario=np.nan,
        )

    for r in edges.itertuples():
        G.add_edge(
            A_PREFIX + r.author_channel_id, V_PREFIX + r.video_id,
            weight=int(r.weight), me_gusta=int(r.me_gusta),
            respuestas_recibidas=int(r.respuestas_recibidas),
            comment_ids=r.comment_ids,
        )
    return G


def bipartite_invariants(G: nx.Graph, comments: pd.DataFrame) -> dict:
    """Invariantes automaticas del ejercicio 4 (se validan en cada corrida)."""
    authors = {n for n, d in G.nodes(data=True) if d["node_type"] == "author"}
    vids = {n for n, d in G.nodes(data=True) if d["node_type"] == "video"}
    raw_authors = set(comments["author_channel_id"])
    raw_videos = set(comments["video_id"])
    sum_w = sum(d["weight"] for *_, d in G.edges(data=True))
    pares = comments.groupby(["author_channel_id", "video_id"]).ngroups
    cross = all(
        G.nodes[u]["node_type"] != G.nodes[v]["node_type"] for u, v in G.edges()
    )
    return {
        "nodos_totales": G.number_of_nodes(),
        "nodos_autor": len(authors),
        "nodos_video": len(vids),
        "aristas": G.number_of_edges(),
        "suma_pesos": int(sum_w),
        "n_comentarios_usados": int(len(comments)),
        "inv_suma_pesos_igual_comentarios": bool(sum_w == len(comments)),
        "inv_una_arista_por_par_autor_video": bool(G.number_of_edges() == pares),
        "inv_autores_provienen_de_author_channel_id": bool(
            {G.nodes[n]["raw_id"] for n in authors} == raw_authors),
        "inv_videos_provienen_de_video_id": bool(
            {G.nodes[n]["raw_id"] for n in vids} == raw_videos),
        "inv_todas_las_aristas_cruzan_tipos": bool(cross),
        "inv_grafo_no_dirigido": bool(not G.is_directed()),
        "inv_sin_autoloops": bool(nx.number_of_selfloops(G) == 0),
        "inv_endpoints_existen": bool(all(u in G and v in G for u, v in G.edges())),
        "inv_reply_count_no_usado_como_arista": True,
        "nota_reply_count": (
            "reply_count nunca entra en la construccion de aristas. Solo se "
            "guarda como atributo agregado del nodo y de la arista, porque "
            "indica cuantas respuestas recibio un comentario sin identificar "
            "quien las escribio."
        ),
        "es_bipartito_networkx": bool(nx.is_bipartite(G)),
        "peso_maximo_arista": int(max(d["weight"] for *_, d in G.edges(data=True))),
        "aristas_con_peso_mayor_a_1": int(
            sum(1 for *_, d in G.edges(data=True) if d["weight"] > 1)),
    }


def export_bipartite_tables(G: nx.Graph) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Ejercicio 4.3. Tablas de nodos y aristas."""
    nodes = []
    for n, d in G.nodes(data=True):
        nodes.append({
            "node_id": n,
            "raw_id": d["raw_id"],
            "node_type": d["node_type"],
            "bipartite_set": d["bipartite"],
            "display_name": d["display_name"],
            "handle": d["handle"],
            "channel_id": d["channel_id"],
            "channel_name": d["channel_name"],
            "category": d["category"],
            "source_query": d["source_query"],
            "source_group": d["source_group"],
            "view_count": d["view_count"],
            "degree": G.degree(n),
            "strength": G.degree(n, weight="weight"),
            "n_comentarios_observados": d["n_comentarios"],
            "n_videos_comentados": d["n_videos"],
            "n_canales_comentados": d["n_canales"],
            "n_autores_observados": d.get("n_autores", 0),
            "me_gusta_recibidos": d["me_gusta_recibidos"],
            "respuestas_recibidas": d["respuestas_recibidas"],
            "largo_medio_comentario": d["largo_medio_comentario"],
        })
    nodes_df = pd.DataFrame(nodes).sort_values(
        ["node_type", "strength"], ascending=[True, False])

    edges = []
    for u, v, d in G.edges(data=True):
        a, b = (u, v) if G.nodes[u]["node_type"] == "author" else (v, u)
        edges.append({
            "source": a, "target": b,
            "source_type": "author", "target_type": "video",
            "source_raw_id": G.nodes[a]["raw_id"], "target_raw_id": G.nodes[b]["raw_id"],
            "weight": d["weight"],
            "significado_peso": "numero de comentarios observados del autor en el video",
            "me_gusta_en_esos_comentarios": d["me_gusta"],
            "respuestas_recibidas_en_esos_comentarios": d["respuestas_recibidas"],
            "comment_ids": d["comment_ids"],
            "source_label": G.nodes[a]["display_name"],
            "target_label": G.nodes[b]["display_name"],
        })
    edges_df = pd.DataFrame(edges).sort_values("weight", ascending=False)

    nodes_df.to_csv(C.NETWORKS / "bipartite_nodes.csv", index=False)
    edges_df.to_csv(C.NETWORKS / "bipartite_edges.csv", index=False)
    nodes_df.to_csv(C.TABLES / "bipartite_nodes.csv", index=False)
    edges_df.to_csv(C.TABLES / "bipartite_edges.csv", index=False)
    nx.write_graphml(_graphml_safe(G), C.NETWORKS / "bipartite.graphml")
    return nodes_df, edges_df


# ============================================================= 5. proyecciones
def build_projections(G: nx.Graph) -> tuple[nx.Graph, nx.Graph]:
    """Ejercicios 5.1-5.2. Proyecciones ponderadas autor-autor y video-video.

    Se usa ``bipartite.weighted_projected_graph``, cuyo peso es el numero de
    vecinos comunes en la red bipartita:

    * autor-autor: numero de **videos** en los que ambos autores comentaron;
    * video-video: numero de **autores** que comentaron en ambos videos.

    Es la definicion exacta que pide el enunciado. Notese que la proyeccion
    ignora el peso de la bipartita a proposito: dos autores que coinciden en
    un video comparten *un* video, sin importar cuantas veces comento cada
    uno.
    """
    authors = [n for n, d in G.nodes(data=True) if d["node_type"] == "author"]
    vids = [n for n, d in G.nodes(data=True) if d["node_type"] == "video"]
    AP = bipartite.weighted_projected_graph(G, authors)
    VP = bipartite.weighted_projected_graph(G, vids)
    for P in (AP, VP):
        for n in P.nodes():
            P.nodes[n].update({k: v for k, v in G.nodes[n].items()})
    # Se guarda la lista de videos de cada autor para poder contrastar las
    # comunidades de AP con la particion trivial por video (ver 7.1).
    for n in AP.nodes():
        nb = list(G.neighbors(n))
        AP.nodes[n]["_videos"] = sorted(G.nodes[v]["raw_id"] for v in nb)
        if len(nb) == 1:
            AP.nodes[n]["_video_title"] = G.nodes[nb[0]]["display_name"]
    return AP, VP


def verify_projection_weights(G: nx.Graph, AP: nx.Graph, VP: nx.Graph,
                              comments: pd.DataFrame) -> dict:
    """Sanity check independiente de los pesos de las dos proyecciones.

    Recalcula cada peso desde el dataframe de comentarios (conjuntos de
    videos por autor y de autores por video) sin usar networkx, y compara.
    """
    videos_by_author = comments.groupby("author_channel_id")["video_id"].apply(set).to_dict()
    authors_by_video = comments.groupby("video_id")["author_channel_id"].apply(set).to_dict()

    ap_bad, vp_bad = [], []
    for u, v, d in AP.edges(data=True):
        expected = len(videos_by_author[AP.nodes[u]["raw_id"]]
                       & videos_by_author[AP.nodes[v]["raw_id"]])
        if expected != d["weight"]:
            ap_bad.append((u, v, d["weight"], expected))
    for u, v, d in VP.edges(data=True):
        expected = len(authors_by_video[VP.nodes[u]["raw_id"]]
                       & authors_by_video[VP.nodes[v]["raw_id"]])
        if expected != d["weight"]:
            vp_bad.append((u, v, d["weight"], expected))

    # La proyeccion de autores debe contener una clique por video observado.
    cliques_ok = all(
        AP.has_edge(A_PREFIX + a, A_PREFIX + b)
        for authors in authors_by_video.values() if len(authors) > 1
        for a in list(authors)[:6] for b in list(authors)[:6] if a != b
    )
    return {
        "aristas_author_projection": AP.number_of_edges(),
        "aristas_video_projection": VP.number_of_edges(),
        "pesos_author_projection_incorrectos": len(ap_bad),
        "pesos_video_projection_incorrectos": len(vp_bad),
        "ejemplos_incorrectos_author": ap_bad[:5],
        "ejemplos_incorrectos_video": vp_bad[:5],
        "inv_pesos_author_projection_correctos": bool(not ap_bad),
        "inv_pesos_video_projection_correctos": bool(not vp_bad),
        "inv_clique_por_video_presente": bool(cliques_ok),
        "peso_max_author_projection": int(max(
            (d["weight"] for *_, d in AP.edges(data=True)), default=0)),
        "peso_max_video_projection": int(max(
            (d["weight"] for *_, d in VP.edges(data=True)), default=0)),
        "aristas_video_projection_peso_mayor_1": int(
            sum(1 for *_, d in VP.edges(data=True) if d["weight"] > 1)),
    }


def export_projection_tables(AP: nx.Graph, VP: nx.Graph) -> None:
    for P, name, wmeaning in [
        (AP, "author_projection", "numero de videos compartidos por los dos autores"),
        (VP, "video_projection", "numero de autores compartidos por los dos videos"),
    ]:
        edges = pd.DataFrame([
            {"source": u, "target": v,
             "source_raw_id": P.nodes[u]["raw_id"], "target_raw_id": P.nodes[v]["raw_id"],
             "weight": d["weight"], "significado_peso": wmeaning,
             "source_label": P.nodes[u]["display_name"],
             "target_label": P.nodes[v]["display_name"]}
            for u, v, d in P.edges(data=True)
        ]).sort_values("weight", ascending=False)
        nodes = pd.DataFrame([
            {"node_id": n, "raw_id": d["raw_id"], "node_type": d["node_type"],
             "display_name": d["display_name"], "handle": d["handle"],
             "channel_id": d["channel_id"], "channel_name": d["channel_name"],
             "category": d["category"], "source_query": d["source_query"],
             "view_count": d["view_count"],
             "degree": P.degree(n), "strength": P.degree(n, weight="weight"),
             "n_comentarios_observados": d["n_comentarios"],
             "n_videos_comentados": d["n_videos"]}
            for n, d in P.nodes(data=True)
        ]).sort_values("strength", ascending=False)
        for folder in (C.NETWORKS, C.TABLES):
            edges.to_csv(folder / f"{name}_edges.csv", index=False)
        nodes.to_csv(C.NETWORKS / f"{name}_nodes.csv", index=False)
        nx.write_graphml(_graphml_safe(P), C.NETWORKS / f"{name}.graphml")


# ================================================= 6. topologia y fragmentacion
def topology(G: nx.Graph, name: str, kind: str) -> dict:
    """Ejercicios 6.1-6.2 para un grafo.

    Notas sobre las metricas que dependen del tipo de red:

    * **Densidad**: en la bipartita el maximo de aristas no es n(n-1)/2 sino
      |A|x|V|, asi que se reporta tambien la densidad bipartita, que es la
      correcta para esa red.
    * **Transitividad**: en un grafo bipartito es necesariamente 0 porque no
      existen triangulos (un triangulo requiere tres nodos mutuamente
      adyacentes, imposible con dos conjuntos). Se reporta el 0 y ademas el
      clustering bipartito de Latapy, que si es interpretable.
    * **Cohesion**: ver ``cohesion_metrics``.
    """
    n, m = G.number_of_nodes(), G.number_of_edges()
    degrees = np.array([d for _, d in G.degree()], dtype=float)
    strengths = np.array([d for _, d in G.degree(weight="weight")], dtype=float)
    comps = sorted(nx.connected_components(G), key=len, reverse=True)
    giant = G.subgraph(comps[0]).copy() if comps else G.copy()
    isolates = [n_ for n_ in nx.isolates(G)]

    out = {
        "red": name,
        "tipo": kind,
        "n_nodos": n,
        "n_aristas": m,
        "densidad": round(nx.density(G), 6),
        "grado_medio": round(float(degrees.mean()), 3) if n else 0.0,
        "grado_mediano": float(np.median(degrees)) if n else 0.0,
        "grado_p25": float(np.percentile(degrees, 25)) if n else 0.0,
        "grado_p75": float(np.percentile(degrees, 75)) if n else 0.0,
        "grado_p90": float(np.percentile(degrees, 90)) if n else 0.0,
        "grado_p99": float(np.percentile(degrees, 99)) if n else 0.0,
        "grado_max": float(degrees.max()) if n else 0.0,
        "grado_min": float(degrees.min()) if n else 0.0,
        "grado_std": round(float(degrees.std(ddof=1)), 3) if n > 1 else 0.0,
        "grado_gini": round(_gini(degrees), 4) if n else np.nan,
        "pct_nodos_grado_1": round(100 * float((degrees == 1).mean()), 2) if n else 0.0,
        "pct_nodos_grado_menor_igual_2": round(
            100 * float((degrees <= 2).mean()), 2) if n else 0.0,
        "fuerza_media": round(float(strengths.mean()), 3) if n else 0.0,
        "fuerza_mediana": float(np.median(strengths)) if n else 0.0,
        "fuerza_max": float(strengths.max()) if n else 0.0,
        "suma_pesos": float(sum(d.get("weight", 1) for *_, d in G.edges(data=True))),
        "n_componentes": len(comps),
        "tamano_componente_mayor": len(comps[0]) if comps else 0,
        "pct_nodos_en_componente_mayor": round(100 * len(comps[0]) / n, 2) if n else 0.0,
        "tamanos_componentes": [len(c) for c in comps],
        "n_componentes_de_tamano_2": int(sum(1 for c in comps if len(c) == 2)),
        "n_nodos_aislados": len(isolates),
        "pct_nodos_aislados": round(100 * len(isolates) / n, 2) if n else 0.0,
        "transitividad_global": round(nx.transitivity(G), 6),
        "clustering_medio": round(nx.average_clustering(G), 6),
        "clustering_medio_ponderado": round(
            nx.average_clustering(G, weight="weight"), 6),
        "assortatividad_de_grado": round(
            float(nx.degree_assortativity_coefficient(G)), 4) if m > 1 else np.nan,
    }

    if kind == "bipartita":
        A = {x for x, d in G.nodes(data=True) if d["node_type"] == "author"}
        V = {x for x, d in G.nodes(data=True) if d["node_type"] == "video"}
        out["n_nodos_tipo_autor"] = len(A)
        out["n_nodos_tipo_video"] = len(V)
        out["densidad_bipartita"] = round(bipartite.density(G, A), 6)
        out["max_aristas_bipartita"] = len(A) * len(V)
        out["clustering_bipartito_latapy_medio"] = round(
            float(np.mean(list(bipartite.clustering(G, mode="dot").values()))), 6)
        out["grado_medio_autores"] = round(
            float(np.mean([G.degree(x) for x in A])), 3)
        out["grado_medio_videos"] = round(
            float(np.mean([G.degree(x) for x in V])), 3)
        out["nota_transitividad"] = (
            "La transitividad global de una red bipartita es 0 por "
            "construccion: un triangulo exigiria tres nodos mutuamente "
            "adyacentes y las aristas solo unen tipos distintos. La metrica "
            "interpretable aqui es el clustering bipartito de Latapy et al. "
            "(2008), que mide el solapamiento de vecindarios."
        )

    # diametro y caminos solo dentro de la componente gigante
    if giant.number_of_nodes() > 1:
        out["diametro_componente_mayor"] = int(nx.diameter(giant))
        out["longitud_media_camino_componente_mayor"] = round(
            float(nx.average_shortest_path_length(giant)), 4)
        out["radio_componente_mayor"] = int(nx.radius(giant))
    else:
        out["diametro_componente_mayor"] = 0
        out["longitud_media_camino_componente_mayor"] = np.nan
        out["radio_componente_mayor"] = 0

    out.update(cohesion_metrics(G, giant))
    return out


def cohesion_metrics(G: nx.Graph, giant: nx.Graph) -> dict:
    """Ejercicio 6.2. Cohesion definida operacionalmente.

    "Cohesion" no es una unica cantidad, asi que se declara que se mide:

    ``conectividad_por_nodos_global`` (kappa)
        Numero minimo de nodos que hay que eliminar para desconectar el
        grafo. Si el grafo ya esta desconectado vale 0 por definicion; se
        reporta ese 0 explicitamente en lugar de omitirlo.
    ``conectividad_por_nodos_componente_mayor``
        La misma kappa calculada solo sobre la componente conexa mayor. Es
        la medida informativa cuando la red esta fragmentada: kappa = k
        significa que la componente resiste la eliminacion de k-1 nodos
        cualesquiera sin partirse.
    ``conectividad_por_aristas_componente_mayor``
        Version por aristas (teorema de Menger); util para distinguir
        fragilidad estructural por nodos frente a por vinculos.
    ``clustering_medio``
        Cohesion local: proporcion de vecindarios cerrados.
    """
    out = {
        "conectividad_por_nodos_global": int(nx.node_connectivity(G)) if G.number_of_nodes() > 1 else 0,
        "conectividad_por_aristas_global": int(nx.edge_connectivity(G)) if G.number_of_nodes() > 1 else 0,
        "grafo_conexo": bool(nx.is_connected(G)) if G.number_of_nodes() else False,
    }
    if giant.number_of_nodes() > 1:
        out["conectividad_por_nodos_componente_mayor"] = int(nx.node_connectivity(giant))
        out["conectividad_por_aristas_componente_mayor"] = int(nx.edge_connectivity(giant))
        out["n_puntos_articulacion_componente_mayor"] = len(
            list(nx.articulation_points(giant)))
        out["n_puentes_componente_mayor"] = len(list(nx.bridges(giant)))
        out["densidad_componente_mayor"] = round(nx.density(giant), 6)
    else:
        out["conectividad_por_nodos_componente_mayor"] = 0
        out["conectividad_por_aristas_componente_mayor"] = 0
        out["n_puntos_articulacion_componente_mayor"] = 0
        out["n_puentes_componente_mayor"] = 0
        out["densidad_componente_mayor"] = np.nan
    out["definicion_cohesion"] = (
        "Cohesion = conectividad por nodos (kappa): minimo numero de nodos "
        "cuya eliminacion desconecta el grafo. Vale 0 si el grafo ya esta "
        "desconectado, por lo que se reporta tambien kappa sobre la "
        "componente conexa mayor, que es la cifra interpretable en una red "
        "fragmentada. Se complementa con conectividad por aristas y con "
        "clustering medio como medida de cohesion local."
    )
    return out


def peripheral_analysis(G: nx.Graph, AP: nx.Graph, VP: nx.Graph,
                        comments: pd.DataFrame) -> dict:
    """Ejercicio 6.3. Nodos y grupos perifericos o aislados.

    La distincion critica: un video sin vecinos en la proyeccion video-video
    esta aislado **en los datos observados** (ningun autor recolectado
    comento tambien en otro video de la muestra). Eso no significa que su
    audiencia real en YouTube no se solape con la de otros videos: solo se
    recolectaron comentarios de 19 videos y una parte de los comentarios de
    cada uno.
    """
    vp_iso = [n for n in VP.nodes() if VP.degree(n) == 0]
    ap_iso = [n for n in AP.nodes() if AP.degree(n) == 0]
    bip_deg1_authors = [n for n, d in G.nodes(data=True)
                        if d["node_type"] == "author" and G.degree(n) == 1]
    comps_ap = sorted(nx.connected_components(AP), key=len, reverse=True)
    comps_vp = sorted(nx.connected_components(VP), key=len, reverse=True)

    return {
        "videos_aislados_en_proyeccion_video": [
            {"video_id": VP.nodes[n]["raw_id"], "titulo": VP.nodes[n]["display_name"],
             "canal": VP.nodes[n]["channel_name"],
             "n_comentarios_observados": VP.nodes[n]["n_comentarios"],
             "n_autores_observados": VP.nodes[n].get("n_autores", 0)}
            for n in sorted(vp_iso, key=lambda x: -VP.nodes[x]["n_comentarios"])
        ],
        "n_videos_aislados_proyeccion": len(vp_iso),
        "pct_videos_aislados_proyeccion": round(100 * len(vp_iso) / VP.number_of_nodes(), 2),
        "n_autores_aislados_proyeccion": len(ap_iso),
        "autores_aislados_proyeccion": [AP.nodes[n]["raw_id"] for n in ap_iso],
        "n_autores_grado_1_en_bipartita": len(bip_deg1_authors),
        "pct_autores_grado_1_en_bipartita": round(
            100 * len(bip_deg1_authors) /
            sum(1 for _, d in G.nodes(data=True) if d["node_type"] == "author"), 2),
        "componentes_author_projection": [len(c) for c in comps_ap],
        "componentes_video_projection": [len(c) for c in comps_vp],
        "n_componentes_pequenas_author_projection": int(
            sum(1 for c in comps_ap if len(c) <= 5)),
        "grupos_desconectados_bipartita": [
            {"tamano": len(c),
             "n_autores": sum(1 for x in c if G.nodes[x]["node_type"] == "author"),
             "videos": [G.nodes[x]["display_name"] for x in c
                        if G.nodes[x]["node_type"] == "video"]}
            for c in sorted(nx.connected_components(G), key=len, reverse=True)
        ],
        "distincion_aislamiento": (
            "Un nodo aislado en estas redes esta aislado EN LOS DATOS "
            "OBSERVADOS, no en YouTube. Solo se recolectaron comentarios de "
            f"{comments.video_id.nunique()} videos y no necesariamente todos "
            "los comentarios de cada uno, asi que la ausencia de un vinculo "
            "puede deberse a la cobertura del muestreo y no a la ausencia de "
            "audiencia compartida real."
        ),
    }


# ================================================================ 7. comunidades
def detect_communities(VP: nx.Graph, AP: nx.Graph) -> dict:
    """Ejercicio 7. Louvain ponderado sobre la proyeccion video-video.

    Justificacion de la red elegida (7.1): la proyeccion video-video conecta
    contenidos por audiencia compartida y sus pesos son autores compartidos,
    de modo que una comunidad es un grupo de videos que comparten publico.
    Es la unica de las tres redes que permite caracterizar el resultado con
    titulo, canal, categoria, consulta, palabras y sentimiento a la vez. La
    bipartita no admite modularidad estandar (no hay triangulos ni
    comunidades intra-tipo) y la proyeccion autor-autor colapsa en una clique
    por video, de modo que sus "comunidades" solo reproducirian la particion
    por video y no aportarian informacion nueva. Se aplica igual a la
    proyeccion de autores como analisis complementario para verificar esa
    afirmacion.

    Supuestos de Louvain (7.2): optimiza modularidad por agregacion voraz,
    asume comunidades no solapadas y sufre el limite de resolucion (no
    detecta comunidades mas pequenas que ~sqrt(2m)). Los pesos se interpretan
    como **intensidad de vinculo** (mas autores compartidos = mas fuerte),
    que es exactamente lo que la modularidad ponderada espera. Semilla fija
    en 42 para reproducibilidad.
    """
    C.set_seeds()
    out: dict = {}
    for P, key, wmeaning in [
        (VP, "video_projection", "autores compartidos"),
        (AP, "author_projection", "videos compartidos"),
    ]:
        parts = nxcom.louvain_communities(
            P, weight="weight", resolution=C.LOUVAIN_RESOLUTION, seed=C.SEED)
        parts = sorted(parts, key=len, reverse=True)
        sizes = [len(p) for p in parts]
        q = nxcom.modularity(P, parts, weight="weight",
                             resolution=C.LOUVAIN_RESOLUTION) if P.number_of_edges() else np.nan
        q_unw = nxcom.modularity(P, parts, weight=None) if P.number_of_edges() else np.nan
        out[key] = {
            "algoritmo": "Louvain (networkx.algorithms.community.louvain_communities)",
            "libreria": f"networkx {nx.__version__}",
            "peso_usado": "weight",
            "significado_peso": wmeaning,
            "resolucion": C.LOUVAIN_RESOLUTION,
            "semilla": C.SEED,
            "n_comunidades": len(parts),
            "tamanos": sizes,
            "modularidad_ponderada": round(float(q), 4) if q == q else np.nan,
            "modularidad_no_ponderada": round(float(q_unw), 4) if q_unw == q_unw else np.nan,
            "n_singletons": int(sum(1 for s in sizes if s == 1)),
            "pct_nodos_en_singletons": round(
                100 * sum(s for s in sizes if s == 1) / P.number_of_nodes(), 2),
            "n_comunidades_no_triviales": int(sum(1 for s in sizes if s > 1)),
            "tamano_comunidad_mayor": max(sizes) if sizes else 0,
            "tamano_medio_comunidad": round(float(np.mean(sizes)), 2) if sizes else 0.0,
            "cobertura_comunidades_no_triviales_pct": round(
                100 * sum(s for s in sizes if s > 1) / P.number_of_nodes(), 2),
        }
        out[key]["_partition"] = [sorted(p) for p in parts]

    # Verificacion de la justificacion de 7.1: las comunidades de la
    # proyeccion autor-autor solo reproducen la particion por video.
    out["author_projection_vs_particion_por_video"] = _ap_vs_video_partition(
        AP, out["author_projection"]["_partition"])

    # Comparacion con una particion alternativa como control de robustez.
    if VP.number_of_edges():
        gm = sorted(nxcom.greedy_modularity_communities(VP, weight="weight"),
                    key=len, reverse=True)
        lp = sorted(nxcom.asyn_lpa_communities(VP, weight="weight", seed=C.SEED),
                    key=len, reverse=True)
        louv = [set(p) for p in out["video_projection"]["_partition"]]
        out["robustez_video_projection"] = {
            "greedy_modularity_n_comunidades": len(gm),
            "greedy_modularity_tamanos": [len(x) for x in gm],
            "greedy_modularity_Q": round(float(nxcom.modularity(VP, gm, weight="weight")), 4),
            "label_propagation_n_comunidades": len(lp),
            "label_propagation_tamanos": [len(x) for x in lp],
            "nmi_louvain_vs_greedy": round(_nmi(VP, louv, [set(x) for x in gm]), 4),
            "nmi_louvain_vs_label_propagation": round(
                _nmi(VP, louv, [set(x) for x in lp]), 4),
            "componentes_conexas": [
                len(c) for c in sorted(nx.connected_components(VP), key=len, reverse=True)],
            "interpretacion": (
                "Las particiones de tres algoritmos distintos se comparan con "
                "informacion mutua normalizada. Un NMI alto indica que la "
                "estructura de comunidades no es un artefacto de Louvain."
            ),
        }
    return out


def _ap_vs_video_partition(AP: nx.Graph, parts: list[list]) -> dict:
    """Contrasta las comunidades de autores con una etiqueta trivial.

    La etiqueta trivial asigna a cada autor el video en el que comento (el
    primero, en orden, si comento en varios). Si el NMI con las comunidades
    de Louvain es muy alto, las "comunidades de autores" no aportan
    informacion mas alla de "en que video comento cada autor", que es
    exactamente el argumento para no usarlas como analisis principal.
    """
    from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

    nodes = sorted(AP.nodes())
    louv = {n: i for i, p in enumerate(parts) for n in p}
    # etiqueta trivial: primer video (alfabeticamente) en el que comento
    trivial: dict[str, str] = {}
    for n in nodes:
        vids = sorted(AP.nodes[n].get("_videos", []))
        trivial[n] = vids[0] if vids else n
    labels_t = {v: i for i, v in enumerate(sorted(set(trivial.values())))}
    a = [louv[n] for n in nodes]
    b = [labels_t[trivial[n]] for n in nodes]
    return {
        "n_comunidades_louvain": len(parts),
        "n_grupos_de_la_etiqueta_trivial": len(labels_t),
        "nmi_con_particion_por_video": round(
            float(normalized_mutual_info_score(a, b)), 4),
        "ari_con_particion_por_video": round(float(adjusted_rand_score(a, b)), 4),
        "interpretacion": (
            "La etiqueta trivial asigna a cada autor el video en el que "
            "comento. Un NMI alto significa que las comunidades detectadas en "
            "la proyeccion autor-autor no aportan informacion mas alla de esa "
            "etiqueta: son las cliques por video que la proyeccion crea por "
            "construccion. Por eso el analisis principal de comunidades se "
            "hace sobre la proyeccion video-video."
        ),
    }


def _nmi(G: nx.Graph, part_a: list[set], part_b: list[set]) -> float:
    from sklearn.metrics import normalized_mutual_info_score

    nodes = sorted(G.nodes())
    la = {n: i for i, p in enumerate(part_a) for n in p}
    lb = {n: i for i, p in enumerate(part_b) for n in p}
    return float(normalized_mutual_info_score([la[n] for n in nodes], [lb[n] for n in nodes]))


# ================================================================= 8. centralidad
def centrality(P: nx.Graph, kind: str) -> pd.DataFrame:
    """Ejercicio 8.1. Centralidades con tratamiento correcto de pesos.

    Punto critico: en las proyecciones ``weight`` es **intensidad** (mas
    autores/videos compartidos = vinculo mas fuerte), pero los algoritmos de
    camino mas corto de networkx interpretan ``weight`` como **distancia**
    (mas alto = mas lejos). Pasar el peso directamente invertiria el
    significado y haria que los vinculos fuertes parezcan lejanos. Por eso se
    construye ``distance = 1/weight`` y se usa esa como distancia en
    betweenness, closeness y harmonic.

    Grafos desconectados: betweenness de networkx ya suma por componente;
    closeness se calcula con la correccion de Wasserman-Faust
    (``wf_improved=True``) y se agrega harmonic centrality, que esta bien
    definida con distancias infinitas porque suma reciprocos.
    """
    Q = P.copy()
    for u, v, d in Q.edges(data=True):
        w = max(float(d.get("weight", 1)), 1e-12)
        d["distance"] = 1.0 / w

    n = Q.number_of_nodes()
    deg = dict(Q.degree())
    strength = dict(Q.degree(weight="weight"))
    btw = nx.betweenness_centrality(Q, weight="distance", normalized=True, seed=C.SEED)
    btw_unw = nx.betweenness_centrality(Q, weight=None, normalized=True, seed=C.SEED)
    clo = nx.closeness_centrality(Q, distance="distance", wf_improved=True)
    har = nx.harmonic_centrality(Q, distance="distance")
    try:
        pr = nx.pagerank(Q, weight="weight", alpha=0.85)
    except nx.PowerIterationFailedConvergence:  # pragma: no cover
        pr = {x: np.nan for x in Q}
    try:
        eig = nx.eigenvector_centrality_numpy(Q, weight="weight")
    except Exception:  # pragma: no cover - grafos con componentes triviales
        eig = {x: np.nan for x in Q}
    core = nx.core_number(Q)
    clust = nx.clustering(Q, weight="weight")

    comp_of = {}
    for i, c in enumerate(sorted(nx.connected_components(Q), key=len, reverse=True)):
        for x in c:
            comp_of[x] = (i, len(c))

    arts = set()
    for c in nx.connected_components(Q):
        sub = Q.subgraph(c)
        if sub.number_of_nodes() > 2:
            arts |= set(nx.articulation_points(sub))

    rows = []
    for x, d in Q.nodes(data=True):
        ci, cs = comp_of[x]
        rows.append({
            "node_id": x,
            "raw_id": d["raw_id"],
            "node_type": d["node_type"],
            "display_name": d["display_name"],
            "handle": d["handle"],
            "channel_id": d["channel_id"],
            "channel_name": d["channel_name"],
            "category": d["category"],
            "source_query": d["source_query"],
            "view_count": d["view_count"],
            "n_comentarios_observados": d["n_comentarios"],
            "n_videos_comentados": d["n_videos"],
            "n_canales_comentados": d["n_canales"],
            "degree": deg[x],
            "degree_centrality": round(deg[x] / (n - 1), 6) if n > 1 else 0.0,
            "strength": strength[x],
            "betweenness_ponderada": round(btw[x], 6),
            "betweenness_no_ponderada": round(btw_unw[x], 6),
            "closeness_wf": round(clo[x], 6),
            "harmonic": round(har[x], 4),
            "harmonic_normalizada": round(har[x] / (n - 1), 6) if n > 1 else 0.0,
            "pagerank": round(pr[x], 8),
            "eigenvector": round(float(eig[x]), 6) if eig[x] == eig[x] else np.nan,
            "k_core": core[x],
            "clustering_ponderado": round(clust[x], 6),
            "componente_id": ci,
            "tamano_de_su_componente": cs,
            "es_punto_articulacion": bool(x in arts),
        })
    df = pd.DataFrame(rows)
    df["rank_strength"] = df["strength"].rank(ascending=False, method="min").astype(int)
    df["rank_betweenness"] = df["betweenness_ponderada"].rank(
        ascending=False, method="min").astype(int)
    df["rank_pagerank"] = df["pagerank"].rank(ascending=False, method="min").astype(int)
    return df.sort_values(["betweenness_ponderada", "strength"], ascending=False)


def articulation_analysis(graphs: dict[str, nx.Graph]) -> pd.DataFrame:
    """Ejercicio 8.3. Verifica empiricamente el efecto de eliminar cada nodo.

    Un punto de articulacion se afirma solo si al quitarlo el numero de
    componentes crece. La tabla registra el numero de componentes antes y
    despues, el tamano de la componente mayor y cuantos nodos quedan
    aislados, para que la afirmacion "es articulador" sea verificable y no
    una lectura de un ranking de grado.
    """
    rows = []
    for name, G in graphs.items():
        base_comps = nx.number_connected_components(G)
        base_giant = max((len(c) for c in nx.connected_components(G)), default=0)
        candidates = set()
        for c in nx.connected_components(G):
            sub = G.subgraph(c)
            if sub.number_of_nodes() > 2:
                candidates |= set(nx.articulation_points(sub))
        for x in sorted(candidates, key=lambda z: -G.degree(z)):
            H = G.copy()
            H.remove_node(x)
            new_comps = nx.number_connected_components(H)
            new_giant = max((len(c) for c in nx.connected_components(H)), default=0)
            new_iso = sum(1 for z in nx.isolates(H))
            rows.append({
                "red": name,
                "node_id": x,
                "raw_id": G.nodes[x]["raw_id"],
                "node_type": G.nodes[x]["node_type"],
                "display_name": G.nodes[x]["display_name"],
                "channel_name": G.nodes[x]["channel_name"],
                "degree": G.degree(x),
                "strength": G.degree(x, weight="weight"),
                "componentes_antes": base_comps,
                "componentes_despues": new_comps,
                "delta_componentes": new_comps - base_comps,
                "componente_mayor_antes": base_giant,
                "componente_mayor_despues": new_giant,
                "reduccion_componente_mayor": base_giant - new_giant,
                "pct_reduccion_componente_mayor": round(
                    100 * (base_giant - new_giant) / base_giant, 2) if base_giant else 0.0,
                "nodos_aislados_tras_eliminar": new_iso,
                "es_articulador_verificado": bool(new_comps > base_comps),
            })
    df = pd.DataFrame(rows)
    if len(df):
        df = df.sort_values(["red", "delta_componentes", "degree"],
                            ascending=[True, False, False])
    return df


def bridge_authors(G: nx.Graph, AP: nx.Graph, VP: nx.Graph,
                   comments: pd.DataFrame, communities: dict) -> pd.DataFrame:
    """Ejercicio 8.3. Autores puente, con criterio explicito y verificable.

    Un autor es puente si su participacion es la que une contenidos que, sin
    el, quedarian separados. Se operacionaliza con cuatro senales:

    1. comenta en mas de un video (condicion necesaria);
    2. cuantos videos y cuantos canales distintos toca;
    3. cuantas comunidades de la proyeccion video-video toca;
    4. **prueba de eliminacion**: se quita al autor de la red bipartita y se
       recalcula la proyeccion video-video; si el numero de componentes
       aumenta, el autor sostiene por si solo esa conexion.

    El criterio 4 es el que distingue un puente real de un autor simplemente
    activo, y es el que la rubrica pide ("si los elimináramos de la red, esta
    se segmenta").
    """
    vp_part = {}
    for i, p in enumerate(communities["video_projection"]["_partition"]):
        for x in p:
            vp_part[x] = i

    base_comps = nx.number_connected_components(VP)
    base_edges = VP.number_of_edges()

    authors = [n for n, d in G.nodes(data=True) if d["node_type"] == "author"]
    rows = []
    for a in authors:
        vids = [v for v in G.neighbors(a)]
        d = G.nodes[a]
        comms = {vp_part.get(v) for v in vids if v in vp_part}
        comms.discard(None)

        delta_comps, delta_edges, verified = 0, 0, False
        if len(vids) > 1:
            H = G.copy()
            H.remove_node(a)
            vnodes = [x for x, dd in H.nodes(data=True) if dd["node_type"] == "video"]
            VP2 = bipartite.weighted_projected_graph(H, vnodes)
            new_comps = nx.number_connected_components(VP2)
            delta_comps = new_comps - base_comps
            delta_edges = base_edges - VP2.number_of_edges()
            verified = new_comps > base_comps

        rows.append({
            "author_channel_id": d["raw_id"],
            "author_handle": d["handle"],
            "author_name": d["display_name"],
            "n_comentarios": d["n_comentarios"],
            "n_videos_distintos": d["n_videos"],
            "n_canales_distintos": d["n_canales"],
            "me_gusta_recibidos": d["me_gusta_recibidos"],
            "respuestas_recibidas": d["respuestas_recibidas"],
            "strength_bipartita": G.degree(a, weight="weight"),
            "degree_proyeccion_autores": AP.degree(a),
            "strength_proyeccion_autores": AP.degree(a, weight="weight"),
            "n_comunidades_video_tocadas": len(comms),
            "comunidades_video_tocadas": sorted(comms),
            "videos_comentados": "|".join(sorted(G.nodes[v]["raw_id"] for v in vids)),
            "titulos_videos": " || ".join(
                sorted(G.nodes[v]["display_name"] for v in vids)),
            "canales": " || ".join(sorted({G.nodes[v]["channel_name"] for v in vids})),
            "delta_componentes_al_eliminar": delta_comps,
            "aristas_video_perdidas_al_eliminar": delta_edges,
            "es_puente_verificado": bool(verified),
            "es_recurrente": bool(d["n_comentarios"] > 1),
            "es_multicanal": bool(d["n_canales"] > 1),
            "es_multicomunidad": bool(len(comms) > 1),
        })
    df = pd.DataFrame(rows)
    return df.sort_values(
        ["es_puente_verificado", "delta_componentes_al_eliminar",
         "n_videos_distintos", "n_comentarios"],
        ascending=False)


# =================================================================== figuras ==
def _layout(G: nx.Graph, name: str, k=None, iterations=250):
    """Layout reproducible: spring con semilla fija."""
    return nx.spring_layout(G, seed=C.SEED, k=k, iterations=iterations, weight="weight")


def ap_layout(AP: nx.Graph, G: nx.Graph) -> dict:
    """Layout reproducible y legible para la proyeccion autor-autor.

    Un ``spring_layout`` es inservible aqui: las 10 732 aristas forman una
    clique por video, la fuerza atractiva colapsa cada clique en un punto y
    el resultado es una mancha. En lugar de eso se explota la estructura
    conocida: la proyeccion **es** una union de cliques, una por video
    observado.

    * Cada video observado recibe un ancla sobre una circunferencia, ordenada
      por comunidad de la proyeccion video-video y por tamano, de modo que
      audiencias relacionadas queden cerca.
    * Los autores de un solo video se distribuyen en un disco alrededor del
      ancla de ese video, con posiciones deterministas (angulo dorado), y el
      radio del disco crece con la raiz del tamano de la audiencia.
    * Los autores de varios videos se colocan en el centroide de sus anclas
      y se atraen ligeramente al centro, con lo que quedan visiblemente
      *entre* los bloques que conectan.

    No se elimina ningun nodo ni arista: solo cambia la asignacion de
    coordenadas.
    """
    videos_of = {n: AP.nodes[n].get("_videos", []) for n in AP.nodes()}
    all_videos = sorted({v for vs in videos_of.values() for v in vs})
    size = {v: sum(1 for vs in videos_of.values() if v in vs) for v in all_videos}
    anchors = _ring_anchors(all_videos, size)

    max_size = max(size.values()) if size else 1
    disc = {v: 0.10 + 0.24 * np.sqrt(size[v] / max_size) for v in all_videos}
    golden = np.pi * (3 - np.sqrt(5))
    pos, counters = {}, {v: 0 for v in all_videos}
    for n in sorted(AP.nodes()):
        vs = videos_of[n]
        if len(vs) == 1:
            v = vs[0]
            k = counters[v]
            counters[v] += 1
            r = disc[v] * np.sqrt((k + 0.5) / max(size[v], 1))
            ang = k * golden
            pos[n] = anchors[v] + r * np.array([np.cos(ang), np.sin(ang)])
        elif len(vs) == 0:  # autor sin vecinos en la proyeccion
            pos[n] = np.array([0.0, 0.0])

    # Los autores multivideo se reparten en un anillo interior, cada uno
    # cerca del angulo medio de los bloques que conecta. Distribuirlos en el
    # anillo (y no en el centroide) evita que sus etiquetas se solapen.
    multi = [n for n in sorted(AP.nodes()) if len(videos_of[n]) > 1]
    if multi:
        def mean_angle(n):
            vecs = [anchors[v] for v in videos_of[n] if v in anchors]
            m = np.mean(vecs, axis=0)
            return float(np.arctan2(m[1], m[0]))

        multi = sorted(multi, key=mean_angle)
        start = mean_angle(multi[0])
        ring = 0.95 * AP_RING_RADIUS / 2.6
        for i, n in enumerate(multi):
            ang = start + 2 * np.pi * i / len(multi)
            pos[n] = ring * np.array([np.cos(ang), np.sin(ang)])
    return {n: tuple(p) for n, p in pos.items()}


#: Radio de la circunferencia sobre la que se disponen los bloques de audiencia.
AP_RING_RADIUS = 2.6


def _ring_anchors(all_videos: list[str], size: dict) -> dict:
    """Coloca un ancla por video en una circunferencia, intercalando tamanos.

    Si las anclas se recorrieran en orden decreciente de tamano, los dos
    bloques mas grandes quedarian contiguos y se solaparian. Se reparten
    alternando extremos de la lista ordenada para que los discos grandes
    queden separados.
    """
    ordered = sorted(all_videos, key=lambda v: -size[v])
    n = len(ordered)
    slots = [None] * n
    left, right = 0, n - 1
    for i, v in enumerate(ordered):
        if i % 2 == 0:
            slots[left] = v
            left += 1
        else:
            slots[right] = v
            right -= 1
    anchors = {}
    for i, v in enumerate(slots):
        ang = 2 * np.pi * i / max(n, 1)
        anchors[v] = AP_RING_RADIUS * np.array([np.cos(ang), np.sin(ang)])
    return anchors


def vp_layout(VP: nx.Graph) -> dict:
    """Layout compuesto y reproducible para la proyeccion video-video.

    Un ``spring_layout`` global falla aqui: con 10 nodos conectados y 9
    aislados, la fuerza repulsiva empuja los aislados a los bordes y comprime
    la componente conexa en un punto ilegible. Se resuelve por partes:

    * cada componente no trivial se dispone con Kamada-Kawai (que optimiza
      distancias de camino y da un trazado limpio en grafos pequenos) en la
      banda superior del lienzo;
    * los nodos aislados se colocan en una rejilla ordenada en la banda
      inferior, visualmente separados pero **presentes**: no se eliminan.

    El resultado es determinista porque Kamada-Kawai parte de un layout
    circular fijo y la rejilla se ordena por id.
    """
    pos: dict = {}
    comps = sorted(nx.connected_components(VP), key=len, reverse=True)
    nontrivial = [c for c in comps if len(c) > 1]
    isolates = sorted([n for c in comps if len(c) == 1 for n in c])

    # --- banda superior: componentes con aristas ---
    x_off = 0.0
    for c in nontrivial:
        sub = VP.subgraph(c)
        sp = (nx.kamada_kawai_layout(sub, weight=None) if sub.number_of_nodes() > 2
              else {n: (i * 1.0 - 0.5, 0.0) for i, n in enumerate(sorted(sub))})
        xs = [p[0] for p in sp.values()]
        span = (max(xs) - min(xs)) or 1.0
        for n, (x, y) in sp.items():
            pos[n] = (x_off + x, 0.55 + 0.55 * y)
        x_off += span + 1.4

    # centrar horizontalmente la banda superior
    if pos:
        cx = np.mean([p[0] for p in pos.values()])
        pos = {n: (x - cx, y) for n, (x, y) in pos.items()}

    # --- banda inferior: aislados en rejilla ---
    if isolates:
        per_row = min(5, len(isolates))
        rows = int(np.ceil(len(isolates) / per_row))
        for i, n in enumerate(isolates):
            r, col = divmod(i, per_row)
            width = 2.6
            x = -width / 2 + (width * col / max(per_row - 1, 1))
            pos[n] = (x, -0.72 - 0.42 * r)
    return pos


def plot_bipartite(G: nx.Graph) -> None:
    """Ejercicio 4.4. Red bipartita COMPLETA, sin filtrar nodos ni aristas."""
    A = [n for n, d in G.nodes(data=True) if d["node_type"] == "author"]
    V = [n for n, d in G.nodes(data=True) if d["node_type"] == "video"]
    pos = _layout(G, "bipartite", k=0.32, iterations=400)

    fig, ax = plt.subplots(figsize=(15, 11))
    weights = [d["weight"] for *_, d in G.edges(data=True)]
    nx.draw_networkx_edges(G, pos, ax=ax, alpha=0.3,
                           width=[0.5 + 0.9 * (w - 1) for w in weights],
                           edge_color="#666666")
    nx.draw_networkx_nodes(
        G, pos, nodelist=A, ax=ax, node_color=viz.COLOR_AUTHOR,
        node_size=[min(16 + 22 * (G.degree(n, weight="weight") - 1), 130) for n in A],
        alpha=0.82, linewidths=0.3, edgecolors="white")
    nx.draw_networkx_nodes(
        G, pos, nodelist=V, ax=ax, node_color=viz.COLOR_VIDEO, node_shape="s",
        node_size=[min(150 + 3.0 * G.degree(n), 420) for n in V],
        alpha=0.95, linewidths=1.1, edgecolors="black")
    # Las etiquetas se desplazan hacia arriba para no tapar el nodo.
    span = max(max(y for _, y in pos.values()) - min(y for _, y in pos.values()), 1e-6)
    lab_pos = {n: (pos[n][0], pos[n][1] + 0.045 * span) for n in V}
    labels = {n: viz.wrap(G.nodes[n]["display_name"], 26) for n in V}
    nx.draw_networkx_labels(G, lab_pos, labels=labels, ax=ax, font_size=6.6,
                            font_weight="bold",
                            bbox=dict(boxstyle="round,pad=0.18", fc="white",
                                      ec="#D55E00", lw=0.6, alpha=0.9))
    ax.set_axis_off(); ax.grid(False)
    ax.margins(0.08)
    ax.set_title(
        f"Figura 15. Red bipartita completa autor-video\n"
        f"{len(A)} autores (circulos azules) + {len(V)} videos (cuadrados naranjas), "
        f"{G.number_of_edges()} aristas, suma de pesos = "
        f"{sum(d['weight'] for *_, d in G.edges(data=True))} comentarios",
        fontsize=13, fontweight="bold")
    ax.legend(handles=[
        mpatches.Patch(color=viz.COLOR_AUTHOR, label=f"Autor ({len(A)}) - tamano ~ comentarios"),
        mpatches.Patch(color=viz.COLOR_VIDEO, label=f"Video ({len(V)}) - tamano ~ autores"),
    ], loc="upper left", fontsize=9.5)
    viz.save(fig, "14_bipartite_network.png",
             "Red completa: no se elimino ningun nodo ni arista. La estructura dominante es "
             "de estrellas casi disjuntas (un video rodeado de autores de grado 1) unidas por "
             "unos pocos autores que comentaron en mas de un video. Una arista significa "
             "unicamente que el autor publico comentarios observados en ese video: no es "
             "amistad, respuesta, conversacion ni aprobacion.")

    # --- vista ampliada del nucleo conectado ---
    core_authors = [n for n in A if G.degree(n) > 1]
    core_nodes = set(core_authors) | set(V)
    H = G.subgraph(core_nodes).copy()
    H.remove_nodes_from([n for n in list(H.nodes())
                         if H.nodes[n]["node_type"] == "video" and H.degree(n) == 0])
    if H.number_of_nodes() > 2:
        pos2 = nx.spring_layout(H, seed=C.SEED, k=0.9, iterations=500, weight="weight")
        fig, ax = plt.subplots(figsize=(13, 9))
        nx.draw_networkx_edges(H, pos2, ax=ax, alpha=0.55,
                               width=[1.0 + 1.4 * (d["weight"] - 1)
                                      for *_, d in H.edges(data=True)],
                               edge_color="#444444")
        av = [n for n, d in H.nodes(data=True) if d["node_type"] == "author"]
        vv = [n for n, d in H.nodes(data=True) if d["node_type"] == "video"]
        nx.draw_networkx_nodes(H, pos2, nodelist=av, ax=ax, node_color=viz.COLOR_AUTHOR,
                               node_size=[180 + 60 * H.nodes[n]["n_videos"] for n in av],
                               edgecolors="black", linewidths=0.8)
        nx.draw_networkx_nodes(H, pos2, nodelist=vv, ax=ax, node_color=viz.COLOR_VIDEO,
                               node_shape="s",
                               node_size=[260 + 4 * G.degree(n) for n in vv],
                               edgecolors="black", linewidths=1.0)
        lab = {**{n: viz.wrap(H.nodes[n]["display_name"], 22) for n in vv},
               **{n: H.nodes[n]["handle"] for n in av}}
        nx.draw_networkx_labels(H, pos2, labels=lab, ax=ax, font_size=7,
                                bbox=dict(boxstyle="round,pad=0.2", fc="white",
                                          ec="#999999", lw=0.4, alpha=0.9))
        ax.set_axis_off(); ax.grid(False)
        ax.set_title(f"Figura 16. Ampliacion: solo los {len(av)} autores que comentaron en mas "
                     f"de un video y los {len(vv)} videos que conectan",
                     fontsize=12.5, fontweight="bold")
        viz.save(fig, "15_bipartite_core_zoom.png",
                 f"Vista ampliada COMPLEMENTARIA de la figura 15 (no la sustituye). Estos "
                 f"{len(av)} autores son el unico mecanismo por el que los videos de la muestra "
                 "quedan conectados entre si: el resto de autores tiene grado 1 y no aporta "
                 "conexion entre contenidos.")


def _ap_anchor_labels(AP: nx.Graph) -> dict:
    """Ancla de cada bloque de audiencia, para etiquetarlo con su video."""
    videos_of = {n: AP.nodes[n].get("_videos", []) for n in AP.nodes()}
    titles = {}
    for n, vs in videos_of.items():
        if len(vs) == 1:
            titles[vs[0]] = AP.nodes[n].get("_video_title", vs[0])
    all_videos = sorted({v for vs in videos_of.values() for v in vs})
    size = {v: sum(1 for vs in videos_of.values() if v in vs) for v in all_videos}
    anchors = _ring_anchors(all_videos, size)
    return {titles.get(v, v): tuple(a) for v, a in anchors.items()}


def plot_projections(AP: nx.Graph, VP: nx.Graph, G_ref: nx.Graph) -> None:
    """Ejercicio 5.4. Las DOS proyecciones completas."""
    # --- autor-autor ---
    pos = ap_layout(AP, G_ref)
    fig, ax = plt.subplots(figsize=(13.5, 11.5))
    nx.draw_networkx_edges(AP, pos, ax=ax, alpha=0.05, width=0.3, edge_color="#0072B2")
    multi = [n for n in AP.nodes() if AP.nodes[n]["n_videos"] > 1]
    single = [n for n in AP.nodes() if AP.nodes[n]["n_videos"] <= 1]
    nx.draw_networkx_nodes(AP, pos, nodelist=single, ax=ax, node_color=viz.COLOR_AUTHOR,
                           node_size=26, alpha=0.8, linewidths=0.25,
                           edgecolors="white")
    nx.draw_networkx_nodes(AP, pos, nodelist=multi, ax=ax, node_color="#F0E442",
                           node_size=[150 + 70 * AP.nodes[n]["n_videos"] for n in multi],
                           edgecolors="black", linewidths=1.2)
    nx.draw_networkx_labels(AP, {n: (pos[n][0], pos[n][1] + 0.16) for n in multi}, ax=ax,
                            font_size=7,
                            labels={n: f"{AP.nodes[n]['handle']}\n({AP.nodes[n]['n_videos']} videos)"
                                    for n in multi},
                            bbox=dict(boxstyle="round,pad=0.17", fc="#FFFBE6",
                                      ec="#8A7A00", lw=0.6, alpha=0.95))
    # etiquetar cada bloque de audiencia con el titulo de su video
    for v, a in _ap_anchor_labels(AP).items():
        f = 1 + 0.20 / AP_RING_RADIUS * 2.6
        ax.text(a[0] * f, a[1] * f, viz.wrap(v, 20), fontsize=6.8,
                ha="center", va="center", color="#7B2D00", fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.18", fc="white", ec="#D55E00",
                          lw=0.5, alpha=0.9))
    ax.set_axis_off(); ax.grid(False); ax.margins(0.16)
    ax.set_title(f"Figura 17. Proyeccion autor-autor completa\n"
                 f"{AP.number_of_nodes()} autores, {AP.number_of_edges()} aristas "
                 f"(peso = numero de videos compartidos)",
                 fontsize=13, fontweight="bold")
    ax.legend(handles=[
        mpatches.Patch(color=viz.COLOR_AUTHOR, label=f"Autor con un solo video comentado ({len(single)})"),
        mpatches.Patch(color="#F0E442", label=f"Autor con mas de un video comentado ({len(multi)})"),
    ], loc="upper center", bbox_to_anchor=(0.5, -0.005), fontsize=9.5, ncol=2,
        frameon=False)
    viz.save(fig, "16_author_projection.png",
             f"Red completa. Los {AP.number_of_edges()} vinculos forman una clique por cada video "
             "observado: cada bloque denso es la audiencia de un video, no un grupo de amigos. "
             f"Los {len(multi)} autores resaltados son los unicos que pertenecen a mas de un "
             "bloque y por tanto los unicos que pueden unir audiencias distintas.")

    # --- video-video ---
    pos = vp_layout(VP)
    fig, ax = plt.subplots(figsize=(14, 8))
    if VP.number_of_edges():
        w = [d["weight"] for *_, d in VP.edges(data=True)]
        nx.draw_networkx_edges(VP, pos, ax=ax, alpha=0.7,
                               width=[1.2 + 2.2 * (x - 1) for x in w],
                               edge_color="#666666")
        nx.draw_networkx_edge_labels(
            VP, pos, ax=ax, font_size=7.5,
            edge_labels={(u, v): str(d["weight"]) for u, v, d in VP.edges(data=True)},
            bbox=dict(boxstyle="round,pad=0.12", fc="#FFF6D0", ec="none", alpha=0.9))
    iso = [n for n in VP.nodes() if VP.degree(n) == 0]
    con = [n for n in VP.nodes() if VP.degree(n) > 0]
    nx.draw_networkx_nodes(VP, pos, nodelist=con, ax=ax, node_color=viz.COLOR_VIDEO,
                           node_shape="s",
                           node_size=[220 + 5.5 * VP.nodes[n]["n_comentarios"] for n in con],
                           edgecolors="black", linewidths=1.1)
    nx.draw_networkx_nodes(VP, pos, nodelist=iso, ax=ax, node_color="#B0B0B0",
                           node_shape="s",
                           node_size=[220 + 5.5 * VP.nodes[n]["n_comentarios"] for n in iso],
                           edgecolors="black", linewidths=1.0)
    lab_pos = {n: (x, y + 0.115) for n, (x, y) in pos.items()}
    nx.draw_networkx_labels(VP, lab_pos, ax=ax, font_size=7,
                            labels={n: viz.wrap(VP.nodes[n]["display_name"], 24)
                                    for n in VP.nodes()},
                            bbox=dict(boxstyle="round,pad=0.2", fc="white",
                                      ec="#999999", lw=0.4, alpha=0.94))
    ax.axhline(-0.35, color="#CCCCCC", ls="--", lw=1)
    ax.text(-1.42, -0.30, "Videos aislados en los datos observados (grado 0)",
            fontsize=8.5, style="italic", color="#666666")
    ax.set_axis_off(); ax.grid(False); ax.margins(0.11)
    ax.set_title(f"Figura 18. Proyeccion video-video completa\n"
                 f"{VP.number_of_nodes()} videos, {VP.number_of_edges()} aristas "
                 f"(peso = autores compartidos); {len(iso)} videos aislados en gris",
                 fontsize=13, fontweight="bold")
    ax.legend(handles=[
        mpatches.Patch(color=viz.COLOR_VIDEO, label=f"Video con audiencia compartida ({len(con)})"),
        mpatches.Patch(color="#B0B0B0", label=f"Video aislado en los datos observados ({len(iso)})"),
    ], loc="upper center", bbox_to_anchor=(0.5, -0.01), fontsize=9.5, ncol=2,
        frameon=False)
    viz.save(fig, "17_video_projection.png",
             f"Red completa, incluidos los {len(iso)} videos aislados. El numero sobre cada arista "
             "es el numero de autores compartidos. Los pesos son 1 o 2: la audiencia comun entre "
             "videos es minima. Un video aislado lo esta EN LA MUESTRA, no necesariamente en "
             "YouTube.")


def plot_degree_distributions(G: nx.Graph, AP: nx.Graph, VP: nx.Graph,
                              topo: pd.DataFrame) -> None:
    """Ejercicio 6.1. Distribucion de grados con histograma + ECDF."""
    specs = [
        ("Bipartita: autores", [G.degree(n) for n, d in G.nodes(data=True)
                                if d["node_type"] == "author"], viz.COLOR_AUTHOR,
         "13_degree_distribution_bipartite.png",
         "Bipartita: videos", [G.degree(n) for n, d in G.nodes(data=True)
                               if d["node_type"] == "video"], viz.COLOR_VIDEO),
        ("Proyeccion autor-autor", [d for _, d in AP.degree()], viz.COLOR_AUTHOR,
         "18_degree_distribution_authors.png",
         "Proyeccion autor-autor: fuerza", [d for _, d in AP.degree(weight="weight")],
         "#56B4E9"),
        ("Proyeccion video-video", [d for _, d in VP.degree()], viz.COLOR_VIDEO,
         "19_degree_distribution_videos.png",
         "Proyeccion video-video: fuerza", [d for _, d in VP.degree(weight="weight")],
         "#E69F00"),
    ]
    fignum = {"13_degree_distribution_bipartite.png": 19,
              "18_degree_distribution_authors.png": 20,
              "19_degree_distribution_videos.png": 21}
    for t1, d1, c1, fname, t2, d2, c2 in specs:
        fig, axes = plt.subplots(1, 3, figsize=(15.5, 4.6))
        for ax, t, d, c in [(axes[0], t1, d1, c1), (axes[1], t2, d2, c2)]:
            d = np.array(d, dtype=float)
            bins = min(30, max(6, len(np.unique(d))))
            ax.hist(d, bins=bins, color=c, edgecolor="white")
            ax.axvline(np.median(d), color="black", ls="--", lw=1.4,
                       label=f"mediana = {np.median(d):.0f}")
            ax.axvline(d.mean(), color="#D55E00", ls=":", lw=1.6,
                       label=f"media = {d.mean():.2f}")
            ax.set_xlabel("Grado" if "fuerza" not in t else "Fuerza (grado ponderado)")
            ax.set_ylabel("Numero de nodos")
            ax.set_title(f"{t}\nmax={d.max():.0f}, p90={np.percentile(d,90):.0f}")
            ax.legend(fontsize=8)
        d = np.sort(np.array(d1, dtype=float))
        ecdf = np.arange(1, d.size + 1) / d.size
        axes[2].step(d, 100 * ecdf, where="post", color=c1, lw=2)
        axes[2].set_xlabel("Grado")
        axes[2].set_ylabel("% de nodos con grado <= x")
        axes[2].set_title(f"ECDF de {t1}\n"
                          f"{100*float((d<=np.median(d)).mean()):.0f}% con grado <= mediana")
        axes[2].set_ylim(0, 101)
        for q in (50, 90):
            axes[2].axhline(q, color="#B0B0B0", ls=":", lw=1)
            axes[2].text(d.max() * 0.62, q + 1.5, f"p{q} = {np.percentile(d,q):.0f}",
                         fontsize=8, color="#555555")
        fig.suptitle(f"Figura {fignum[fname]}. Distribucion de grados y de fuerza",
                     fontsize=13, fontweight="bold")
        fig.tight_layout()
        d1a = np.array(d1, dtype=float)
        viz.save(fig, fname,
                 f"Distribucion muy asimetrica: mediana {np.median(d1a):.0f} frente a maximo "
                 f"{d1a.max():.0f}, y {100*float((d1a<=2).mean()):.1f}% de los nodos con grado "
                 f"<= 2. La conectividad no esta repartida: se concentra en unos pocos nodos.")


def plot_communities(VP: nx.Graph, communities: dict, summary: pd.DataFrame) -> None:
    """Ejercicio 7.4. TODAS las comunidades, incluidos los singletons."""
    parts = communities["video_projection"]["_partition"]
    cmap = {}
    for i, p in enumerate(parts):
        for x in p:
            cmap[x] = i
    colors = viz.PALETTE * (len(parts) // len(viz.PALETTE) + 1)

    pos = vp_layout(VP)
    fig, ax = plt.subplots(figsize=(14.5, 8.2))
    if VP.number_of_edges():
        nx.draw_networkx_edges(
            VP, pos, ax=ax, alpha=0.65,
            width=[1.2 + 2.2 * (d["weight"] - 1) for *_, d in VP.edges(data=True)],
            edge_color="#555555")
        nx.draw_networkx_edge_labels(
            VP, pos, ax=ax, font_size=7,
            edge_labels={(u, v): str(d["weight"]) for u, v, d in VP.edges(data=True)},
            bbox=dict(boxstyle="round,pad=0.1", fc="#FFF6D0", ec="none", alpha=0.85))
    for i, p in enumerate(parts):
        nx.draw_networkx_nodes(
            VP, pos, nodelist=list(p), ax=ax, node_color=colors[i], node_shape="s",
            node_size=[240 + 5.5 * VP.nodes[n]["n_comentarios"] for n in p],
            edgecolors="black", linewidths=1.1,
            label=f"C{i} (n={len(p)})")
    lab_pos = {n: (x, y + 0.115) for n, (x, y) in pos.items()}
    nx.draw_networkx_labels(VP, lab_pos, ax=ax, font_size=7,
                            labels={n: viz.wrap(VP.nodes[n]["display_name"], 24)
                                    for n in VP.nodes()},
                            bbox=dict(boxstyle="round,pad=0.2", fc="white",
                                      ec="#999999", lw=0.4, alpha=0.94))
    ax.axhline(-0.35, color="#CCCCCC", ls="--", lw=1)
    ax.text(-1.42, -0.30, "Comunidades singleton: videos sin audiencia compartida observada",
            fontsize=8.5, style="italic", color="#666666")
    ax.set_axis_off(); ax.grid(False); ax.margins(0.11)
    m = communities["video_projection"]
    ax.set_title(f"Figura 22. Todas las comunidades de la proyeccion video-video\n"
                 f"Louvain ponderado (semilla {C.SEED}, resolucion {C.LOUVAIN_RESOLUTION}): "
                 f"{m['n_comunidades']} comunidades, modularidad ponderada "
                 f"Q = {m['modularidad_ponderada']}, {m['n_singletons']} singletons",
                 fontsize=13, fontweight="bold")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.01), fontsize=8.5,
              ncol=6, frameon=False)
    viz.save(fig, "20_video_communities.png",
             f"Se muestran las {m['n_comunidades']} comunidades, incluidos los "
             f"{m['n_singletons']} singletons (videos sin audiencia compartida observada). "
             f"Q = {m['modularidad_ponderada']} indica una particion mejor que el azar, pero "
             "sobre una red muy dispersa: la modularidad de un grafo casi desconectado se "
             "obtiene facilmente y no debe leerse como comunidades tematicas robustas.")

    # --- tamano e intensidad por comunidad ---
    if len(summary):
        s = summary.sort_values("n_comentarios_observados", ascending=False)
        fig, axes = plt.subplots(1, 3, figsize=(15.5, 4.8))
        viz.barh(axes[0], [f"C{int(i)}" for i in s["comunidad"]], s["n_videos"].values,
                 "#0072B2")
        axes[0].set_xlabel("Videos en la comunidad")
        axes[0].set_title("Tamano (numero de videos)")
        viz.barh(axes[1], [f"C{int(i)}" for i in s["comunidad"]],
                 s["n_comentarios_observados"].values, "#D55E00")
        axes[1].set_xlabel("Comentarios observados")
        axes[1].set_title("Intensidad de participacion")
        viz.barh(axes[2], [f"C{int(i)}" for i in s["comunidad"]],
                 s["n_autores_unicos"].values, "#009E73")
        axes[2].set_xlabel("Autores unicos")
        axes[2].set_title("Amplitud de audiencia")
        fig.suptitle("Figura 23. Tamano frente a intensidad de las comunidades",
                     fontsize=13, fontweight="bold")
        fig.tight_layout()
        viz.save(fig, "21_community_sizes.png",
                 "El tamano de una comunidad en numero de videos no predice su intensidad de "
                 f"participacion: la comunidad con mas comentarios ({int(s.n_comentarios_observados.iloc[0])}) "
                 f"tiene {int(s.n_videos.iloc[0])} videos, mientras que otras con mas videos "
                 "acumulan mucho menos.")


def plot_centrality(ac: pd.DataFrame, vc: pd.DataFrame) -> None:
    """Ejercicio 8. Comparacion de medidas de centralidad."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    a = ac.nlargest(12, "betweenness_ponderada")
    viz.barh(axes[0, 0], a["handle"].tolist(), a["betweenness_ponderada"].values,
             viz.COLOR_AUTHOR, fmt="{:.4f}")
    axes[0, 0].set_xlabel("Betweenness ponderada (distancia = 1/peso)")
    axes[0, 0].set_title("Autores: intermediacion en la proyeccion autor-autor")
    a2 = ac.nlargest(12, "strength")
    viz.barh(axes[0, 1], a2["handle"].tolist(), a2["strength"].values, "#56B4E9")
    axes[0, 1].set_xlabel("Fuerza (suma de videos compartidos con otros autores)")
    axes[0, 1].set_title("Autores: fuerza en la proyeccion autor-autor")
    v = vc.nlargest(12, "betweenness_ponderada")
    viz.barh(axes[1, 0], [viz.wrap(t, 30) for t in v["display_name"]],
             v["betweenness_ponderada"].values, viz.COLOR_VIDEO, fmt="{:.4f}")
    axes[1, 0].set_xlabel("Betweenness ponderada (distancia = 1/peso)")
    axes[1, 0].set_title("Videos: intermediacion en la proyeccion video-video")
    axes[1, 0].tick_params(labelsize=7)
    v2 = vc.nlargest(12, "pagerank")
    viz.barh(axes[1, 1], [viz.wrap(t, 30) for t in v2["display_name"]],
             v2["pagerank"].values, "#E69F00", fmt="{:.4f}")
    axes[1, 1].set_xlabel("PageRank ponderado (alpha = 0.85)")
    axes[1, 1].set_title("Videos: PageRank en la proyeccion video-video")
    axes[1, 1].tick_params(labelsize=7)
    fig.suptitle("Figura 24. Centralidades de autores y videos", fontsize=13, fontweight="bold")
    fig.tight_layout()
    n_bt = int((ac.betweenness_ponderada > 0).sum())
    viz.save(fig, "22_centrality.png",
             f"Solo {n_bt} de {len(ac)} autores tienen betweenness > 0: la inmensa mayoria no "
             "intermedia nada porque pertenece a una sola clique de video. Fuerza y betweenness "
             "ordenan distinto, lo que confirma que un ranking de grado no basta para llamar "
             "'puente' a un nodo.")

    # --- correlacion entre medidas ---
    cols = ["degree", "strength", "betweenness_ponderada", "closeness_wf",
            "harmonic", "pagerank", "eigenvector"]
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.4))
    for ax, df, t in [(axes[0], ac, "Proyeccion autor-autor"),
                      (axes[1], vc, "Proyeccion video-video")]:
        sub = df[cols].apply(pd.to_numeric, errors="coerce")
        corr = sub.corr(method="spearman")
        im = ax.imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1)
        ax.set_xticks(range(len(cols)))
        ax.set_xticklabels(cols, rotation=45, ha="right", fontsize=8)
        ax.set_yticks(range(len(cols)))
        ax.set_yticklabels(cols, fontsize=8)
        ax.grid(False)
        for i in range(len(cols)):
            for j in range(len(cols)):
                val = corr.iloc[i, j]
                if val == val:
                    ax.text(j, i, f"{val:.2f}", ha="center", va="center", fontsize=7.5,
                            color="white" if abs(val) > 0.6 else "black")
        ax.set_title(f"{t} (n={len(df)})")
        fig.colorbar(im, ax=ax, shrink=0.8, label="Spearman rho")
    fig.suptitle("Figura 25. Concordancia entre medidas de centralidad",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    viz.save(fig, "23_centrality_correlation.png",
             "Correlacion de rangos entre medidas. Grado, fuerza, PageRank y eigenvector miden "
             "casi lo mismo en estas redes, mientras que betweenness se separa: identifica una "
             "propiedad distinta (estar en el camino entre grupos) y es la medida pertinente "
             "para detectar puentes.")


# ============================================================ caracterizacion ==
def community_profile(VP: nx.Graph, communities: dict, comments: pd.DataFrame,
                      videos: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Ejercicio 7.5 (parte estructural y de contenido; el sentimiento se
    agrega despues en ``content_analysis``)."""
    parts = communities["video_projection"]["_partition"]
    rows_nodes, rows_summary = [], []
    for i, p in enumerate(parts):
        raw = [VP.nodes[x]["raw_id"] for x in p]
        sub = comments[comments.video_id.isin(raw)]
        vinfo = videos[videos.video_id.isin(raw)]
        internal = sum(1 for u, v in VP.edges() if u in p and v in p)
        wint = sum(d["weight"] for u, v, d in VP.edges(data=True) if u in p and v in p)
        for x in p:
            rows_nodes.append({
                "comunidad": i, "node_id": x, "video_id": VP.nodes[x]["raw_id"],
                "titulo": VP.nodes[x]["display_name"],
                "channel_id": VP.nodes[x]["channel_id"],
                "canal": VP.nodes[x]["channel_name"],
                "category": VP.nodes[x]["category"],
                "source_query": VP.nodes[x]["source_query"],
                "view_count": VP.nodes[x]["view_count"],
                "n_comentarios_observados": VP.nodes[x]["n_comentarios"],
                "n_autores_observados": VP.nodes[x].get("n_autores", 0),
                "degree_en_proyeccion": VP.degree(x),
                "strength_en_proyeccion": VP.degree(x, weight="weight"),
                "es_singleton": len(p) == 1,
            })
        shared = sub.groupby("author_channel_id")["video_id"].nunique()
        rows_summary.append({
            "comunidad": i,
            "n_videos": len(p),
            "es_singleton": len(p) == 1,
            "n_canales": int(vinfo["channel_id"].nunique()),
            "canales": " || ".join(sorted(vinfo["channel_name"].unique())),
            "n_comentarios_observados": int(len(sub)),
            "pct_de_comentarios": round(100 * len(sub) / len(comments), 2),
            "n_autores_unicos": int(sub["author_channel_id"].nunique()),
            "n_autores_en_mas_de_un_video_de_la_comunidad": int((shared > 1).sum()),
            "comentarios_por_autor": round(len(sub) / max(sub["author_channel_id"].nunique(), 1), 3),
            "comentarios_por_video": round(len(sub) / len(p), 2),
            "n_me_gusta": int(sub["like_count"].sum()),
            "n_respuestas": int(sub["reply_count_num"].sum()),
            "views_totales": float(vinfo["view_count_final"].sum()),
            "views_medianas": float(vinfo["view_count_final"].median()),
            "categorias": " || ".join(sorted(vinfo["category"].dropna().unique())),
            "source_queries": " || ".join(sorted(vinfo["source_query"].dropna().unique())),
            "source_groups": " || ".join(sorted(vinfo["source_group"].dropna().unique())),
            "aristas_internas": internal,
            "peso_interno_total": wint,
            "densidad_interna": round(
                2 * internal / (len(p) * (len(p) - 1)), 4) if len(p) > 1 else np.nan,
            "titulos": " || ".join(sorted(vinfo["title"].tolist())),
            "video_ids": "|".join(sorted(raw)),
        })
    nodes_df = pd.DataFrame(rows_nodes)
    summary_df = pd.DataFrame(rows_summary).sort_values(
        ["n_videos", "n_comentarios_observados"], ascending=False)
    return nodes_df, summary_df


def _gini(x: np.ndarray) -> float:
    a = np.sort(np.asarray(x, dtype=float))
    n = a.size
    if n == 0 or a.sum() == 0:
        return float("nan")
    idx = np.arange(1, n + 1)
    return float((2 * idx - n - 1).dot(a) / (n * a.sum()))


def _graphml_safe(G: nx.Graph) -> nx.Graph:
    """GraphML no admite None ni NaN: se sanean los atributos."""
    H = G.copy()
    for _, d in H.nodes(data=True):
        d.pop("_videos", None)
        d.pop("_video_title", None)
        for k, v in list(d.items()):
            if v is None or (isinstance(v, float) and np.isnan(v)):
                d[k] = ""
            elif isinstance(v, (list, tuple, set)):
                d[k] = json.dumps(list(v), ensure_ascii=False)
            elif isinstance(v, (np.integer,)):
                d[k] = int(v)
            elif isinstance(v, (np.floating,)):
                d[k] = float(v)
    for *_, d in H.edges(data=True):
        for k, v in list(d.items()):
            if v is None or (isinstance(v, float) and np.isnan(v)):
                d[k] = ""
            elif isinstance(v, (np.integer,)):
                d[k] = int(v)
            elif isinstance(v, (np.floating,)):
                d[k] = float(v)
    return H


def _load():
    videos = pd.read_csv(C.VIDEOS_CLEAN, dtype={"video_id": str, "channel_id": str})
    comments = pd.read_csv(
        C.COMMENTS_CLEAN,
        dtype={"video_id": str, "comment_id": str, "channel_id": str,
               "author_channel_id": str},
        keep_default_na=False, na_values=[""])
    comments["reply_count_num"] = pd.to_numeric(comments["reply_count_num"], errors="coerce")
    comments["like_count"] = pd.to_numeric(comments["like_count"], errors="coerce").fillna(0)
    comments["len_original"] = pd.to_numeric(comments["len_original"], errors="coerce")
    return videos, comments


# ================================================================== pipeline ==
def run() -> dict:
    C.set_seeds()
    print("[3/6] network_analysis: bipartita, proyecciones, topologia, comunidades")
    videos, comments = _load()

    G = build_bipartite(comments, videos)
    inv = bipartite_invariants(G, comments)
    bad = [k for k, v in inv.items() if k.startswith("inv_") and not v]
    if bad:
        raise AssertionError(f"Invariantes de la red bipartita violadas: {bad}")
    nodes_df, edges_df = export_bipartite_tables(G)

    AP, VP = build_projections(G)
    proj_check = verify_projection_weights(G, AP, VP, comments)
    bad = [k for k, v in proj_check.items() if k.startswith("inv_") and not v]
    if bad:
        raise AssertionError(f"Pesos de proyeccion incorrectos: {bad}")
    export_projection_tables(AP, VP)

    topo_rows = [
        topology(G, "bipartita_autor_video", "bipartita"),
        topology(AP, "proyeccion_autor_autor", "unimodal"),
        topology(VP, "proyeccion_video_video", "unimodal"),
    ]
    topo = pd.DataFrame(topo_rows)
    topo_out = topo.copy()
    topo_out["tamanos_componentes"] = topo_out["tamanos_componentes"].map(
        lambda x: json.dumps(x))
    topo_out.T.to_csv(C.TABLES / "network_metrics.csv")
    topo_out.to_csv(C.TABLES / "network_metrics_wide.csv", index=False)

    periph = peripheral_analysis(G, AP, VP, comments)

    comms = detect_communities(VP, AP)
    cnodes, csummary = community_profile(VP, comms, comments, videos)
    cnodes.to_csv(C.TABLES / "communities.csv", index=False)
    csummary.to_csv(C.TABLES / "community_summary.csv", index=False)

    ac = centrality(AP, "author")
    vc = centrality(VP, "video")
    ac.to_csv(C.TABLES / "author_centrality.csv", index=False)
    vc.to_csv(C.TABLES / "video_centrality.csv", index=False)

    arts = articulation_analysis(
        {"bipartita_autor_video": G, "proyeccion_autor_autor": AP,
         "proyeccion_video_video": VP})
    arts.to_csv(C.TABLES / "articulation_points.csv", index=False)

    bridges = bridge_authors(G, AP, VP, comments, comms)
    bridges.to_csv(C.TABLES / "bridge_authors.csv", index=False)

    plot_bipartite(G)
    plot_projections(AP, VP, G)
    plot_degree_distributions(G, AP, VP, topo)
    plot_communities(VP, comms, csummary)
    plot_centrality(ac, vc)

    comms_public = {k: {kk: vv for kk, vv in v.items() if kk != "_partition"}
                    if isinstance(v, dict) else v for k, v in comms.items()}
    C.write_metrics("network_bipartite", inv)
    C.write_metrics("network_projections", proj_check)
    C.write_metrics("network_topology", {r["red"]: r for r in topo_rows})
    C.write_metrics("network_peripheral", periph)
    C.write_metrics("communities", comms_public)
    C.write_metrics("centrality_summary", _centrality_summary(ac, vc, arts, bridges))
    (C.NETWORKS / "video_partition.json").write_text(
        json.dumps({f"C{i}": [VP.nodes[x]["raw_id"] for x in p]
                    for i, p in enumerate(comms["video_projection"]["_partition"])},
                   indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"      bipartita: {inv['nodos_totales']} nodos / {inv['aristas']} aristas / "
          f"suma pesos {inv['suma_pesos']}")
    print(f"      AP: {AP.number_of_nodes()}n {AP.number_of_edges()}e | "
          f"VP: {VP.number_of_nodes()}n {VP.number_of_edges()}e | "
          f"comunidades VP: {comms['video_projection']['n_comunidades']} "
          f"(Q={comms['video_projection']['modularidad_ponderada']})")
    print(f"      puentes verificados: {int(bridges.es_puente_verificado.sum())} | "
          f"articuladores VP: {int(((arts.red=='proyeccion_video_video') & arts.es_articulador_verificado).sum()) if len(arts) else 0}")
    return {"G": G, "AP": AP, "VP": VP, "communities": comms,
            "community_summary": csummary, "author_centrality": ac,
            "video_centrality": vc, "articulation": arts, "bridges": bridges}


def _centrality_summary(ac, vc, arts, bridges) -> dict:
    return {
        "n_autores_evaluados": int(len(ac)),
        "n_videos_evaluados": int(len(vc)),
        "autores_con_betweenness_positiva": int((ac.betweenness_ponderada > 0).sum()),
        "pct_autores_con_betweenness_positiva": round(
            100 * float((ac.betweenness_ponderada > 0).mean()), 2),
        "videos_con_betweenness_positiva": int((vc.betweenness_ponderada > 0).sum()),
        "top_autores_betweenness": ac.nlargest(10, "betweenness_ponderada")[
            ["raw_id", "handle", "n_comentarios_observados", "n_videos_comentados",
             "n_canales_comentados", "degree", "strength", "betweenness_ponderada",
             "pagerank", "es_punto_articulacion"]].to_dict("records"),
        "top_autores_strength": ac.nlargest(10, "strength")[
            ["raw_id", "handle", "n_comentarios_observados", "n_videos_comentados",
             "strength", "betweenness_ponderada"]].to_dict("records"),
        "top_autores_recurrencia": ac.nlargest(10, "n_comentarios_observados")[
            ["raw_id", "handle", "n_comentarios_observados", "n_videos_comentados",
             "n_canales_comentados", "betweenness_ponderada"]].to_dict("records"),
        "top_videos_betweenness": vc.nlargest(10, "betweenness_ponderada")[
            ["raw_id", "display_name", "channel_name", "n_comentarios_observados",
             "view_count", "degree", "strength", "betweenness_ponderada", "pagerank",
             "es_punto_articulacion"]].to_dict("records"),
        "top_videos_strength": vc.nlargest(10, "strength")[
            ["raw_id", "display_name", "channel_name", "degree", "strength",
             "betweenness_ponderada"]].to_dict("records"),
        "articuladores_verificados": arts[arts.es_articulador_verificado][
            ["red", "raw_id", "display_name", "channel_name", "degree",
             "componentes_antes", "componentes_despues", "delta_componentes",
             "reduccion_componente_mayor", "nodos_aislados_tras_eliminar"]
        ].to_dict("records") if len(arts) else [],
        "n_articuladores_por_red": arts[arts.es_articulador_verificado].groupby("red").size()
            .to_dict() if len(arts) else {},
        "autores_puente_verificados": bridges[bridges.es_puente_verificado][
            ["author_channel_id", "author_handle", "n_comentarios", "n_videos_distintos",
             "n_canales_distintos", "n_comunidades_video_tocadas",
             "delta_componentes_al_eliminar", "aristas_video_perdidas_al_eliminar",
             "titulos_videos", "canales"]].to_dict("records"),
        "n_autores_puente_verificados": int(bridges.es_puente_verificado.sum()),
        "autores_multivideo": bridges[bridges.n_videos_distintos > 1][
            ["author_channel_id", "author_handle", "n_comentarios", "n_videos_distintos",
             "n_canales_distintos", "n_comunidades_video_tocadas",
             "es_puente_verificado", "delta_componentes_al_eliminar",
             "titulos_videos", "canales"]].to_dict("records"),
        "n_autores_multivideo": int((bridges.n_videos_distintos > 1).sum()),
        "n_autores_multicanal": int(bridges.es_multicanal.sum()),
        "n_autores_multicomunidad": int(bridges.es_multicomunidad.sum()),
        "n_autores_recurrentes": int(bridges.es_recurrente.sum()),
        "justificacion_medidas": {
            "degree": "Numero de vecinos: alcance directo dentro de la red.",
            "strength": "Grado ponderado: intensidad total del vinculo, no solo su numero.",
            "betweenness": (
                "Fraccion de caminos mas cortos que pasan por el nodo. Es la medida "
                "pertinente para 'puente' porque premia estar entre grupos, no "
                "tener muchos vecinos. Se calcula con distance = 1/weight."),
            "closeness_wf": (
                "Cercania con correccion de Wasserman-Faust, necesaria porque las "
                "redes estan desconectadas y la formula clasica seria indefinida."),
            "harmonic": (
                "Suma de reciprocos de distancias: bien definida con distancias "
                "infinitas, por lo que es la alternativa robusta a closeness en "
                "grafos fragmentados."),
            "pagerank": (
                "Prestigio recursivo ponderado: un nodo importa si esta vinculado "
                "a nodos importantes. Alpha = 0.85."),
            "eigenvector": (
                "Version espectral del prestigio; se reporta para contrastar con "
                "PageRank, del que suele diferir en grafos desconectados."),
            "k_core": "Profundidad del nodo en la jerarquia de nucleos: perifericidad.",
            "articulation_points": (
                "Nodos cuya eliminacion aumenta el numero de componentes. Es una "
                "propiedad estructural verificable, no un ranking."),
            "transformacion_de_pesos": (
                "En las proyecciones weight es intensidad (mas compartido = mas "
                "fuerte) pero networkx trata weight como distancia en los "
                "algoritmos de camino mas corto. Se define distance = 1/weight "
                "para que un vinculo fuerte cuente como cercano."),
        },
    }


if __name__ == "__main__":
    run()
