# Reporte del modelo de analisis de sentimiento

**Laboratorio 6 — CC3084 Data Science — Analisis de redes sociales (YouTube)**
Documento generado automaticamente por `src/content_analysis.py` a partir de
`results/metrics/sentiment.json`. Fecha de ejecucion (UTC):
`2026-09-07T03:52:28+00:00`.

---

## 1. Identificacion exacta del modelo

| Campo | Valor |
|---|---|
| Identificador en Hugging Face | `pysentimiento/robertuito-sentiment-analysis` |
| Familia / arquitectura | RobertaForSequenceClassification (`model_type = roberta`) |
| Clase de modelo cargada | `RobertaForSequenceClassification` |
| Numero de parametros | 108,791,043 |
| Capas ocultas / hidden size | 12 / 768 |
| Tokenizer | `TokenizersBackend`, vocabulario de 30,000 tokens |
| Framework | PyTorch via HuggingFace transformers |
| Version de `transformers` | 5.16.1 |
| Version de `torch` | 2.14.0+cu130 |
| Python / plataforma | 3.13.14 / Linux 6.18.33.2-microsoft-standard-WSL2 (x86_64) |
| Dispositivo de inferencia | `cpu` (CUDA disponible: False) |
| Semilla | 42 |
| Tiempo de inferencia | 25.73 s para 406 comentarios (15.8 comentarios/s) |

## 2. Motivo de la seleccion

Se necesitaba clasificar polaridad en comentarios de YouTube escritos en
espanol de Guatemala: textos cortos, con ortografia libre, emojis, ironia y
lexico local. Se eligio `pysentimiento/robertuito-sentiment-analysis` por cuatro razones concretas:

1. **Es un modelo especifico de espanol.** RoBERTuito se preentreno desde cero
   sobre texto en espanol, no como una de cien lenguas dentro de un modelo
   multilingue. Su vocabulario no compite con otros idiomas.
2. **Su dominio de preentrenamiento coincide con el de los datos.** Se
   entreno sobre aproximadamente 500 millones de tweets en espanol. Los
   comentarios de YouTube comparten con los tweets la brevedad, los emojis y
   la escritura informal.
3. **Fue afinado explicitamente para polaridad** con el corpus TASS 2020,
   que es un corpus academico de sentimiento en espanol con variantes
   dialectales de America Latina y Espana.
4. **Devuelve tres clases interpretables con probabilidades**, lo que permite
   reportar distribucion, confianza y casos ambiguos sin inventar umbrales.

### 2.1 Por que es adecuado para el espanol

RoBERTuito **no es un modelo multilingue adaptado**: se preentreno desde cero
sobre un corpus exclusivamente en espanol, y su tokenizador BPE se aprendio
sobre ese mismo corpus. Tres consecuencias practicas para estos datos:

* **El vocabulario no compite con otros idiomas.** En un mBERT o un XLM-R, el
  presupuesto de subpalabras se reparte entre mas de cien lenguas, de modo que
  el espanol se segmenta en piezas mas cortas y menos informativas. Aqui las
  palabras frecuentes del corpus (*diputado*, *pueblo*, *corrupto*) tienden a
  ser tokens unicos o de pocas piezas.
* **Cubre la morfologia flexiva del espanol.** Conjugaciones, enclisis
  (*deportarlos*, *verlos*) y diminutivos (*almuercitos*, que aparece en los
  datos) estan representados en el preentrenamiento.
* **El corpus de afinado es de espanol y dialectalmente diverso.** TASS 2020
  incluye variantes de Espana, Mexico, Peru, Uruguay y Costa Rica, lo que
  reduce (sin eliminar) el desajuste con el espanol de Guatemala. Su limitacion
  para el lexico guatemalteco se documenta en la seccion 11.

### 2.2 Por que es adecuado para texto de redes sociales

Su corpus de preentrenamiento son ~500 millones de **tweets**, no noticias ni
resenas ni Wikipedia. Los comentarios de YouTube comparten con los tweets las
propiedades que rompen a un modelo entrenado en texto formal:

| Propiedad del texto | Presencia en estos datos | Por que importa |
|---|---|---|
| Brevedad | longitud mediana de 96,5 caracteres | Un modelo de documentos largos depende de contexto que aqui no existe |
| Emojis | 199 emojis en 61 de 406 comentarios | El modelo los vio en entrenamiento como texto normalizado |
| Ortografia libre | *ba* por *va*, *tube* por *tuve*, *corrpcion* | Reduce los tokens fuera de vocabulario |
| Mayusculas expresivas y puntuacion repetida | frecuentes | Se conservan como senal, no se normalizan a la baja |
| Menciones y hashtags | 5 y 1 comentarios respectivamente | Tienen token generico propio en el preentrenamiento |
| Alargamientos y risa | *jajajaja*, repeticiones de vocales | Normalizados igual que en entrenamiento |

Esto no elimina el salto de dominio: sigue habiendo diferencia entre Twitter de
2020 y YouTube, y esa limitacion se declara en la seccion 11.

### 2.3 Alternativas descartadas y por que

| Alternativa | Motivo del descarte |
|---|---|
| TextBlob | Su analizador de polaridad es un lexico de ingles. Aplicado a espanol, la mayoria de los tokens quedaria fuera de diccionario y produciria polaridad 0 por ausencia de vocabulario, no por neutralidad del texto. No es una medicion. |
| VADER (`nltk.sentiment`) | Mismo problema: el lexico y las reglas de intensificacion son de ingles. Esta bien disenado para redes sociales, pero en ingles. |
| Diccionarios de sentimiento en espanol (p. ej. ML-SentiCon) | Son lexicos de palabra aislada: no modelan negacion ("no me gusta"), ni ironia, ni el contexto de la oracion. Serviria como respaldo, no como metodo principal. |
| Modelos multilingues genericos (mBERT, XLM-R sin afinar para sentimiento) | Requeririan afinado propio y no hay datos etiquetados de este dominio para hacerlo ni para validarlo. |

## 3. Etiquetas y su significado

| Etiqueta | id interno | Significado operativo |
|---|---|---|
| `NEG` | 0 | polaridad negativa (critica, queja, rechazo, insulto) |
| `NEU` | 1 | polaridad neutra (informativo, pregunta, sin carga afectiva clara) |
| `POS` | 2 | polaridad positiva (aprobacion, agradecimiento, elogio, apoyo) |

El mapeo de etiquetas se toma directamente de `model.config.id2label`
(`{"0": "NEG", "1": "NEU", "2": "POS"}`); no se reordena ni se
renombra manualmente.

## 4. Preprocesamiento y texto de entrada

**Se usa `texto_original`, no `texto_limpio`.** La razon es metodologica: la
version tematica elimina mayusculas, puntuacion, emojis y stopwords, y
precisamente esos elementos portan senal de polaridad. "NO me gusta" y "me
gusta" son identicos tras quitar stopwords, pero opuestos en sentimiento.

Sobre `texto_original` se aplica la normalizacion que el modelo vio en
entrenamiento (equivalente a `pysentimiento.preprocessing.preprocess_tweet`,
reimplementada en `src/text_processing.py::preprocess_for_sentiment` para no
fijar una version antigua de `transformers`):

| Paso | Transformacion | Motivo |
|---|---|---|
| Menciones | `@usuario` | El modelo vio ese token generico; el nombre concreto no aporta polaridad. |
| URL | `url` | Igual que arriba. |
| Hashtags | se quita el `#`, se conserva la palabra | La palabra si es contenido. |
| Emojis | descripcion en espanol entre delimitadores `emoji ... emoji` | Es la representacion vista en entrenamiento (`emoji.demojize(language="es")`). |
| Repeticiones | mas de 3 caracteres iguales se acortan a 3 | Reduce variantes fuera de vocabulario. |
| Risa | `jajajaja` -> `jaja` | Normalizacion vista en entrenamiento. |
| Case, puntuacion, negaciones | **se conservan** | Son senal de polaridad. |

## 5. Configuracion de inferencia

| Parametro | Valor |
|---|---|
| `max_length` | 128 tokens (limite del tokenizer: 128) |
| `truncation` | True |
| `padding` | longest por lote |
| `batch_size` | 32 |
| Modo | inferencia con torch.no_grad(), model.eval() |
| Determinismo | La inferencia es determinista: no hay dropout activo ni muestreo. La semilla se fija de todos modos para que cualquier operacion estocastica futura sea reproducible. |

## 6. Distribucion de clases obtenida

Sobre los **406 comentarios**
(100.0% de cobertura: ningun comentario quedo sin
prediccion):

| Clase | n | % |
|---|---:|---:|
| NEG | 250 | 61.58 |
| NEU | 77 | 18.97 |
| POS | 79 | 19.46 |
| **Total** | **406** | **100.0** |

Clase mayoritaria: **NEG**. Polaridad neta global
(%POS - %NEG): **-42.12 puntos porcentuales**.

## 7. Confianza de las predicciones

| Metrica | Valor |
|---|---|
| Confianza media | 0.8084 |
| Confianza mediana | 0.8685 |
| Rango intercuartil | 0.6815 - 0.9492 |
| Confianza minima | 0.3548 |
| Predicciones con confianza < 0.5 | 16 (3.94%) |
| Predicciones con margen < 0.2 | 40 (9.85%) |
| Entropia media de la distribucion | 0.4864 |

Confianza media por clase:
- `NEG`: 0.8637999892234802
- `NEU`: 0.6284999847412109
- `POS`: 0.8083000183105469

> **Advertencia.** La confianza es la probabilidad de la clase mas probable, no una medida de intensidad de polaridad. Una prediccion NEG con confianza 0.95 no es 'mas negativa' que una con 0.60: es una clasificacion mas segura.

## 8. Comparaciones por grupo

Se reporta el `n` de cada grupo y se marca explicitamente si es comparable
(n >= 10). Los grupos pequenos se muestran pero no se interpretan: un
porcentaje sobre 2 comentarios no es una estimacion.

### 8.1 Por canal

| Grupo | n | % NEG | % NEU | % POS | Polaridad neta | Confianza media | Comparable (n>=10) |
|---|---:|---:|---:|---:|---:|---:|:--:|
| Quorum | 256 | 69.92 | 15.62 | 14.45 | -55.5 | 0.8292 | si |
| Gobierno de la República de Guatemala | 70 | 48.57 | 27.14 | 24.29 | -24.3 | 0.7705 | si |
| Noticias Telemundo | 25 | 72.0 | 20.0 | 8.0 | -64.0 | 0.724 | si |
| Municipalidad de Guatemala | 25 | 8.0 | 12.0 | 80.0 | +72.0 | 0.835 | si |
| Noti7 | 14 | 28.57 | 50.0 | 21.43 | -7.1 | 0.7326 | si |
| PrensaLibreOficial | 7 | 85.71 | 14.29 | 0.0 | -85.7 | 0.8335 | NO |
| TN23 Guatemala | 7 | 85.71 | 14.29 | 0.0 | -85.7 | 0.736 | NO |
| Noticiero Guatevisión 13 Hrs. | 2 | 50.0 | 50.0 | 0.0 | -50.0 | 0.8795 | NO |

Prueba chi-cuadrado de independencia (solo canales con n >= 10):
chi2 = 82.0701, gl = 8, p = 0.0,
V de Cramer = 0.3244
(5 canales, n = 390).
Parte de las frecuencias esperadas es menor que 5, por lo que el valor p es aproximado.

### 8.2 Por comunidad de la proyeccion video-video

| Grupo | n | % NEG | % NEU | % POS | Polaridad neta | Confianza media | Comparable (n>=10) |
|---|---:|---:|---:|---:|---:|---:|:--:|
| C0 | 225 | 76.0 | 15.11 | 8.89 | -67.1 | 0.8265 | si |
| C1 | 84 | 45.24 | 30.95 | 23.81 | -21.4 | 0.7642 | si |
| C2 | 34 | 50.0 | 20.59 | 29.41 | -20.6 | 0.836 | si |
| C5 | 25 | 72.0 | 20.0 | 8.0 | -64.0 | 0.724 | si |
| C9 | 25 | 8.0 | 12.0 | 80.0 | +72.0 | 0.835 | si |
| C6 | 4 | 25.0 | 0.0 | 75.0 | +50.0 | 0.9496 | NO |
| C4 | 3 | 33.33 | 0.0 | 66.67 | +33.3 | 0.6428 | NO |
| C3 | 2 | 50.0 | 50.0 | 0.0 | -50.0 | 0.8795 | NO |
| C11 | 1 | 0.0 | 100.0 | 0.0 | +0.0 | 0.5853 | NO |
| C10 | 1 | 0.0 | 0.0 | 100.0 | +100.0 | 0.7521 | NO |
| C7 | 1 | 0.0 | 0.0 | 100.0 | +100.0 | 0.9743 | NO |
| C8 | 1 | 100.0 | 0.0 | 0.0 | -100.0 | 0.8537 | NO |

Chi-cuadrado (comunidades con n >= 10): chi2 = 100.3471,
gl = 8, p = 0.0,
V de Cramer = 0.3573. Parte de las frecuencias esperadas es menor que 5, por lo que el valor p es aproximado.

### 8.3 Por video (solo los comparables)

| Grupo | n | % NEG | % NEU | % POS | Polaridad neta | Confianza media | Comparable (n>=10) |
|---|---:|---:|---:|---:|---:|---:|:--:|
| Qué rico come tu diputado | 161 | 80.75 | 13.66 | 5.59 | -75.2 | 0.8373 | si |
| La cooptación de Walter Mazariegos en la USAC | 50 | 58.0 | 20.0 | 22.0 | -36.0 | 0.8032 | si |
| Inician los trabajos de recuperación del Puente Beli... | 45 | 40.0 | 31.11 | 28.89 | -11.1 | 0.7612 | si |
| Plan 2032 Ciudad de Guatemala | 25 | 8.0 | 12.0 | 80.0 | +72.0 | 0.835 | si |
| Conferencia de Prensa del Gobierno de Guatemala. #La... | 25 | 64.0 | 20.0 | 16.0 | -48.0 | 0.7873 | si |
| EE.UU. envía a mexicanos deportados a Guatemala ante... | 25 | 72.0 | 20.0 | 8.0 | -64.0 | 0.724 | si |
| Arroz con pollo a la MONOPOLIO | 16 | 56.25 | 12.5 | 31.25 | -25.0 | 0.8871 | si |
| Capturan a presuntos delincuentes disfrazados de muj... | 14 | 28.57 | 50.0 | 21.43 | -7.1 | 0.7326 | si |
| Internet: escoger el menos malo | 12 | 33.33 | 33.33 | 33.33 | +0.0 | 0.7602 | si |

Chi-cuadrado (videos con n >= 10): chi2 = 115.292,
gl = 16, p = 0.0,
V de Cramer = 0.3931. Parte de las frecuencias esperadas es menor que 5, por lo que el valor p es aproximado.

### 8.4 Asociacion con metricas de interaccion

| Clase | 'Me gusta' mediana | 'Me gusta' media | Longitud mediana (car.) | % con emoji |
|---|---:|---:|---:|---:|
| NEG | 0 | 1.66 | 132 | 11.2 |
| NEU | 1 | 7.4 | 41 | 18.18 |
| POS | 2 | 16.97 | 76 | 24.05 |

## 9. Ejemplos representativos

Para cada clase se muestran el caso de mayor confianza, el caso de confianza mediana y el de menor confianza. Es una seleccion posicional y reproducible, no una eleccion manual de los ejemplos mas favorables.

### Negativos
- **NEG** (confianza 0.986; NEG 0.99 / NEU 0.01 / POS 0.00) · posicion en confianza: **maxima**
  > Que indignante saber como se artan estos coches y finalmente el pueblo esta ciendo dañado
  <br>Video: *Qué rico come tu diputado*
- **NEG** (confianza 0.915; NEG 0.91 / NEU 0.08 / POS 0.01) · posicion en confianza: **mediana**
  > Me pregunto si antes de ser diputados les alcanzaba su dinero para comer esos almuercitos y en esos lugares? Pero como don pueblo paga....vengase el almuercito. La historia ni él se la cree. O sea.... la 3a. parte de su salario para un almuerzo???
  <br>Video: *Qué rico come tu diputado*
- **NEG** (confianza 0.435; NEG 0.44 / NEU 0.42 / POS 0.14) · posicion en confianza: **minima**
  > Ay ricos shucos en la calle jajaja
  <br>Video: *Qué rico come tu diputado*

### Neutros
- **NEU** (confianza 0.885; NEG 0.06 / NEU 0.89 / POS 0.06) · posicion en confianza: **maxima**
  > Pregúntenle si se acuerda de la marca del vino que se toma todos los días
  <br>Video: *Conferencia de Prensa del Gobierno de Guatemala. #LaRondaGt*
- **NEU** (confianza 0.589; NEG 0.29 / NEU 0.59 / POS 0.12) · posicion en confianza: **mediana**
  > Así metan los al tambo con minifaldas allí no les ba a faltar la moronga.
  <br>Video: *Capturan a presuntos delincuentes disfrazados de mujer señalados de cometer asalto*
- **NEU** (confianza 0.355; NEG 0.33 / NEU 0.35 / POS 0.32) · posicion en confianza: **minima**
  > Este hombre esta loco
  <br>Video: *Conferencia de Prensa del Gobierno de Guatemala. #LaRondaGt*

### Positivos
- **POS** (confianza 0.978; NEG 0.00 / NEU 0.02 / POS 0.98) · posicion en confianza: **maxima**
  > Es un proyecto extraordinario , vamos adelante mi guate hermosa!
  <br>Video: *Plan 2032 Ciudad de Guatemala*
- **POS** (confianza 0.858; NEG 0.01 / NEU 0.13 / POS 0.86) · posicion en confianza: **mediana**
  > Guatemala nunca se tube que llamar guatemala dino guatebella guatehermosa guatelinda la eterna primavera es guatebella abrazos hnos de un salvadoreno que viva el amor y la armonia
  <br>Video: *Plan 2032 Ciudad de Guatemala*
- **POS** (confianza 0.473; NEG 0.26 / NEU 0.27 / POS 0.47) · posicion en confianza: **minima**
  > Despues de tanta corrpcion y desfalco por los anteriores gobiernos ladrones que esperaba Rolando? ahora si se puede ver que los fondos de nuestros impuestos se estan usando en lo que deberian de haberse usado hace 40 anios, es muy bueno ver que al fin hay un presidente que esta trabajando no sentado...
  <br>Video: *Inician los trabajos de recuperación del Puente Belice II.*

## 10. Casos ambiguos

Los seis comentarios con menor confianza del corpus. Sirven para calibrar
cuanto peso admite una prediccion individual:

- **NEU** (confianza 0.355; NEG 0.33 / NEU 0.35 / POS 0.32)
  > Este hombre esta loco
  <br>Video: *Conferencia de Prensa del Gobierno de Guatemala. #LaRondaGt*
- **NEG** (confianza 0.435; NEG 0.44 / NEU 0.42 / POS 0.14)
  > Ay ricos shucos en la calle jajaja
  <br>Video: *Qué rico come tu diputado*
- **NEU** (confianza 0.442; NEG 0.43 / NEU 0.44 / POS 0.13)
  > " Ayudanos a luchar contra el racismo y los malos tratos; vete de regreso a tu pais"                                               Someone.
  <br>Video: *EE.UU. envía a mexicanos deportados a Guatemala antes de su regreso a México | Noticias Telemundo*
- **NEU** (confianza 0.470; NEG 0.43 / NEU 0.47 / POS 0.10)
  > Mantenidos
  <br>Video: *Qué rico come tu diputado*
- **NEU** (confianza 0.473; NEG 0.47 / NEU 0.47 / POS 0.06)
  > Pero hay que ver el lado bueno si los deportan por la Frontera los carteles los secuestran para sacar dinero a los familiares en USA
  <br>Video: *EE.UU. envía a mexicanos deportados a Guatemala antes de su regreso a México | Noticias Telemundo*
- **POS** (confianza 0.473; NEG 0.26 / NEU 0.27 / POS 0.47)
  > Despues de tanta corrpcion y desfalco por los anteriores gobiernos ladrones que esperaba Rolando? ahora si se puede ver que los fondos de nuestros impuestos se estan usando en lo que deberian de haberse usado hace 40 anios, es muy bueno ver que al fin hay un presidente que esta trabajando no sentado...
  <br>Video: *Inician los trabajos de recuperación del Puente Belice II.*

La inspeccion de estos casos muestra el patron esperado: fallan la ironia
("Ay ricos shucos en la calle jajaja", clasificado NEG con 0.44 de
confianza), el sarcasmo citado entre comillas, las expresiones de una sola
palabra sin contexto ("Mantenidos") y el lexico guatemalteco no presente en
el corpus de entrenamiento ("shucos", "tambo", "moronga", "ba" por "va").

## 11. Limitaciones

| Limitacion | Como se manifiesta en estos datos |
|---|---|
| **Sarcasmo e ironia** | El modelo clasifica la superficie lexica. "Ay ricos shucos en la calle jajaja" es una burla, pero recibe NEG con confianza 0.44. |
| **Slang y variacion dialectal** | Terminos guatemaltecos ("shucos", "moronga", "tambo", "chapin") no estan en el vocabulario de TASS ni son frecuentes en el preentrenamiento. |
| **Ortografia no normativa** | "ba" por "va", "artan" por "hartan", "tube" por "tuve", "corrpcion". Aumentan los tokens fuera de vocabulario. |
| **Lenguaje mixto** | Aparecen fragmentos en ingles dentro de comentarios en espanol; el modelo no esta entrenado para code-switching. |
| **Emojis** | Se traducen a texto, pero su valor pragmatico (un emoji de risa puede marcar burla, no alegria) no se recupera. |
| **Negacion y alcance** | Los transformers manejan la negacion mejor que un lexico, pero siguen fallando en oraciones largas con negacion distante. |
| **Nombres propios** | Nombres de politicos e instituciones aparecen en contextos criticos; el modelo puede asociar la entidad con la polaridad en lugar de la predicacion sobre ella. |
| **Contexto ausente** | Un comentario responde a un video que el modelo no ve. "Este hombre esta loco" es ininterpretable sin saber de quien se habla. |
| **Comentarios muy cortos** | La longitud minima observada es de 1 caracter. Con menos de cinco tokens la prediccion es poco informativa. |
| **Domain shift** | Entrenado en tweets (2020, TASS), aplicado a comentarios de YouTube. Comparten registro pero no plataforma ni epoca. |
| **Truncamiento** | Los comentarios de mas de 128 tokens se truncan; el comentario mas largo tiene 1 525 caracteres. |
| **Error del modelo** | No se dispone de un conjunto etiquetado a mano de este dominio, asi que **no se puede reportar exactitud ni F1 sobre estos datos**. Las cifras de esta seccion describen la distribucion de las predicciones, no su correccion. |
| **Tres clases, no intensidad** | El modelo no mide cuan negativo es un comentario. La confianza no es intensidad. |

## 12. Referencia

- Model card: <https://huggingface.co/pysentimiento/robertuito-sentiment-analysis>
- Perez, J. M., Furman, D. A., Alonso Alemany, L. y Luque, F. (2022).
  *RoBERTuito: a pre-trained language model for social media text in Spanish*.
  LREC 2022. <https://aclanthology.org/2022.lrec-1.785/>
- Perez, J. M., Giudici, J. C. y Luque, F. (2021). *pysentimiento: A Python
  Toolkit for Sentiment Analysis and SocialNLP tasks*.
  <https://arxiv.org/abs/2106.09462>
- Corpus de afinado: TASS 2020, Task 1 (polaridad a nivel de tweet en
  espanol). <http://tass.sepln.org/>

## 13. Advertencia final

> **La prediccion del modelo no equivale a la intencion real del autor.**
> La etiqueta del modelo es una prediccion estadistica sobre la superficie del texto. NO equivale a la intencion real del autor ni a su estado emocional.
>
> Cada etiqueta es una inferencia estadistica sobre la superficie del texto,
> producida por un clasificador entrenado en otro corpus, sin acceso al video
> comentado, al hilo de conversacion ni al contexto cultural del autor. Las
> distribuciones agregadas de este reporte son descripciones de lo que el
> modelo predijo sobre 406 comentarios
> recolectados, no una medicion del estado de animo de ninguna poblacion.
