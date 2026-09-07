"""Orquestador del pipeline completo del Laboratorio 6.

Uso
---
    uv run python -m src.run_all

Ejecuta, en orden y con la semilla fija, las seis etapas del analisis y
valida al final que existan todos los entregables obligatorios. Cada etapa es
tambien ejecutable por separado (``uv run python -m src.<modulo>``), pero el
orden importa: el analisis de contenido consume las comunidades de la red y
las predicciones de sentimiento, y el informe consume todo lo anterior.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

from . import config as C

STAGES = [
    ("data_preparation", "Ejercicios 1-2: carga, integracion, calidad y limpieza"),
    ("exploratory_analysis", "Ejercicio 3: EDA, concentracion y popularidad"),
    ("network_analysis", "Ejercicios 4-8: redes, topologia, comunidades, centralidad"),
    ("sentiment_analysis", "Ejercicio 9: sentimiento en espanol"),
    ("content_analysis", "Ejercicios 7.5, 3.5 y 3.6: contenido y preguntas"),
    ("report_generation", "Ejercicio 10: informe final en Markdown y PDF"),
]

#: Entregables que deben existir al terminar el pipeline.
REQUIRED_OUTPUTS = [
    "report/Laboratorio_6_Analisis_Redes_Sociales_YouTube.pdf",
    "report/laboratorio_6_reporte.md",
    "results/model/sentiment_model_report.md",
    "results/networks/bipartite_nodes.csv",
    "results/networks/bipartite_edges.csv",
    "results/networks/author_projection_edges.csv",
    "results/networks/video_projection_edges.csv",
    "results/tables/data_quality_videos.csv",
    "results/tables/data_quality_comments.csv",
    "results/tables/consistency_checks.csv",
    "results/tables/cleaning_effect.csv",
    "results/tables/videos_summary.csv",
    "results/tables/comments_by_video.csv",
    "results/tables/comments_by_channel.csv",
    "results/tables/top_words.csv",
    "results/tables/top_bigrams.csv",
    "results/tables/top_hashtags.csv",
    "results/tables/network_metrics.csv",
    "results/tables/author_centrality.csv",
    "results/tables/video_centrality.csv",
    "results/tables/articulation_points.csv",
    "results/tables/bridge_authors.csv",
    "results/tables/communities.csv",
    "results/tables/community_summary.csv",
    "results/tables/sentiment_predictions.csv",
    "results/tables/sentiment_summary.csv",
    "data/processed/comments_clean.csv",
    "data/processed/videos_clean.csv",
    "data/processed/comments_videos_joined.csv",
]

REQUIRED_METRICS = [
    "load", "quality", "join", "cleaning", "descriptives", "concentration",
    "popularity", "coverage_bias", "network_bipartite", "network_projections",
    "network_topology", "network_peripheral", "communities",
    "centrality_summary", "sentiment", "community_characterization",
    "questions_mandatory", "questions_additional",
]

MIN_FIGURES = 24


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    only = [a for a in argv if not a.startswith("-")]
    C.set_seeds()

    print("=" * 74)
    print("CC3084 Laboratorio 6 - Analisis de redes sociales (YouTube)")
    print(f"Raiz del proyecto: {C.ROOT}")
    print(f"Semilla global: {C.SEED} | Modelo de sentimiento: {C.SENTIMENT_MODEL_ID}")
    print("=" * 74)

    t_start = time.perf_counter()
    for name, desc in STAGES:
        if only and name not in only:
            print(f"[omitido] {name}")
            continue
        print(f"\n--- {name}: {desc}")
        t0 = time.perf_counter()
        module = __import__(f"src.{name}", fromlist=["run"])
        module.run()
        print(f"      completado en {time.perf_counter() - t0:.1f}s")

    if only:
        print("\n[aviso] ejecucion parcial: no se validan los entregables.")
        return 0

    print("\n" + "=" * 74)
    print("Validacion de entregables")
    print("=" * 74)
    missing = [p for p in REQUIRED_OUTPUTS if not (C.ROOT / p).exists()]
    empty = [p for p in REQUIRED_OUTPUTS
             if (C.ROOT / p).exists() and (C.ROOT / p).stat().st_size == 0]
    missing_metrics = [m for m in REQUIRED_METRICS
                       if not (C.METRICS / f"{m}.json").exists()]
    figures = sorted(C.FIGURES.glob("*.png"))

    ok = True
    for label, items in [("archivos faltantes", missing), ("archivos vacios", empty),
                         ("metricas faltantes", missing_metrics)]:
        if items:
            ok = False
            print(f"  FALLO - {label}: {items}")
    print(f"  {'OK  ' if not missing and not empty else 'FALLO'} - "
          f"{len(REQUIRED_OUTPUTS) - len(missing) - len(empty)}/"
          f"{len(REQUIRED_OUTPUTS)} entregables presentes y no vacios")
    print(f"  {'OK  ' if not missing_metrics else 'FALLO'} - "
          f"{len(REQUIRED_METRICS) - len(missing_metrics)}/{len(REQUIRED_METRICS)} "
          "bloques de metricas presentes")
    if len(figures) < MIN_FIGURES:
        ok = False
        print(f"  FALLO - solo {len(figures)} figuras (se esperan >= {MIN_FIGURES})")
    else:
        print(f"  OK   - {len(figures)} figuras PNG generadas")

    pdf = C.REPORT / "Laboratorio_6_Analisis_Redes_Sociales_YouTube.pdf"
    if pdf.exists():
        from .report_generation import validate_pdf

        v = validate_pdf(pdf)
        for k, val in v.items():
            if k.startswith("ok_") and not val:
                ok = False
                print(f"  FALLO - validacion del PDF: {k}")
        print(f"  {'OK  ' if all(val for k, val in v.items() if k.startswith('ok_')) else 'FALLO'}"
              f" - PDF: {v['n_paginas']} paginas, {v['tamano_kb']} KB, "
              f"{v['n_caracteres_texto']} caracteres de texto extraible, "
              f"{v['n_imagenes']} imagenes incrustadas")

    print("=" * 74)
    print(f"{'PIPELINE COMPLETO' if ok else 'PIPELINE CON FALLOS'} "
          f"en {time.perf_counter() - t_start:.1f}s")
    print("=" * 74)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
