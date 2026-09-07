"""Parser de conteos, normalizacion de identificadores y limpieza de texto."""
from __future__ import annotations

import math

import pytest

from src.text_processing import (clean_text, extract_emoji_shortcodes,
                                 extract_hashtags, extract_mentions,
                                 is_percent_encoded, normalize_display,
                                 normalize_handle, normalize_id, normalize_key,
                                 parse_count, preprocess_for_sentiment)


# ------------------------------------------------------------- parse_count ---
@pytest.mark.parametrize("raw,expected", [
    # separadores de miles
    ("29,736 vistas", 29736.0),
    ("2,390 vistas", 2390.0),
    ("1.234.567", 1234567.0),
    ("1 234 567", 1234567.0),
    # enteros simples
    ("4", 4.0),
    ("  12 ", 12.0),
    ("0", 0.0),
    # abreviaturas
    ("1.5K", 1500.0),
    ("2.3M vistas", 2300000.0),
    ("3B", 3_000_000_000.0),
    ("1,5 mil", 1500.0),
    ("2 millones", 2_000_000.0),
    ("1.2 millon", 1_200_000.0),
    # invalidos -> None, nunca 0
    (" ", None),
    ("", None),
    ("   ", None),
    ("abc", None),
    ("vistas", None),
    ("-", None),
    (None, None),
    (float("nan"), None),
])
def test_parse_count(raw, expected):
    got = parse_count(raw)
    if expected is None:
        assert got is None, f"{raw!r} deberia dar None y dio {got!r}"
    else:
        assert got == pytest.approx(expected), f"{raw!r} -> {got!r}, esperado {expected}"


def test_parse_count_nunca_inventa_cero():
    """Un valor invalido debe ser nulo, no 0: inventar ceros sesgaria las medias."""
    for bad in (" ", "", "abc", None, "N/A", "sin datos"):
        assert parse_count(bad) is None


def test_parse_count_coincide_con_view_count(videos):
    """El parser sobre view_count_text debe reproducir view_count."""
    import pandas as pd

    sub = videos.dropna(subset=["view_count_text", "view_count"])
    assert len(sub) > 200
    parsed = sub["view_count_text"].map(parse_count)
    real = pd.to_numeric(sub["view_count"], errors="coerce")
    # YouTube redondea el texto ("2,390 vistas" con view_count 2357), asi que
    # se exige coincidencia aproximada al 5 %, no exacta.
    rel = (parsed - real).abs() / real.clip(lower=1)
    assert (rel <= 0.05).mean() > 0.95


def test_like_count_blanco_se_imputa_a_cero_con_bandera(comments):
    blancos = comments["like_count_blank"].astype(str).str.lower().isin(["true", "1"])
    assert blancos.sum() > 0
    assert (comments.loc[blancos, "like_count"] == 0).all()
    no_blancos = comments.loc[~blancos, "like_count"]
    assert no_blancos.min() >= 1, "si hubiera ceros explicitos, blanco != 0"


# ------------------------------------------------------------ normalizacion ---
def test_normalize_id_conserva_el_case():
    assert normalize_id("  UCq0Cm-3SKthEySQc2JZBi1A ") == "UCq0Cm-3SKthEySQc2JZBi1A"
    assert normalize_id("UCq0Cm") != "ucq0cm"


def test_normalize_id_maneja_nulos():
    assert normalize_id(None) == ""
    assert normalize_id("nan") == ""
    assert normalize_id(float("nan")) == ""


def test_normalize_handle_decodifica_percent_encoding():
    assert normalize_handle("/@ErmeP%C3%A9rez-q4s") == "@ErmePérez-q4s"
    assert normalize_handle("/@Iv%C3%A1nP%C3%A9rez-j4j") == "@IvánPérez-j4j"


def test_normalize_handle_unifica_variantes_de_ruta():
    assert normalize_handle("@quorumgt/videos") == "@quorumgt"
    assert normalize_handle("/@quorumgt") == "@quorumgt"
    assert normalize_handle("quorumgt") == "@quorumgt"


def test_is_percent_encoded():
    assert is_percent_encoded("/@ErmeP%C3%A9rez-q4s")
    assert not is_percent_encoded("/@quorumgt")


def test_normalize_display_no_destruye_contenido():
    assert normalize_display("  Municipalidad   de  Guatemala ") == "Municipalidad de Guatemala"
    assert normalize_display("Bernardo Arévalo") == "Bernardo Arévalo"


def test_normalize_key_solo_para_comparar():
    assert normalize_key("Más") == normalize_key("mas")
    assert normalize_key("  Ciudad  de   Guatemala ") == "ciudad de guatemala"


# ------------------------------------------------------------- clean_text ---
def test_clean_text_extrae_antes_de_destruir():
    t = ("Ese corrupto 😡 amigo de @vieja_fiscal #JusticiaYa!! "
         "miren https://x.com/a 100 veces")
    r = clean_text(t)
    assert r["hashtags"] == ["justiciaya"]
    assert r["mentions"] == ["vieja_fiscal"]
    assert r["urls"] == ["https://x.com/a"]
    assert r["emojis"] == ["😡"]
    limpio = r["texto_limpio"]
    assert "justiciaya" in limpio, "la palabra del hashtag debe conservarse"
    assert "vieja_fiscal" not in limpio, "la mencion debe eliminarse"
    assert "http" not in limpio and "x.com" not in limpio
    assert "😡" not in limpio
    assert "100" not in limpio.split(), "los numeros sueltos se eliminan"
    assert "corrupto" in limpio


def test_clean_text_quita_stopwords_y_baja_a_minusculas():
    r = clean_text("El PUEBLO y los diputados de la ciudad")
    limpio = r["texto_limpio"]
    assert limpio == limpio.lower()
    for stop in (" el ", " los ", " de ", " la ", " y "):
        assert stop not in f" {limpio} "


def test_clean_text_lematiza():
    r = clean_text("Los diputados pagan sueldos altos")
    toks = r["texto_limpio"].split()
    assert "diputado" in toks or "diputados" in toks
    assert any(t.startswith("pag") for t in toks)


def test_clean_text_elimina_atajos_de_emoji_textuales():
    r = clean_text("buenisima investigacion :hand-purple-blue-peace:")
    assert r["emoji_shortcodes"] == [":hand-purple-blue-peace:"]
    for leak in ("hand", "purple", "blue", "peace"):
        assert leak not in r["texto_limpio"].split()
    assert "investigacion" in r["texto_limpio"]


def test_extract_emoji_shortcodes():
    assert extract_emoji_shortcodes("a :face-blue-smiling: b") == [":face-blue-smiling:"]
    assert extract_emoji_shortcodes("sin atajos") == []


def test_clean_text_es_robusto_a_entradas_degeneradas():
    for bad in (None, "", "   ", "!!!", "😡😡😡", "123", "a"):
        r = clean_text(bad)
        assert isinstance(r["texto_limpio"], str)
        assert isinstance(r["hashtags"], list)


# ------------------------------------------------- entrada para sentimiento ---
def test_preprocess_para_sentimiento_conserva_la_senal():
    t = "NO me gusta nada!! 😡 @alguien https://x.com #Basta"
    s = preprocess_for_sentiment(t)
    assert "NO me gusta" in s, "el case y la negacion deben conservarse"
    assert "!!" in s, "la puntuacion expresiva debe conservarse"
    assert "@usuario" in s and "@alguien" not in s
    assert "url" in s and "x.com" not in s
    assert "Basta" in s and "#Basta" not in s
    assert "emoji" in s, "el emoji debe traducirse a texto, no eliminarse"


def test_preprocess_traduce_emojis_al_espanol():
    s = preprocess_for_sentiment("que alegria 😍")
    assert "emoji" in s
    assert "corazón" in s or "corazon" in s or "sonriendo" in s


def test_preprocess_normaliza_risa_y_repeticiones():
    assert "jaja" in preprocess_for_sentiment("jajajajajaja")
    assert "holaaaa" not in preprocess_for_sentiment("holaaaaaaaa")


def test_texto_original_es_copia_fiel(comments, comments_raw):
    """texto_original debe ser identico al campo text del archivo crudo."""
    a = comments.set_index("comment_id")["texto_original"].fillna("")
    b = comments_raw.set_index("comment_id")["text"].fillna("")
    common = a.index.intersection(b.index)
    assert len(common) == len(comments_raw)
    assert (a.loc[common].astype(str) == b.loc[common].astype(str)).all()
