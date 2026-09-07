"""Invariantes de la red bipartita, de las proyecciones y de las metricas."""
from __future__ import annotations

import math

import networkx as nx
import pandas as pd
import pytest

from src import config as C
from src.network_analysis import build_bipartite, build_projections


@pytest.fixture(scope="module")
def graphs(videos, comments):
    comments = comments.copy()
    comments["reply_count_num"] = pd.to_numeric(comments["reply_count_num"],
                                                errors="coerce")
    comments["like_count"] = pd.to_numeric(comments["like_count"],
                                           errors="coerce").fillna(0)
    comments["len_original"] = pd.to_numeric(comments["len_original"], errors="coerce")
    G = build_bipartite(comments, videos)
    AP, VP = build_projections(G)
    return G, AP, VP, comments


# ------------------------------------------------------ bipartita: estructura ---
def test_bipartita_es_no_dirigida_y_bipartita(graphs):
    G, *_ = graphs
    assert not G.is_directed()
    assert nx.is_bipartite(G)
    assert nx.number_of_selfloops(G) == 0


def test_toda_arista_une_autor_con_video(graphs):
    G, *_ = graphs
    for u, v in G.edges():
        assert G.nodes[u]["node_type"] != G.nodes[v]["node_type"]


def test_nodos_provienen_de_los_identificadores_correctos(graphs):
    G, _, _, comments = graphs
    autores = {G.nodes[n]["raw_id"] for n, d in G.nodes(data=True)
               if d["node_type"] == "author"}
    videos_ = {G.nodes[n]["raw_id"] for n, d in G.nodes(data=True)
               if d["node_type"] == "video"}
    assert autores == set(comments["author_channel_id"])
    assert videos_ == set(comments["video_id"])


def test_suma_de_pesos_igual_al_numero_de_comentarios(graphs):
    """Invariante central: si fallara, se habria usado la variable equivocada."""
    G, _, _, comments = graphs
    assert sum(d["weight"] for *_, d in G.edges(data=True)) == len(comments)


def test_una_sola_arista_por_par_autor_video(graphs):
    G, _, _, comments = graphs
    assert G.number_of_edges() == comments.groupby(
        ["author_channel_id", "video_id"]).ngroups


def test_pesos_coinciden_con_el_conteo_de_comentarios(graphs):
    """Recalculo independiente de cada peso desde el dataframe."""
    G, _, _, comments = graphs
    esperado = comments.groupby(["author_channel_id", "video_id"]).size()
    for u, v, d in G.edges(data=True):
        a, b = (u, v) if G.nodes[u]["node_type"] == "author" else (v, u)
        key = (G.nodes[a]["raw_id"], G.nodes[b]["raw_id"])
        assert d["weight"] == esperado[key]


def test_reply_count_no_se_uso_como_arista(graphs):
    """El total de respuestas difiere del de comentarios: la suma de pesos
    debe coincidir con el segundo y nunca con el primero."""
    G, _, _, comments = graphs
    total_respuestas = int(comments["reply_count_num"].fillna(0).sum())
    suma_pesos = sum(d["weight"] for *_, d in G.edges(data=True))
    assert total_respuestas != len(comments), "el caso de prueba perderia sentido"
    assert suma_pesos == len(comments)
    assert suma_pesos != total_respuestas


def test_endpoints_existen_en_la_tabla_de_nodos(table):
    nodes = table("bipartite_nodes")
    edges = table("bipartite_edges")
    ids = set(nodes["node_id"])
    assert set(edges["source"]) <= ids
    assert set(edges["target"]) <= ids


def test_tabla_de_nodos_tiene_tipo_y_atributos(table):
    nodes = table("bipartite_nodes")
    assert set(nodes["node_type"]) == {"author", "video"}
    for col in ("node_id", "raw_id", "node_type", "display_name", "degree",
                "strength", "n_comentarios_observados"):
        assert col in nodes.columns
    assert nodes["node_id"].duplicated().sum() == 0


def test_tabla_de_aristas_documenta_el_peso(table):
    edges = table("bipartite_edges")
    assert (edges["weight"] >= 1).all()
    assert edges["significado_peso"].str.contains("comentarios").all()
    assert (edges["source_type"] == "author").all()
    assert (edges["target_type"] == "video").all()
    assert edges[["source", "target"]].duplicated().sum() == 0


def test_invariantes_persistidas_todas_cumplen(metrics):
    inv = metrics("network_bipartite")
    fallidas = [k for k, v in inv.items() if k.startswith("inv_") and not v]
    assert fallidas == [], f"invariantes violadas: {fallidas}"


# ------------------------------------------------------------- proyecciones ---
def test_proyeccion_autores_peso_es_videos_compartidos(graphs):
    G, AP, _, comments = graphs
    vids = comments.groupby("author_channel_id")["video_id"].apply(set).to_dict()
    for u, v, d in AP.edges(data=True):
        esperado = len(vids[AP.nodes[u]["raw_id"]] & vids[AP.nodes[v]["raw_id"]])
        assert d["weight"] == esperado
        assert esperado >= 1


def test_proyeccion_videos_peso_es_autores_compartidos(graphs):
    G, _, VP, comments = graphs
    auts = comments.groupby("video_id")["author_channel_id"].apply(set).to_dict()
    for u, v, d in VP.edges(data=True):
        esperado = len(auts[VP.nodes[u]["raw_id"]] & auts[VP.nodes[v]["raw_id"]])
        assert d["weight"] == esperado
        assert esperado >= 1


def test_proyecciones_conservan_todos_los_nodos(graphs):
    G, AP, VP, comments = graphs
    assert AP.number_of_nodes() == comments["author_channel_id"].nunique()
    assert VP.number_of_nodes() == comments["video_id"].nunique()


def test_la_audiencia_de_cada_video_forma_una_clique(graphs):
    G, AP, _, comments = graphs
    for vid, auts in comments.groupby("video_id")["author_channel_id"].apply(set).items():
        auts = sorted(auts)
        for i, a in enumerate(auts):
            for b in auts[i + 1:]:
                assert AP.has_edge("A:" + a, "A:" + b), f"falta arista en {vid}"


def test_componentes_coinciden_entre_bipartita_y_proyecciones(graphs):
    G, AP, VP, _ = graphs
    assert (nx.number_connected_components(G)
            == nx.number_connected_components(VP))


def test_verificacion_de_pesos_persistida(metrics):
    pj = metrics("network_projections")
    assert pj["pesos_author_projection_incorrectos"] == 0
    assert pj["pesos_video_projection_incorrectos"] == 0
    assert pj["inv_clique_por_video_presente"] is True


# ---------------------------------------------------------------- topologia ---
def test_metricas_topologicas_sin_nan_inexplicado(metrics):
    """Solo se admiten NaN en metricas indefinidas por construccion."""
    permitidos = {
        "densidad_componente_mayor", "longitud_media_camino_componente_mayor",
        "assortatividad_de_grado", "grado_gini",
        "clustering_bipartito_latapy_medio",
    }
    topo = metrics("network_topology")
    for red, m in topo.items():
        for k, v in m.items():
            if isinstance(v, float) and math.isnan(v):
                assert k in permitidos, f"NaN inesperado en {red}.{k}"


def test_transitividad_bipartita_es_cero_por_construccion(metrics):
    b = metrics("network_topology")["bipartita_autor_video"]
    assert b["transitividad_global"] == 0.0
    assert b["clustering_bipartito_latapy_medio"] > 0


def test_cohesion_esta_definida_y_es_coherente(metrics):
    for red, m in metrics("network_topology").items():
        assert "definicion_cohesion" in m
        if not m["grafo_conexo"]:
            assert m["conectividad_por_nodos_global"] == 0, red
        assert m["conectividad_por_nodos_componente_mayor"] >= 0


def test_densidad_bipartita_usa_el_maximo_correcto(metrics):
    b = metrics("network_topology")["bipartita_autor_video"]
    assert b["max_aristas_bipartita"] == (b["n_nodos_tipo_autor"]
                                          * b["n_nodos_tipo_video"])
    assert b["densidad_bipartita"] == pytest.approx(
        b["n_aristas"] / b["max_aristas_bipartita"], rel=1e-3)


def test_componentes_suman_el_total_de_nodos(metrics):
    for red, m in metrics("network_topology").items():
        assert sum(m["tamanos_componentes"]) == m["n_nodos"], red
        assert m["tamano_componente_mayor"] == max(m["tamanos_componentes"]), red


# -------------------------------------------------- comunidades y centralidad ---
def test_comunidades_particionan_todos_los_videos(metrics, table):
    cm = metrics("communities")["video_projection"]
    nodes = table("communities")
    assert sum(cm["tamanos"]) == metrics("network_topology")[
        "proyeccion_video_video"]["n_nodos"]
    assert len(nodes) == sum(cm["tamanos"])
    assert nodes["video_id"].duplicated().sum() == 0
    assert nodes["comunidad"].nunique() == cm["n_comunidades"]


def test_modularidad_en_rango_valido(metrics):
    for key in ("video_projection", "author_projection"):
        q = metrics("communities")[key]["modularidad_ponderada"]
        assert -0.5 <= q <= 1.0


def test_singletons_reportados_explicitamente(metrics):
    cm = metrics("communities")["video_projection"]
    assert cm["n_singletons"] == sum(1 for s in cm["tamanos"] if s == 1)
    assert cm["n_comunidades_no_triviales"] == sum(1 for s in cm["tamanos"] if s > 1)


def test_articuladores_verificados_por_eliminacion(table):
    arts = table("articulation_points")
    assert len(arts) > 0
    for r in arts.itertuples():
        if r.es_articulador_verificado:
            assert r.componentes_despues > r.componentes_antes
            assert r.delta_componentes >= 1


def test_articuladores_reproducen_el_efecto_declarado(graphs, table):
    """Se re-elimina cada articulador de la proyeccion video-video y se
    comprueba que el numero de componentes crece como dice la tabla."""
    _, _, VP, _ = graphs
    arts = table("articulation_points")
    sub = arts[(arts.red == "proyeccion_video_video")
               & arts.es_articulador_verificado]
    base = nx.number_connected_components(VP)
    assert len(sub) > 0
    for r in sub.itertuples():
        H = VP.copy()
        H.remove_node("V:" + str(r.raw_id))
        assert nx.number_connected_components(H) - base == r.delta_componentes


def test_autores_puente_requieren_mas_de_un_video(table):
    br = table("bridge_authors")
    puentes = br[br.es_puente_verificado]
    assert len(puentes) > 0
    assert (puentes["n_videos_distintos"] > 1).all()
    assert (puentes["delta_componentes_al_eliminar"] >= 1).all()


def test_centralidad_cubre_todos_los_nodos(table, graphs):
    _, AP, VP, _ = graphs
    ac, vc = table("author_centrality"), table("video_centrality")
    assert len(ac) == AP.number_of_nodes()
    assert len(vc) == VP.number_of_nodes()
    for df in (ac, vc):
        assert df["raw_id"].duplicated().sum() == 0
        assert (df["betweenness_ponderada"] >= 0).all()
        assert (df["betweenness_ponderada"] <= 1).all()
        assert df["pagerank"].notna().all()
        assert df["pagerank"].sum() == pytest.approx(1.0, abs=1e-3)


def test_betweenness_usa_distancia_inversa_al_peso(graphs):
    """Con distance = 1/weight, una arista de peso alto debe acortar el camino.

    Se construye un grafo de prueba de cuatro nodos con dos rutas: una corta
    en numero de saltos pero de peso bajo, y otra de peso alto. Si el peso se
    pasara como distancia, el resultado se invertiria.
    """
    from src.network_analysis import centrality

    T = nx.Graph()
    for n, t in [("V:a", "video"), ("V:b", "video"), ("V:c", "video")]:
        T.add_node(n, node_type=t, raw_id=n[2:], display_name=n, handle="",
                   channel_id="", channel_name="", category="", source_query="",
                   source_group="", view_count=float("nan"), n_comentarios=0,
                   n_videos=0, n_canales=0, largo_medio_comentario=float("nan"),
                   me_gusta_recibidos=0, respuestas_recibidas=0)
    T.add_edge("V:a", "V:b", weight=10)
    T.add_edge("V:b", "V:c", weight=10)
    df = centrality(T, "video").set_index("raw_id")
    # b es el unico intermediario: su betweenness debe ser la maxima
    assert df.loc["b", "betweenness_ponderada"] > df.loc["a", "betweenness_ponderada"]
    assert df.loc["a", "betweenness_ponderada"] == 0.0
