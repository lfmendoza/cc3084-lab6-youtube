# Decisiones metodológicas

Registro de las decisiones que el enunciado no fija explícitamente, con la
alternativa elegida y su justificación. Cada una es verificable en el código y
en las salidas de `results/`.

---

## 1. Carga e integración

| Decisión | Alternativas | Elegida y por qué |
|---|---|---|
| Codificación | `utf-8`, `utf-8-sig`, `latin-1` | **`utf-8-sig`**. Ambos archivos traen marca BOM; sin quitarla la primera columna se llama `﻿video_id` y el join falla por completo. |
| Tipos en la carga | inferencia de pandas, `dtype=str` | **`dtype=str` en todas las columnas.** La inferencia convierte identificadores con apariencia numérica y puede recortar ceros a la izquierda. Toda conversión posterior es explícita y auditada. |
| Dirección del join | inner, left desde comentarios, outer | **LEFT desde comentarios.** La pregunta del inciso 1.4 es cuántos comentarios se asocian a un video; un inner join respondería la pregunta ocultando su propia respuesta. |
| Columnas homónimas | sobrescribir, sufijar | **Sufijar `_c` / `_v`.** Permite auditar su consistencia en lugar de perder silenciosamente una de las dos versiones. |

## 2. Calidad y limpieza

| Decisión | Alternativas | Elegida y por qué |
|---|---|---|
| Valores atípicos | winsorizar, recortar por IQR, conservar | **Conservar todos.** Los conteos de popularidad siguen leyes de potencia (asimetría de `view_count` = 14,7; máximo 6 970× la mediana). Un video con 8,2 M de vistas no es un error: es el fenómeno que se estudia. Se reportan y se usan estadísticos robustos (mediana, percentiles, Spearman). |
| `like_count_text` en blanco (189 registros) | dejar nulo, imputar 0, eliminar filas | **Imputar 0 con bandera `like_count_blank`.** Justificación empírica: el mínimo no vacío observado es 1, es decir, no existe ningún cero explícito. YouTube oculta el contador cuando vale 0. Se conservan las tres columnas: texto original, parseado con nulos, e imputado con bandera. |
| Case de los identificadores | `lower()`, conservar | **Conservar.** Los IDs de YouTube distinguen mayúsculas (`UCq0Cm-3SKthEySQc2JZBi1A`); bajarlos a minúsculas colapsaría identificadores distintos. |
| `author_handle` percent-encoded (14 registros) | ignorar, decodificar | **Decodificar en `author_handle_norm`, original intacto.** Anomalía detectada por el diagnóstico: el archivo guarda `/@ErmeP%C3%A9rez-q4s` mientras `author_name` guarda `@ErmePérez-q4s`. Sin decodificar, el mismo autor parece tener dos etiquetas distintas. Misma anomalía en 13 `channel_handle`. |
| Fechas relativas | convertir a fecha absoluta, dejar como texto | **No convertir.** `published_text` es relativo al momento de recolección y redondeado por YouTube. Se deriva `published_days_approx` solo para ordenar por antigüedad, declarado como aproximación. |
| Eliminación de registros | eliminar vacíos y duplicados, conservar | **No eliminar ninguno.** Los 10 textos que quedan vacíos tras la limpieza temática conservan su `texto_original` (válido para sentimiento) y su autor sigue siendo un participante real de la red. Excluirlos borraría aristas legítimas y sesgaría la estructura hacia los comentarios largos. |

## 3. Texto

| Decisión | Alternativas | Elegida y por qué |
|---|---|---|
| Versiones del texto | una sola, dos | **Dos con propósitos distintos.** `texto_original` para auditoría y sentimiento (mayúsculas, puntuación, emojis y negaciones son señal de polaridad); `texto_limpio` para frecuencias, bigramas y TF-IDF (ahí sí conviene destruir la forma). |
| Hashtags | eliminar completos, conservar la palabra | **Extraer primero, conservar la palabra sin `#`.** El símbolo es marca sintáctica; la palabra es contenido temático legítimo. |
| Menciones | conservar, eliminar | **Extraer aparte y eliminar del texto temático.** Una mención identifica una cuenta, no un tema. |
| Reducción morfológica | stemming (Snowball), lematización (spaCy), nada | **Lematización con `es_core_news_sm`.** Un stemmer produce raíces no legibles (`diput`) que arruinan la interpretación de los rankings; el lema (`diputado`) es leíble y agrupa igual de bien. |
| Stopwords | solo NLTK, NLTK + spaCy + dominio | **Las tres fuentes.** Las listas estándar dejan pasar ruido conversacional de YouTube (`jaja`, `q`, `xq`, `pq`, `tmb`) que domina los rankings de frecuencia si no se añade. La comparación se hace sin acentos para que `más`/`mas` caigan igual. |
| Emojis | eliminar en todo, conservar en todo | **Eliminar del texto temático, traducir a español en la entrada del modelo.** En una bolsa de palabras no son términos; en polaridad sí aportan señal, y el modelo fue entrenado con esa representación. |
| Atajos de emoji textualizados | ignorar, eliminar | **Eliminar del texto temático.** Hallazgo del diagnóstico: el CSV crudo contiene 4 atajos ya convertidos a texto por el recolector (`:hand-purple-blue-peace:`) que sin tratarlos producían los bigramas «hand purple» y «purple blue» entre los más frecuentes de una comunidad: vocabulario creado por la recolección, no por los usuarios. |

## 4. Redes

| Decisión | Alternativas | Elegida y por qué |
|---|---|---|
| Nodos de autor | `author_name`, `author_handle`, `author_channel_id` | **`author_channel_id`.** Es el único identificador estable; nombre y handle son etiquetas mutables. |
| Prefijos de nodo | ninguno, `A:` / `V:` | **Con prefijo.** `author_channel_id` y `video_id` viven en el mismo espacio de nombres del grafo; sin prefijo una colisión sería silenciosa. Las tablas exportadas incluyen `raw_id` sin prefijo. |
| Aristas repetidas | una por comentario, una por par con peso | **Una por par autor–video con `weight` = número de comentarios.** Es lo que pide el inciso 4.2 y evita multiaristas. |
| `reply_count` | usar como arista, usar como atributo | **Solo como atributo.** Indica cuántas respuestas recibió un comentario, no quién las escribió. El pipeline verifica en cada corrida que la suma de pesos sea igual al número de comentarios (406) y no al de respuestas (51). |
| Pesos de la proyección | heredar el peso bipartito, contar vecinos comunes | **Contar vecinos comunes** (`bipartite.weighted_projected_graph`): videos compartidos en la de autores, autores compartidos en la de videos. Es la definición del enunciado, y la correcta para medir solapamiento en lugar de volumen. |
| Filtrado para visualizar | filtrar nodos poco conectados, mostrar todo | **Mostrar todo.** Se ajusta solo la presentación (transparencia, tamaño, etiquetas selectivas, trazados construidos ad hoc). Ningún nodo ni arista se elimina. |
| Trazado de las proyecciones | `spring_layout` global, trazado construido | **Trazado construido y determinista.** `spring_layout` es inservible aquí: en la proyección de autores colapsa las 10 732 aristas de clique en una mancha, y en la de videos empuja los 9 aislados a los bordes comprimiendo la componente conexa. Se sustituye por un disco por audiencia de video (autores) y por Kamada-Kawai en banda superior + rejilla de aislados en banda inferior (videos). Cambia solo la asignación de coordenadas. |

## 5. Topología

| Decisión | Alternativas | Elegida y por qué |
|---|---|---|
| Densidad de la bipartita | fórmula estándar, densidad bipartita | **Ambas, indicando cuál es la correcta.** El máximo de aristas de una red bipartita es \|A\|·\|B\|, no n(n−1)/2, así que la fórmula estándar subestima la conectividad. |
| Transitividad de la bipartita | omitir, reportar el 0 | **Reportar el 0 y explicar que es estructural**, y añadir el clustering bipartito de Latapy et al. (2008), que sí es interpretable. Un triángulo exigiría tres nodos mutuamente adyacentes, imposible con dos conjuntos. |
| Definición de cohesión | clustering, densidad, conectividad | **Conectividad por nodos (κ).** Se declara la definición, se reporta κ global (0, porque las redes están desconectadas) **y** κ sobre la componente mayor (la cifra interpretable en una red fragmentada), más conectividad por aristas y clustering medio como cohesión local. |
| Closeness en grafos desconectados | omitir, clásica, Wasserman-Faust | **Wasserman-Faust (`wf_improved=True`) más harmonic centrality.** La fórmula clásica es indefinida con distancias infinitas; harmonic suma recíprocos y está bien definida. |

## 6. Comunidades

| Decisión | Alternativas | Elegida y por qué |
|---|---|---|
| Red para detectar comunidades | bipartita, autor–autor, video–video | **Video–video ponderada.** (a) Es la única cuyas comunidades tienen interpretación sustantiva (grupos de videos con público compartido, caracterizables por título, canal, categoría, palabras y sentimiento). (b) La bipartita no admite modularidad estándar: su modelo nulo asume que cualquier par de nodos puede conectarse, lo que en una red bipartita es falso. (c) Las comunidades de la proyección de autores no aportan información nueva — **comprobado**: NMI = 0,90 y ARI = 0,89 frente a la etiqueta trivial «en qué video comentó», porque la proyección crea una clique por video. Se reportan igual como análisis complementario. |
| Algoritmo | Louvain, Leiden, greedy, label propagation | **Louvain** como principal (implementación de networkx, sin dependencias extra), contrastado con greedy modularity y label propagation. Louvain y greedy devuelven **la misma partición** (NMI = 1,0), lo que descarta que sea un artefacto del algoritmo. |
| Tratamiento del peso | invertir, pasar directo | **Pasar directo.** El peso es intensidad (más autores compartidos = vínculo más fuerte), que es exactamente la semántica que la modularidad ponderada espera. |
| Resolución | ajustar para forzar más comunidades, dejar en 1,0 | **1,0**, la formulación estándar. Ajustarla para obtener un número «mejor» de comunidades sería sobreajustar la partición al resultado deseado. |
| Singletons | descartar, reportar | **Reportar explícitamente.** Son 9 de 12 comunidades (47,4 % de los videos). Ocultarlos inflaría artificialmente la cobertura de las comunidades no triviales, que es del 52,6 %. |

## 7. Centralidad

| Decisión | Alternativas | Elegida y por qué |
|---|---|---|
| Peso en caminos mínimos | pasar `weight`, usar `1/weight` | **`distance = 1/weight`.** Es el punto que decide si los resultados son correctos: `weight` es intensidad, pero networkx trata `weight` como distancia en los algoritmos de camino mínimo, así que pasarlo directo invertiría el significado (dos videos con 2 autores compartidos aparecerían al *doble* de distancia que dos con 1). El peso sin transformar se usa en fuerza, PageRank y eigenvector, donde la semántica de intensidad es la correcta. |
| Criterio de «puente» | ranking de grado, ranking de betweenness, prueba de eliminación | **Prueba de eliminación.** Se retira al autor de la red bipartita, se recalcula la proyección video–video y se declara puente solo si aumentó el número de componentes. Distingue un puente real de un autor simplemente activo: 2 de los 9 autores multivideo **no** son puentes porque su conexión está duplicada por otro autor. |
| Criterio de «articulador» | ranking, definición de networkx, verificación | **Verificación empírica** con el estado antes/después registrado en `results/tables/articulation_points.csv`, más un test que re-elimina cada nodo y comprueba que el efecto declarado se reproduce. |

## 8. Contenido y sentimiento

| Decisión | Alternativas | Elegida y por qué |
|---|---|---|
| Caracterización temática | LDA, BERTopic, TF-IDF + keywords | **TF-IDF por comunidad + keywords + títulos.** Con 406 comentarios y comunidades de 6 a 225 documentos, un modelo de tópicos estaría estimando muchos parámetros sobre muy pocos datos y sus tópicos no serían estables. TF-IDF responde exactamente la pregunta pertinente (qué términos distinguen a esta comunidad) y es interpretable. |
| Unidad del IDF | comentario, comunidad | **Comunidad.** Tomando cada comunidad como un documento, un término frecuente en todas ellas (`guatemala`) queda penalizado y emergen los diferenciadores. |
| Etiqueta temática de comunidad | siempre poner una, solo si converge la evidencia | **Solo si converge.** Las tres comunidades no triviales reciben etiqueta porque términos TF-IDF de comentarios, keywords del emisor, bigramas y títulos apuntan al mismo campo semántico. Los 9 singletons no reciben etiqueta: con un solo video no se puede distinguir el tema del video del tema de una supuesta comunidad. |
| Modelo de sentimiento | TextBlob, VADER, léxico español, transformer español | **`pysentimiento/robertuito-sentiment-analysis`.** Modelo *de español* (no multilingüe), preentrenado en ~500 M de tweets (dominio informal de redes sociales, el mismo registro que los comentarios de YouTube) y afinado con TASS 2020. TextBlob y VADER se descartan porque sus léxicos son de inglés: producirían neutralidad por vocabulario fuera de diccionario, que no es una medición. Un léxico español sería mejor pero no modela negación ni contexto. |
| Entrada del modelo | `texto_limpio`, `texto_original` | **`texto_original` normalizado como en entrenamiento.** «NO me gusta» y «me gusta» son idénticos tras quitar stopwords, y opuestos en sentimiento. |
| Preprocesamiento para el modelo | ninguno, `pysentimiento` como dependencia, reimplementación | **Reimplementación documentada** de `preprocess_tweet` (menciones → `@usuario`, URL → `url`, hashtags sin `#`, emojis a descripción en español entre delimitadores, repeticiones acortadas, risa normalizada). Instalar `pysentimiento` fijaría una versión antigua de `transformers`. |
| Comparaciones por grupo | comparar todo, marcar los grupos pequeños | **Reportar todos con su `n` visible y marcar comparable solo si n ≥ 10.** Un porcentaje sobre 2 comentarios no es una estimación. Las pruebas chi-cuadrado se limitan a los grupos comparables y reportan cuántas celdas quedan con frecuencia esperada < 5. |
| Ejemplos representativos | selección manual, posicional | **Posicional** (máxima, mediana y mínima confianza de cada clase). Evita elegir a mano los ejemplos que mejor quedan. |
| Métricas de calidad del modelo | reportar accuracy del paper, no reportar | **No reportar exactitud ni F1.** No existe un conjunto etiquetado a mano de este dominio, así que cualquier cifra de desempeño sería de otro corpus. Se describe la distribución de las predicciones y su confianza, declarando que no es su corrección. |

## 9. Estadística

| Decisión | Alternativas | Elegida y por qué |
|---|---|---|
| Correlación principal | Pearson, Spearman | **Spearman.** Con n = 19 y asimetrías de 14,7 (vistas) y 2,6 (comentarios), un Pearson sobre valores brutos estaría dominado por uno o dos videos. Se complementa con Pearson sobre `log1p` (defendible porque linealiza relaciones de potencia) y Kendall tau (más robusto con n pequeña). Los tres coinciden en signo y magnitud. |
| Contraste de sesgo de cobertura | ninguno, t de Student, Mann-Whitney | **Mann-Whitney U.** Las visualizaciones no son normales y los grupos son de tamaño muy distinto (19 vs 274). |
| Diferencias de sentimiento entre grupos | comparar porcentajes, chi-cuadrado | **Chi-cuadrado con V de Cramer** y reporte de las celdas con esperado < 5, para no presentar una diferencia de porcentajes como si fuera un hallazgo. |
| Comparación de distribuciones por clase | ANOVA, Kruskal-Wallis | **Kruskal-Wallis.** Longitudes y «me gusta» tienen colas pesadas; no se cumple normalidad. |
| Concordancia entre particiones | NMI, ARI | **Ambas, atendiendo al ARI.** El NMI no corrige por azar y se infla cuando una partición tiene muchos grupos pequeños (aquí, 9 singletons de 12). El ARI sí corrige, y es la cifra que sostiene la conclusión de que las comunidades no son una relectura de la consulta de recolección (ARI = 0,083). |
| Medida de concentración | solo top-k, Gini + Lorenz + top-k | **Las tres.** El Gini resume, la curva de Lorenz muestra la forma y los top-k son interpretables directamente. La combinación es lo que revela que la concentración es de atención (alta por video y canal) y no de voz (baja por autor). |

## 10. Informe

| Decisión | Alternativas | Elegida y por qué |
|---|---|---|
| Origen de las cifras del texto | escribirlas a mano, leerlas de las métricas | **Leerlas de `results/metrics/*.json` en tiempo de generación.** Ninguna cifra del informe está escrita a mano; si cambiaran los datos, el texto cambiaría con ellos y no podría quedar inconsistente. |
| Pies de figura | escribirlos en el informe, calcularlos al generar la figura | **Calcularlos al generar la figura** y persistirlos en `results/figures/_captions.jsonl`, de donde los toma el informe. |
| Caption dentro del PNG | incrustarlo, dejarlo solo en el informe | **Solo en el informe.** Incrustado en el PNG quedaba a tamaño ilegible al escalar la figura para el PDF y se duplicaba con el pie que el informe ya renderiza. |
| Generación del PDF | Pandoc + LaTeX, ReportLab | **ReportLab.** Pandoc y LaTeX no estaban disponibles y su instalación habría añadido cientos de megabytes de dependencias del sistema. ReportLab es una dependencia de Python, ya fijada en el lock. |
| Tablas anchas | girar la página, reducir la fuente | **Reducir la fuente en tres niveles.** Girar la página dejaba páginas casi vacías antes de cada giro (114 páginas frente a 80 con el mismo contenido) y rompía la uniformidad del documento. |
| Orden de nodos y aristas de los grafos | dejar el de `networkx`, canonizar | **Canonizar en orden lexicográfico** (`_canonical`). `weighted_projected_graph` recorre conjuntos de vecinos, cuyo orden de iteración depende de la aleatorización de hashes de Python. El contenido del grafo era idéntico entre corridas, pero el orden de inserción no, y se filtraba al orden de filas de las tablas exportadas, al GraphML, al orden de dibujo de las aristas translúcidas (píxeles distintos) y al estado inicial de los trazados de fuerzas. Fijar `PYTHONHASHSEED` dentro del proceso no sirve: solo afecta a un intérprete nuevo. Tras canonizar, dos corridas producen salidas byte a byte idénticas salvo la fecha de ejecución y el tiempo de inferencia. |
| Fuente del PDF | Helvetica, DejaVu | **DejaVu Sans** si está en el sistema. Helvetica no tiene glifos para κ, Δ, ≥ ni las comillas angulares, que aparecerían como cuadros vacíos. Los emojis se describen por nombre y punto de código porque ninguna fuente incrustable los cubre. |
