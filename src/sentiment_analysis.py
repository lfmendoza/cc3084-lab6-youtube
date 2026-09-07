"""Ejercicio 9.1-9.2: analisis de sentimiento en espanol.

Modelo principal
----------------
``pysentimiento/robertuito-sentiment-analysis``: RoBERTuito (Perez et al.,
2022), un RoBERTa preentrenado desde cero sobre ~500 M de tweets en espanol
y afinado para polaridad con el corpus TASS 2020. Se eligio por tres
razones concretas:

1. **Es un modelo de espanol, no multilingue.** Su vocabulario y su
   preentrenamiento son de espanol, de modo que no compite por capacidad con
   otras 100 lenguas como en un mBERT o XLM-R.
2. **Su dominio de preentrenamiento es texto informal de redes sociales.**
   Los comentarios de YouTube comparten con los tweets la longitud corta, los
   emojis, la ortografia libre y las mayusculas expresivas. Un modelo
   entrenado en resenas o en noticias sufriria un salto de dominio mayor.
3. **Devuelve tres clases interpretables (NEG/NEU/POS)** con probabilidades,
   lo que permite reportar distribucion y confianza sin inventar un umbral.

Se descarta explicitamente TextBlob y VADER como solucion principal: sus
lexicos son de ingles y aplicarlos a texto espanol produciria mayormente
neutro por vocabulario fuera de diccionario, no una medicion.

Entrada del modelo
------------------
Se usa ``texto_original`` (no ``texto_limpio``), preprocesado con la
normalizacion que el modelo vio en entrenamiento: menciones a ``@usuario``,
URL a ``url``, emojis traducidos a su descripcion en espanol y repeticiones
acortadas. Las mayusculas, la puntuacion, las negaciones y los emojis se
conservan porque son senal de polaridad; ``texto_limpio`` los destruye y se
reserva para el analisis tematico.
"""
from __future__ import annotations

import json
import platform
import time
from datetime import datetime, timezone

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from . import config as C
from . import viz

LABEL_MEANING = {
    "NEG": "polaridad negativa (critica, queja, rechazo, insulto)",
    "NEU": "polaridad neutra (informativo, pregunta, sin carga afectiva clara)",
    "POS": "polaridad positiva (aprobacion, agradecimiento, elogio, apoyo)",
}
LABEL_ORDER = ["NEG", "NEU", "POS"]


def load_model():
    """Carga tokenizer y modelo, y devuelve tambien sus metadatos exactos."""
    import torch
    import transformers
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(C.SENTIMENT_MODEL_ID)
    model = AutoModelForSequenceClassification.from_pretrained(C.SENTIMENT_MODEL_ID)
    model.eval()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)
    meta = {
        "model_id": C.SENTIMENT_MODEL_ID,
        "framework": "PyTorch via HuggingFace transformers",
        "transformers_version": transformers.__version__,
        "torch_version": torch.__version__,
        "tokenizer_class": type(tok).__name__,
        "tokenizer_vocab_size": int(tok.vocab_size),
        "model_class": type(model).__name__,
        "arquitectura": model.config.architectures,
        "model_type": model.config.model_type,
        "n_parametros": int(sum(p.numel() for p in model.parameters())),
        "n_capas": int(getattr(model.config, "num_hidden_layers", -1)),
        "hidden_size": int(getattr(model.config, "hidden_size", -1)),
        "id2label": {int(k): v for k, v in model.config.id2label.items()},
        "clases": [model.config.id2label[i] for i in sorted(model.config.id2label)],
        "max_length_usado": C.SENTIMENT_MAX_LEN,
        "model_max_length_tokenizer": int(tok.model_max_length),
        "truncation": True,
        "padding": "longest por lote",
        "batch_size": C.SENTIMENT_BATCH_SIZE,
        "device": device,
        "cuda_disponible": bool(torch.cuda.is_available()),
        "plataforma": f"{platform.system()} {platform.release()} ({platform.machine()})",
        "python": platform.python_version(),
        "seed": C.SEED,
        "modo": "inferencia con torch.no_grad(), model.eval()",
        "determinismo": (
            "La inferencia es determinista: no hay dropout activo ni muestreo. "
            "La semilla se fija de todos modos para que cualquier operacion "
            "estocastica futura sea reproducible."
        ),
        "fecha_ejecucion_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    return tok, model, device, meta


def predict(texts: list[str], tok, model, device) -> tuple[list[str], np.ndarray]:
    import torch

    probs_all = []
    for i in range(0, len(texts), C.SENTIMENT_BATCH_SIZE):
        batch = texts[i:i + C.SENTIMENT_BATCH_SIZE]
        enc = tok(batch, return_tensors="pt", padding=True, truncation=True,
                  max_length=C.SENTIMENT_MAX_LEN)
        enc = {k: v.to(device) for k, v in enc.items()}
        with torch.no_grad():
            logits = model(**enc).logits
        probs_all.append(torch.softmax(logits, dim=-1).cpu().numpy())
    probs = np.vstack(probs_all)
    id2label = model.config.id2label
    labels = [id2label[int(i)] for i in probs.argmax(axis=1)]
    return labels, probs


def group_comparison(df: pd.DataFrame, by: str, label: str,
                     min_n: int = 10) -> pd.DataFrame:
    """Distribucion de sentimiento por grupo, con el n de cada grupo visible.

    ``min_n`` no elimina grupos: los marca. Un grupo con n<10 se reporta pero
    se senala como no comparable, porque un porcentaje sobre 3 comentarios no
    es una estimacion utilizable.
    """
    rows = []
    for key, g in df.groupby(by, dropna=False):
        counts = g["predicted_label"].value_counts()
        row = {
            "agrupacion": label,
            "grupo": key,
            "n": int(len(g)),
            "comparable_n_mayor_igual_10": bool(len(g) >= min_n),
        }
        for lab in LABEL_ORDER:
            row[f"n_{lab}"] = int(counts.get(lab, 0))
            row[f"pct_{lab}"] = round(100 * float(counts.get(lab, 0)) / len(g), 2)
        row["confianza_media"] = round(float(g["confidence"].mean()), 4)
        row["confianza_mediana"] = round(float(g["confidence"].median()), 4)
        # Indice de polaridad neta: (%POS - %NEG) en [-100, 100].
        row["polaridad_neta"] = round(row["pct_POS"] - row["pct_NEG"], 2)
        row["etiqueta_mayoritaria"] = counts.idxmax() if len(counts) else ""
        rows.append(row)
    out = pd.DataFrame(rows).sort_values("n", ascending=False)
    return out


def chi2_test(df: pd.DataFrame, by: str, min_n: int = 10) -> dict:
    """Prueba chi-cuadrado de independencia entre grupo y clase de sentimiento.

    Se limita a los grupos con n >= ``min_n`` para que las frecuencias
    esperadas no sean demasiado pequenas, y se reporta cuantas celdas quedan
    con esperado < 5, que es la condicion de validez de la aproximacion.
    """
    from scipy import stats

    sizes = df.groupby(by).size()
    keep = sizes[sizes >= min_n].index
    sub = df[df[by].isin(keep)]
    if sub[by].nunique() < 2:
        return {"aplicable": False,
                "razon": f"menos de 2 grupos con n >= {min_n}",
                "grupos_con_n_suficiente": int(len(keep))}
    table = pd.crosstab(sub[by], sub["predicted_label"])
    chi2, p, dof, expected = stats.chi2_contingency(table)
    n = table.to_numpy().sum()
    k = min(table.shape)
    return {
        "aplicable": True,
        "agrupacion": by,
        "grupos_incluidos": int(table.shape[0]),
        "grupos_excluidos_por_n_bajo": int(sizes.shape[0] - table.shape[0]),
        "n_incluido": int(n),
        "chi2": round(float(chi2), 4),
        "gl": int(dof),
        "p_valor": round(float(p), 5),
        "significativo_0.05": bool(p < 0.05),
        "v_de_cramer": round(float(np.sqrt(chi2 / (n * (k - 1)))), 4) if k > 1 else np.nan,
        "celdas_con_esperado_menor_5": int((expected < 5).sum()),
        "n_celdas": int(expected.size),
        "advertencia_validez": (
            "Parte de las frecuencias esperadas es menor que 5, por lo que el "
            "valor p es aproximado."
            if (expected < 5).any() else
            "Todas las frecuencias esperadas son >= 5."
        ),
        "tabla_observada": table.to_dict(),
    }


def representative_examples(df: pd.DataFrame, n_per_class: int = 4) -> dict:
    """Ejemplos por clase SIN cherry-picking.

    Para cada clase se toman ejemplos en tres posiciones fijas de la
    distribucion de confianza (el mas confiado, la mediana y el menos
    confiado) mas los casos ambiguos globales. El criterio es posicional y
    reproducible, de modo que no se seleccionan a mano los comentarios que
    mejor quedan.
    """
    out: dict = {"criterio": (
        "Para cada clase se muestran el caso de mayor confianza, el caso de "
        "confianza mediana y el de menor confianza. Es una seleccion "
        "posicional y reproducible, no una eleccion manual de los ejemplos "
        "mas favorables."
    )}
    cols = ["comment_id", "video_title", "predicted_label", "confidence",
            "prob_NEG", "prob_NEU", "prob_POS", "texto_original"]
    for lab in LABEL_ORDER:
        g = df[df.predicted_label == lab].sort_values("confidence", ascending=False)
        if g.empty:
            out[lab] = []
            continue
        idx = [0, len(g) // 2, len(g) - 1][:min(3, len(g))]
        picks = g.iloc[sorted(set(idx))].copy()
        picks["posicion_en_confianza"] = [
            "maxima", "mediana", "minima"][:len(picks)]
        out[lab] = picks[cols + ["posicion_en_confianza"]].to_dict("records")
    amb = df.nsmallest(6, "confidence")
    out["casos_ambiguos_global"] = amb[cols].to_dict("records")
    out["margen_bajo"] = df[df.margen < 0.20][cols + ["margen"]].head(8).to_dict("records")
    return out


# ==================================================================== figuras
def make_figures(df: pd.DataFrame, by_video: pd.DataFrame, by_channel: pd.DataFrame,
                 by_community: pd.DataFrame, by_category: pd.DataFrame,
                 metrics: dict) -> None:
    viz.apply_style()
    counts = df["predicted_label"].value_counts().reindex(LABEL_ORDER).fillna(0)

    # --- distribucion global + confianza ---
    fig, axes = plt.subplots(1, 3, figsize=(15.5, 4.9))
    bars = axes[0].bar(LABEL_ORDER, counts.values,
                       color=[viz.SENTIMENT_COLORS[x] for x in LABEL_ORDER],
                       edgecolor="white")
    for b, v in zip(bars, counts.values):
        axes[0].text(b.get_x() + b.get_width() / 2, v + 4,
                     f"{int(v)}\n({100*v/len(df):.1f}%)", ha="center", fontsize=9)
    axes[0].set_ylabel("Numero de comentarios")
    axes[0].set_xlabel("Clase predicha")
    axes[0].set_ylim(0, counts.max() * 1.24)
    axes[0].set_title(f"Distribucion de clases (n={len(df)})")

    for lab in LABEL_ORDER:
        sub = df[df.predicted_label == lab]["confidence"]
        axes[1].hist(sub, bins=22, alpha=0.62, label=f"{lab} (n={len(sub)})",
                     color=viz.SENTIMENT_COLORS[lab], edgecolor="white")
    axes[1].set_xlabel("Confianza = probabilidad de la clase predicha")
    axes[1].set_ylabel("Numero de comentarios")
    axes[1].axvline(df["confidence"].median(), color="black", ls="--",
                    label=f"mediana global = {df.confidence.median():.3f}")
    axes[1].set_title("Confianza por clase\n(confianza NO es polaridad)")
    axes[1].legend(fontsize=8)

    axes[2].scatter(df["prob_NEG"], df["prob_POS"], s=22, alpha=0.6,
                    c=[viz.SENTIMENT_COLORS[x] for x in df["predicted_label"]],
                    edgecolors="black", linewidths=0.25)
    axes[2].plot([0, 1], [1, 0], "--", color="#B0B0B0", lw=1)
    axes[2].set_xlabel("P(NEG)"); axes[2].set_ylabel("P(POS)")
    axes[2].set_title("Espacio de probabilidades\n(la diagonal es indecision NEG/POS)")
    axes[2].set_xlim(-0.02, 1.02); axes[2].set_ylim(-0.02, 1.02)
    fig.suptitle("Figura 26. Sentimiento de los comentarios: distribucion y confianza",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    viz.save(fig, "24_sentiment_distribution.png",
             f"El {metrics['pct_por_clase']['NEG']}% de los comentarios se clasifica como "
             f"negativo, {metrics['pct_por_clase']['NEU']}% neutro y "
             f"{metrics['pct_por_clase']['POS']}% positivo. La confianza mediana es "
             f"{metrics['confianza_mediana']}, y {metrics['pct_confianza_menor_0.5']}% de las "
             "predicciones tiene confianza < 0.5, casos que deben leerse como indecision del "
             "modelo y no como neutralidad del autor.")

    # --- por video y por canal ---
    fig, axes = plt.subplots(1, 2, figsize=(15.5, 6.4))
    for ax, tab, title, labcol in [
        (axes[0], by_video.nlargest(12, "n"), "Por video (12 con mas comentarios)", "grupo_label"),
        (axes[1], by_channel.nlargest(8, "n"), "Por canal", "grupo_label"),
    ]:
        y = np.arange(len(tab))
        left = np.zeros(len(tab))
        for lab in LABEL_ORDER:
            ax.barh(y, tab[f"pct_{lab}"], left=left, color=viz.SENTIMENT_COLORS[lab],
                    label=lab, edgecolor="white", height=0.72)
            left += tab[f"pct_{lab}"].to_numpy()
        ax.set_yticks(y)
        ax.set_yticklabels([f"{viz.wrap(t, 34)}\n(n={n})"
                            for t, n in zip(tab[labcol], tab["n"])], fontsize=7)
        ax.invert_yaxis()
        ax.set_xlabel("% de comentarios del grupo")
        ax.set_xlim(0, 100)
        ax.set_title(title)
        ax.legend(loc="lower right", fontsize=8, ncol=3)
    fig.suptitle("Figura 27. Composicion de sentimiento por video y por canal",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    ch = metrics["chi2_por_canal"]
    viz.save(fig, "25_sentiment_by_video_channel.png",
             f"El n de cada grupo aparece en su etiqueta: los grupos pequenos no son "
             f"comparables. Restringido a canales con n>=10, la prueba chi-cuadrado da "
             f"chi2={ch.get('chi2')} (gl={ch.get('gl')}, p={ch.get('p_valor')}), "
             f"{'significativa' if ch.get('significativo_0.05') else 'no significativa'} al 5%: "
             f"V de Cramer = {ch.get('v_de_cramer')}.")

    # --- por comunidad ---
    if len(by_community):
        tab = by_community.sort_values("n", ascending=False)
        fig, axes = plt.subplots(1, 2, figsize=(15, 5.4))
        y = np.arange(len(tab))
        left = np.zeros(len(tab))
        for lab in LABEL_ORDER:
            axes[0].barh(y, tab[f"pct_{lab}"], left=left,
                         color=viz.SENTIMENT_COLORS[lab], label=lab,
                         edgecolor="white", height=0.7)
            left += tab[f"pct_{lab}"].to_numpy()
        axes[0].set_yticks(y)
        axes[0].set_yticklabels([f"{g} (n={n})" for g, n in zip(tab["grupo_label"], tab["n"])],
                                fontsize=8)
        axes[0].invert_yaxis()
        axes[0].set_xlabel("% de comentarios de la comunidad")
        axes[0].set_xlim(0, 100)
        axes[0].set_title("Composicion de sentimiento por comunidad")
        axes[0].legend(loc="lower right", fontsize=8, ncol=3)

        colors = ["#D55E00" if v < 0 else "#009E73" for v in tab["polaridad_neta"]]
        axes[1].barh(y, tab["polaridad_neta"], color=colors, edgecolor="white")
        axes[1].set_yticks(y)
        axes[1].set_yticklabels([f"{g} (n={n})" for g, n in zip(tab["grupo_label"], tab["n"])],
                                fontsize=8)
        axes[1].invert_yaxis()
        axes[1].axvline(0, color="black", lw=1)
        axes[1].set_xlabel("Polaridad neta = %POS - %NEG (puntos porcentuales)")
        axes[1].set_title("Polaridad neta por comunidad")
        for yi, v in zip(y, tab["polaridad_neta"]):
            axes[1].text(v + (2 if v >= 0 else -2), yi, f"{v:+.1f}", va="center",
                         ha="left" if v >= 0 else "right", fontsize=8)
        fig.suptitle("Figura 28. Sentimiento por comunidad de la proyeccion video-video",
                     fontsize=13, fontweight="bold")
        fig.tight_layout()
        cc = metrics["chi2_por_comunidad"]
        viz.save(fig, "26_sentiment_by_community.png",
                 "Las comunidades difieren en polaridad neta, pero la comparacion formal solo "
                 f"incluye las de n>=10. Chi-cuadrado: "
                 f"{'chi2=' + str(cc.get('chi2')) + ', p=' + str(cc.get('p_valor')) if cc.get('aplicable') else 'no aplicable (' + str(cc.get('razon')) + ')'}. "
                 "La direccion del signo es el hallazgo interpretable; su magnitud exacta "
                 "depende de muestras pequenas.")

    # --- sentimiento vs metricas de interaccion ---
    fig, axes = plt.subplots(1, 3, figsize=(15.5, 4.7))
    data = [df[df.predicted_label == lab]["like_count"] for lab in LABEL_ORDER]
    bp = axes[0].boxplot(data, tick_labels=LABEL_ORDER, patch_artist=True,
                         medianprops=dict(color="black", lw=1.6))
    for patch, lab in zip(bp["boxes"], LABEL_ORDER):
        patch.set_facecolor(viz.SENTIMENT_COLORS[lab]); patch.set_alpha(0.65)
    axes[0].set_yscale("symlog")
    axes[0].set_ylabel("'Me gusta' (escala symlog)")
    axes[0].set_title("'Me gusta' por clase de sentimiento")

    data = [df[df.predicted_label == lab]["len_original"] for lab in LABEL_ORDER]
    bp = axes[1].boxplot(data, tick_labels=LABEL_ORDER, patch_artist=True,
                         medianprops=dict(color="black", lw=1.6))
    for patch, lab in zip(bp["boxes"], LABEL_ORDER):
        patch.set_facecolor(viz.SENTIMENT_COLORS[lab]); patch.set_alpha(0.65)
    axes[1].set_ylabel("Longitud del comentario (caracteres)")
    axes[1].set_title("Longitud por clase de sentimiento")

    emo = df.groupby("predicted_label").agg(
        pct_con_emoji=("n_emojis", lambda s: 100 * float((s > 0).mean())),
        pct_con_respuesta=("reply_count_num", lambda s: 100 * float((s > 0).mean())),
    ).reindex(LABEL_ORDER)
    x = np.arange(len(LABEL_ORDER))
    axes[2].bar(x - 0.2, emo["pct_con_emoji"], 0.4, label="% con al menos un emoji",
                color="#0072B2")
    axes[2].bar(x + 0.2, emo["pct_con_respuesta"], 0.4, label="% que recibio respuesta",
                color="#CC79A7")
    axes[2].set_xticks(x); axes[2].set_xticklabels(LABEL_ORDER)
    axes[2].set_ylabel("% de comentarios de la clase")
    axes[2].set_title("Emojis y respuestas por clase")
    axes[2].legend(fontsize=8)
    for i, (a, b) in enumerate(zip(emo["pct_con_emoji"], emo["pct_con_respuesta"])):
        axes[2].text(i - 0.2, a + 0.6, f"{a:.1f}", ha="center", fontsize=8)
        axes[2].text(i + 0.2, b + 0.6, f"{b:.1f}", ha="center", fontsize=8)
    fig.suptitle("Figura 29. Sentimiento frente a metricas de interaccion observadas",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    viz.save(fig, "27_sentiment_vs_engagement.png",
             f"Los comentarios negativos tienen una mediana de "
             f"{metrics['me_gusta_mediana_por_clase']['NEG']} 'me gusta' frente a "
             f"{metrics['me_gusta_mediana_por_clase']['POS']} de los positivos. "
             "Es una asociacion descriptiva sobre conteos parciales al momento de la "
             "recoleccion, no evidencia de que la negatividad genere aprobacion.")


# =================================================================== pipeline
def run() -> dict:
    C.set_seeds()
    print("[4/6] sentiment_analysis: inferencia en espanol con RoBERTuito")
    comments = pd.read_csv(
        C.COMMENTS_CLEAN,
        dtype={"video_id": str, "comment_id": str, "channel_id": str,
               "author_channel_id": str},
        keep_default_na=False, na_values=[""])
    comments["texto_original"] = comments["texto_original"].fillna("")
    comments["texto_sentimiento"] = comments["texto_sentimiento"].fillna("")
    for col in ("like_count", "reply_count_num", "len_original", "n_emojis"):
        comments[col] = pd.to_numeric(comments[col], errors="coerce")

    tok, model, device, meta = load_model()
    t0 = time.perf_counter()
    labels, probs = predict(comments["texto_sentimiento"].tolist(), tok, model, device)
    elapsed = time.perf_counter() - t0
    meta["segundos_de_inferencia"] = round(elapsed, 2)
    meta["comentarios_por_segundo"] = round(len(comments) / elapsed, 1)

    classes = [model.config.id2label[i] for i in sorted(model.config.id2label)]
    pred = comments[[
        "comment_id", "video_id", "video_title", "channel_id", "channel_name",
        "author_channel_id", "author_handle_norm", "texto_original", "texto_sentimiento",
        "texto_limpio", "like_count", "reply_count_num", "len_original", "n_emojis",
        "source_query", "source_group",
    ]].copy()
    pred["predicted_label"] = labels
    for i, cls in enumerate(classes):
        pred[f"prob_{cls}"] = probs[:, i].round(6)
    pred["confidence"] = probs.max(axis=1).round(6)
    ordered = np.sort(probs, axis=1)
    pred["margen"] = (ordered[:, -1] - ordered[:, -2]).round(6)
    pred["entropia"] = (-(probs * np.log(probs + 1e-12)).sum(axis=1)).round(6)
    pred["significado_label"] = pred["predicted_label"].map(LABEL_MEANING)
    pred["prediccion_de_baja_confianza"] = pred["confidence"] < 0.5
    pred["modelo"] = C.SENTIMENT_MODEL_ID

    assert len(pred) == len(comments), "faltan predicciones"
    assert pred["predicted_label"].notna().all(), "hay etiquetas nulas"
    pred.to_csv(C.TABLES / "sentiment_predictions.csv", index=False)

    # --- resumenes y comparaciones ---
    counts = pred["predicted_label"].value_counts().reindex(LABEL_ORDER).fillna(0).astype(int)
    metrics = {
        "modelo": meta,
        "n_comentarios_evaluados": int(len(pred)),
        "n_comentarios_totales": int(len(comments)),
        "cobertura_pct": round(100 * len(pred) / len(comments), 2),
        "clases": classes,
        "significado_clases": LABEL_MEANING,
        "conteo_por_clase": counts.to_dict(),
        "pct_por_clase": {k: round(100 * v / len(pred), 2) for k, v in counts.items()},
        "clase_mayoritaria": counts.idxmax(),
        "confianza_media": round(float(pred.confidence.mean()), 4),
        "confianza_mediana": round(float(pred.confidence.median()), 4),
        "confianza_p25": round(float(pred.confidence.quantile(0.25)), 4),
        "confianza_p75": round(float(pred.confidence.quantile(0.75)), 4),
        "confianza_min": round(float(pred.confidence.min()), 4),
        "confianza_media_por_clase": pred.groupby("predicted_label").confidence.mean()
            .round(4).to_dict(),
        "confianza_mediana_por_clase": pred.groupby("predicted_label").confidence.median()
            .round(4).to_dict(),
        "n_confianza_menor_0.5": int((pred.confidence < 0.5).sum()),
        "pct_confianza_menor_0.5": round(100 * float((pred.confidence < 0.5).mean()), 2),
        "n_margen_menor_0.2": int((pred.margen < 0.2).sum()),
        "pct_margen_menor_0.2": round(100 * float((pred.margen < 0.2).mean()), 2),
        "entropia_media": round(float(pred.entropia.mean()), 4),
        "polaridad_neta_global": round(
            100 * float((pred.predicted_label == "POS").mean() -
                        (pred.predicted_label == "NEG").mean()), 2),
        "me_gusta_mediana_por_clase": pred.groupby("predicted_label").like_count.median()
            .to_dict(),
        "me_gusta_medio_por_clase": pred.groupby("predicted_label").like_count.mean()
            .round(2).to_dict(),
        "longitud_mediana_por_clase": pred.groupby("predicted_label").len_original.median()
            .to_dict(),
        "pct_con_emoji_por_clase": pred.groupby("predicted_label").n_emojis
            .apply(lambda s: round(100 * float((s > 0).mean()), 2)).to_dict(),
        "advertencia_confianza": (
            "La confianza es la probabilidad de la clase mas probable, no una "
            "medida de intensidad de polaridad. Una prediccion NEG con "
            "confianza 0.95 no es 'mas negativa' que una con 0.60: es una "
            "clasificacion mas segura."
        ),
        "advertencia_intencion": (
            "La etiqueta del modelo es una prediccion estadistica sobre la "
            "superficie del texto. NO equivale a la intencion real del autor "
            "ni a su estado emocional."
        ),
    }

    # --- comparaciones por grupo ---
    part = json.loads((C.NETWORKS / "video_partition.json").read_text(encoding="utf-8"))
    video_to_comm = {v: k for k, vs in part.items() for v in vs}
    pred["comunidad"] = pred["video_id"].map(video_to_comm)
    videos = pd.read_csv(C.VIDEOS_CLEAN, dtype={"video_id": str})
    pred["category"] = pred["video_id"].map(videos.set_index("video_id")["category"])

    by_video = group_comparison(pred, "video_id", "video")
    by_video["grupo_label"] = by_video["grupo"].map(
        pred.drop_duplicates("video_id").set_index("video_id")["video_title"])
    by_channel = group_comparison(pred, "channel_id", "canal")
    by_channel["grupo_label"] = by_channel["grupo"].map(
        pred.drop_duplicates("channel_id").set_index("channel_id")["channel_name"])
    by_community = group_comparison(pred, "comunidad", "comunidad")
    by_community["grupo_label"] = by_community["grupo"]
    by_category = group_comparison(pred, "category", "categoria")
    by_category["grupo_label"] = by_category["grupo"]
    by_query = group_comparison(pred, "source_query", "consulta de recoleccion")
    by_query["grupo_label"] = by_query["grupo"]

    summary = pd.concat([by_video, by_channel, by_community, by_category, by_query],
                        ignore_index=True)
    summary.to_csv(C.TABLES / "sentiment_summary.csv", index=False)
    pd.DataFrame([{"clase": k, "n": v,
                   "pct": metrics["pct_por_clase"][k],
                   "significado": LABEL_MEANING[k],
                   "confianza_media": metrics["confianza_media_por_clase"].get(k),
                   "confianza_mediana": metrics["confianza_mediana_por_clase"].get(k)}
                  for k, v in counts.items()]).to_csv(
        C.TABLES / "sentiment_global_distribution.csv", index=False)

    metrics["chi2_por_canal"] = chi2_test(pred, "channel_id")
    metrics["chi2_por_video"] = chi2_test(pred, "video_id")
    metrics["chi2_por_comunidad"] = chi2_test(pred, "comunidad")
    metrics["chi2_por_categoria"] = chi2_test(pred, "category")
    metrics["comparacion_por_video"] = by_video.to_dict("records")
    metrics["comparacion_por_canal"] = by_channel.to_dict("records")
    metrics["comparacion_por_comunidad"] = by_community.to_dict("records")
    metrics["comparacion_por_categoria"] = by_category.to_dict("records")
    metrics["comparacion_por_consulta"] = by_query.to_dict("records")
    metrics["grupos_comparables"] = {
        "videos_con_n_mayor_igual_10": int(by_video.comparable_n_mayor_igual_10.sum()),
        "videos_totales": int(len(by_video)),
        "canales_con_n_mayor_igual_10": int(by_channel.comparable_n_mayor_igual_10.sum()),
        "canales_totales": int(len(by_channel)),
        "comunidades_con_n_mayor_igual_10": int(by_community.comparable_n_mayor_igual_10.sum()),
        "comunidades_totales": int(len(by_community)),
    }
    metrics["ejemplos"] = representative_examples(pred)

    make_figures(pred, by_video, by_channel, by_community, by_category, metrics)
    C.write_metrics("sentiment", metrics)

    print(f"      {len(pred)} comentarios clasificados en {elapsed:.1f}s ({device}) | "
          f"NEG {metrics['pct_por_clase']['NEG']}% / "
          f"NEU {metrics['pct_por_clase']['NEU']}% / "
          f"POS {metrics['pct_por_clase']['POS']}%")
    return {"predictions": pred, "metrics": metrics, "by_video": by_video,
            "by_channel": by_channel, "by_community": by_community}


if __name__ == "__main__":
    run()
