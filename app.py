
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(
    page_title="Smart Trading SMC 2.0",
    page_icon="📊",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background-color: #071b14;
    color: white;
}
h1, h2, h3 {
    color: #35c98a !important;
}
[data-testid="stMetricValue"] {
    color: #35c98a;
}
</style>
""", unsafe_allow_html=True)

st.title("📊 SMART TRADING SMC 2.0")
st.caption("Gold XAUUSD | Analyse pédagogique SMC & Wyckoff")

st.sidebar.header("PARAMÈTRES")

instrument = "GOLD (XAUUSD)"

timeframe = st.sidebar.selectbox(
    "Unité de temps",
    ["H4", "H1", "M15", "M5"]
)

st.sidebar.success("Instrument : GOLD")

st.sidebar.info(
    "Importe les données OHLC de ton graphique "
    "pour effectuer une analyse."
)

uploaded = st.file_uploader(
    "Importer les données Gold (CSV)",
    type=["csv"]
)

def demo_data():
    np.random.seed(42)
    n = 250
    close = 2650 + np.cumsum(np.random.normal(0, 2, n))
    open_price = np.r_[close[0], close[:-1]]
    high = np.maximum(open_price, close) + np.random.uniform(0.2, 2, n)
    low = np.minimum(open_price, close) - np.random.uniform(0.2, 2, n)

    return pd.DataFrame({
        "datetime": pd.date_range(
            end=pd.Timestamp.now(),
            periods=n,
            freq="h"
        ),
        "open": open_price,
        "high": high,
        "low": low,
        "close": close,
        "volume": np.random.randint(100, 1000, n)
    })

if "demo" not in st.session_state:
    st.session_state.demo = False

if st.button("Charger des données de démonstration"):
    st.session_state.demo = True

if uploaded is not None:
    st.session_state.demo = False

df = None

if uploaded is not None:
    try:
        df = pd.read_csv(uploaded)
        df.columns = df.columns.str.lower().str.strip()

        if "datetime" not in df.columns:
            if "date" in df.columns:
                df = df.rename(columns={"date": "datetime"})
            elif "time" in df.columns:
                df = df.rename(columns={"time": "datetime"})

        required = [
            "datetime", "open", "high", "low", "close"
        ]

        if not all(c in df.columns for c in required):
            st.error("Colonnes requises : datetime, open, high, low, close")
            df = None
        else:
            df["datetime"] = pd.to_datetime(
                df["datetime"], errors="coerce"
            )
            for col in ["open", "high", "low", "close"]:
                df[col] = pd.to_numeric(
                    df[col], errors="coerce"
                )
            df = df.dropna(subset=required)
            df = df.sort_values("datetime").reset_index(drop=True)

    except Exception as e:
        st.error(f"Erreur de lecture du fichier : {e}")
        df = None

elif st.session_state.demo:
    df = demo_data()
    st.warning("Données fictives : démonstration uniquement.")

if df is not None:

    if len(df) < 15:
        st.error("Il faut au moins 15 chandeliers.")
        st.stop()

    st.divider()
    st.subheader("1. Graphique du Gold")

    df["EMA20"] = df["close"].ewm(span=20).mean()
    df["EMA50"] = df["close"].ewm(span=50).mean()

    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df["datetime"],
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"],
        increasing_line_color="#35c98a",
        decreasing_line_color="#d6a84b",
        name="Gold"
    ))

    fig.add_trace(go.Scatter(
        x=df["datetime"],
        y=df["EMA20"],
        name="EMA 20",
        line=dict(color="#35c98a", width=1)
    ))

    fig.add_trace(go.Scatter(
        x=df["datetime"],
        y=df["EMA50"],
        name="EMA 50",
        line=dict(color="#d6a84b", width=1)
    ))

    fig.update_layout(
        template="plotly_dark",
        height=500,
        xaxis_rangeslider_visible=False
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("2. Structure du marché")

    window = 5

    df["Swing_High"] = (
        df["high"] == df["high"].rolling(
            window * 2 + 1, center=True
        ).max()
    )

    df["Swing_Low"] = (
        df["low"] == df["low"].rolling(
            window * 2 + 1, center=True
        ).min()
    )

    highs = df.loc[df["Swing_High"], "high"]
    lows = df.loc[df["Swing_Low"], "low"]

    last = df.iloc[-1]

    if len(highs) > 0 and len(lows) > 0:
        resistance = highs.iloc[-1]
        support = lows.iloc[-1]

        st.metric("Dernier prix", f"{last['close']:.2f}")
        st.metric("Dernier sommet identifié", f"{resistance:.2f}")
        st.metric("Dernier creux identifié", f"{support:.2f}")

        if last["close"] > resistance:
            structure = "Cassure haussière possible (BOS)"
        elif last["close"] < support:
            structure = "Cassure baissière possible (BOS)"
        else:
            structure = "Prix entre les derniers swings"

        st.info(structure)
    else:
        support = df["low"].min()
        resistance = df["high"].max()
        st.info("Structure insuffisamment confirmée.")

    st.subheader("3. Détection indicative des FVG")

    fvg_list = []

    for i in range(2, len(df)):
        if df.iloc[i]["low"] > df.iloc[i-2]["high"]:
            fvg_list.append({
                "Type": "FVG haussier",
                "Bas": df.iloc[i-2]["high"],
                "Haut": df.iloc[i]["low"]
            })

        elif df.iloc[i]["high"] < df.iloc[i-2]["low"]:
            fvg_list.append({
                "Type": "FVG baissier",
                "Bas": df.iloc[i]["high"],
                "Haut": df.iloc[i-2]["low"]
            })

    if fvg_list:
        st.dataframe(
            pd.DataFrame(fvg_list[-10:]),
            use_container_width=True
        )
    else:
        st.write("Aucun FVG détecté.")

    st.subheader("4. Order Blocks indicatifs")

    ob_list = []

    for i in range(2, len(df)):
        previous = df.iloc[i-1]
        current = df.iloc[i]

        if current["close"] > previous["high"] and previous["close"] < previous["open"]:
            ob_list.append({
                "Type": "OB haussier potentiel",
                "Bas": previous["low"],
                "Haut": previous["open"]
            })

        elif current["close"] < previous["low"] and previous["close"] > previous["open"]:
            ob_list.append({
                "Type": "OB baissier potentiel",
                "Bas": previous["open"],
                "Haut": previous["high"]
            })

    if ob_list:
        st.dataframe(
            pd.DataFrame(ob_list[-10:]),
            use_container_width=True
        )
    else:
        st.write("Aucun OB potentiel détecté.")

    st.subheader("5. Analyse de liquidité")

    recent = df.tail(30)

    st.write(
        "Liquidité haute indicative :",
        round(recent["high"].max(), 2)
    )

    st.write(
        "Liquidité basse indicative :",
        round(recent["low"].min(), 2)
    )

    st.caption(
        "Les niveaux de liquidité sont des extrêmes récents, "
        "pas des preuves de présence d'ordres institutionnels."
    )

    st.subheader("6. Observations Wyckoff")

    spring = (
        (df["low"] < df["low"].shift(1)) &
        (df["close"] > df["low"].shift(1))
    )

    utad = (
        (df["high"] > df["high"].shift(1)) &
        (df["close"] < df["high"].shift(1))
    )

    col1, col2 = st.columns(2)

    with col1:
        st.write("Spring :")
        st.write(
            "Observation possible"
            if spring.iloc[-1]
            else "Non détecté sur la dernière bougie"
        )

    with col2:
        st.write("UTAD :")
        st.write(
            "Observation possible"
            if utad.iloc[-1]
            else "Non détecté sur la dernière bougie"
        )

    st.subheader("7. Synthèse multi-unités")

    st.write("Unité analysée :", timeframe)

    st.write("""
    Pour une analyse multi-unités complète :

    - H4 : structure générale.
    - H1 : zones de travail.
    - M15 : recherche de confirmations.
    - M5 : observation des réactions.
    """)

    st.subheader("8. Conclusion pédagogique")

    st.info("""
    Cette application identifie des configurations techniques
    indicatives. Elle ne confirme pas automatiquement une entrée.

    Une cassure doit être étudiée avec son contexte, la liquidité,
    la clôture des bougies et la réaction du prix.

    Les données importées doivent correspondre à l'unité de temps
    sélectionnée.
    """)

else:
    st.info(
        "Bienvenue dans Smart Trading SMC 2.0. "
        "Importe un fichier CSV ou charge les données de démonstration."
    )

st.divider()
st.caption("SMART TRADING SMC 2.0 | Outil pédagogique d'analyse")
