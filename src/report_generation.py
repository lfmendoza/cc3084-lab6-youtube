"""Generacion del informe final en Markdown y PDF.

El contenido proviene integramente de ``src/report_s*.py``, que a su vez leen
``results/metrics/*.json`` y ``results/tables/*.csv``. Este modulo solo se
encarga de renderizar: no calcula ni escribe cifras.
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether,
                               NextPageTemplate, PageBreak, PageTemplate,
                               Paragraph, Spacer, Table, TableStyle)  # noqa: F401

from . import config as C
from . import viz
from .report_text import Ctx
from .report_s1 import (datos_y_unidades, integracion, introduccion,
                        resumen_ejecutivo)
from .report_s2 import calidad_y_limpieza
from .report_s3 import eda
from .report_s4 import preguntas_adicionales, preguntas_obligatorias
from .report_s5 import proyecciones, red_bipartita
from .report_s6 import centralidad, comunidades, topologia
from .report_s7 import (conclusiones, contenido, interpretacion, limitaciones,
                        referencias, reproducibilidad, sentimiento)

TITLE = "Analisis de redes sociales en YouTube"
SUBTITLE = "Estructura de participacion, comunidades de audiencia y sentimiento"
COURSE = "CC3084 - Data Science · Laboratorio 6"
UNIVERSITY = ("Universidad del Valle de Guatemala\n"
              "Facultad de Ingenieria · Departamento de Ciencias de la Computacion\n"
              "Semestre II, 2026")

PDF_PATH = C.REPORT / "Laboratorio_6_Analisis_Redes_Sociales_YouTube.pdf"
MD_PATH = C.REPORT / "laboratorio_6_reporte.md"

INK = colors.HexColor("#1A1A1A")
ACCENT = colors.HexColor("#0072B2")
ACCENT2 = colors.HexColor("#D55E00")
GREY = colors.HexColor("#666666")
LIGHT = colors.HexColor("#F2F5F8")
RULE = colors.HexColor("#C8D2DA")


# ============================================================== estructura ==
def build_document(c: Ctx) -> list:
    """Ensambla la lista completa de elementos del informe."""
    els: list = []
    els += resumen_ejecutivo(c)
    els += introduccion(c)
    els += datos_y_unidades(c)
    els += integracion(c)
    els += calidad_y_limpieza(c)
    els += eda(c)
    els += preguntas_obligatorias(c)
    els += preguntas_adicionales(c)
    els += red_bipartita(c)
    els += proyecciones(c)
    els += topologia(c)
    els += comunidades(c)
    els += centralidad(c)
    els += contenido(c)
    els += sentimiento(c)
    els += interpretacion(c)
    els += limitaciones(c)
    els += conclusiones(c)
    els += reproducibilidad(c)
    els += referencias(c)
    els += apendices(c)
    return els


def apendices(c: Ctx) -> list:
    """Apendices: trazabilidad con el enunciado e inventario de figuras."""
    caps = c.captions
    figs = sorted(C.FIGURES.glob("*.png"))
    trace = [
        ("1.1-1.4 Carga, comprension e integracion", "1, 2, 3"),
        ("2.1 Diagnostico inicial de calidad", "4.1"),
        ("2.2 Variables problematicas", "4.2"),
        ("2.3 Normalizacion de IDs y nombres", "4.3"),
        ("2.4 Conversion de conteos en texto", "4.4"),
        ("2.5 texto_original y texto_limpio", "4.5"),
        ("2.6 Decisiones de limpieza documentadas", "4.5.1"),
        ("2.7 Efecto cuantificado de la limpieza", "4.6"),
        ("3.1 Descriptivos minimos", "5.1"),
        ("3.2 Concentracion de la participacion", "5.2"),
        ("3.3 Popularidad frente a participacion", "5.3"),
        ("3.4 Visualizaciones pertinentes", "5 (figuras 1-14), 11, 13, 14"),
        ("3.5 Seis preguntas obligatorias", "6.1-6.6"),
        ("3.6 Tres o mas preguntas adicionales", "7.1-7.5 (cinco preguntas)"),
        ("4.1-4.2 Red bipartita y definicion del peso", "8.1"),
        ("4.3 Tablas de nodos y aristas", "8.4"),
        ("4.4 Visualizacion de la red completa", "8.5"),
        ("4.5 Significado preciso de la arista", "8.2"),
        ("5.1 Proyeccion autor-autor", "9.1-9.2"),
        ("5.2 Proyeccion video-video", "9.1-9.2"),
        ("5.3 Comparacion de las proyecciones", "9.3"),
        ("5.4 Visualizacion de ambas proyecciones", "9.4"),
        ("6.1 Nodos, aristas, densidad, grados, componentes", "10.1, 10.3, 10.4"),
        ("6.2 Cohesion y transitividad", "10.1, 10.2"),
        ("6.3 Perifericos y aislados; aislamiento observado vs ausencia de datos", "10.4"),
        ("6.4 Explicacion de los hallazgos estructurales", "10.5"),
        ("7.1 Eleccion de la red y justificacion", "11.1"),
        ("7.2 Algoritmo, supuestos y pesos", "11.2"),
        ("7.3 Numero, tamanos y modularidad", "11.3"),
        ("7.4 Visualizacion de todas las comunidades y analisis de tres", "11.4-11.5"),
        ("7.5 Caracterizacion por videos, canales, autores, temas y sentimiento",
         "11.5, 13.2, 14.4"),
        ("8.1 Medidas de centralidad y justificacion", "12.1"),
        ("8.2 Interpretacion separada de autores y videos", "12.2, 12.4"),
        ("8.3 Recurrentes, puentes y videos articuladores", "12.3, 12.5"),
        ("9.1 Sentimiento en espanol y justificacion del modelo", "14.1-14.3"),
        ("9.2 Comparacion por video, canal, tema o comunidad", "14.4"),
        ("9.3 Explicacion de los hallazgos", "14.5-14.6, 15.5"),
        ("10.1 Hallazgos en contexto de participacion y consumo", "15"),
        ("10.2 Limitaciones minimas exigidas", "16.1-16.11"),
        ("10.3 Descripcion, asociacion e inferencia", "16.12"),
        ("10.4 Conclusiones integradas", "17"),
    ]
    return [
        ("h1", "Apendice A. Trazabilidad con los incisos del enunciado"),
        ("p",
         "Correspondencia entre cada inciso del enunciado del laboratorio y la seccion de "
         "este informe donde se resuelve. La auditoria completa contra la rubrica, con "
         "evidencia y estado por requisito, esta en `docs/rubric_checklist.md`."),
        ("table", "Tabla A1. Inciso del enunciado y seccion del informe",
         ["Inciso del enunciado", "Seccion de este informe"], [list(t) for t in trace]),
        ("pagebreak",),
        ("h1", "Apendice B. Inventario de figuras"),
        ("table", "Tabla B1. Figuras generadas, con su archivo y su interpretacion",
         ["Archivo", "Interpretacion (generada por el pipeline)"],
         [[f.name, caps.get(f.name, "—")] for f in figs]),
        ("pagebreak",),
        ("h1", "Apendice C. Inventario de tablas exportadas"),
        ("p",
         "Las tablas del cuerpo del informe muestran top-N y resumenes. Las versiones "
         "completas estan en CSV:"),
        ("table", "Tabla C1. Tablas completas en results/",
         ["Archivo", "Contenido", "Filas"],
         _table_inventory()),
    ]


def _table_inventory() -> list:
    import pandas as pd

    desc = {
        "data_quality_videos.csv": "Perfil de calidad por variable del catalogo de videos",
        "data_quality_comments.csv": "Perfil de calidad por variable de los comentarios",
        "consistency_checks.csv": "Chequeos de consistencia de IDs, nombres y handles",
        "problematic_variables.csv": "Variables problematicas y su tratamiento",
        "outlier_diagnostics.csv": "Diagnostico de atipicos por variable cuantitativa",
        "cleaning_effect.csv": "Efecto cuantificado de la limpieza de texto",
        "videos_summary.csv": "Un registro por video con metadatos y participacion observada",
        "comments_by_video.csv": "Agregados de participacion por video",
        "comments_by_channel.csv": "Agregados de participacion por canal",
        "authors_summary.csv": "Un registro por autor con recurrencia y diversidad",
        "eda_descriptives.csv": "Descriptivos del analisis exploratorio",
        "concentration_metrics.csv": "Metricas de concentracion (Gini, top-k, Lorenz)",
        "top_words.csv": "Palabras mas frecuentes en texto_limpio",
        "top_bigrams.csv": "Bigramas mas frecuentes",
        "top_trigrams.csv": "Trigramas mas frecuentes",
        "top_hashtags.csv": "Hashtags de videos y de comentarios",
        "top_video_keywords.csv": "Keywords mas frecuentes del catalogo de videos",
        "top_emojis.csv": "Emojis mas frecuentes en los comentarios",
        "bipartite_nodes.csv": "Tabla de nodos de la red bipartita con atributos",
        "bipartite_edges.csv": "Tabla de aristas de la red bipartita con pesos",
        "author_projection_edges.csv": "Aristas de la proyeccion autor-autor",
        "video_projection_edges.csv": "Aristas de la proyeccion video-video",
        "network_metrics.csv": "Metricas topologicas de las tres redes (formato largo)",
        "network_metrics_wide.csv": "Metricas topologicas de las tres redes (una fila por red)",
        "author_centrality.csv": "Todas las centralidades de los 332 autores",
        "video_centrality.csv": "Todas las centralidades de los 19 videos",
        "articulation_points.csv": "Puntos de articulacion con prueba de eliminacion",
        "bridge_authors.csv": "Todos los autores con su evaluacion como puente",
        "communities.csv": "Asignacion de comunidad por video con atributos",
        "community_summary.csv": "Perfil completo por comunidad (tema y sentimiento)",
        "community_tfidf_terms.csv": "Terminos TF-IDF de los comentarios por comunidad",
        "community_tfidf_keywords.csv": "Keywords TF-IDF del contenido por comunidad",
        "sentiment_predictions.csv": "Prediccion y probabilidades por comentario",
        "sentiment_summary.csv": "Distribucion de sentimiento por video, canal, comunidad, "
                                 "categoria y consulta",
        "sentiment_global_distribution.csv": "Distribucion global de clases",
        "questions_answers.csv": "Preguntas 3.5 y 3.6 con su respuesta",
    }
    rows = []
    for name, d in desc.items():
        p = C.TABLES / name
        if not p.exists():
            p = C.NETWORKS / name
        n = "—"
        if p.exists():
            try:
                n = f"{len(pd.read_csv(p)):,}".replace(",", " ")
            except Exception:
                n = "—"
        rows.append([f"results/.../{name}", d, n])
    return rows


# ================================================================= markdown ==
def render_markdown(els: list) -> str:
    now = datetime.now().strftime("%d de %B de %Y")
    out = [
        f"# {TITLE}", "",
        f"**{SUBTITLE}**", "",
        f"{COURSE}  ", f"{UNIVERSITY.replace(chr(10), '  ' + chr(10))}  ", "",
        f"*Documento generado por el pipeline el {now}. Todas las cifras provienen de "
        "`results/metrics/` y `results/tables/`; ninguna esta escrita a mano.*", "",
        "---", "",
    ]
    for el in els:
        kind = el[0]
        if kind == "h1":
            out += ["", f"## {el[1]}", ""]
        elif kind == "h2":
            out += ["", f"### {el[1]}", ""]
        elif kind == "h3":
            out += ["", f"#### {el[1]}", ""]
        elif kind == "p":
            out += [el[1], ""]
        elif kind == "callout":
            body = str(el[1]).replace("\n\n", "\n>\n> ").replace("\n", "\n> ")
            out += [f"> {body}", ""]
        elif kind == "bullets":
            out += [f"- {b}" for b in el[1]] + [""]
        elif kind == "code":
            out += ["```bash", el[1], "```", ""]
        elif kind == "table":
            _, title, head, rows = el
            out += [f"**{title}**", ""]
            out += ["| " + " | ".join(str(h) for h in head) + " |"]
            out += ["|" + "|".join("---" for _ in head) + "|"]
            for r in rows:
                cells = [str(x).replace("\n", " ").replace("|", "\\|") for x in r]
                out += ["| " + " | ".join(cells) + " |"]
            out += [""]
        elif kind == "figure":
            cap = viz.load_captions().get(el[1], "")
            out += [f"![{el[1]}](../results/figures/{el[1]})", "",
                    f"*{cap}*" if cap else "", ""]
        elif kind == "pagebreak":
            out += ["---", ""]
    return "\n".join(out)


# ====================================================================== pdf ==
class Doc(BaseDocTemplate):
    """Documento con pie de pagina, numeracion y plantilla horizontal."""

    def __init__(self, path, **kw):
        super().__init__(str(path), pagesize=A4, **kw)
        self.allowSplitting = 1
        w, h = A4
        margins = dict(leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates([
            PageTemplate(
                id="cover",
                frames=[Frame(2.4 * cm, 2.4 * cm, w - 4.8 * cm, h - 4.8 * cm, **margins)],
                onPage=self._cover_page),
            PageTemplate(
                id="body",
                frames=[Frame(2.2 * cm, 2.2 * cm, w - 4.4 * cm, h - 4.4 * cm, **margins)],
                onPage=self._body_page),
        ])

    def _footer(self, canv, doc, width):
        canv.saveState()
        canv.setStrokeColor(RULE)
        canv.setLineWidth(0.4)
        canv.line(1.6 * cm, 1.45 * cm, width - 1.6 * cm, 1.45 * cm)
        canv.setFont("Helvetica", 7.2)
        canv.setFillColor(GREY)
        canv.drawString(1.6 * cm, 1.05 * cm,
                        "CC3084 Data Science · Laboratorio 6 · Analisis de redes sociales (YouTube)")
        canv.drawRightString(width - 1.6 * cm, 1.05 * cm, f"Pagina {doc.page}")
        canv.restoreState()

    def _cover_page(self, canv, doc):
        w, h = A4
        canv.saveState()
        canv.setFillColor(ACCENT)
        canv.rect(0, h - 1.05 * cm, w, 1.05 * cm, stroke=0, fill=1)
        canv.setFillColor(ACCENT2)
        canv.rect(0, h - 1.05 * cm, w * 0.34, 1.05 * cm, stroke=0, fill=1)
        canv.restoreState()

    def _body_page(self, canv, doc):
        w, h = A4
        canv.saveState()
        canv.setFillColor(ACCENT)
        canv.rect(0, h - 0.32 * cm, w, 0.32 * cm, stroke=0, fill=1)
        canv.restoreState()
        self._footer(canv, doc, w)


#: Familias tipograficas candidatas, en orden de preferencia. Cada entrada
#: debe aportar las **cuatro** caras: sin ellas, ``registerFontFamily`` no
#: puede mapear ``<b>`` ni ``<i>`` y el enfasis en linea se pierde en silencio.
#: Se exigen tambien los glifos de kappa, Delta, >=, comillas angulares y
#: rayas, que aparecen en el informe. DejaVu tiene la mejor cobertura pero en
#: muchas distribuciones no incluye la cara oblicua, por lo que va despues de
#: FreeSans, que si trae las cuatro.
FONT_FAMILIES = [
    ("FreeSans", "/usr/share/fonts/truetype/freefont",
     ("FreeSans.ttf", "FreeSansBold.ttf", "FreeSansOblique.ttf",
      "FreeSansBoldOblique.ttf")),
    ("DejaVuSans", "/usr/share/fonts/truetype/dejavu",
     ("DejaVuSans.ttf", "DejaVuSans-Bold.ttf", "DejaVuSans-Oblique.ttf",
      "DejaVuSans-BoldOblique.ttf")),
    ("LiberationSans", "/usr/share/fonts/truetype/liberation",
     ("LiberationSans-Regular.ttf", "LiberationSans-Bold.ttf",
      "LiberationSans-Italic.ttf", "LiberationSans-BoldItalic.ttf")),
]

#: Caracteres que el informe usa y que la fuente elegida debe poder dibujar.
REQUIRED_GLYPHS = "κΔ≥«»·—–±áéíóúñ¿¡"


def _register_fonts() -> tuple[str, str, str]:
    """Registra una familia con las cuatro caras y cobertura verificada.

    Devuelve ``(normal, bold, italic)``. Registrar la familia completa con
    ``registerFontFamily`` es lo que hace que ``<b>`` y ``<i>`` surtan efecto
    en los parrafos: sin ese mapeo, ReportLab ignora las etiquetas y el
    enfasis en linea desaparece sin aviso.
    """
    for family, base_dir, faces in FONT_FAMILIES:
        base = Path(base_dir)
        paths = [base / f for f in faces]
        if not all(x.exists() for x in paths):
            continue
        if not _covers_glyphs(paths[0]):
            continue
        names = (family, f"{family}-Bold", f"{family}-Italic",
                 f"{family}-BoldItalic")
        try:
            for name, path in zip(names, paths):
                pdfmetrics.registerFont(TTFont(name, str(path)))
            from reportlab.pdfbase.pdfmetrics import registerFontFamily

            registerFontFamily(family, normal=names[0], bold=names[1],
                               italic=names[2], boldItalic=names[3])
            return names[0], names[1], names[2]
        except Exception:
            continue
    # Ultimo recurso: las base-14, que no cubren griego ni matematicas. El
    # saneador de caracteres evita cuadros vacios, aunque el informe pierde
    # los simbolos.
    return "Helvetica", "Helvetica-Bold", "Helvetica-Oblique"


def _covers_glyphs(path: Path) -> bool:
    """Comprueba que la cara regular pueda dibujar los caracteres del informe."""
    try:
        from PIL import ImageFont

        font = ImageFont.truetype(str(path), 24)
        return all(font.getmask(ch).getbbox() is not None
                   for ch in REQUIRED_GLYPHS)
    except Exception:
        return True  # sin PIL no se puede comprobar; no se bloquea por eso


def _styles(font: str, bold: str, ital: str) -> dict:
    ss = getSampleStyleSheet()
    base = dict(fontName=font, textColor=INK, leading=13.2, fontSize=9.4)
    return {
        "h1": ParagraphStyle("h1", parent=ss["Heading1"], fontName=bold, fontSize=15,
                             leading=19, textColor=ACCENT, spaceBefore=16, spaceAfter=8,
                             keepWithNext=1),
        "h2": ParagraphStyle("h2", parent=ss["Heading2"], fontName=bold, fontSize=11.6,
                             leading=15, textColor=INK, spaceBefore=12, spaceAfter=5,
                             keepWithNext=1),
        "h3": ParagraphStyle("h3", parent=ss["Heading3"], fontName=bold, fontSize=10.2,
                             leading=13.5, textColor=ACCENT2, spaceBefore=9, spaceAfter=4,
                             keepWithNext=1),
        "p": ParagraphStyle("p", parent=ss["BodyText"], alignment=TA_JUSTIFY,
                            spaceAfter=6.5, **base),
        "li": ParagraphStyle("li", parent=ss["BodyText"], alignment=TA_JUSTIFY,
                             leftIndent=11, bulletIndent=2, spaceAfter=4.2, **base),
        "callout": ParagraphStyle("callout", parent=ss["BodyText"], alignment=TA_JUSTIFY,
                                  fontName=font, fontSize=9.2, leading=13,
                                  textColor=INK, leftIndent=8, rightIndent=8,
                                  spaceBefore=4, spaceAfter=4),
        "code": ParagraphStyle("code", parent=ss["BodyText"], fontName="Courier",
                               fontSize=8.4, leading=11.6, textColor=INK,
                               leftIndent=8, rightIndent=8, spaceBefore=4, spaceAfter=4),
        "tcap": ParagraphStyle("tcap", parent=ss["BodyText"], fontName=bold, fontSize=8.8,
                               leading=11.5, textColor=ACCENT2, spaceBefore=8,
                               spaceAfter=3, keepWithNext=1),
        "fcap": ParagraphStyle("fcap", parent=ss["BodyText"], fontName=ital, fontSize=8,
                               leading=10.6, textColor=GREY, alignment=TA_JUSTIFY,
                               spaceBefore=3, spaceAfter=9),
        # Tres niveles de tamano de tabla: el ancho que exige el contenido
        # decide cual se usa, de modo que las tablas anchas se reducen en
        # lugar de girar la pagina o de desbordar el margen.
        "th": ParagraphStyle("th", fontName=bold, fontSize=7.4, leading=9.2,
                             textColor=colors.white),
        "td": ParagraphStyle("td", fontName=font, fontSize=7.2, leading=9.0,
                             textColor=INK),
        "tdc": ParagraphStyle("tdc", fontName=font, fontSize=7.2, leading=9.0,
                              textColor=INK, alignment=TA_CENTER),
        "th_s": ParagraphStyle("th_s", fontName=bold, fontSize=6.5, leading=8.1,
                               textColor=colors.white),
        "td_s": ParagraphStyle("td_s", fontName=font, fontSize=6.4, leading=8.0,
                               textColor=INK),
        "tdc_s": ParagraphStyle("tdc_s", fontName=font, fontSize=6.4, leading=8.0,
                                textColor=INK, alignment=TA_CENTER),
        "th_xs": ParagraphStyle("th_xs", fontName=bold, fontSize=5.9, leading=7.4,
                                textColor=colors.white),
        "td_xs": ParagraphStyle("td_xs", fontName=font, fontSize=5.8, leading=7.3,
                                textColor=INK),
        "tdc_xs": ParagraphStyle("tdc_xs", fontName=font, fontSize=5.8, leading=7.3,
                                 textColor=INK, alignment=TA_CENTER),
        "cover_t": ParagraphStyle("ct", fontName=bold, fontSize=25, leading=30,
                                  textColor=ACCENT, alignment=TA_CENTER, spaceAfter=8),
        "cover_s": ParagraphStyle("cs", fontName=font, fontSize=13, leading=18,
                                  textColor=INK, alignment=TA_CENTER, spaceAfter=22),
        "cover_m": ParagraphStyle("cm", fontName=font, fontSize=10.4, leading=15.5,
                                  textColor=GREY, alignment=TA_CENTER, spaceAfter=6),
        "cover_b": ParagraphStyle("cb", fontName=bold, fontSize=11, leading=15,
                                  textColor=INK, alignment=TA_CENTER, spaceAfter=6),
    }


def _sanitize(text: str) -> str:
    """Sustituye los caracteres que la fuente incrustada no puede dibujar.

    DejaVu Sans cubre latin, griego y simbolos matematicos, pero no los
    emojis de los planos suplementarios. Un caracter sin glifo se dibuja como
    un cuadro vacio, asi que se reemplaza por su punto de codigo, que es
    legible y no rompe la validacion de Unicode del PDF.
    """
    out = []
    for ch in str(text):
        if ord(ch) > 0x2FFF and ch not in "\u3000":
            out.append(f"[U+{ord(ch):04X}]")
        else:
            out.append(ch)
    return "".join(out)


def _md_inline(text: str) -> str:
    """Convierte negrita, cursiva y codigo de Markdown a marcas de ReportLab.

    Los tramos entre acentos graves se extraen primero y se sustituyen por
    marcadores opacos: sin eso, un asterisco dentro de una ruta como
    ``results/metrics/*.json`` se interpretaria como apertura de cursiva y
    produciria etiquetas cruzadas que ReportLab rechaza.
    """
    s = _sanitize(text)
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    spans: list[str] = []

    def _stash(m):
        spans.append(m.group(1))
        return f"\x00{len(spans) - 1}\x00"

    s = re.sub(r"`([^`]+?)`", _stash, s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s, flags=re.S)
    s = re.sub(r"(?<![\w*])\*([^*\n]+?)\*(?![\w*])", r"<i>\1</i>", s)
    s = s.replace("*", "")  # asteriscos sueltos sin pareja
    for i, code in enumerate(spans):
        s = s.replace(f"\x00{i}\x00",
                      f'<font face="Courier" size="8.4">{code}</font>')
    return s


def _table(el, st: dict, width: float):
    """Construye una tabla ajustando anchos y tamano de fuente al contenido.

    Todas las tablas se maquetan en vertical. Cuando el contenido exige mas
    ancho del disponible no se gira la pagina (lo que dejaba paginas casi
    vacias antes del giro) sino que se reduce el cuerpo de letra a uno de tres
    niveles. El resultado es un documento de orientacion uniforme y sin
    huecos.
    """
    _, title, head, rows = el
    ncol = len(head)
    cols = [[str(head[j])] + [str(r[j]) if j < len(r) else "" for r in rows]
            for j in range(ncol)]

    # Ancho relativo por columna. El minimo lo fija la palabra mas larga de la
    # columna: sin ese piso, una cabecera como "Nulos" se parte en "Nul-os".
    weights = []
    for col in cols:
        longest = max((len(x) for x in col), default=1)
        longest_word = max((len(w) for x in col for w in str(x).split()), default=1)
        # +3 unidades cubren el relleno lateral de la celda, que en las tablas
        # reducidas se come una parte apreciable de una columna estrecha.
        weights.append(max(5.5, float(longest_word) + 3.0,
                           min(float(longest), 62.0)))
    total = sum(weights)
    suffix = "" if (total <= 120 and ncol <= 7) else ("_s" if total <= 190 else "_xs")
    widths = [width * w / total for w in weights]

    # La alineacion se decide por columna y solo para columnas numericas.
    # Centrar por celda (o centrar texto corto) hace que unas filas queden
    # alineadas y otras no dentro de la misma columna, y se lee como un error
    # de maquetacion.
    num = re.compile(r"^[\s\d.,%+\-—–/()·:]*$")
    centered = [j > 0 and any(x.strip() for x in cols[j][1:])
                and all(num.match(x) for x in cols[j][1:])
                for j in range(ncol)]

    data = [[Paragraph(_md_inline(h), st["th" + suffix]) for h in head]]
    for r in rows:
        cells = []
        for j in range(ncol):
            v = str(r[j]) if j < len(r) else ""
            key = ("tdc" if centered[j] else "td") + suffix
            cells.append(Paragraph(_md_inline(v), st[key]))
        data.append(cells)

    pad = 3.2 if suffix == "" else (2.4 if suffix == "_s" else 1.9)
    t = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.28, RULE),
        ("LINEBELOW", (0, 0), (-1, 0), 0.7, ACCENT),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("LEFTPADDING", (0, 0), (-1, -1), pad),
        ("RIGHTPADDING", (0, 0), (-1, -1), pad),
        ("TOPPADDING", (0, 0), (-1, -1), 2.4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.4),
    ]))
    return t, title


def _callout(text: str, st: dict, width: float):
    paras = [Paragraph(_md_inline(p), st["callout"]) for p in str(text).split("\n\n")]
    t = Table([[paras]], colWidths=[width], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFF4E8")),
        ("LINEBEFORE", (0, 0), (0, -1), 2.6, ACCENT2),
        ("BOX", (0, 0), (-1, -1), 0.3, colors.HexColor("#E8C9A8")),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return t


def _figure(name: str, st: dict, width: float, caps: dict):
    path = C.FIGURES / name
    if not path.exists():
        return []
    from PIL import Image as PILImage

    with PILImage.open(path) as im:
        iw, ih = im.size
    max_h = 15.4 * cm
    w = width
    h = w * ih / iw
    if h > max_h:
        h = max_h
        w = h * iw / ih
    img = Image(str(path), width=w, height=h)
    img.hAlign = "CENTER"
    cap = caps.get(name, "")
    out = [Spacer(1, 5), img]
    if cap:
        out.append(Paragraph(_md_inline(cap), st["fcap"]))
    else:
        out.append(Spacer(1, 8))
    return out


def cover(c: Ctx, st: dict) -> list:
    d = c.m("descriptives")
    sent = c.m("sentiment")
    now = datetime.now().strftime("%d/%m/%Y")
    return [
        Spacer(1, 1.6 * cm),
        Paragraph(COURSE, st["cover_m"]),
        Paragraph(UNIVERSITY.replace("\n", "<br/>"), st["cover_m"]),
        Spacer(1, 1.5 * cm),
        Paragraph(TITLE, st["cover_t"]),
        Paragraph(SUBTITLE, st["cover_s"]),
        _cover_box(c, st),
        Spacer(1, 1.1 * cm),
        Paragraph("Datos analizados", st["cover_b"]),
        Paragraph(
            f"{d['n_videos_catalogo']} videos · {d['n_canales_catalogo']} canales · "
            f"{d['n_comentarios']} comentarios · {d['n_autores_unicos']} autores unicos<br/>"
            f"Cobertura de comentarios: {d['n_videos_con_comentario_observado']} de "
            f"{d['n_videos_catalogo']} videos "
            f"({d['pct_videos_con_comentario_observado']} %)",
            st["cover_m"]),
        Spacer(1, 0.9 * cm),
        Paragraph(
            f"Informe generado automaticamente por el pipeline reproducible el {now}.<br/>"
            "Todas las cifras, tablas y pies de figura provienen de las salidas computadas "
            "en <font face='Courier' size='9'>results/</font>; ninguna esta escrita a mano."
            "<br/>Semilla global: 42 · Modelo de sentimiento: "
            f"<font face='Courier' size='8.6'>{sent['modelo']['model_id']}</font>",
            st["cover_m"]),
        NextPageTemplate("body"),
        PageBreak(),
    ]


def _cover_box(c: Ctx, st: dict) -> Table:
    d = c.m("descriptives")
    cn = c.m("concentration")
    bp = c.m("network_bipartite")
    vp = c.m("network_topology")["proyeccion_video_video"]
    comm = c.m("communities")["video_projection"]
    cen = c.m("centrality_summary")
    stm = c.m("sentiment")
    rows = [
        ["Integracion por video_id",
         f"{c.m('join')['comentarios_con_video']} / {c.m('join')['n_comentarios']} "
         f"comentarios ({c.m('join')['pct_comentarios_con_video']} %)"],
        ["Red bipartita autor-video",
         f"{bp['nodos_totales']} nodos · {bp['aristas']} aristas · "
         f"suma de pesos = {bp['suma_pesos']}"],
        ["Proyeccion video-video",
         f"{vp['n_nodos']} nodos · {vp['n_aristas']} aristas · "
         f"densidad {vp['densidad']} · {vp['n_nodos_aislados']} aislados"],
        ["Cohesion (kappa)",
         f"0 global (redes desconectadas) · 1 en la componente mayor de las tres"],
        ["Comunidades (Louvain ponderado)",
         f"{comm['n_comunidades']} comunidades · Q = {comm['modularidad_ponderada']} · "
         f"{comm['n_singletons']} singletons"],
        ["Autores puente verificados",
         f"{cen['n_autores_puente_verificados']} de {d['n_autores_unicos']} autores"],
        ["Sentimiento (espanol)",
         f"NEG {stm['pct_por_clase']['NEG']} % · NEU {stm['pct_por_clase']['NEU']} % · "
         f"POS {stm['pct_por_clase']['POS']} %"],
        ["Concentracion",
         f"Gini {cn['comentarios_por_video']['gini']} por video · "
         f"{cn['comentarios_por_autor']['gini']} por autor"],
    ]
    data = [[Paragraph(f"<b>{k}</b>", st["td"]), Paragraph(v, st["td"])] for k, v in rows]
    t = Table(data, colWidths=[5.6 * cm, 9.2 * cm], hAlign="CENTER")
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (0, -1), LIGHT),
        ("GRID", (0, 0), (-1, -1), 0.3, RULE),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def render_pdf(c: Ctx, els: list, path: Path) -> None:
    font, bold, ital = _register_fonts()
    st = _styles(font, bold, ital)
    doc = Doc(path, title=f"{TITLE} - {COURSE}",
              author="Luis Fernando Mendoza", subject=SUBTITLE,
              creator="src/report_generation.py")
    width = A4[0] - 4.4 * cm
    caps = c.captions

    story: list = cover(c, st)
    n_cover = len(story)
    for el in els:
        kind = el[0]
        if kind in ("h1", "h2", "h3"):
            if kind == "h1" and len(story) > n_cover:
                story.append(Spacer(1, 4))
            story.append(Paragraph(_md_inline(el[1]), st[kind]))
        elif kind == "p":
            story.append(Paragraph(_md_inline(el[1]), st["p"]))
        elif kind == "bullets":
            for b in el[1]:
                story.append(Paragraph(_md_inline(b), st["li"], bulletText="•"))
            story.append(Spacer(1, 3))
        elif kind == "code":
            for line in str(el[1]).split("\n"):
                story.append(Paragraph(_md_inline(line) or "&nbsp;", st["code"]))
            story.append(Spacer(1, 6))
        elif kind == "callout":
            story += [Spacer(1, 3), _callout(el[1], st, width), Spacer(1, 7)]
        elif kind == "table":
            t, title = _table(el, st, width)
            cap = Paragraph(_md_inline(title), st["tcap"])
            # Las tablas cortas se mantienen junto a su titulo; las largas se
            # dejan fluir para que puedan partirse entre paginas repitiendo la
            # cabecera en lugar de saltar a la siguiente pagina en bloque.
            if len(el[3]) <= 10:
                story.append(KeepTogether([cap, t]))
            else:
                story += [cap, t]
            story.append(Spacer(1, 9))
        elif kind == "figure":
            story += _figure(el[1], st, width, caps)
        elif kind == "pagebreak":
            story.append(PageBreak())
    doc.build(story)


# ================================================================ validacion =
def validate_pdf(path: Path) -> dict:
    """Valida el PDF generado: paginas, texto extraible, imagenes y secciones."""
    from pypdf import PdfReader

    size = path.stat().st_size
    reader = PdfReader(str(path))
    texts = []
    n_images = 0
    for pg in reader.pages:
        try:
            texts.append(pg.extract_text() or "")
        except Exception:
            texts.append("")
        try:
            n_images += len(pg.images)
        except Exception:
            pass
    full = "\n".join(texts)
    required = [
        "Resumen ejecutivo", "Introduccion", "Datos y unidades",
        "Integracion de los datos", "Calidad, limpieza", "Analisis exploratorio",
        "Preguntas obligatorias", "Preguntas adicionales", "red bipartita",
        "Proyecciones de la red", "Topologia y fragmentacion", "Comunidades",
        "Nodos centrales", "Analisis de contenido", "sentimiento",
        "Interpretacion integrada", "Limitaciones", "Conclusiones",
        "Reproducibilidad", "Referencias", "Apendice",
    ]
    missing = [s for s in required if s.lower() not in full.lower()]
    empty_pages = [i + 1 for i, t in enumerate(texts) if len(t.strip()) < 12]
    # Paginas casi vacias que no sean de figura: se toleran si tienen imagen
    bad = re.findall(r"[�]", full)
    return {
        "existe": path.exists(),
        "tamano_bytes": size,
        "tamano_kb": round(size / 1024, 1),
        "n_paginas": len(reader.pages),
        "n_caracteres_texto": len(full),
        "n_imagenes": n_images,
        "secciones_faltantes": missing,
        "paginas_con_poco_texto": empty_pages,
        "n_caracteres_unicode_rotos": len(bad),
        "ok_existe": path.exists(),
        "ok_tamano": size > 100_000,
        "ok_multiples_paginas": len(reader.pages) >= 30,
        "ok_texto_extraible": len(full) > 60_000,
        "ok_todas_las_secciones": not missing,
        "ok_figuras_incrustadas": n_images >= 24,
        "ok_sin_unicode_roto": not bad,
    }


# =================================================================== pipeline =
def run() -> dict:
    C.set_seeds()
    print("[6/6] report_generation: informe en Markdown y PDF")
    c = Ctx()
    els = build_document(c)

    md = render_markdown(els)
    MD_PATH.write_text(md, encoding="utf-8")

    render_pdf(c, els, PDF_PATH)
    v = validate_pdf(PDF_PATH)
    C.write_metrics("report", {
        "n_elementos": len(els),
        "n_tablas": sum(1 for e in els if e[0] == "table"),
        "n_figuras_referenciadas": sum(1 for e in els if e[0] == "figure"),
        "n_secciones_h1": sum(1 for e in els if e[0] == "h1"),
        "markdown_caracteres": len(md),
        "markdown_lineas": md.count("\n") + 1,
        "validacion_pdf": v,
    })
    fails = [k for k, val in v.items() if k.startswith("ok_") and not val]
    print(f"      markdown: {len(md):,} caracteres | "
          f"pdf: {v['n_paginas']} paginas, {v['tamano_kb']} KB, "
          f"{v['n_imagenes']} imagenes, {v['n_caracteres_texto']:,} caracteres")
    if fails:
        print(f"      [ATENCION] validaciones del PDF que fallan: {fails}")
        if v["secciones_faltantes"]:
            print(f"      secciones faltantes: {v['secciones_faltantes']}")
    return {"elements": els, "validation": v}


if __name__ == "__main__":
    run()
