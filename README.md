# Laboratorio 6 — Análisis de redes sociales (YouTube)

**CC3084 Data Science · Universidad del Valle de Guatemala · Semestre II, 2026**

Análisis reproducible de la estructura de participación de usuarios en YouTube a
partir de dos conjuntos de datos: un catálogo de **293 videos** de **97 canales**
y **406 comentarios principales** publicados por **332 autores** distintos.

📄 **Informe final:** [`report/Laboratorio_6_Analisis_Redes_Sociales_YouTube.pdf`](report/Laboratorio_6_Analisis_Redes_Sociales_YouTube.pdf)
(78 páginas, 29 figuras, 83 tablas)
📝 **Fuente editable:** [`report/laboratorio_6_reporte.md`](report/laboratorio_6_reporte.md)
🤖 **Reporte del modelo de sentimiento:** [`results/model/sentiment_model_report.md`](results/model/sentiment_model_report.md)
✅ **Auditoría contra la rúbrica:** [`docs/rubric_checklist.md`](docs/rubric_checklist.md)

---

## Objetivo

Estudiar la estructura de participación de los usuarios, la relación entre
canales y temas, y el contenido de las conversaciones observadas. El trabajo
construye una red bipartita **autor–video** de co-participación, sus dos
proyecciones ponderadas, mide su topología y fragmentación, detecta comunidades
de audiencia compartida, identifica participantes puente y videos articuladores,
y caracteriza el contenido y el sentimiento en español de los comentarios.

> **Restricción conceptual que gobierna todo el análisis.** Los datos **no**
> identifican quién respondió a quién. `reply_count` indica cuántas respuestas
> recibió un comentario, pero no a sus autores, por lo que **nunca** se usa como
> arista entre usuarios. Una arista autor–video significa exclusivamente que ese
> autor publicó uno o más comentarios observados en ese video: no es amistad, ni
> respuesta, ni conversación, ni aprobación.

## Hallazgos principales

| | Resultado |
|---|---|
| Integración por `video_id` | 406 / 406 comentarios asociados a un video (100 %) |
| Cobertura de comentarios | 19 de 293 videos (6,5 %) y 8 de 97 canales (8,2 %) |
| Concentración | Gini 0,660 por video · 0,664 por canal · **0,164 por autor** |
| Red bipartita | 351 nodos · 343 aristas · suma de pesos = 406 comentarios |
| Proyección video–video | 19 nodos · 11 aristas · densidad 0,064 · 9 videos aislados |
| Cohesión (κ) | 0 global en las tres redes · 1 en la componente mayor |
| Comunidades (Louvain ponderado) | 12 comunidades · Q = 0,405 · 9 singletons · 3 no triviales |
| Autores puente verificados | 7 de 332 autores |
| Videos articuladores | 5 de 19 en la proyección video–video |
| Sentimiento | NEG 61,6 % · NEU 19,0 % · POS 19,5 % (confianza mediana 0,869) |
| Visibilidad vs participación | Spearman ρ = 0,811 (p = 2 × 10⁻⁵) |

## Requisitos

- **Python 3.11 – 3.13** (desarrollado y validado con 3.13.14)
- **[uv](https://docs.astral.sh/uv/)** (recomendado). Si no está disponible, el
  script de ejecución recurre a `python3 -m venv` + `pip` con `requirements.txt`.
- ~2,5 GB de espacio en disco (PyTorch en CPU y el modelo de sentimiento)
- Conexión a internet **solo la primera vez**, para descargar el modelo de spaCy
  y el modelo de sentimiento de Hugging Face. Después el análisis corre offline.
- No requiere GPU: la inferencia de sentimiento tarda ~25 s en CPU.

## Instalación

```bash
git clone https://github.com/lfmendoza/cc3084-lab6-youtube.git
cd cc3084-lab6-youtube
UV_TORCH_BACKEND=cpu uv sync
uv run python -m spacy download es_core_news_sm
```

Los recursos de NLTK (`stopwords`, `punkt`) se descargan automáticamente en la
primera ejecución.

<details>
<summary>Sin <code>uv</code></summary>

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download es_core_news_sm
```
</details>

## Cómo reproducir todo desde cero

Un solo comando, copiable tal cual:

```bash
uv run python -m src.run_all
```

O bien el script equivalente, que además sincroniza el entorno, descarga los
recursos de NLP si faltan y ejecuta las validaciones:

```bash
./scripts/run_analysis.sh
```

`./scripts/run_analysis.sh --clean` borra todas las salidas generadas (nunca los
datos de `data/raw/`) y las vuelve a producir desde cero. `--no-tests` omite las
validaciones.

El pipeline ejecuta en orden: **(1)** validación de los datos, **(2)**
limpieza y preprocesamiento, **(3)** análisis exploratorio, **(4)** construcción
de las redes, **(5)** métricas topológicas, **(6)** detección de comunidades,
**(7)** centralidades y articulaciones, **(8)** análisis de sentimiento, **(9)**
generación de todas las tablas y figuras y **(10)** producción del informe en
Markdown y PDF. Al terminar valida que existan los 29 entregables obligatorios,
los 18 bloques de métricas y las 29 figuras, comprueba el PDF (páginas, texto
extraíble, secciones, figuras incrustadas, Unicode) y devuelve código de salida
distinto de cero si algo falta. Duración total: **~90 s** en CPU.

Cada etapa también es ejecutable por separado:

```bash
uv run python -m src.data_preparation     # ejercicios 1 y 2
uv run python -m src.exploratory_analysis # ejercicio 3
uv run python -m src.network_analysis     # ejercicios 4 a 8
uv run python -m src.sentiment_analysis   # ejercicio 9
uv run python -m src.content_analysis     # ejercicios 7.5, 3.5 y 3.6
uv run python -m src.report_generation    # ejercicio 10
```

> El orden importa: `content_analysis` consume las comunidades de
> `network_analysis` y las predicciones de `sentiment_analysis`, y
> `report_generation` consume todo lo anterior.

## Cómo ejecutar los tests

```bash
uv run pytest              # 159 tests
uv run pytest -q --tb=line # salida compacta
uv run pytest tests/test_networks.py -v
```

Las validaciones se ejecutan sobre los resultados **calculados**, no sobre
valores fijados a mano. Cubren: dimensiones y columnas exactas de los dos
archivos, unicidad de las llaves primarias, ausencia de identificadores vacíos,
integridad y cardinalidad del join, el parser numérico caso por caso (incluidos
separadores de miles, abreviaturas K/M/B y valores inválidos), que los IDs no se
hayan bajado a minúsculas, la corrección del percent-encoding en los handles,
que la suma de pesos de la red bipartita sea igual al número de comentarios,
que exista una sola arista por par autor–video, que todos los extremos de las
aristas existan en la tabla de nodos, que `reply_count` no se haya usado para
crear aristas, que los pesos de las dos proyecciones coincidan con un recálculo
independiente por intersección de conjuntos, que cada articulador reproduzca el
efecto declarado al re-eliminarlo, que la transformación `distance = 1/weight`
esté aplicada, que ninguna métrica sea `NaN` sin justificación, que cada uno de
los 406 comentarios tenga salida de sentimiento con probabilidades que sumen 1,
que todas las figuras tengan interpretación, que el PDF sea válido y que no haya
secretos en el repositorio.

Además, el propio pipeline aborta con `AssertionError` si alguna de las 9
invariantes de la red bipartita o alguna verificación de pesos de proyección
falla, de modo que no es posible generar el informe sobre una red mal construida.

## Estructura del proyecto

```
cc3084-lab6-youtube/
├── README.md                     Este archivo
├── pyproject.toml / uv.lock      Dependencias fijadas
├── requirements.txt              Alternativa sin uv
├── .gitattributes                Preserva data/raw byte a byte
├── data/
│   ├── raw/                      INMUTABLE: los dos CSV originales
│   └── processed/                Datos limpios y conjunto integrado
├── docs/
│   ├── Laboratorio_6_...2026.pdf Enunciado del laboratorio
│   ├── methodology.md            Decisiones metodológicas y su justificación
│   ├── rubric_checklist.md       Auditoría requisito por requisito
│   └── submission_checklist.md   Ubicación de cada entregable
├── src/
│   ├── config.py                 Rutas, semillas, constantes
│   ├── text_processing.py        Normalización de IDs, parser de conteos, limpieza
│   ├── viz.py                    Estilo común de figuras
│   ├── data_preparation.py       Ejercicios 1–2
│   ├── exploratory_analysis.py   Ejercicio 3
│   ├── network_analysis.py       Ejercicios 4–8
│   ├── sentiment_analysis.py     Ejercicio 9
│   ├── content_analysis.py       Ejercicios 7.5, 3.5 y 3.6
│   ├── report_text.py            Utilidades de narrativa
│   ├── report_s1..s7.py          Secciones del informe (leen las métricas)
│   ├── report_generation.py      Renderizado a Markdown y PDF
│   └── run_all.py                Orquestador y validación de entregables
├── tests/                        159 validaciones
├── results/
│   ├── figures/                  29 PNG a 300 dpi + _captions.jsonl
│   ├── tables/                   Tablas completas en CSV
│   ├── networks/                 Nodos, aristas y GraphML de las tres redes
│   ├── metrics/                  18 bloques JSON que alimentan el informe
│   └── model/                    Reporte y metadatos del modelo de sentimiento
├── report/                       Informe en PDF y en Markdown
└── scripts/run_analysis.sh       Reproducción completa en un comando
```

## Ubicación de los outputs

| Qué | Dónde |
|---|---|
| Informe final en PDF | `report/Laboratorio_6_Analisis_Redes_Sociales_YouTube.pdf` |
| Informe en Markdown | `report/laboratorio_6_reporte.md` |
| Tabla de nodos de la red bipartita | `results/networks/bipartite_nodes.csv` |
| Tabla de aristas de la red bipartita | `results/networks/bipartite_edges.csv` |
| Aristas de las proyecciones | `results/networks/{author,video}_projection_edges.csv` |
| Redes para Gephi | `results/networks/*.graphml` |
| Figuras | `results/figures/*.png` (300 dpi) |
| Interpretación de cada figura | `results/figures/_captions.jsonl` |
| Tablas completas | `results/tables/*.csv` |
| Métricas que alimentan el informe | `results/metrics/*.json` |
| Reporte del modelo de sentimiento | `results/model/sentiment_model_report.md` |
| Predicción por comentario | `results/tables/sentiment_predictions.csv` |
| Datos limpios | `data/processed/*.csv` |

## Modelo de sentimiento

**[`pysentimiento/robertuito-sentiment-analysis`](https://huggingface.co/pysentimiento/robertuito-sentiment-analysis)**
— RoBERTuito (`RobertaForSequenceClassification`, 108,8 M de parámetros,
12 capas, `hidden_size` 768), preentrenado desde cero sobre ~500 M de tweets en
español y afinado para polaridad con el corpus **TASS 2020**. Devuelve tres
clases: `NEG` / `NEU` / `POS` con probabilidades.

Se eligió por ser un modelo **de español** (no multilingüe), cuyo dominio de
preentrenamiento es **texto informal de redes sociales**, con clases
interpretables y model card pública. Se descartaron TextBlob y VADER como
solución principal porque sus léxicos son de inglés: aplicados a texto español
producirían neutralidad por vocabulario fuera de diccionario, que no es una
medición.

La inferencia usa **`texto_original`**, no `texto_limpio`: mayúsculas,
puntuación, emojis y negaciones son señal de polaridad y la versión temática las
destruye. Sobre el texto original se aplica la normalización que el modelo vio
en entrenamiento (menciones → `@usuario`, URL → `url`, hashtags sin `#`, emojis
traducidos a su descripción en español, repeticiones acortadas). Configuración:
`max_length=128`, `truncation=True`, `batch_size=32`, `model.eval()` con
`torch.no_grad()`.

El [reporte del modelo](results/model/sentiment_model_report.md) documenta los
17 puntos exigidos, incluidas 13 limitaciones (sarcasmo, ironía, slang
guatemalteco, ortografía no normativa, code-switching, emojis, negación, nombres
propios, contexto ausente, comentarios muy cortos, *domain shift*, truncamiento
y error del modelo) y la advertencia de que **la predicción del modelo no
equivale a la intención real del autor**. No se dispone de un conjunto etiquetado
a mano de este dominio, por lo que **no se reporta exactitud ni F1**.

## Semillas y notas de reproducibilidad

Semilla global **42**, fijada en `src/config.py::set_seeds()` e invocada al
inicio de cada etapa. Cubre `random`, `numpy`, `PYTHONHASHSEED` y `torch`.

| Componente | Configuración |
|---|---|
| Louvain | `seed=42`, `resolution=1.0`, `weight="weight"` |
| Betweenness | `seed=42` (cálculo exacto, sin muestreo de pivotes) |
| Label propagation (control) | `seed=42` |
| Trazado de redes | `spring_layout(seed=42)` y trazados deterministas propios para las dos proyecciones |
| Nube de palabras | `random_state=42` |
| Inferencia de sentimiento | `torch.manual_seed(42)`, `model.eval()`, determinista por naturaleza |
| TF-IDF | sin aleatoriedad |

Otras notas:

- **Los datos de `data/raw/` son inmutables** y se versionan sin conversión de
  fin de línea (`.gitattributes`) para que sus MD5 sigan coincidiendo tras
  clonar en cualquier plataforma:
  `d338be279d181215295037b0c938862b` (videos) y
  `c45c1dcc72e33971106845e6a9674b9e` (comentarios). El pipeline los recalcula y
  registra en cada corrida.
- **Ninguna cifra del informe está escrita a mano.** El texto se genera a partir
  de `results/metrics/*.json` y `results/tables/*.csv`; los pies de figura se
  calculan al generar cada gráfico y se persisten en
  `results/figures/_captions.jsonl`. Si cambiaran los datos de entrada, el texto
  del informe cambiaría con ellos.
- **El pipeline es determinista.** Dos ejecuciones consecutivas producen
  salidas byte a byte idénticas en las 29 figuras, las 36 tablas, los 10
  archivos de red y los 18 bloques de métricas. Lo único que cambia entre
  corridas son la fecha de ejecución y el tiempo de inferencia
  (`fecha_ejecucion_utc`, `segundos_de_inferencia`), que se registran a
  propósito porque la rúbrica pide documentar cuándo se ejecutó el modelo. Los
  grafos se reconstruyen en orden lexicográfico de nodos y aristas
  (`_canonical`) porque `weighted_projected_graph` recorre conjuntos de
  vecinos, cuyo orden de iteración depende de la aleatorización de hashes de
  Python; el contenido era idéntico pero el orden se filtraba a las tablas, al
  GraphML y al dibujo de las aristas translúcidas.
- Las dependencias están fijadas en `uv.lock`; `uv sync --frozen` reproduce el
  entorno exacto.
- La única fuente de variación entre máquinas es la descarga inicial del modelo
  de Hugging Face y de spaCy; las versiones quedan registradas en
  `results/model/sentiment_model_metadata.json`.

## Repositorio

- **Remoto:** https://github.com/lfmendoza/cc3084-lab6-youtube (privado)
- **Espacio colaborativo del grupo:** pendiente — ver
  [`docs/submission_checklist.md`](docs/submission_checklist.md).

## Licencia y datos

Trabajo académico para CC3084. Los datos provienen de contenido público de
YouTube recolectado por el curso y se incluyen únicamente con fines de
evaluación. Los identificadores de autor se conservan tal como llegaron porque
son la llave del análisis de red, pero no se realiza ninguna caracterización
individual de personas: todo el análisis es agregado.
