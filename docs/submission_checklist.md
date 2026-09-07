# Checklist de entrega

Laboratorio 6 — CC3084 Data Science — Análisis de redes sociales (YouTube)

## Entregables exigidos por el enunciado

- [x] **Informe final en PDF**
  `report/Laboratorio_6_Analisis_Redes_Sociales_YouTube.pdf`
  78 páginas · 29 figuras incrustadas · 83 tablas · 23 secciones · 178 k
  caracteres de texto extraíble. Validado automáticamente en cada corrida
  (existencia, tamaño, número de páginas, texto extraíble, presencia de las 21
  secciones obligatorias, figuras incrustadas y ausencia de Unicode roto).

- [x] **Script reproducible de Python**
  `src/` — 13 módulos. Comando único y copiable:
  ```bash
  uv run python -m src.run_all
  ```
  Equivalente con verificación de entorno y de recursos NLP:
  ```bash
  ./scripts/run_analysis.sh
  ```

- [x] **README con instrucciones para ejecutar el análisis y dependencias**
  `README.md` — objetivo, hallazgos principales, requisitos, versión de Python,
  instalación, reproducción desde cero, ejecución de los tests, ubicación de
  todos los outputs, modelo de sentimiento, semillas y notas de
  reproducibilidad.

- [x] **Enlace al repositorio utilizado para versionar el código**
  https://github.com/lfmendoza/cc3084-lab6-youtube (privado)
  También registrado en la sección «Repositorio» del `README.md`.

- [ ] **Enlace al espacio colaborativo del grupo** — ⚠️ **PENDIENTE EXTERNO**
  No existe en el entorno local ninguna información que permita descubrir esta
  URL (no hay configuración de grupo, ni enlace en el enunciado, ni referencia
  en los datos). **No se inventa.** Es el único elemento de la entrega que
  depende de información externa no proporcionada.
  **Acción requerida:** pegar aquí y en el `README.md` la URL del espacio
  colaborativo del grupo (Drive, Notion, Teams o el que use el grupo) antes de
  entregar.
  **Este pendiente no afecta ningún requisito analítico ni ningún otro
  entregable local**, todos los cuales están completos.

## Ubicación de cada componente

### Código fuente

| Componente | Ruta |
|---|---|
| Configuración, rutas y semillas | `src/config.py` |
| Normalización de IDs, parser de conteos y limpieza de texto | `src/text_processing.py` |
| Estilo común de figuras | `src/viz.py` |
| Ejercicios 1–2 (carga, integración, calidad, limpieza) | `src/data_preparation.py` |
| Ejercicio 3 (EDA, concentración, popularidad) | `src/exploratory_analysis.py` |
| Ejercicios 4–8 (redes, topología, comunidades, centralidad) | `src/network_analysis.py` |
| Ejercicio 9 (sentimiento en español) | `src/sentiment_analysis.py` |
| Ejercicios 7.5, 3.5 y 3.6 (contenido y preguntas) | `src/content_analysis.py` |
| Narrativa del informe (lee las métricas computadas) | `src/report_text.py`, `src/report_s1.py` … `src/report_s7.py` |
| Renderizado a Markdown y PDF | `src/report_generation.py` |
| Orquestador y validación de entregables | `src/run_all.py` |
| Reproducción en un comando | `scripts/run_analysis.sh` |

### Tablas de nodos y aristas

| Componente | Ruta |
|---|---|
| Nodos de la red bipartita (22 columnas) | `results/networks/bipartite_nodes.csv` |
| Aristas de la red bipartita (11 columnas, con `weight` y `comment_ids`) | `results/networks/bipartite_edges.csv` |
| Nodos y aristas de la proyección autor-autor | `results/networks/author_projection_{nodes,edges}.csv` |
| Nodos y aristas de la proyección video-video | `results/networks/video_projection_{nodes,edges}.csv` |
| Las tres redes para Gephi | `results/networks/*.graphml` |
| Partición en comunidades | `results/networks/video_partition.json` |
| Copia de las tablas de red junto a las demás | `results/tables/` |

### Visualizaciones

29 figuras PNG a 300 dpi en `results/figures/`, con su interpretación calculada
por el pipeline en `results/figures/_captions.jsonl`:

| Archivo | Contenido |
|---|---|
| `01_missing_values.png` | Completitud de las variables por dataset |
| `02_comments_by_video.png` | Comentarios y autores únicos por video |
| `03_comments_by_channel.png` | Participación observada por canal |
| `04_category_distribution.png` | Composición temática y de muestreo |
| `05_source_queries.png` | Consultas de recolección: catálogo vs comentarios |
| `05_top_hashtags.png` | Hashtags del emisor vs de la audiencia |
| `06_top_words.png` | 25 palabras más frecuentes |
| `07_top_bigrams.png` | 25 bigramas más frecuentes |
| `08_views_distribution.png` | Distribución de visualizaciones y sesgo de cobertura |
| `09_views_vs_comments.png` | Visibilidad frente a participación observada |
| `10_participation_concentration.png` | Curvas de Lorenz de la concentración |
| `11_wordcloud.png` | Nube de palabras (complementaria) |
| `12_engagement_distributions.png` | «Me gusta», respuestas y recurrencia |
| `13_videos_per_channel.png` | Estructura del catálogo por canal |
| `13_degree_distribution_bipartite.png` | Distribución de grados de la bipartita |
| `14_bipartite_network.png` | **Red bipartita completa** |
| `15_bipartite_core_zoom.png` | Ampliación del núcleo conectado |
| `16_author_projection.png` | **Proyección autor-autor completa** |
| `17_video_projection.png` | **Proyección video-video completa** |
| `18_degree_distribution_authors.png` | Grados y fuerza de la proyección de autores |
| `19_degree_distribution_videos.png` | Grados y fuerza de la proyección de videos |
| `20_video_communities.png` | **Todas las comunidades, singletons incluidos** |
| `21_community_sizes.png` | Tamaño frente a intensidad por comunidad |
| `22_centrality.png` | Centralidades de autores y videos |
| `23_centrality_correlation.png` | Concordancia entre medidas de centralidad |
| `24_sentiment_distribution.png` | Distribución de sentimiento y confianza |
| `25_sentiment_by_video_channel.png` | Sentimiento por video y por canal |
| `26_sentiment_by_community.png` | Sentimiento por comunidad |
| `27_sentiment_vs_engagement.png` | Sentimiento frente a interacción observada |

### Modelo y reporte de sentimiento

| Componente | Ruta |
|---|---|
| Reporte del modelo (17 secciones exigidas) | `results/model/sentiment_model_report.md` |
| Metadatos exactos de ejecución | `results/model/sentiment_model_metadata.json` |
| Predicción y probabilidades por comentario | `results/tables/sentiment_predictions.csv` |
| Distribución por video, canal, comunidad, categoría y consulta | `results/tables/sentiment_summary.csv` |
| Distribución global de clases | `results/tables/sentiment_global_distribution.csv` |

### Documentación

| Componente | Ruta |
|---|---|
| Enunciado del laboratorio | `docs/Laboratorio_6_Analisis_de_redes_sociales_YouTube_2026.pdf` |
| Decisiones metodológicas justificadas | `docs/methodology.md` |
| Auditoría contra la rúbrica (100 pts) | `docs/rubric_checklist.md` |
| Este checklist | `docs/submission_checklist.md` |

### Validaciones

| Componente | Ruta |
|---|---|
| Suite de tests (159 validaciones) | `tests/` |
| Comando | `uv run pytest` |

### Repositorio Git

- [x] Git inicializado en la raíz del proyecto
- [x] `.gitignore` configurado (`.venv/`, `__pycache__/`, cachés de modelos y NLP)
- [x] `.gitattributes` que preserva `data/raw/*.csv` byte a byte
- [x] Commits lógicos por etapa del trabajo
- [x] Árbol de trabajo limpio
- [x] Remoto privado configurado y con push realizado
- [x] Sin secretos ni tokens (verificado por `test_no_hay_secretos_en_el_repositorio`)
- [x] `.venv/` no versionado
- [x] Sin cachés en el repositorio

## Verificación previa a la entrega

```bash
# 1. Reproducir todo desde cero
./scripts/run_analysis.sh --clean

# 2. Confirmar que el pipeline termina con exit code 0
echo $?

# 3. Ejecutar las validaciones
uv run pytest

# 4. Confirmar la integridad de los datos crudos
md5sum data/raw/*.csv
# d338be279d181215295037b0c938862b  data/raw/youtube_videos.csv
# c45c1dcc72e33971106845e6a9674b9e  data/raw/youtube_comments.csv

# 5. Confirmar que el árbol está limpio
git status
```
