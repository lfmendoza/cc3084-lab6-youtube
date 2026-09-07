"""Narrativa del informe, construida a partir de las metricas computadas.

Este modulo no contiene ningun numero escrito a mano: cada cifra se lee de
``results/metrics/*.json`` en el momento de generar el informe, de modo que
el texto no puede quedar desfasado respecto a los resultados.

Cada bloque devuelve una lista de elementos:

* ``("h1"|"h2"|"h3", texto)`` encabezados;
* ``("p", texto)`` parrafo (admite ``**negrita**`` y ``*cursiva*``);
* ``("bullets", [texto, ...])`` lista;
* ``("table", titulo, encabezados, filas)`` tabla;
* ``("figure", nombre_archivo)`` figura de ``results/figures``;
* ``("callout", texto)`` recuadro destacado;
* ``("pagebreak",)`` salto de pagina.
"""
from __future__ import annotations

import json

import pandas as pd

from . import config as C


class Ctx:
    """Acceso perezoso a las metricas y tablas computadas."""

    def __init__(self) -> None:
        self._m: dict = {}
        self._t: dict = {}

    def m(self, name: str) -> dict:
        if name not in self._m:
            self._m[name] = C.read_metrics(name)
        return self._m[name]

    def t(self, name: str, **kw) -> pd.DataFrame:
        if name not in self._t:
            self._t[name] = pd.read_csv(C.TABLES / f"{name}.csv", **kw)
        return self._t[name]

    @property
    def captions(self) -> dict:
        from . import viz

        return viz.load_captions()


def fmt(x, dec: int = 0) -> str:
    """Formatea un numero con separador de miles y decimales fijos."""
    if x is None:
        return "n/d"
    try:
        v = float(x)
    except (TypeError, ValueError):
        return str(x)
    if v != v:  # NaN
        return "n/d"
    return f"{v:,.{dec}f}".replace(",", " ")


def pct(x, dec: int = 1) -> str:
    return "n/d" if x is None else f"{float(x):.{dec}f}%"


def trunc(s, n: int = 46) -> str:
    s = str(s)
    return s if len(s) <= n else s[: n - 1] + "…"
