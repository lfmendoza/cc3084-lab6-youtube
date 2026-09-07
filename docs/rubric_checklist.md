# Auditoría contra la rúbrica

Matriz de cada requisito de la rúbrica y del enunciado, con su estado, la
evidencia concreta que lo respalda y su ubicación. Se auditaron los **100 puntos**
de la rúbrica y los 10 incisos del enunciado.

**Estados:** `COMPLETE` · `NOT APPLICABLE` (con justificación) · `BLOCKED` (solo
por dependencia externa realmente inevitable).

**Resultado global: 100/100 puntos COMPLETE · 0 NOT APPLICABLE · 0 BLOCKED.**

---

## (18 puntos) Calidad, limpieza y preprocesamiento

| # | Requisito | Estado | Evidencia | Archivo / sección |
|---|---|---|---|---|
| 1.1 | **(4 pts)** Diagnóstico inicial: **dimensiones** | COMPLETE | 293×20 y 406×17, verificadas contra las declaradas y coincidentes | Informe §1.2 tabla 1; `results/metrics/load.json`; test `test_videos_shape`, `test_comments_shape` |
| 1.2 | Diagnóstico: **tipos de variables** | COMPLETE | Tipo inferido por variable (entero, fecha ISO, booleano, lista serializada, conteo como texto, tiempo relativo) en las 37 columnas | `results/tables/data_quality_{videos,comments}.csv` col. `tipo_inferido`; informe §4.1 |
| 1.3 | Diagnóstico: **valores faltantes** | COMPLETE | 4 variables de videos con faltantes (<9 %); `viewer_rating` vacía al 100 %; 189 `like_count_text` en blanco (46,6 %) | Informe §4.1 fig. 1 + tabla 7; `results/metrics/quality.json` |
| 1.4 | Diagnóstico: **duplicados** | COMPLETE | 0 filas duplicadas completas; 0 duplicados en `video_id` y `comment_id`; duplicados esperados en llaves foráneas | Informe §4.1 tabla 6; test `test_video_id_unico_en_videos`, `test_comment_id_unico` |
| 1.5 | Diagnóstico: **variables constantes** | COMPLETE | `is_pinned` (un valor: `False`) y `viewer_rating` (vacía); además 2 redundantes (`upload_date`, `owner_handle`) | Informe §4.1; test `test_variables_constantes_detectadas`, `test_redundancias_confirmadas` |
| 1.6 | Diagnóstico: **valores atípicos** | COMPLETE | IQR y z robusto sobre 10 variables, con asimetría, curtosis y ratio máx/mediana. **No se elimina ninguno**, con justificación de cola pesada | Informe §4.1 tabla 8 + fig. 9; `results/tables/outlier_diagnostics.csv` |
| 1.7 | Diagnóstico: **consistencia de IDs / nombres / handles** | COMPLETE | 17 chequeos automáticos; 2 anomalías reales detectadas y corregidas (percent-encoding en `author_handle` ×14 y `channel_handle` ×13) | Informe §3.1 tabla 5; `results/tables/consistency_checks.csv`; test `test_handles_percent_encoded_quedan_decodificados` |
| 2 | **(2 pts)** Variables problemáticas o de uso delicado, con justificación | COMPLETE | 15 variables clasificadas (inutilizable / uso delicado / requiere conversión / redundante / faltantes) con evidencia y tratamiento | Informe §4.2 tabla 9; `results/tables/problematic_variables.csv` |
| 3 | **(2 pts)** Normaliza IDs y nombres manteniendo `channel_id`, `video_id`, `comment_id`, `author_channel_id` como IDs | COMPLETE | 4 reglas por tipo de campo; case preservado en IDs; nombres y handles en columnas derivadas `*_norm` con original intacto; **ningún ID sustituido por un nombre** | Informe §4.3 tabla 10; `src/text_processing.py`; test `test_ids_no_se_bajaron_a_minusculas`, `test_normalize_id_conserva_el_case` |
| 4 | **(3 pts)** Conversión a numérico documentando **separadores, abreviaturas y valores inválidos** | COMPLETE | Parser con 7 reglas: coma/punto/espacio de miles, sufijos K/M/B y `mil`/`millones`, decimal con sufijo, vacío→nulo, no numérico→nulo (nunca 0). Blanco de `like_count_text` imputado a 0 con bandera y justificación empírica (mínimo no vacío = 1) | Informe §4.4 tabla 11; `src/text_processing.py::parse_count`; 25 tests parametrizados en `test_parse_count` + `test_parse_count_coincide_con_view_count` |
| 5 | **(3 pts)** Crea y conserva `texto_original` y `texto_limpio` con justificación metodológica | COMPLETE | Dos columnas con propósitos distintos y justificación explícita (la señal de polaridad vive en la forma que el texto temático destruye) | Informe §4.5 tabla 12; `data/processed/comments_clean.csv`; test `test_texto_original_es_copia_fiel`, `test_se_uso_texto_original_como_entrada` |
| 6 | **(2 pts)** Documenta decisiones: minúsculas, URL, hashtags, menciones, puntuación, números, stopwords, lematización, emojis | COMPLETE | Las 9 exigidas más 2 adicionales (atajos de emoji textualizados, repeticiones), cada una con decisión, justificación y evidencia numérica | Informe §4.5.1 tabla 13; `docs/methodology.md` §3; tests `test_clean_text_*` |
| 7 | **(2 pts)** Cuantifica el efecto: registros eliminados/modificados, vacíos y duplicados antes y después | COMPLETE | 0 eliminados · 405 modificados (99,8 %) · vacíos 0→10 · duplicados exactos 2 → 14 de `texto_limpio` (5 no vacíos) · reducción 47,9 % caracteres y 60,8 % tokens | Informe §4.6 tabla 14; `results/tables/cleaning_effect.csv`; test `test_no_se_eliminaron_filas_en_la_limpieza` |

## (18 puntos) Análisis exploratorio

| # | Requisito | Estado | Evidencia | Archivo / sección |
|---|---|---|---|---|
| 8.1 | **(6 pts)** **videos, canales, comentarios, autores** | COMPLETE | 293 · 97 · 406 · 332 | Informe §5.1 tabla 15; `results/metrics/descriptives.json` |
| 8.2 | **videos por canal** | COMPLETE | Mediana 1, máx 20, 62 canales con un solo video; distribución completa | Informe §5.1 tabla 16 + fig. 14 |
| 8.3 | **comentarios y autores únicos por video** | COMPLETE | Mediana 7 y 7; máx 161 y 128; calculados sobre los 19 videos observados, no sobre 293 | Informe §5.1 tabla 17 + fig. 2 |
| 8.4 | **visualizaciones** | COMPLETE | Mediana 1 175, máx 8 190 449, asimetría 14,7, Gini 0,949; catálogo frente a videos observados | Informe §5.1 tabla 18 + fig. 9 |
| 8.5 | **respuestas** | COMPLETE | 51 respuestas totales; 30 de 406 comentarios (7,4 %) recibieron alguna; valores observados 0–7 | Informe §5.1 tabla 19 + fig. 13 |
| 8.6 | **«me gusta»** | COMPLETE | Suma 2 325, mediana 1, máx 405, Gini 0,896; 46,5 % con cero | Informe §5.1 tabla 19 |
| 8.7 | **categorías** | COMPLETE | 11 categorías; News & Politics 138/293 (47,1 %); catálogo frente a comentarios | Informe §5.1 fig. 4 |
| 8.8 | **consultas de búsqueda** | COMPLETE | 21 en el catálogo, 6 en los comentarios; `@quorumgt/videos` aporta 231/406 (56,9 %) | Informe §5.1 fig. 5 |
| 8.9 | **hashtags** | COMPLETE | Separados por fuente: los publica el emisor, no la audiencia | Informe §5.1 tabla 21 + fig. 6; `results/tables/top_hashtags.csv` |
| 8.10 | **palabras y bigramas frecuentes** | COMPLETE | Top 60 de cada uno con frecuencia y % de documentos; más trigramas | Informe §5.1 tabla 22 + fig. 7 y 8; `results/tables/top_{words,bigrams,trigrams}.csv` |
| 9 | **(3 pts)** Concentración de la participación en videos y canales más activos | COMPLETE | Gini + curvas de Lorenz + top-1/3/5/10 + unidades para el 50 % y el 80 %, en 7 distribuciones. Hallazgo: concentración de atención (0,660 video / 0,664 canal) y no de voz (0,164 autor) | Informe §5.2 tabla 23-25 + fig. 11; `results/tables/concentration_metrics.csv` |
| 10 | **(2 pts)** Compara popularidad y participación con sus limitaciones | COMPLETE | Spearman ρ = 0,811 (p = 2e-05) como medida principal + Pearson log-log + Kendall; contraste de sesgo de cobertura (Mann-Whitney p = 0,203); tres advertencias explícitas | Informe §5.3 tabla 26 + fig. 10; `results/metrics/{popularity,coverage_bias}.json` |
| 11 | **(3 pts)** Visualizaciones pertinentes y bien interpretadas | COMPLETE | 29 figuras a 300 dpi, cada una con título, ejes rotulados, unidades e interpretación calculada por el pipeline. Nube de palabras incluida y declarada complementaria | `results/figures/` + `_captions.jsonl`; apéndice B; test `test_todas_las_figuras_tienen_interpretacion` |
| 12 | **(2 pts)** Responde con evidencia las 6 preguntas obligatorias de 3.5 | COMPLETE | Las 6 respondidas por separado, cada una con cifras, tablas y remisión a la sección donde se derivan | Informe §6.1–6.6; `results/metrics/questions_mandatory.json`; test `test_seis_preguntas_obligatorias_respondidas` |
| 13 | **(2 pts)** Formula ≥3 preguntas adicionales y las responde con evidencia | COMPLETE | **5 preguntas**, cada una con la motivación (el hallazgo que la origina) y una prueba estadística (Spearman, Kruskal-Wallis, NMI/ARI) | Informe §7.1–7.5; `results/metrics/questions_additional.json`; test `test_al_menos_tres_preguntas_adicionales_con_evidencia` |

## (10 puntos) Construcción de la red bipartita autor-video

| # | Requisito | Estado | Evidencia | Archivo / sección |
|---|---|---|---|---|
| 14 | **(2 pts)** Red bipartita **no dirigida** autor-video correcta | COMPLETE | 351 nodos (332 autor + 19 video), 343 aristas; `nx.is_bipartite` = True; no dirigida; sin bucles; toda arista cruza tipos | Informe §8.1 y §8.3 tabla 31-32; test `test_bipartita_es_no_dirigida_y_bipartita`, `test_toda_arista_une_autor_con_video` |
| 15 | **(2 pts)** Arista y peso = número de comentarios del autor en ese video | COMPLETE | Una arista por par; **suma de pesos = 406 = número de comentarios**; peso máx 6; 9 invariantes verificadas en cada corrida con `AssertionError` si falla. `reply_count` nunca usado como arista | Informe §8.2; `results/metrics/network_bipartite.json`; tests `test_suma_de_pesos_igual_al_numero_de_comentarios`, `test_pesos_coinciden_con_el_conteo_de_comentarios`, `test_reply_count_no_se_uso_como_arista` |
| 16 | **(3 pts)** Tabla de nodos y de aristas con tipo de nodo y atributos relevantes | COMPLETE | Nodos: 22 columnas (`node_id`, `raw_id`, `node_type`, `bipartite_set`, etiquetas, metadatos de canal/video, grado, fuerza, agregados). Aristas: 11 columnas incluidas `weight`, `significado_peso` y los `comment_id` que la sostienen. También GraphML para Gephi | `results/networks/bipartite_{nodes,edges}.csv` + `bipartite.graphml`; informe §8.4 tablas 33-34; tests `test_tabla_de_nodos_tiene_tipo_y_atributos`, `test_endpoints_existen_en_la_tabla_de_nodos` |
| 17 | **(2 pts)** Visualiza la red **completa** sin eliminar estructuras por estética | COMPLETE | Figura 15 contiene los 351 nodos y las 343 aristas; solo se ajusta presentación (transparencia, tamaño, etiquetas en los 19 videos). Figura 16 es una ampliación **complementaria**, declarada como tal | Informe §8.5 fig. 15 y 16 |
| 18 | **(1 pt)** Explica el significado de la arista sin sobreinterpretarla | COMPLETE | Recuadro explícito: **no** amistad, **no** respuesta, **no** conversación, **no** acuerdo, **no** aprobación. Repetido en el pie de la figura y en `results/networks/bipartite_edges.csv` col. `significado_peso` | Informe §8.2 |

## (8 puntos) Proyecciones de la red

| # | Requisito | Estado | Evidencia | Archivo / sección |
|---|---|---|---|---|
| 19 | **(3 pts)** Proyección autor-autor con peso = videos compartidos | COMPLETE | 332 nodos, 10 732 aristas; los 10 732 pesos revalidados por intersección de conjuntos sin networkx: 0 incorrectos | Informe §9.1-9.2 tablas 35-36; `results/networks/author_projection_{nodes,edges}.csv`; test `test_proyeccion_autores_peso_es_videos_compartidos` |
| 20 | **(3 pts)** Proyección video-video con peso = autores compartidos | COMPLETE | 19 nodos, 11 aristas, pesos 1–2; los 11 pesos revalidados independientemente: 0 incorrectos; verificado que la audiencia de cada video forma una clique en la proyección de autores | Informe §9.1-9.2; `results/networks/video_projection_{nodes,edges}.csv`; tests `test_proyeccion_videos_peso_es_autores_compartidos`, `test_la_audiencia_de_cada_video_forma_una_clique` |
| 21 | **(1 pt)** Compara ambas y discute qué fenómeno representa cada una | COMPLETE | Tabla comparativa de 9 dimensiones + discusión de por qué las 10 732 aristas de la proyección de autores son un artefacto mecánico de las cliques y no audiencias entrelazadas | Informe §9.3 tabla 37 |
| 22 | **(1 pt)** Visualiza ambas proyecciones | COMPLETE | Ambas completas (fig. 17 y 18), con trazados construidos y deterministas porque `spring_layout` las hace ilegibles. Ningún nodo ni arista eliminado. Las 11 aristas de la proyección de videos también en tabla | Informe §9.4 fig. 17-18 + tabla 38 |

## (12 puntos) Topología y fragmentación

| # | Requisito | Estado | Evidencia | Archivo / sección |
|---|---|---|---|---|
| 23.1 | **(5 pts)** **Nodos, aristas, densidad, grado medio** | COMPLETE | Las tres redes; además densidad **bipartita** (\|A\|·\|B\|) porque la estándar subestima en una red bipartita | Informe §10.1 tabla 39; `results/tables/network_metrics.csv` |
| 23.2 | **Distribución de grados** (¿pocas conexiones o concentradas?) | COMPLETE | Histograma + ECDF de las tres redes (fig. 19-21) + tabla con mediana, p75, p90, p99, máx, Gini del grado y % con grado ≤2. Respuesta: **concentradas** (93,2 % con grado 1 en la bipartita, Gini 0,478) | Informe §10.3 tabla 41 + fig. 19-21 |
| 23.3 | **Componentes conexos y tamaño de la mayor** | COMPLETE | 10 componentes en las tres redes; mayor de 286 nodos (81,5 %) en la bipartita, 276 (83,1 %) y 10 (52,6 %) en las proyecciones; tamaños de todas | Informe §10.4 tabla 42; test `test_componentes_suman_el_total_de_nodos` |
| 23.4 | **Cohesión** | COMPLETE | **Definida operacionalmente** como conectividad por nodos κ: 0 global (redes desconectadas, reportado explícitamente) y 1 en la componente mayor de las tres. Complementada con conectividad por aristas, puntos de articulación, puentes y clustering medio | Informe §10.2 tabla 40 + recuadro de definición; test `test_cohesion_esta_definida_y_es_coherente` |
| 23.5 | **Transitividad** | COMPLETE | 0 en la bipartita (**explicado como propiedad estructural, no hallazgo**), 0,984 en la de autores, 0,316 en la de videos. Añadido clustering bipartito de Latapy (0,892), que sí es interpretable | Informe §10.1; test `test_transitividad_bipartita_es_cero_por_construccion` |
| 23.6 | **Autores, videos o grupos periféricos y aislados** | COMPLETE | 309 autores de grado 1 (93,1 %), 9 videos aislados en la proyección (47,4 %), 4 autores aislados, 4 componentes ≤5 nodos, tabla con los 9 videos aislados | Informe §10.4 tablas 43-44; `results/metrics/network_peripheral.json` |
| 23.7 | **Distingue aislamiento observado de ausencia de datos** | COMPLETE | Recuadro dedicado con el caso ejemplar: «Plan 2032», el video **más visto** del corpus (304 089 vistas), aparece aislado. Con 274 videos sin comentarios recolectados, la no-detección es el resultado esperado | Informe §10.4 recuadro; §16.1 |
| 24 | **(7 pts)** Interpreta correctamente los hallazgos estructurales basándose en gráficos y análisis | COMPLETE | Sección dedicada con 5 hallazgos interpretados: falta de reincidencia como mecanismo, estructura de estrella (asortatividad −0,428), fragilidad (κ=1 vs conectividad por aristas 5), separación de fragmentación real y de muestreo, y lectura del diámetro 12 / camino medio 4,72 | Informe §10.5; ampliado en §15 |

## (10 puntos) Comunidades

| # | Requisito | Estado | Evidencia | Archivo / sección |
|---|---|---|---|---|
| 25 | **(2 pts)** Selecciona una red adecuada y justifica la elección | COMPLETE | Video-video ponderada, con 3 razones. La tercera se **comprueba empíricamente**: las comunidades de la proyección de autores tienen NMI 0,90 / ARI 0,89 con la etiqueta trivial «en qué video comentó», es decir, no aportan información nueva | Informe §11.1 tabla 45; `results/metrics/communities.json` |
| 26 | **(3 pts)** Aplica un algoritmo apropiado explicando supuestos y tratamiento de pesos | COMPLETE | Louvain ponderado (networkx 3.6.1, `seed=42`, `resolution=1.0`); 4 supuestos explicados (no solapamiento, dependencia del orden, límite de resolución, modularidad alta por azar en redes dispersas); peso pasado directo con justificación. Contrastado con greedy modularity (**NMI = 1,0**, misma partición) y label propagation (NMI = 0,881) | Informe §11.2 tabla 46 + §11.3 tabla 48 |
| 27 | **(2 pts)** Reporta número, tamaños y modularidad | COMPLETE | 12 comunidades; tamaños [4,3,3,1×9]; Q ponderada 0,405 y no ponderada 0,376; 9 singletons (47,4 % de los nodos) **reportados explícitamente**; cobertura no trivial 52,6 %. Advertencia de que Q alta es fácil en un grafo casi desconectado | Informe §11.3 tabla 47 + recuadro; tests `test_comunidades_particionan_todos_los_videos`, `test_singletons_reportados_explicitamente` |
| 28 | **(1 pt)** Visualiza **todas** las comunidades | COMPLETE | Figura 22 muestra las 12, singletons incluidos y separados por una línea con rótulo. Figura 23 contrasta tamaño con intensidad | Informe §11.4 fig. 22-23 |
| 29 | **(2 pts)** Analiza hasta 3 comunidades principales: videos, canales, autores, intensidad, temas y sentimiento | COMPLETE | Las 3 no triviales (todas las que existen, justificado). Cada una con 23 dimensiones: títulos, canales, categorías, consultas, comentarios, autores, autores compartidos, intensidad por video y por autor, «me gusta», respuestas, vistas, aristas y densidad internas, términos TF-IDF de comentarios, keywords TF-IDF del emisor, palabras, bigramas, hashtags y distribución de sentimiento con su n | Informe §11.5 tablas 49-51 + §11.6 tabla 52; `results/tables/community_summary.csv`; test `test_comunidades_caracterizadas_con_tema_y_sentimiento` |

## (7 puntos) Nodos centrales y participantes puente

| # | Requisito | Estado | Evidencia | Archivo / sección |
|---|---|---|---|---|
| 30 | **(3 pts)** Investiga y calcula medidas apropiadas de centralidad justificando su uso | COMPLETE | 9 medidas con justificación individual: grado, fuerza, betweenness, closeness Wasserman-Faust, harmonic, PageRank, eigenvector, k-core, puntos de articulación. **`distance = 1/weight`** explicado como el punto que decide la corrección. Grafos desconectados tratados de 3 formas. Matriz de correlación de rangos (fig. 25) que justifica calcular varias | Informe §12.1 tabla 53 + recuadro + fig. 25; `results/metrics/centrality_summary.json`; test `test_betweenness_usa_distancia_inversa_al_peso` |
| 31 | **(2 pts)** Interpreta **por separado** autores y videos | COMPLETE | **Autores** (§12.2): 4 dimensiones distinguidas (recurrencia, amplitud de contenido, diversidad de emisores, papel estructural) con la evidencia de que **no coinciden** — el autor más recurrente (6 comentarios) tiene betweenness 0. **Videos** (§12.4): alcance, audiencia compartida, fuerza, betweenness, PageRank, con la evidencia de que el papel estructural no se deriva de la popularidad (ρ=0,289 p=0,231 con vistas; ρ=0,678 p=0,001 con comentarios) | Informe §12.2 tablas 54-56 y §12.4 tabla 58 |
| 32 | **(2 pts)** Identifica participantes recurrentes, autores puente y videos articuladores; explica hallazgos | COMPLETE | **Recurrentes**: 46 autores con >1 comentario, top 10 tabulado. **Puentes**: 7 verificados por prueba de eliminación de 9 multivideo (2 no lo son porque su conexión está duplicada). **Articuladores**: 5 videos en la proyección, 22 nodos en la bipartita, con componentes antes/después y reducción de la componente mayor. Advertencia sobre su fragilidad | Informe §12.3 tabla 57 y §12.5 tablas 59-60 + recuadro; `results/tables/{bridge_authors,articulation_points}.csv`; tests `test_articuladores_reproducen_el_efecto_declarado`, `test_autores_puente_requieren_mas_de_un_video` |

## (5 puntos) Análisis de contenido y sentimiento

| # | Requisito | Estado | Evidencia | Archivo / sección |
|---|---|---|---|---|
| 33 | **(2 pts)** Sentimiento con herramienta adecuada para español, con justificación | COMPLETE | `pysentimiento/robertuito-sentiment-analysis` (RoBERTuito, 108,8 M parámetros, preentrenado en ~500 M de tweets en español, afinado con TASS 2020). 4 razones de selección y tabla de 4 alternativas descartadas con el motivo (TextBlob y VADER: léxico de inglés → neutralidad por vocabulario fuera de diccionario, que no es medición). Entrada: `texto_original` con la normalización vista en entrenamiento. 406/406 comentarios clasificados | Informe §14.1-14.3 tabla 66; `results/model/sentiment_model_report.md` (17 puntos exigidos); tests `test_cada_comentario_tiene_prediccion`, `test_metadatos_del_modelo_completos` |
| 34 | **(1 pt)** Compara sentimiento por video, canal, tema o comunidad cuando el tamaño lo permita | COMPLETE | Las 5 agrupaciones (video, canal, comunidad, categoría, consulta) con el **n visible** y marca `comparable_n_mayor_igual_10`. Chi-cuadrado con V de Cramer solo sobre los comparables, reportando las celdas con esperado <5. Canal: χ²=82,07 p<0,001 V=0,324. Comunidad: χ²=100,35 p<0,001 V=0,357 | Informe §14.4 tablas 68-70 + fig. 27-28; `results/tables/sentiment_summary.csv`; test `test_comparaciones_declaran_el_n` |
| 35 | **(2 pts)** Explica claramente los hallazgos de contenido y sentimiento | COMPLETE | **Contenido**: TF-IDF por comunidad convergente con keywords del emisor; caída de frecuencias palabra→bigrama→trigrama (72→9→3) que descarta coordinación; desajuste entre el marco del emisor y el de la audiencia. **Sentimiento**: 61,6 % NEG; el contraste más fuerte es entre **tipos de emisor** (Municipalidad 80 % POS vs periodismo 50-86 % NEG); dos registros de participación (los negativos son más largos, 132 vs 76 caracteres, y reciben menos «me gusta», 0 vs 2; Kruskal-Wallis p<0,001) | Informe §13, §14.5-14.6, §15.5 |

## (12 puntos) Interpretación, limitaciones y conclusiones

| # | Requisito | Estado | Evidencia | Archivo / sección |
|---|---|---|---|---|
| 36 | **(3 pts)** Explica los hallazgos en el contexto de participación y consumo en YouTube | COMPLETE | 6 hallazgos, cada uno con el patrón descripción / qué significa / qué no puede concluirse: consumo paralelo no conversación; concentración de atención no de voz; audiencia compartida mínima y frágil; coincidencia de estructura de audiencia y estructura temática; la crítica se argumenta más y se premia menos; la visibilidad ordena pero no determina | Informe §15.1-15.6 |
| 37 | **(4 pts)** Discute las limitaciones mínimas exigidas | COMPLETE | Las 6 exigidas y 5 más, ordenadas por capacidad de invalidar conclusiones, cada una indicando **qué afirmación concreta restringe**: (1) cobertura de comentarios 6,5 %; (2) selección por consultas, con `@quorumgt/videos` = 56,9 %; (3) fechas relativas sin resolución; (4) conteos al momento de la recolección; (5) ausencia de relaciones explícitas entre autores; (6) concentración en pocos videos; (7) solo comentarios principales; (8) límites del sentimiento automático (sin accuracy reportable); (9) sesgo por selección de canales; (10) no representa a los usuarios de YouTube; (11) no representa a la población de Guatemala | Informe §16.1-16.11 |
| 38 | **(2 pts)** Distingue descripción, asociación e inferencia y evita generalizaciones indebidas | COMPLETE | Sección dedicada con tabla de los 3 niveles, su formulación, un ejemplo real de este informe y qué autoriza cada uno. El patrón se aplica en las 6 subsecciones de §15. Se declara que **ninguna** conclusión es inferencial | Informe §16.12 tabla 72 + recuadro |
| 39 | **(3 pts)** Conclusiones integradas que conectan redes, contenido, sentimiento y limitaciones | COMPLETE | Conclusión integrada que cruza los 3 bloques y nombra el mecanismo común (falta de reincidencia: 9/332 autores, que explica los 10 componentes, la audiencia mínima, κ=1 y los 7 puentes) + 6 afirmaciones sostenidas + 6 no sostenidas + 5 datos que harían falta para ir más allá | Informe §17.1-17.4 |

## Material a entregar (enunciado)

| # | Requisito | Estado | Evidencia |
|---|---|---|---|
| 40 | Informe en PDF con resultados, visualizaciones, interpretación y conclusiones | COMPLETE | `report/Laboratorio_6_Analisis_Redes_Sociales_YouTube.pdf` — 78 páginas, 29 figuras incrustadas, 83 tablas, 23 secciones, 178 k caracteres de texto extraíble. Validado automáticamente (páginas, texto, secciones, figuras, Unicode) |
| 41 | Script reproducible de Python | COMPLETE | `src/` (13 módulos) + `scripts/run_analysis.sh`. Comando único: `uv run python -m src.run_all` |
| 42 | Enlace al espacio colaborativo del grupo | BLOCKED (dependencia externa) | No existe información local que permita descubrirlo y no se inventa. Registrado como pendiente externo en `docs/submission_checklist.md`. **No afecta ningún requisito analítico.** |
| 43 | Enlace al repositorio de versionado | COMPLETE | https://github.com/lfmendoza/cc3084-lab6-youtube (privado) — también en el README |
| 44 | README con instrucciones y dependencias | COMPLETE | `README.md` — objetivo, hallazgos, requisitos, versión de Python, instalación, reproducción desde cero, tests, ubicación de outputs, modelo de sentimiento, semillas, notas de reproducibilidad, enlaces |

## Trazabilidad con los incisos del enunciado

| Inciso | Sección del informe |
|---|---|
| 1.1–1.4 Carga, comprensión e integración | §1, §2, §3 |
| 2.1–2.7 Calidad, limpieza y preprocesamiento | §4.1–4.6 |
| 3.1–3.4 Análisis exploratorio y visualizaciones | §5.1–5.3 |
| 3.5 Seis preguntas obligatorias | §6.1–6.6 |
| 3.6 Preguntas adicionales | §7.1–7.5 |
| 4.1–4.5 Red bipartita | §8.1–8.5 |
| 5.1–5.4 Proyecciones | §9.1–9.4 |
| 6.1–6.4 Topología y fragmentación | §10.1–10.5 |
| 7.1–7.5 Comunidades | §11.1–11.6 |
| 8.1–8.3 Centralidad y puentes | §12.1–12.5 |
| 9.1–9.3 Contenido y sentimiento | §13, §14 |
| 10.1–10.4 Interpretación, limitaciones y conclusiones | §15, §16, §17 |

Apéndice A del informe reproduce esta trazabilidad inciso por inciso.

## Segunda pasada de auditoría

Tras el primer borrador se releyó el enunciado y la rúbrica completos buscando
omisiones. Se detectaron y corrigieron **siete**:

1. **Cohesión sin definir.** La primera versión reportaba κ sin declarar qué
   medía ni explicar el 0 de las redes desconectadas. Se añadió el recuadro de
   definición operacional en §10.2 y κ sobre la componente mayor.
2. **Transitividad 0 presentada como hallazgo.** Se corrigió a propiedad
   estructural de una red bipartita y se añadió el clustering de Latapy.
3. **Densidad bipartita ausente.** Se añadió, porque la fórmula estándar usa un
   máximo inalcanzable en una red bipartita.
4. **Correlación mal interpretada.** Un pie de figura afirmaba que la relación
   entre visualizaciones y comentarios no era significativa; el cálculo da
   ρ=0,811 con p=2e-05. Se hicieron **todos** los pies de figura data-driven.
5. **ARI mal interpretado.** Se describía como «alta» una concordancia de
   ARI=0,083. Se corrigió explicando por qué el NMI se infla con particiones
   fragmentadas y por qué el ARI es la cifra a la que atender.
6. **Caption duplicado e ilegible.** Los pies se incrustaban en el PNG a tamaño
   ilegible y se repetían en el informe. Se dejaron solo en el informe.
7. **Fuga de vocabulario del recolector.** Los bigramas «hand purple» y «purple
   blue» aparecían entre los más frecuentes de una comunidad; provenían de 4
   atajos de emoji textualizados en el CSV crudo. Se detectan, se cuentan y se
   eliminan del texto temático.
