import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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
st.caption("GOLD XAUUSD | Analyse pédagogique SMC & Wyckoff")

st.sidebar.header("PARAMÈTRES")

timeframes = ["H4", "H1", "M15", "M5"]

selected_tf = st.sidebar.selectbox(
    "Unité à afficher",
    timeframes
)

st.sidebar.success("Instrument : GOLD XAUUSD")

st.info(
    "Importe un fichier CSV distinct pour chaque unité de temps. "
    "Tu peux aussi commencer avec une seule unité."
)

# IMPORTATION DES DONNÉES

uploaded_files = {}

st.subheader("1. Importation des données OHLC")

col1, col2 = st.columns(2)

with col1:
    uploaded_files["H4"] = st.file_uploader(
        "Importer les données H4",
        type=["csv"],
        key="file_h4"
    )

    uploaded_files["H1"] = st.file_uploader(
        "Importer les données H1",
        type=["csv"],
        key="file_h1"
    )

with col2:
    uploaded_files["M15"] = st.file_uploader(
        "Importer les données M15",
        type=["csv"],
        key="file_m15"
    )

    uploaded_files["M5"] = st.file_uploader(
        "Importer les données M5",
        type=["csv"],
        key="file_m5"
    )


def load_data(file):
    df = pd.read_csv(file)
    df.columns = df.columns.str.lower().str.strip()

    rename = {
        "date": "datetime",
        "time": "datetime",
        "timestamp": "datetime"
    }

    df = df.rename(columns=rename)

    required = [
        "datetime", "open", "high", "low", "close"
    ]

    if not all(c in df.columns for c in required):
        raise ValueError(
            "Colonnes nécessaires : datetime, open, high, low, close"
        )

    df["datetime"] = pd.to_datetime(
        df["datetime"], errors="coerce"
    )

    for col in ["open", "high", "low", "close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=required)
    df = df.sort_values("datetime").reset_index(drop=True)

    if len(df) < 15:
        raise ValueError(
            "Il faut au moins 15 chandeliers valides."
        )

    return df


data = {}
errors = {}

for tf, file in uploaded_files.items():
    if file is not None:
        try:
            data[tf] = load_data(file)
        except Exception as e:
            errors[tf] = str(e)

for tf, df in data.items():
    st.success(f"{tf} : {len(df)} chandeliers chargés")

for tf, error in errors.items():
    st.error(f"Erreur {tf} : {error}")


  
# GRAPHIQUE INTERACTIF

st.divider()
st.subheader("2. Graphique en chandeliers et volume")

if selected_tf in data:
    chart_df = data[selected_tf]

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
        row_heights=[0.75, 0.25]
    )

    fig.add_trace(
        go.Candlestick(
            x=chart_df["datetime"],
            open=chart_df["open"],
            high=chart_df["high"],
            low=chart_df["low"],
            close=chart_df["close"],
            name=selected_tf
        ),
        row=1,
        col=1
    )

    # DETECTION PEDAGOGIQUE BOS / CHOCH

    structure_events = []
    trend = 0
    lookback = 5

    for i in range(lookback, len(chart_df)):
        previous_high = chart_df["high"].iloc[i-lookback:i].max()
        previous_low = chart_df["low"].iloc[i-lookback:i].min()

        current_close = chart_df["close"].iloc[i]

        if current_close > previous_high:
            event = "BOS haussier" if trend >= 0 else "CHOCH haussier"
            trend = 1
            structure_events.append(
                (i, current_close, event)
            )

        elif current_close < previous_low:
            event = "BOS baissier" if trend <= 0 else "CHOCH baissier"
            trend = -1
            structure_events.append(
                (i, current_close, event)
            )

    for i, price, event in structure_events:
        bullish = "haussier" in event
        if "BOS" in event:
            marker_color = "lime" if bullish else "red"
        else:
            marker_color = "cyan" if bullish else "orange"
        fig.add_trace(
            go.Scatter(
                x=[chart_df["datetime"].iloc[i]],
                y=[price],
                mode="markers+text",
                                marker=dict(
                    size=12,
                    color=marker_color,
                    symbol="triangle-up" if bullish else "triangle-down"
                ),
                text=[event],
                textposition="top center" if bullish else "bottom center",
                name=event,
                showlegend=True
            ),
            row=1,
            col=1
        )

    # DETECTION PEDAGOGIQUE DES ORDER BLOCKS

    ob_zones = []

    for i, price, event in structure_events:
        if "haussier" in event:
            for j in range(i - 1, max(-1, i - 6), -1):
                if chart_df["close"].iloc[j] < chart_df["open"].iloc[j]:
                    ob_zones.append({
                        "type": "OB haussier",
                        "start": chart_df["datetime"].iloc[j],
                        "end": chart_df["datetime"].iloc[-1],
                        "high": chart_df["high"].iloc[j],
                        "low": chart_df["low"].iloc[j]
                    })
                    break

        elif "baissier" in event:
            for j in range(i - 1, max(-1, i - 6), -1):
                if chart_df["close"].iloc[j] > chart_df["open"].iloc[j]:
                    ob_zones.append({
                        "type": "OB baissier",
                        "start": chart_df["datetime"].iloc[j],
                        "end": chart_df["datetime"].iloc[-1],
                        "high": chart_df["high"].iloc[j],
                        "low": chart_df["low"].iloc[j]
                    })
                    break

    for ob in ob_zones:
        fig.add_shape(
            type="rect",
            x0=ob["start"],
            x1=ob["end"],
            y0=ob["low"],
            y1=ob["high"],
            fillcolor="rgba(0, 180, 100, 0.15)"
            if ob["type"] == "OB haussier"
            else "rgba(255, 70, 70, 0.15)",
            line=dict(
                color="lime" if ob["type"] == "OB haussier" else "red",
                width=1
            ),
            row=1,
            col=1
        )

    if "volume" in chart_df.columns:
        fig.add_trace(
            go.Bar(
                x=chart_df["datetime"],
                y=chart_df["volume"],
                name="Volume"
            ),
            row=2,
            col=1
        )
    else:
        st.warning("Aucune colonne Volume détectée.")

    fig.update_layout(
        title=f"GOLD XAUUSD - {selected_tf}",
        template="plotly_dark",
        height=700,
        xaxis_rangeslider_visible=False
    )

    fig.update_yaxes(title_text="Prix", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)

    st.plotly_chart(fig, use_container_width=True)

else:
    st.info(
        f"Importe les données {selected_tf} "
        "pour afficher le graphique."
    )


# FONCTIONS D'ANALYSE

def analyze_market(df):

    result = {}

    last = df.iloc[-1]

    result["price"] = float(last["close"])

    result["high_liquidity"] = float(
        df.tail(30)["high"].max()
    )

    result["low_liquidity"] = float(
        df.tail(30)["low"].min()
    )

    # Sommets et creux
    df["swing_high"] = (
        df["high"] ==
        df["high"].rolling(11, center=True).max()
    )

    df["swing_low"] = (
        df["low"] ==
        df["low"].rolling(11, center=True).min()
    )

    highs = df.loc[df["swing_high"], "high"]
    lows = df.loc[df["swing_low"], "low"]

    result["resistance"] = (
        float(highs.iloc[-1])
        if len(highs) else float(df["high"].max())
    )

    result["support"] = (
        float(lows.iloc[-1])
        if len(lows) else float(df["low"].min())
    )

    # Tendance EMA
    ema20 = df["close"].ewm(span=20).mean().iloc[-1]
    ema50 = df["close"].ewm(span=50).mean().iloc[-1]

    if ema20 > ema50:
        result["trend"] = "Orientation haussière"
    elif ema20 < ema50:
        result["trend"] = "Orientation baissière"
    else:
        result["trend"] = "Orientation neutre"

    # FVG
    fvg = []

    for i in range(2, len(df)):
        if df.iloc[i]["low"] > df.iloc[i-2]["high"]:
            fvg.append({
                "Type": "FVG haussier",
                "Bas": df.iloc[i-2]["high"],
                "Haut": df.iloc[i]["low"],
                "Date": df.iloc[i]["datetime"]
            })

        elif df.iloc[i]["high"] < df.iloc[i-2]["low"]:
            fvg.append({
                "Type": "FVG baissier",
                "Bas": df.iloc[i]["high"],
                "Haut": df.iloc[i-2]["low"],
                "Date": df.iloc[i]["datetime"]
            })

    result["fvg"] = fvg

    # Order Blocks indicatifs
    obs = []

    for i in range(1, len(df)):
        previous = df.iloc[i-1]
        current = df.iloc[i]

        if (
            current["close"] > previous["high"]
            and previous["close"] < previous["open"]
        ):
            obs.append({
                "Type": "OB haussier potentiel",
                "Bas": previous["low"],
                "Haut": previous["open"],
                "Date": previous["datetime"]
            })

        elif (
            current["close"] < previous["low"]
            and previous["close"] > previous["open"]
        ):
            obs.append({
                "Type": "OB baissier potentiel",
                "Bas": previous["open"],
                "Haut": previous["high"],
                "Date": previous["datetime"]
            })

    result["obs"] = obs

    # Observations de liquidité / Wyckoff
    previous = df.iloc[-2]

    result["spring"] = (
        last["low"] < previous["low"]
        and last["close"] > previous["low"]
    )

    result["utad"] = (
        last["high"] > previous["high"]
        and last["close"] < previous["high"]
    )

    return result


# TABLEAU MULTI-UNITÉS

st.divider()
st.subheader("2. Tableau de bord multi-unités")

if data:

    rows = []

    for tf in timeframes:
        if tf in data:
            analysis = analyze_market(data[tf])

            rows.append({
                "Unité": tf,
                "Dernier prix": round(analysis["price"], 2),
                "Orientation": analysis["trend"],
                "Support": round(analysis["support"], 2),
                "Résistance": round(analysis["resistance"], 2),
                "FVG détectés": len(analysis["fvg"]),
                "OB potentiels": len(analysis["obs"])
            })

    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True
    )

else:
    st.warning(
        "Aucune donnée chargée. Importe au moins un fichier CSV."
    )


# ANALYSE DE L'UNITÉ SÉLECTIONNÉE

st.divider()
st.subheader("3. Analyse détaillée")

if selected_tf in data:

    df = data[selected_tf].copy()
    analysis = analyze_market(df)

    st.write("Unité analysée :", selected_tf)

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Dernier prix",
        f"{analysis['price']:.2f}"
    )

    col2.metric(
        "Support indicatif",
        f"{analysis['support']:.2f}"
    )

    col3.metric(
        "Résistance indicative",
        f"{analysis['resistance']:.2f}"
    )

    st.info(analysis["trend"])

    # Graphique

    st.subheader("4. Graphique du Gold")

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

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # FVG

    st.subheader("5. Détection des FVG")

    if analysis["fvg"]:
        st.dataframe(
            pd.DataFrame(analysis["fvg"][-10:]),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.write("Aucun FVG détecté.")

    # ORDER BLOCKS

    st.subheader("6. Order Blocks")

    if analysis["obs"]:
        st.dataframe(
            pd.DataFrame(analysis["obs"][-10:]),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.write("Aucun OB potentiel détecté.")

    # LIQUIDITÉ

    st.subheader("7. Analyse de liquidité")

    st.write(
        "Liquidité haute indicative :",
        round(analysis["high_liquidity"], 2)
    )

    st.write(
        "Liquidité basse indicative :",
        round(analysis["low_liquidity"], 2)
    )

    # WYCKOFF

    st.subheader("8. Observations Wyckoff")

    col1, col2 = st.columns(2)

    with col1:
        st.write("Spring :")
        st.write(
            "Observation possible"
            if analysis["spring"]
            else "Non détecté sur la dernière bougie"
        )

    with col2:
        st.write("UTAD :")
        st.write(
            "Observation possible"
            if analysis["utad"]
            else "Non détecté sur la dernière bougie"
        )

    # BOS / CHOCH : observations simples

    st.subheader("9. Structure et cassures")

    if analysis["price"] > analysis["resistance"]:
        st.success("Cassure haussière potentielle à examiner.")
    elif analysis["price"] < analysis["support"]:
        st.warning("Cassure baissière potentielle à examiner.")
    else:
        st.info("Prix entre les derniers niveaux identifiés.")

else:
    st.info(
        f"Importe les données {selected_tf} pour afficher "
        "son analyse détaillée."
    )


# SYNTHÈSE

st.divider()
st.subheader("10. Méthode de travail")

st.markdown("""
- **H4 :** déterminer la structure générale.
- **H1 :** repérer les zones de travail.
- **M15 :** rechercher les confirmations.
- **M5 :** examiner les réactions et les confirmations finales.

Une analyse sérieuse doit combiner la structure, la liquidité,
les zones OB/FVG et les confirmations de prix.
""")

st.warning("""
Les détections sont indicatives et doivent être vérifiées.
Les Spring, UTAD, BOS, CHOCH et OB ne sont pas tous confirmés
automatiquement par cette version. Les données doivent être
réelles et correctement exportées depuis le graphique.

Cette application est un outil pédagogique, pas un générateur
de signaux garantis.
""")

st.caption(
    "SMART TRADING SMC 2.0 | GOLD XAUUSD"
)