import json
import os
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from huggingface_hub import hf_hub_download

st.set_page_config(
    page_title="OR-TXCORE | FraudShield",
    page_icon="🛡️",
    layout="wide"
)

MODEL_DIR = Path("models/credit-card-fraud")
V_COLS = [f"V{i}" for i in range(1, 29)]
INPUT_COLS = ["Time", *V_COLS, "Amount"]


@st.cache_resource
def carregar_modelo():
    config = json.loads(
        (MODEL_DIR / "config.json").read_text()
    )
    model = joblib.load(MODEL_DIR / "model.joblib")
    scaler = joblib.load(MODEL_DIR / "scaler.joblib")
    threshold = config["models"][config["best"]]["threshold"]
    return model, scaler, float(threshold)


@st.cache_data
def carregar_amostra():
    arquivo = hf_hub_download(
        repo_id="shalev396/credit-card-fraud",
        filename="examples/mixed_transactions.csv",
        repo_type="space"
    )
    return pd.read_csv(arquivo)


st.title("🛡️ OR-TXCORE | FraudShield")
st.caption(
    "Laboratório local de Machine Learning, "
    "análise de risco e eventos transacionais"
)

@st.cache_data(ttl=10)
def obter_saude_servicos():
    """A card is explicitly synthetic if an API is unavailable."""
    base = os.getenv("PAYMENT_CORE_URL", "http://127.0.0.1:8000")
    try:
        with urlopen(f"{base}/healthz", timeout=1) as response:
            return {"payment-core": "ONLINE" if response.status == 200 else "DEGRADED"}, False
    except (URLError, OSError):
        return {"payment-core": "SIMULATED/OFFLINE"}, True

statuses, simulated = obter_saude_servicos()
with st.sidebar:
    st.subheader("Serviços")
    for name, state in statuses.items(): st.write(f"{name}: {state}")
    if simulated: st.caption("Status sintético: API local indisponível.")

tab1, tab2 = st.tabs([
    "Inteligência Antifraude",
    "Simulador de Eventos"
])

with tab1:
    try:
        modelo, scaler, limite_padrao = carregar_modelo()
    except Exception as erro:
        st.error(f"Erro ao carregar o modelo: {erro}")
        st.stop()

    st.success("Modelo Hugging Face carregado")

    arquivo = st.file_uploader(
        "Enviar CSV de transações no formato ULB",
        type=["csv"]
    )

    dados = None

    if arquivo is not None:
        dados = pd.read_csv(arquivo)
    else:
        try:
            dados = carregar_amostra()
            st.info("Exibindo amostra pública do modelo.")
        except Exception as erro:
            st.warning(
                "Não foi possível baixar a amostra: "
                f"{erro}. Envie um CSV para testar."
            )

    limite = st.slider(
        "Limiar para sinalizar revisão",
        min_value=0.01,
        max_value=1.0,
        value=limite_padrao,
        step=0.01
    )

    if dados is not None:
        dados = dados.head(10000).copy()

        faltantes = [
            c for c in INPUT_COLS
            if c not in dados.columns
        ]

        if faltantes:
            st.error(f"Colunas ausentes: {faltantes}")
            st.stop()

        entradas = dados[INPUT_COLS].apply(
            pd.to_numeric, errors="coerce"
        )

        if entradas.isna().any().any():
            st.error("O CSV possui entradas inválidas.")
            st.stop()

        valores_escalados = scaler.transform(
            entradas[["Amount", "Time"]]
        )

        features = np.hstack([
            entradas[V_COLS].to_numpy(),
            valores_escalados
        ]).astype(np.float32)

        scores = modelo.predict_proba(features)[:, 1]
        sinalizadas = scores >= limite

        resultados = pd.DataFrame({
            "Tempo": entradas["Time"].to_numpy(),
            "Valor": entradas["Amount"].to_numpy(),
            "Score": scores,
            "Decisão": np.where(
                sinalizadas, "REVIEW", "ALLOW"
            )
        })

        c1, c2, c3 = st.columns(3)

        c1.metric("Transações analisadas", len(scores))
        c2.metric("Sinalizadas", int(sinalizadas.sum()))
        c3.metric(
            "Taxa sinalizada",
            f"{sinalizadas.mean() * 100:.2f}%"
        )

        st.subheader("Distribuição dos scores — Matplotlib")

        fig, ax = plt.subplots(figsize=(10, 4))
        ax.hist(scores, bins=20, edgecolor="black")
        ax.axvline(
            limite,
            linestyle="--",
            label=f"Limiar: {limite:.2f}"
        )
        ax.set_xlabel("Score do modelo (0–1)")
        ax.set_ylabel("Quantidade")
        ax.legend()
        st.pyplot(fig)
        plt.close(fig)

        st.subheader("Transações e risco — Plotly")

        grafico = px.scatter(
            resultados,
            x="Valor",
            y="Score",
            color="Decisão",
            hover_data=["Tempo"],
            title="Score do modelo por valor"
        )
        grafico.add_hline(
            y=limite, line_dash="dash"
        )
        st.plotly_chart(
            grafico, use_container_width=True
        )

        st.subheader("Resultado das análises")
        st.dataframe(
            resultados.round(4),
            use_container_width=True
        )

        st.download_button(
            "Exportar análises CSV",
            resultados.to_csv(index=False),
            file_name="fraudshield_resultados.csv",
            mime="text/csv"
        )

    st.caption(
        "Scores não calibrados. REVIEW significa apenas "
        "sinalização experimental, não fraude confirmada."
    )

with tab2:
    st.subheader("Simulação de tráfego por eventos")

    taxa = st.slider(
        "Média de eventos sintéticos por segundo",
        5, 500, 100
    )

    rng = np.random.default_rng(42)
    segundos = np.arange(60)
    eventos = rng.poisson(taxa, size=60)

    simulacao = pd.DataFrame({
        "Segundo": segundos,
        "Eventos": eventos
    })

    c1, c2 = st.columns(2)
    c1.metric("Eventos simulados", int(eventos.sum()))
    c2.metric(
        "Média de eventos/s",
        f"{eventos.mean():.1f}"
    )

    grafico = px.line(
        simulacao,
        x="Segundo",
        y="Eventos",
        markers=True,
        title="Fluxo sintético de eventos"
    )
    st.plotly_chart(
        grafico, use_container_width=True
    )

    st.warning(
        "Os eventos são gerados estatisticamente. "
        "Isto não é um benchmark real do motor de pagamentos."
    )
