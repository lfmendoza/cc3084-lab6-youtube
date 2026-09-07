"""Normalizacion de texto y de identificadores para el Laboratorio 6.

Separa dos rutas de procesamiento con proposito distinto (ejercicio 2.5-2.6):

``texto_original``
    Copia fiel del comentario. Es la version de auditoria y la entrada del
    modelo de sentimiento, porque emojis, signos de exclamacion, mayusculas y
    negaciones son senal legitima para un clasificador de polaridad.

``texto_limpio``
    Bolsa de palabras tematica. Aqui si se destruye informacion (mayusculas,
    puntuacion, stopwords) porque el objetivo es contar contenido, no tono.
"""
from __future__ import annotations

import re
import unicodedata
from functools import lru_cache
from urllib.parse import unquote

import emoji

# --------------------------------------------------------------- patrones ---
RE_URL = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)
RE_HASHTAG = re.compile(r"#(\w+)", re.UNICODE)
RE_MENTION = re.compile(r"@([\w.\-]+)", re.UNICODE)
RE_DIGIT_TOKEN = re.compile(r"^\d+(?:[.,]\d+)*$")
RE_WS = re.compile(r"\s+")
RE_REPEAT = re.compile(r"(.)\1{2,}")
#: Conteos con separador de miles y/o sufijo abreviado (K/M/B/mil/millones).
RE_COUNT = re.compile(
    r"^\s*([\d]+(?:[.,\s  ][\d]{3})*(?:[.,][\d]+)?)\s*"
    r"(k|m|b|mil|millones|millon|mill|kk)?\b",
    re.IGNORECASE,
)

MULTIPLIERS = {
    None: 1,
    "": 1,
    "k": 1_000,
    "mil": 1_000,
    "m": 1_000_000,
    "millon": 1_000_000,
    "millones": 1_000_000,
    "mill": 1_000_000,
    "b": 1_000_000_000,
}

#: Stopwords adicionales de dominio: ruido conversacional de YouTube que
#: sobrevive a la lista de NLTK y no aporta contenido tematico.
EXTRA_STOPWORDS = {
    "q", "x", "d", "k", "pq", "xq", "ke", "tb", "tmb", "jaja", "jajaja",
    "jajajaja", "jeje", "jjj", "aja", "eh", "ah", "oh", "uy", "ay", "si",
    "no", "ya", "va", "van", "ser", "sido", "hacer", "haciendo", "hace",
    "dice", "dijo", "decir", "solo", "solamente", "tan", "mas", "muy",
    "asi", "aqui", "alla", "ahi", "hoy", "ayer", "manana", "vez", "veces",
    "gente", "cosa", "cosas", "the", "and", "you", "for", "que", "gracias",
}


def normalize_id(value) -> str:
    """Normaliza un identificador de YouTube.

    Solo recorta espacios y normaliza Unicode a NFKC. **No** cambia el case:
    los IDs de YouTube (``UCq0Cm-3SKthEySQc2JZBi1A``) son sensibles a
    mayusculas y minusculas, por lo que bajarlos a lowercase colapsaria
    identificadores distintos.
    """
    if value is None:
        return ""
    text = str(value)
    if text.lower() == "nan":
        return ""
    return unicodedata.normalize("NFKC", text).strip()


def normalize_display(value) -> str:
    """Normaliza un nombre visible conservando su contenido legible.

    Aplica NFKC (unifica variantes de compatibilidad Unicode), colapsa
    espacios y recorta. No baja a minusculas ni quita acentos: eso se hace en
    ``normalize_key`` cuando se necesita una llave de comparacion.
    """
    if value is None:
        return ""
    text = str(value)
    if text.lower() == "nan":
        return ""
    return RE_WS.sub(" ", unicodedata.normalize("NFKC", text)).strip()


def normalize_key(value) -> str:
    """Llave de comparacion insensible a case, acentos y espacios.

    Se usa solo para *auditar* consistencia entre nombres y handles, nunca
    para reemplazar el valor original ni un identificador.
    """
    text = normalize_display(value).casefold()
    text = "".join(
        ch for ch in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(ch)
    )
    return RE_WS.sub(" ", text).strip()


RE_PERCENT = re.compile(r"%[0-9A-Fa-f]{2}")


def is_percent_encoded(value) -> bool:
    """Detecta handles con caracteres no ASCII codificados como ``%C3%ADn``."""
    return bool(RE_PERCENT.search(str(value or "")))


def normalize_handle(value) -> str:
    """Normaliza un handle a la forma ``@nombre`` conservando el case.

    Tres transformaciones, todas necesarias en estos datos:

    1. Se decodifica el percent-encoding. ``author_handle`` almacena los
       caracteres no ASCII codificados para URL (``/@ErmeP%C3%A9rez-q4s``)
       mientras ``author_name`` los guarda literales (``@ErmePérez-q4s``).
       Sin decodificar, el mismo autor parece tener dos etiquetas distintas.
    2. Se quita el prefijo ``/`` y el sufijo de ruta (``@quorumgt/videos``
       -> ``@quorumgt``), que pertenecen a la URL y no al handle.
    3. Se garantiza el prefijo ``@``.

    El case se conserva: los handles de YouTube lo respetan. El campo
    original nunca se sobrescribe; esta es una columna derivada ``*_norm``.
    """
    text = normalize_id(value)
    if not text:
        return ""
    if RE_PERCENT.search(text):
        text = unquote(text)
    text = unicodedata.normalize("NFKC", text).lstrip("/")
    text = text.split("/")[0]
    if text and not text.startswith("@"):
        text = "@" + text
    return text


def parse_count(value) -> float | None:
    """Convierte un conteo almacenado como texto a numero (ejercicio 2.4).

    Reglas documentadas:

    * ``None``/``NaN``/cadena vacia/cadena de solo espacios -> ``None``.
      En ``like_count_text`` YouTube deja el contador en blanco cuando el
      comentario no tiene "me gusta"; la conversion a 0 se hace despues, de
      forma explicita y con una bandera, no dentro del parser.
    * Separadores de miles ``,``  ``.``  espacio y espacio fino se eliminan
      (``"29,736 vistas"`` -> ``29736``).
    * Separador decimal: se interpreta como decimal solo cuando hay sufijo
      abreviado (``"1.5K"`` -> ``1500``); sin sufijo un grupo de tres digitos
      se trata como separador de miles.
    * Sufijos ``K``/``M``/``B`` y sus equivalentes en espanol (``mil``,
      ``millones``) multiplican por 1e3/1e6/1e9.
    * Cualquier cadena que no empiece por un numero reconocible -> ``None``
      (valor invalido), nunca 0, para no inventar ceros.
    """
    if value is None:
        return None
    raw = str(value)
    if raw.lower() == "nan":
        return None
    text = unicodedata.normalize("NFKC", raw).strip()
    if not text:
        return None
    match = RE_COUNT.match(text)
    if not match:
        return None
    number, suffix = match.group(1), (match.group(2) or "").lower()
    number = number.replace(" ", "").replace(" ", "").replace(" ", "")

    if suffix:
        # Con sufijo, el ultimo separador es decimal: "1.5K", "1,5 mil".
        number = number.replace(",", ".")
        if number.count(".") > 1:  # "1.234.5K" -> miles + decimal
            head, _, tail = number.rpartition(".")
            number = head.replace(".", "") + "." + tail
    else:
        # Sin sufijo, "," y "." son separadores de miles en este dataset.
        number = number.replace(",", "").replace(".", "")
    try:
        return float(number) * MULTIPLIERS.get(suffix, 1)
    except ValueError:
        return None


def extract_urls(text: str) -> list[str]:
    return RE_URL.findall(text or "")


def extract_hashtags(text: str) -> list[str]:
    """Devuelve las palabras de los hashtags en minusculas, sin ``#``."""
    return [h.lower() for h in RE_HASHTAG.findall(text or "")]


def extract_mentions(text: str) -> list[str]:
    """Devuelve las menciones ``@usuario`` en minusculas, sin ``@``."""
    return [m.lower().rstrip(".") for m in RE_MENTION.findall(text or "")]


def extract_emojis(text: str) -> list[str]:
    return [d["emoji"] for d in emoji.emoji_list(text or "")]


@lru_cache(maxsize=1)
def _spanish_stopwords() -> frozenset[str]:
    """Stopwords de espanol: NLTK + spaCy + lista de dominio."""
    words: set[str] = set()
    try:
        from nltk.corpus import stopwords

        words |= set(stopwords.words("spanish"))
    except Exception:  # pragma: no cover
        pass
    try:
        from spacy.lang.es.stop_words import STOP_WORDS

        words |= set(STOP_WORDS)
    except Exception:  # pragma: no cover
        pass
    words |= EXTRA_STOPWORDS
    # Comparacion sin acentos para que "más"/"mas" caigan igual.
    return frozenset({normalize_key(w) for w in words if w})


@lru_cache(maxsize=1)
def _nlp():
    """Carga el pipeline de espanol de spaCy solo para lematizar."""
    import spacy

    return spacy.load("es_core_news_sm", disable=["ner", "parser"])


def clean_text(text: str) -> dict:
    """Construye ``texto_limpio`` y devuelve las piezas extraidas.

    Secuencia (ejercicio 2.6), en este orden por dependencia:

    1. Extraer emojis, URLs, hashtags y menciones **antes** de destruirlos.
    2. Quitar URLs (no aportan tema y contaminan el vocabulario).
    3. Quitar el ``#`` conservando la palabra del hashtag como token tematico.
    4. Quitar las menciones completas: identifican cuentas, no tema.
    5. Reemplazar cada emoji por espacio en la version tematica (su contenido
       se analiza aparte); su senal afectiva se conserva para sentimiento
       porque ahi se usa ``texto_original``.
    6. Minusculas y eliminacion de acentos para unificar "más"/"mas".
    7. Quitar puntuacion y numeros no informativos.
    8. Quitar stopwords de espanol y tokens de 1-2 caracteres.
    9. Lematizar con ``es_core_news_sm`` para colapsar flexiones.
    """
    original = "" if text is None else str(text)
    emojis = extract_emojis(original)
    urls = extract_urls(original)
    hashtags = extract_hashtags(original)
    mentions = extract_mentions(original)

    work = RE_URL.sub(" ", original)
    work = RE_MENTION.sub(" ", work)
    work = RE_HASHTAG.sub(r" \1 ", work)
    work = emoji.replace_emoji(work, replace=" ")
    work = RE_REPEAT.sub(r"\1\1", work)  # "holaaaa" -> "holaa"
    work = normalize_key(work)
    work = re.sub(r"[^\w\s]", " ", work, flags=re.UNICODE)
    work = re.sub(r"_", " ", work)

    tokens = [t for t in work.split() if t]
    tokens = [t for t in tokens if not RE_DIGIT_TOKEN.match(t)]
    tokens = [t for t in tokens if len(t) > 2]

    stops = _spanish_stopwords()
    tokens = [t for t in tokens if t not in stops]

    lemmas = _lemmatize(tokens)
    lemmas = [t for t in lemmas if len(t) > 2 and t not in stops]

    return {
        "texto_limpio": " ".join(lemmas),
        "texto_sin_lema": " ".join(tokens),
        "hashtags": hashtags,
        "mentions": mentions,
        "urls": urls,
        "emojis": emojis,
    }


def _lemmatize(tokens: list[str]) -> list[str]:
    if not tokens:
        return []
    try:
        doc = _nlp()(" ".join(tokens))
    except Exception:  # pragma: no cover - fallback sin lematizacion
        return tokens
    out = []
    for tok in doc:
        lemma = normalize_key(tok.lemma_ or tok.text)
        out.append(lemma if lemma else tok.text)
    return [t for t in out if t]


def preprocess_for_sentiment(text: str) -> str:
    """Preprocesamiento que espera RoBERTuito (model card de pysentimiento).

    El modelo fue entrenado sobre tweets normalizados con
    ``pysentimiento.preprocessing.preprocess_tweet``. Se reimplementan aqui
    sus pasos relevantes para no introducir una dependencia que fija una
    version antigua de ``transformers``:

    * las menciones se sustituyen por el token generico ``@usuario``;
    * las URL se sustituyen por ``url``;
    * los hashtags se dejan como palabra (se quita el ``#``);
    * los emojis se traducen a su descripcion en espanol entre delimitadores
      ``emoji ... emoji``, que es la representacion vista en entrenamiento;
    * las repeticiones de mas de tres caracteres se acortan;
    * la risa se normaliza a ``jaja``.

    El contenido lexico, el case y la puntuacion se conservan: son senal para
    la polaridad.
    """
    raw = "" if text is None else str(text)
    out = RE_URL.sub("url", raw)
    out = RE_MENTION.sub("@usuario", out)
    out = RE_HASHTAG.sub(r"\1", out)
    out = re.sub(r"\b(?:[jha]{4,})\b", "jaja", out, flags=re.IGNORECASE)
    out = RE_REPEAT.sub(r"\1\1\1", out)
    out = emoji.demojize(out, language="es", delimiters=(" emoji ", " emoji "))
    out = re.sub(r"(?<= )([a-zA-Z\u00c0-\u017f]+(?:_[a-zA-Z\u00c0-\u017f0-9]+)+)(?= )",
                 lambda m: m.group(1).replace("_", " "), out)
    return RE_WS.sub(" ", out).strip()
