"""Estilo comun de figuras y utilidades de guardado."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from . import config as C  # noqa: E402

#: Paleta categorica accesible (Okabe-Ito, distinguible en deuteranopia).
PALETTE = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00",
           "#56B4E9", "#F0E442", "#7F3C8D", "#8C8C8C", "#000000"]

COLOR_AUTHOR = "#0072B2"
COLOR_VIDEO = "#D55E00"
COLOR_NEG = "#D55E00"
COLOR_NEU = "#8C8C8C"
COLOR_POS = "#009E73"
SENTIMENT_COLORS = {"NEG": COLOR_NEG, "NEU": COLOR_NEU, "POS": COLOR_POS}


def apply_style() -> None:
    plt.rcParams.update({
        "figure.dpi": 110,
        "savefig.dpi": C.FIG_DPI,
        "savefig.bbox": "tight",
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.titleweight": "bold",
        "axes.labelsize": 10,
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.alpha": 0.25,
        "grid.linewidth": 0.6,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "legend.frameon": False,
        "figure.autolayout": False,
        "axes.prop_cycle": plt.cycler(color=PALETTE),
    })


def save(fig, name: str, caption: str = "") -> Path:
    """Guarda la figura en ``results/figures`` y registra su caption.

    El caption se persiste junto a la imagen para que el informe lo tome del
    pipeline y no de texto escrito a mano.
    """
    apply_style()
    path = C.FIGURES / name
    if caption:
        fig.text(0.5, -0.035, caption, ha="center", va="top", fontsize=8,
                 style="italic", color="#333333", wrap=True)
    fig.savefig(path, dpi=C.FIG_DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    (C.FIGURES / "_captions.jsonl").open("a", encoding="utf-8").write(
        __import__("json").dumps({"figure": name, "caption": caption},
                                 ensure_ascii=False) + "\n"
    )
    return path


def reset_captions() -> None:
    p = C.FIGURES / "_captions.jsonl"
    if p.exists():
        p.unlink()


def load_captions() -> dict[str, str]:
    import json

    p = C.FIGURES / "_captions.jsonl"
    if not p.exists():
        return {}
    out = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.strip():
            d = json.loads(line)
            out[d["figure"]] = d["caption"]
    return out


def barh(ax, labels, values, color=COLOR_AUTHOR, fmt="{:,.0f}", pad=0.02):
    """Barras horizontales ordenadas de mayor a menor con etiqueta de valor."""
    y = range(len(labels))
    ax.barh(list(y), list(values), color=color, edgecolor="white", linewidth=0.5)
    ax.set_yticks(list(y))
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    vmax = max(values) if len(values) else 1
    for yi, v in zip(y, values):
        ax.text(v + vmax * pad, yi, fmt.format(v), va="center", fontsize=8)
    ax.set_xlim(0, vmax * 1.18)
    return ax


def wrap(text: str, width: int = 42) -> str:
    import textwrap

    return "\n".join(textwrap.wrap(str(text), width=width, max_lines=2,
                                   placeholder="..."))
