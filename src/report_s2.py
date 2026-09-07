"""Seccion 4 del informe: calidad, limpieza y preprocesamiento."""
from __future__ import annotations

import pandas as pd

from . import config as C
from .report_text import Ctx, fmt, pct, trunc


def calidad_y_limpieza(c: Ctx) -> list:
    q, cl = c.m("quality"), c.m("cleaning")
    qv = c.t("data_quality_videos")
    qc = c.t("data_quality_comments")
    prob = c.t("problematic_variables")
    out = c.t("outlier_diagnostics")

    els: list = [
        ("h1", "4. Calidad, limpieza y preprocesamiento"),
        ("h2", "4.1 Diagnostico inicial de calidad"),
        ("p",
         "El diagnostico se ejecuta sobre los datos **crudos**, antes de cualquier "
         "transformacion, y produce un perfil por variable con tipo inferido, faltantes, "
         "celdas en blanco, cardinalidad y constancia. Las tablas completas estan en "
         "`results/tables/data_quality_videos.csv` y "
         "`results/tables/data_quality_comments.csv`; aqui se resume lo relevante."),
        ("h3", "Dimensiones, duplicados y llaves"),
        ("table", "Tabla 6. Duplicados y unicidad de las llaves candidatas",
         ["Conjunto", "Filas", "Cols.", "Filas duplicadas", "Llave", "Unicos",
          "Duplicados", "Es unica"],
         _dup_rows(q)),
        ("p",
         "No hay filas duplicadas completas en ninguno de los dos archivos, y las dos "
         "llaves primarias declaradas (`video_id` y `comment_id`) son efectivamente unicas "
         "y sin nulos. `channel_id`, `video_id` (en comentarios) y `author_channel_id` se "
         "repiten como corresponde a su papel de llave foranea o de agrupacion."),
        ("h3", "Valores faltantes"),
        ("figure", "01_missing_values.png"),
        ("table", "Tabla 7. Variables con valores faltantes",
         ["Conjunto", "Variable", "Nulos", "% nulos", "Tratamiento"],
         _missing_rows(q)),
        ("p",
         f"El catalogo de videos tiene faltantes en cuatro variables, todas por debajo del "
         f"9 %. Es importante que `view_count` **no** este entre ellas: tiene 0 nulos, "
         f"mientras que `view_count_text` tiene 13. Eso confirma la recomendacion del "
         f"enunciado de usar `view_count` para los calculos cuantitativos y reservar "
         f"`view_count_text` como respaldo. En el conjunto de comentarios el unico faltante "
         f"es `viewer_rating`, vacia en las {fmt(cl['n_comentarios'])} filas."),
        ("h3", "Variables constantes y sin varianza"),
        ("p",
         f"Dos variables del conjunto de comentarios no aportan informacion: "
         f"**`is_pinned`** toma un unico valor (`False`) en los "
         f"{fmt(cl['n_comentarios'])} registros, y **`viewer_rating`** esta completamente "
         f"vacia. Una variable de varianza cero no puede explicar ni segmentar nada, asi "
         f"que ninguna de las dos entra en el analisis. En el catalogo de videos no hay "
         f"variables constantes en sentido estricto, pero si dos **redundantes**: "
         f"`upload_date` es identica a `publish_date` y `owner_handle` es identico a "
         f"`channel_handle` en el 100 % de los registros."),
        ("h3", "Valores atipicos"),
        ("figure", "08_views_distribution.png"),
        ("table", "Tabla 8. Diagnostico de atipicos en las variables cuantitativas",
         ["Variable", "n", "Mediana", "Media", "p90", "Max", "Asimetria",
          "Atipicos IQR", "Max/mediana"],
         _outlier_rows(out)),
        ("p",
         "**No se elimino ningun valor atipico.** La decision es deliberada y se sostiene "
         "en la forma de las distribuciones. Los conteos de popularidad en redes sociales "
         "siguen leyes de potencia: la asimetria de `view_count` es de "
         f"{_get(out, 'view_count_num', 'asimetria')} y su maximo es "
         f"{_get(out, 'view_count_num', 'ratio_max_mediana')} veces la mediana. Bajo el "
         "criterio de rango intercuartil, "
         f"{_get(out, 'view_count_num', 'n_atipicos_iqr')} videos "
         f"({_get(out, 'view_count_num', 'pct_atipicos_iqr')} %) serian atipicos; pero un "
         "video con 8,2 millones de visualizaciones no es un error de captura, es un video "
         "que se hizo viral. Recortar la cola derecha eliminaria precisamente el fenomeno "
         "que se quiere estudiar y sesgaria a la baja toda medida de concentracion."),
        ("p",
         "Se aplico el mismo criterio a `like_count` (maximo de "
         f"{_get(out, 'like_count', 'max')} en un comentario, frente a una mediana de "
         f"{_get(out, 'like_count', 'mediana')}) y a la longitud del texto (maximo de "
         f"{_get(out, 'len_original', 'max')} caracteres). Los valores se reportan y se "
         "discuten como plausibles; los analisis que podrian verse afectados por la cola "
         "usan estadisticos robustos (mediana, percentiles, Spearman) en lugar de la media "
         "y Pearson."),
        ("pagebreak",),
        ("h2", "4.2 Variables problematicas o de uso delicado"),
        ("table", "Tabla 9. Clasificacion de las variables que requieren precauciones",
         ["Conjunto", "Variable", "Clasificacion", "Evidencia", "Tratamiento"],
         [[r.dataset, trunc(r.variable, 30), r.clasificacion, trunc(r.evidencia, 72),
           trunc(r.tratamiento, 96)] for r in prob.itertuples()]),
        ("p",
         "Tres casos de esa tabla merecen el enfasis que la rubrica pide. El primero es "
         "**`reply_count`**: es una variable perfectamente utilizable como atributo de "
         "intensidad de un comentario, y a la vez es la variable cuyo mal uso invalidaria "
         "todo el analisis de red. Indica cuantas respuestas recibio un comentario, no "
         "quien las escribio; usarla como arista construiria vinculos entre personas que "
         "los datos no respaldan. En este trabajo aparece unicamente como atributo agregado "
         "de nodos y aristas, y el pipeline verifica en cada corrida que la suma de pesos de "
         "la red bipartita coincida con el numero de comentarios y no con el de respuestas."),
        ("p",
         "El segundo es **`published_text`** (y su equivalente `published_time` en videos): "
         "es un tiempo relativo al momento de recoleccion («hace 2 años»), redondeado por "
         "YouTube. No se convierte a fecha absoluta porque no se conoce la fecha de "
         "recoleccion con precision y porque el redondeo destruye la resolucion. Se deriva "
         "unicamente `published_days_approx` para poder ordenar por antiguedad, y se declara "
         "explicitamente como aproximacion."),
        ("p",
         "El tercero es **`source_query`**: describe el procedimiento de muestreo, no el "
         "tema del video. Un video recuperado por la consulta `guatemala lluvias` puede "
         "tratar de trafico, y de hecho la seccion 7 muestra que la concordancia entre "
         "consulta y comunidad detectada es baja una vez corregida por azar. Se usa para "
         "diagnosticar cobertura y sesgo, nunca como etiqueta tematica."),
        ("h2", "4.3 Normalizacion de identificadores y nombres"),
        ("p",
         "La regla que gobierna esta seccion es que **un identificador nunca se sustituye "
         "por un nombre visible**. `channel_id`, `video_id`, `comment_id` y "
         "`author_channel_id` son los identificadores del analisis; los nombres y handles se "
         "usan solo como etiquetas de figuras y tablas."),
        ("table", "Tabla 10. Reglas de normalizacion aplicadas",
         ["Tipo de campo", "Transformacion", "Justificacion"],
         [["Identificadores (`*_id`)",
           "NFKC + recorte de espacios. **Sin** cambio de mayusculas/minusculas.",
           "Los IDs de YouTube distinguen mayusculas (`UCq0Cm-3SKthEySQc2JZBi1A`). "
           "Bajarlos a minusculas colapsaria identificadores distintos."],
          ["Nombres visibles",
           "NFKC + colapso de espacios, en columna derivada `*_norm`. Original intacto.",
           "NFKC unifica variantes Unicode de compatibilidad sin destruir el contenido "
           "legible. No se quitan acentos ni se baja el case."],
          ["Handles",
           "Decodificacion de percent-encoding + quita `/` inicial y sufijo de ruta + "
           "garantiza `@`, en `*_norm`.",
           "El mismo canal aparece como `/@quorumgt`, `@quorumgt` y `@quorumgt/videos`; y "
           "los no-ASCII vienen codificados para URL."],
          ["Llaves de comparacion",
           "`normalize_key`: minusculas, sin acentos, espacios colapsados. Solo para auditar.",
           "Permite comparar `más`/`mas` al verificar consistencia, sin que ese valor "
           "reemplace nunca al original ni a un ID."]]),
        ("h2", "4.4 Conversion de los conteos almacenados como texto"),
        ("p",
         "Dos variables llegan como texto y deben convertirse: `view_count_text` en videos "
         "(`\"29,736 vistas\"`) y `like_count_text` en comentarios. El parser esta en "
         "`src/text_processing.py::parse_count` y su tratamiento es el siguiente:"),
        ("table", "Tabla 11. Reglas del parser de conteos y su resultado",
         ["Caso de entrada", "Regla aplicada", "Ejemplo", "Salida"],
         [["Separador de miles (`,` o `.` o espacio)", "Se elimina",
           '"29,736 vistas"', "29736"],
          ["Sufijo del texto (`vistas`, `views`)", "Se ignora tras capturar el numero",
           '"2,390 vistas"', "2390"],
          ["Abreviatura K / M / B", "Multiplica por 1e3 / 1e6 / 1e9", '"1.5K"', "1500"],
          ["Abreviatura en espanol (`mil`, `millones`)", "Multiplica igual",
           '"1,5 mil"', "1500"],
          ["Decimal con sufijo", "El ultimo separador se lee como decimal",
           '"2.3M vistas"', "2300000"],
          ["Cadena vacia o solo espacios", "Devuelve nulo, **no** cero", '" "', "nulo"],
          ["Cadena no numerica", "Devuelve nulo, **no** cero", '"abc"', "nulo"]]),
        ("p",
         f"El caso que exige una decision es el de `like_count_text`: "
         f"**{fmt(q['likes_en_blanco'])} de {fmt(cl['n_comentarios'])} comentarios "
         f"({pct(q['pct_likes_en_blanco'])}) traen un unico espacio en blanco**. El parser "
         f"devuelve nulo para ellos, porque inventar un cero dentro de una funcion de "
         f"conversion seria mezclar parseo con imputacion. La imputacion se hace despues, "
         f"de forma explicita y con bandera de auditoria (`like_count_blank`), y la "
         f"justificacion es empirica: el minimo valor no vacio observado es "
         f"**{fmt(q['min_like_no_blanco'])}**, es decir, no existe ningun comentario que "
         f"declare cero «me gusta» de forma explicita. YouTube oculta el contador cuando "
         f"vale cero, asi que blanco equivale a cero. Se conservan las tres columnas: el "
         f"texto original, el valor parseado con nulos y el valor imputado con su bandera."),
        ("pagebreak",),
        ("h2", "4.5 Las dos versiones del texto"),
        ("p",
         "Se crearon `texto_original` y `texto_limpio` con propositos deliberadamente "
         "distintos, y la separacion no es cosmetica: usar la version equivocada cambia el "
         "resultado."),
        ("table", "Tabla 12. Proposito de cada version del texto",
         ["Version", "Contenido", "Se usa para", "Por que"],
         [["`texto_original`", "Copia fiel del comentario, sin ninguna alteracion",
           "Auditoria y **analisis de sentimiento**",
           "Mayusculas, signos de exclamacion, emojis y negaciones son senal de polaridad. "
           "«NO me gusta» y «me gusta» son identicos sin stopwords, y opuestos en "
           "sentimiento."],
          ["`texto_limpio`", "Bolsa de palabras lematizada, sin stopwords ni puntuacion",
           "Frecuencias, bigramas, TF-IDF y caracterizacion tematica",
           "Para contar contenido conviene colapsar flexiones y eliminar el ruido "
           "funcional; ahi si es correcto destruir informacion de forma."]]),
        ("h3", "4.5.1 Decisiones de limpieza de texto_limpio, una por una"),
        ("table", "Tabla 13. Decisiones documentadas del inciso 2.6",
         ["Elemento", "Decision", "Justificacion y evidencia"],
         [["Minusculas", "Se aplican, junto con eliminacion de acentos",
           "Unifica `más`/`mas` y `Diputado`/`diputado`, que de otro modo se cuentan "
           "como terminos distintos. El case se pierde solo en esta version."],
          ["URL", "Se eliminan del texto tematico; se extraen a una columna aparte",
           f"Solo {fmt(cl['comentarios_con_url'])} comentario contiene una URL, pero un "
           "dominio partido en tokens contamina el vocabulario sin aportar tema."],
          ["Hashtags", "Se extraen primero; se conserva la palabra y se elimina el `#`",
           f"El `#` es marca sintactica; la palabra es contenido tematico legitimo. "
           f"Aparecen en {fmt(cl['comentarios_con_hashtag'])} comentario."],
          ["Menciones", "Se extraen aparte y se **eliminan** del texto tematico",
           f"Una mencion identifica una cuenta, no un tema. Aparecen en "
           f"{fmt(cl['comentarios_con_mencion'])} comentarios."],
          ["Puntuacion", "Se elimina por completo",
           "No aporta al conteo de contenido. Su senal se preserva en `texto_original`, "
           "que es lo que consume el modelo de sentimiento."],
          ["Numeros", "Se eliminan los tokens puramente numericos",
           f"Presentes en algunos comentarios como cifras sueltas; sin unidad ni contexto "
           "no identifican tema."],
          ["Stopwords en espanol", "Se eliminan (NLTK + spaCy + lista de dominio)",
           "313 stopwords de NLTK, las de spaCy y una lista de ruido conversacional de "
           "YouTube (`jaja`, `q`, `xq`, `pq`, `tmb`). Sin ellas, los rankings de "
           "frecuencia se llenan de articulos y de risa."],
          ["Lematizacion", "Se aplica con `es_core_news_sm` de spaCy",
           "Colapsa `diputados`/`diputado` y `pagan`/`pagar`, que se refieren al mismo "
           "concepto. Se eligio spaCy sobre un stemmer porque un stemmer produce raices "
           "no legibles (`diput`) que arruinan la interpretacion de los rankings."],
          ["Emojis", "Se eliminan del texto tematico; se extraen y cuentan aparte",
           f"Hay {fmt(cl['total_emojis'])} emojis en {fmt(cl['comentarios_con_emoji'])} "
           "comentarios. En la bolsa de palabras no son terminos; en el analisis de "
           "sentimiento **si se conservan** y se traducen a su descripcion en espanol, "
           "porque el modelo fue entrenado con esa representacion."],
          ["Atajos de emoji textualizados", "Se eliminan del texto tematico",
           f"Hallazgo del diagnostico: el CSV crudo contiene "
           f"{fmt(cl['total_atajos_de_emoji_textual'])} atajos ya convertidos a texto por "
           f"el recolector (`:hand-purple-blue-peace:`) en "
           f"{fmt(cl['comentarios_con_atajo_de_emoji_textual'])} comentarios. Sin tratarlos "
           "producian los bigramas «hand purple» y «purple blue» entre los mas frecuentes "
           "de una comunidad: vocabulario creado por la recoleccion, no por los usuarios."],
          ["Repeticiones de caracteres", "Se acortan a dos (`holaaaa` → `holaa`)",
           "Reduce variantes ortograficas de la misma palabra."]]),
        ("h2", "4.6 Efecto cuantificado de la limpieza"),
        ("table", "Tabla 14. Efecto de la limpieza sobre el texto (inciso 2.7)",
         ["Metrica", "Antes", "Despues"],
         [["Comentarios", fmt(cl["n_comentarios"]), fmt(cl["n_comentarios"])],
          ["Registros eliminados", "—", fmt(cl["registros_eliminados"])],
          ["Textos vacios", fmt(cl["vacios_antes"]), fmt(cl["vacios_despues"])],
          ["Duplicados exactos de texto", fmt(cl["duplicados_exactos_antes"]),
           f"{fmt(cl['duplicados_texto_limpio_despues'])} "
           f"({fmt(cl['duplicados_texto_limpio_no_vacio'])} excluyendo los vacios)"],
          ["Longitud media (caracteres)", fmt(cl["longitud_media_antes"], 1),
           fmt(cl["longitud_media_despues"], 1)],
          ["Longitud mediana (caracteres)", fmt(cl["longitud_mediana_antes"], 1),
           fmt(cl["longitud_mediana_despues"], 1)],
          ["Tokens medios por comentario", fmt(cl["tokens_medios_antes"], 2),
           fmt(cl["tokens_medios_despues"], 2)],
          ["Reduccion total de caracteres", "—", pct(cl["reduccion_media_caracteres_pct"])],
          ["Reduccion total de tokens", "—", pct(cl["reduccion_media_tokens_pct"])],
          ["Textos modificados", "—",
           f"{fmt(cl['textos_modificados'])} ({pct(cl['pct_modificados'])})"],
          ["Textos sin modificacion", "—", fmt(cl["textos_sin_modificacion"])]]),
        ("p",
         f"La limpieza reduce el corpus en {pct(cl['reduccion_media_tokens_pct'])} de sus "
         f"tokens y {pct(cl['reduccion_media_caracteres_pct'])} de sus caracteres, lo que es "
         f"el orden de magnitud esperado al quitar stopwords de espanol. "
         f"{fmt(cl['textos_modificados'])} de {fmt(cl['n_comentarios'])} textos cambian; el "
         f"unico que no cambia es un comentario de una sola palabra de contenido que ya "
         "estaba en minusculas y sin puntuacion."),
        ("p",
         f"**No se elimino ningun comentario.** {fmt(cl['vacios_despues'])} textos quedan "
         f"vacios tras la limpieza tematica, es decir, estaban compuestos solo de "
         f"stopwords, emojis o interjecciones. Se conservan en el conjunto porque su "
         f"`texto_original` sigue siendo valido para el analisis de sentimiento y, sobre "
         "todo, porque su autor sigue siendo un participante real de la red: excluirlos "
         "borraria aristas legitimas de co-participacion y sesgaria la estructura hacia los "
         f"comentarios largos. Los {fmt(cl['duplicados_texto_limpio_no_vacio'])} duplicados "
         "de `texto_limpio` no vacios corresponden a comentarios distintos que, tras "
         "lematizar y quitar stopwords, comparten la misma bolsa de palabras; tampoco se "
         "eliminan, por la misma razon."),
        ("pagebreak",),
    ]
    return els


def _dup_rows(q: dict) -> list:
    rows = []
    for key, label in [("duplicados_videos", "youtube_videos"),
                       ("duplicados_comentarios", "youtube_comments")]:
        d = q[key]
        first = True
        for k, v in d["llaves"].items():
            rows.append([
                label if first else "",
                fmt(d["n_filas"]) if first else "",
                fmt(d["n_columnas"]) if first else "",
                fmt(d["filas_duplicadas_completas"]) if first else "",
                k, fmt(v["unicos"]), fmt(v["duplicados"]),
                "si" if v["es_unica"] else "no",
            ])
            first = False
    return rows


def _missing_rows(q: dict) -> list:
    trat = {
        "published_time": "No se usa como fecha; se prefiere publish_date (0 nulos)",
        "view_count_text": "Respaldo de view_count, que no tiene nulos",
        "description_snippet": "Fragmento de description; los conteos usan los no nulos",
        "description": "Analisis de texto de video sobre los no nulos, reportando el n",
        "viewer_rating": "Excluida del analisis: vacia al 100 %",
    }
    rows = []
    for ds, key in [("videos", "variables_con_nulos_videos"),
                    ("comentarios", "variables_con_nulos_comentarios")]:
        for r in q[key]:
            rows.append([ds, r["variable"], fmt(r["n_nulos"]), pct(r["pct_nulos"]),
                         trat.get(r["variable"], "—")])
    return rows


def _outlier_rows(out: pd.DataFrame) -> list:
    keep = ["view_count_num", "like_count", "reply_count_num", "len_original",
            "tokens_original", "n_emojis"]
    rows = []
    for name in keep:
        s = out[out.variable == name]
        if s.empty:
            continue
        r = s.iloc[0]
        rows.append([name, fmt(r["n"]), fmt(r["mediana"], 1), fmt(r["media"], 1),
                     fmt(r["p90"], 1), fmt(r["max"]), fmt(r["asimetria"], 2),
                     f"{fmt(r['n_atipicos_iqr'])} ({r['pct_atipicos_iqr']:.1f} %)",
                     fmt(r["ratio_max_mediana"], 1)])
    return rows


def _get(out: pd.DataFrame, var: str, col: str):
    s = out[out.variable == var]
    if s.empty:
        return "n/d"
    v = s.iloc[0][col]
    return fmt(v, 1) if isinstance(v, float) and v == v else fmt(v)
