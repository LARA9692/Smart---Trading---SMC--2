import streamlit as st

st.set_page_config(
    page_title="Smart Trading SMC 2.0",
    page_icon="📊",
    layout="wide"
)

st.title("📊 SMART TRADING SMC 2.0")

st.write("Assistant intelligent d'analyse technique")

st.sidebar.header("Paramètres du marché")

instrument = st.sidebar.selectbox(
    "Instrument",
    ["Gold", "Volatility 75", "Volatility 30",
     "Volatility 10", "BTC", "Autre"]
)

timeframe = st.sidebar.selectbox(
    "Unité de temps",
    ["D1", "H4", "H1", "M15", "M5"]
)

st.subheader("Analyse du marché")

st.write("Instrument sélectionné :", instrument)
st.write("Unité de temps :", timeframe)

st.info("Bienvenue dans Smart Trading SMC 2.0")
