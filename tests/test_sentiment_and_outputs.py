"""Sentimiento, comunidades caracterizadas y existencia de los entregables."""
from __future__ import annotations

import math

import pytest

from src import config as C
from src.run_all import MIN_FIGURES, REQUIRED_METRICS, REQUIRED_OUTPUTS

LABELS = {"NEG", "NEU", "POS"}


# ------------------------------------------------------------- sentimiento ---
def test_cada_comentario_tiene_prediccion(table, comments):
    pred = table("sentiment_predictions", dtype={"comment_id": str})
    assert len(pred) == len(comments)
    assert set(pred["comment_id"]) == set(comments["comment_id"].astype(str))
    assert pred["comment_id"].duplicated().sum() == 0
    assert pred["predicted_label"].notna().all()


def test_etiquetas_son_las_del_modelo(table, metrics):
    pred = table("sentiment_predictions")
    assert set(pred["predicted_label"]) <= LABELS
    assert set(metrics("sentiment")["clases"]) == LABELS


def test_probabilidades_bien_formadas(table):
    pred = table("sentiment_predictions")
    cols = ["prob_NEG", "prob_NEU", "prob_POS"]
    for c in cols:
        assert pred[c].between(0, 1).all()
    sumas = pred[cols].sum(axis=1)
    assert sumas.between(0.999, 1.001).all(), "las probabilidades deben sumar 1"


def test_confianza_es_el_maximo_de_las_probabilidades(table):
    pred = table("sentiment_predictions")
    cols = ["prob_NEG", "prob_NEU", "prob_POS"]
    assert (pred[cols].max(axis=1) - pred["confidence"]).abs().max() < 1e-4


def test_etiqueta_es_el_argmax(table):
    pred = table("sentiment_predictions")
    cols = ["prob_NEG", "prob_NEU", "prob_POS"]
    argmax = pred[cols].idxmax(axis=1).str.replace("prob_", "", regex=False)
    assert (argmax == pred["predicted_label"]).all()


def test_confianza_no_se_confunde_con_polaridad(table, metrics):
    """La confianza debe ser >= 1/3 y no correlacionar trivialmente con la clase."""
    pred = table("sentiment_predictions")
    assert pred["confidence"].min() >= 1 / 3 - 1e-6
    assert pred["confidence"].max() <= 1.0
    assert "advertencia_confianza" in metrics("sentiment")


def test_se_uso_texto_original_como_entrada(table):
    """La entrada del modelo debe derivar de texto_original, no de texto_limpio."""
    pred = table("sentiment_predictions")
    assert "texto_sentimiento" in pred.columns
    assert "texto_original" in pred.columns
    dif = (pred["texto_sentimiento"].astype(str)
           != pred["texto_limpio"].astype(str)).mean()
    assert dif > 0.9, "la entrada de sentimiento no puede ser texto_limpio"


def test_metadatos_del_modelo_completos(metrics):
    m = metrics("sentiment")["modelo"]
    for k in ("model_id", "framework", "transformers_version", "torch_version",
              "tokenizer_class", "clases", "id2label", "max_length_usado",
              "truncation", "batch_size", "device", "seed",
              "fecha_ejecucion_utc", "arquitectura", "n_parametros"):
        assert k in m and m[k] not in (None, ""), f"falta metadato {k}"
    assert "robertuito" in m["model_id"].lower(), "el modelo debe ser de espanol"


def test_porcentajes_de_clase_suman_cien(metrics):
    p = metrics("sentiment")["pct_por_clase"]
    assert sum(p.values()) == pytest.approx(100.0, abs=0.05)


def test_comparaciones_declaran_el_n(metrics):
    st = metrics("sentiment")
    for key in ("comparacion_por_video", "comparacion_por_canal",
                "comparacion_por_comunidad", "comparacion_por_categoria"):
        for row in st[key]:
            assert "n" in row and row["n"] >= 1
            assert "comparable_n_mayor_igual_10" in row
            assert row["comparable_n_mayor_igual_10"] == (row["n"] >= 10)


def test_reporte_del_modelo_existe_y_cubre_los_puntos(metrics):
    path = C.MODEL_DIR / "sentiment_model_report.md"
    assert path.exists()
    md = path.read_text(encoding="utf-8")
    assert len(md) > 6000
    for req in ["Identificacion exacta del modelo", "Motivo de la seleccion",
                "Etiquetas y su significado", "Preprocesamiento",
                "Configuracion de inferencia", "Distribucion de clases",
                "Confianza", "Comparaciones por grupo", "Ejemplos representativos",
                "Casos ambiguos", "Limitaciones", "Referencia",
                "Advertencia final", "sarcasmo", "slang", "emojis",
                "domain shift", "no equivale a la intencion real"]:
        assert req.lower() in md.lower(), f"el reporte no cubre: {req}"
    assert metrics("sentiment")["modelo"]["model_id"] in md


# ----------------------------------------------------------- comunidades ---
def test_comunidades_caracterizadas_con_tema_y_sentimiento(table, metrics):
    cs = table("community_summary")
    cm = metrics("communities")["video_projection"]
    assert len(cs) == cm["n_comunidades"]
    for col in ("top_terminos_tfidf", "top_palabras", "top_bigramas",
                "pct_NEG", "pct_NEU", "pct_POS", "n_sentimiento",
                "canales", "categorias", "n_autores_unicos"):
        assert col in cs.columns
    no_trivial = cs[~cs.es_singleton]
    assert len(no_trivial) == cm["n_comunidades_no_triviales"]
    assert no_trivial["top_terminos_tfidf"].str.len().gt(5).all()
    assert (cs["n_sentimiento"] == cs["n_comentarios_observados"]).all()


def test_analiza_al_menos_tres_comunidades_o_todas(metrics):
    det = metrics("community_characterization")
    n = det["n_no_singleton"]
    assert len(det["comunidades_analizadas_en_detalle"]) == min(3, n)
    assert len(det["detalle"]) == min(3, n)
    assert det["justificacion_top3"]


def test_porcentajes_de_sentimiento_por_comunidad_suman_cien(table):
    cs = table("community_summary")
    tot = cs[["pct_NEG", "pct_NEU", "pct_POS"]].sum(axis=1)
    assert tot.between(99.9, 100.1).all()


# ------------------------------------------------------------- preguntas ---
def test_seis_preguntas_obligatorias_respondidas(metrics):
    q = metrics("questions_mandatory")
    assert set(q) == {"q1", "q2", "q3", "q4", "q5", "q6"}
    for k, v in q.items():
        assert v["pregunta"].strip().endswith("?")
        assert len(str(v)) > 300, f"{k} parece vacia"


def test_al_menos_tres_preguntas_adicionales_con_evidencia(metrics):
    a = metrics("questions_additional")
    assert len(a) >= 3
    for k, v in a.items():
        assert v["pregunta"].strip().endswith("?")
        assert len(v["respuesta"]) > 120, f"{k} sin respuesta sustantiva"
        assert len(v["motivacion"]) > 40, f"{k} sin motivacion"
        assert any(ch.isdigit() for ch in v["respuesta"]), \
            f"{k} responde sin cifras"


# ------------------------------------------------------------ entregables ---
@pytest.mark.parametrize("rel", REQUIRED_OUTPUTS)
def test_entregable_existe_y_no_esta_vacio(rel):
    p = C.ROOT / rel
    assert p.exists(), f"falta {rel}"
    assert p.stat().st_size > 0, f"{rel} esta vacio"


@pytest.mark.parametrize("name", REQUIRED_METRICS)
def test_bloque_de_metricas_existe(name):
    p = C.METRICS / f"{name}.json"
    assert p.exists() and p.stat().st_size > 0


def test_hay_suficientes_figuras():
    figs = sorted(C.FIGURES.glob("*.png"))
    assert len(figs) >= MIN_FIGURES
    for f in figs:
        assert f.stat().st_size > 20_000, f"{f.name} parece truncada"


def test_todas_las_figuras_tienen_interpretacion():
    from src import viz

    caps = viz.load_captions()
    for f in sorted(C.FIGURES.glob("*.png")):
        assert f.name in caps, f"{f.name} sin caption registrada"
        assert len(caps[f.name]) > 60, f"{f.name} con caption trivial"


def test_pdf_valido():
    from src.report_generation import PDF_PATH, validate_pdf

    v = validate_pdf(PDF_PATH)
    fallos = [k for k, val in v.items() if k.startswith("ok_") and not val]
    assert fallos == [], f"validaciones del PDF que fallan: {fallos} ({v})"
    assert v["secciones_faltantes"] == []
    assert v["n_caracteres_unicode_rotos"] == 0


def test_markdown_del_informe_completo():
    from src.report_generation import MD_PATH

    md = MD_PATH.read_text(encoding="utf-8")
    assert len(md) > 80_000
    for sec in ["Resumen ejecutivo", "Integracion de los datos", "Limitaciones",
                "Conclusiones", "Reproducibilidad", "Referencias"]:
        assert sec in md


def test_no_hay_secretos_en_el_repositorio():
    import re

    patrones = [re.compile(p, re.IGNORECASE) for p in (
        r"gh[pousr]_[A-Za-z0-9]{20,}", r"sk-[A-Za-z0-9]{20,}",
        r"AKIA[0-9A-Z]{16}", r"hf_[A-Za-z0-9]{30,}",
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    )]
    for path in C.ROOT.rglob("*"):
        if not path.is_file() or ".venv" in path.parts or ".git" in path.parts:
            continue
        if path.suffix.lower() in (".png", ".pdf", ".graphml", ".lock"):
            continue
        try:
            txt = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for pat in patrones:
            assert not pat.search(txt), f"posible secreto en {path.name}"
