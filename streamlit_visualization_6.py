import streamlit as st
import plotly.graph_objects as go
from pathlib import Path
import yfinance as yf
import pandas as pd
from ta.trend import ADXIndicator
from ta.momentum import StochasticOscillator

from core_magic import (
    lade_daten_aktie,
    berechne_indikatoren,
    lade_fundamentaldaten
)

from signals import (
    RSI_signal, 
    macd_signal, 
    adx_signal, 
    stochastic_signal, 
    bollinger_signal,
    kombiniertes_signal,
    analyse_kaufsignal_perioden
)

def go_to(page_name):
    st.session_state.page = page_name

def home_page(themen):
    st.title("📈 Aktien-Dashboard")
    st.write("Wähle eine Aktie aus der Liste:")

    if not themen:
        st.error("Keine Themen gefunden. Bitte überprüfe die Datei themen.txt.")
    else:
        for name in themen:
            if st.button(name):
                go_to(name)


def aktienseite(symbol): 
    symbol = st.session_state.page

    st.set_page_config(
    page_title="Aktien Dashboard",
    layout="wide"  # 💥 macht Seite 100% breit
    )
    
    st.title(f"📊 {symbol} – Analyse")

    max_period = "4y"
    try:
        data_full = lade_daten_aktie(symbol, period=max_period)
        data_full = berechne_indikatoren(data_full)
    except Exception as e:
        st.error(f"Fehler beim Laden der Daten: {e}")
        return
    
    # Einmalige Zeitauswahl oben
    zeitraum = st.sidebar.selectbox("Zeitraum wählen", ["6 Monate", "1 Jahr", "3 Jahre"])
    period_map = {
        "6 Monate": 180,
        "1 Jahr": 365,
        "3 Jahre": 1095
    }
    # Zeitraum als Anzahl Tage, z.B. 90
    tage = period_map[zeitraum]

    min_veraenderung = st.sidebar.slider(
            "📈 Mindestkursanstieg (%)",
            min_value=0.0,
            max_value=0.3,
            value=0.08,
            step=0.01
        )
    
    Auswertung_tage = st.sidebar.slider(
            "📅 Auswertung-Tage für Performance-Auswertung",
            min_value=10,
            max_value=200,
            value=61,
            step=1
        )

    # Heute als Referenzdatum
    heute = pd.Timestamp.today()

    # Startdatum berechnen (heute minus tage)
    startdatum = pd.Timestamp.today(tz=data_full.index.tz) - pd.Timedelta(days=tage)

    # Daten filtern, nur Daten ab Startdatum behalten
    data = data_full.loc[data_full.index >= startdatum]

    # Indikatoren berechnen
    opt = anzeige_optionen_main()
    
    # Tabs definieren
    tab_overview, tab_charts, tab_ichimoku, tab_fundamentals = st.tabs(
        ["📈 Übersicht", "📊 Charts", "🌥️ Ichimoku", "🏦 Fundamentaldaten"]
    )

    with tab_overview:

        # --- 3 Spalten Layout ---
        col1, col2 = st.columns([2, 1])

        # ---------------------------------------------------------
        # 1️⃣ LINKE SPALTE
        # ---------------------------------------------------------
        with col1:
            with st.container(border=True):
                st.subheader("Hauptchart")
                plot_hautpchart(data, symbol, opt, 1)

        # ---------------------------------------------------------
        # 2️⃣ RECHTE SPALTE
        # ---------------------------------------------------------
        with col2:
            with st.container(border=True):
                st.subheader("Analyse der Signale")
                zeige_kaufsignal_analyse(data, Auswertung_tage, min_veraenderung)

        # ---------------------------------------------------------
        # Unten drunter
        # ---------------------------------------------------------
        with st.container(border=True):
            st.subheader("📊 Übersicht der technischen Signale")
            zeige_technische_signale(data)
    
    with tab_charts:
        with st.container(border=True):
            st.subheader("Gesamtübersicht")
            plot_hautpchart(data, symbol, opt, 2)

        col1, col2 = st.columns([1,1])
        # ---------------------------------------------------------
        # 1️⃣ LINKE SPALTE
        # ---------------------------------------------------------
        with col1:
            with st.container(border=True):
                # RSI Chart
                if opt["rsi"] and "RSI" in data.columns: plot_rsi(data, symbol, opt)

        # ---------------------------------------------------------
        # 2️⃣ MITTLERE SPALTE
        # ---------------------------------------------------------
        with col2:
            with st.container(border=True):
                # MACD Chart
                if opt["macd"] and {"MACD", "MACD_Signal", "MACD_Hist"}.issubset(data.columns): plot_macd(data, symbol, opt)

        
        col1, col2 = st.columns([1,1])
        # ---------------------------------------------------------
        # 1️⃣ LINKE SPALTE
        # ---------------------------------------------------------
        with col1:
            with st.container(border=True):
                # Stochastic Oscillator Chart
                if opt["stoch"] and {"Stoch_%K", "Stoch_%D"}.issubset(data.columns):plot_stoch(data, symbol, opt)
        
        # ---------------------------------------------------------
        # 2️⃣ RECHTE SPALTE
        # ---------------------------------------------------------
        with col2:
            with st.container(border=True):
                if opt["adx"] and {"ADX", "+DI", "-DI"}.issubset(data.columns): plot_adx(data, symbol, opt)


    with tab_ichimoku:
        # ---------------------------------------------------------
        # Hauptchart
        # ---------------------------------------------------------
        plot_Ichimoku(data, symbol, opt)


    with tab_fundamentals:
        col1, col2 = st.columns([1,1])
        # ---------------------------------------------------------
        # 1️⃣ LINKE SPALTE
        # ---------------------------------------------------------
        with col1:
            # Technische Kennzahlen als Tabelle
            show_technical_metrics(data, st, title="🔎 Wichtige Marktindikatoren")

        # ---------------------------------------------------------
        # 2️⃣ MITTLERE SPALTE
        # ---------------------------------------------------------
        with col2:
            # Fundamentaldaten
            zeige_fundamentaldaten(symbol)

            

def anzeige_optionen_main():
    return {
        "bollinger": st.sidebar.checkbox("Bollinger-Bänder anzeigen", True),
        "macd": st.sidebar.checkbox("MACD anzeigen", True),
        "rsi": st.sidebar.checkbox("RSI anzeigen", True),
        "pivots": st.sidebar.checkbox("Support/Widerstand anzeigen", True),
        "stoch": st.sidebar.checkbox("Stochastic anzeigen", True),
        "adx": st.sidebar.checkbox("ADX anzeigen", True),
        "ichimoku": st.sidebar.checkbox("Ichimoku anzeigen", True),
        "ma10": st.sidebar.checkbox("MA10 anzeigen", True),
        "ma50": st.sidebar.checkbox("MA50 anzeigen", True),
    }

def plot_hautpchart (data, symbol, opt, version):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=data["Close"], mode="lines", name="Schlusskurs"))
    if opt["ma10"]:
        fig.add_trace(go.Scatter(x=data.index, y=data["MA10"], mode="lines", name="MA10"))
    if opt["ma50"]:
                fig.add_trace(go.Scatter(x=data.index, y=data["MA50"], mode="lines", name="MA50"))

    if opt["bollinger"]: #and "BBIh_Upper" in data.columns and "BB_Lower" in data.columns:
        fig.add_trace(go.Scatter(x=data.index, y=data["BB_Upper"], mode="lines", line=dict(dash='dash'), name="BB Oberband"))
        fig.add_trace(go.Scatter(x=data.index, y=data["BB_Lower"], mode="lines", line=dict(dash='dash'), name="BB Unterband"))

    #if show_pivotsif opt["bollinger"]
    #    for col, color, name in [("Support1", "green", "Support 1"), ("Support2", "green", "Support 2"),
    #                             ("Resistance1", "red", "Resistance 1"), ("Resistance2", "red", "Resistance 2")]:
    #        if col in data.columns:
    #            fig.add_trace(go.Scatter(x=data.index, y=data[col], mode="lines", line=dict(dash='dot', color=color), name=name))
    fig.update_layout(xaxis_title="Datum", yaxis_title="Preis (USD)")
    st.subheader(f"{symbol} Kurs & Indikatoren")
    st.plotly_chart(fig, use_container_width=True, key=f"hauptchart_{version}")


def plot_Ichimoku(data, symbol, opt):

    # Falls Ichimoku ausgeschaltet ist → nichts anzeigen
    if not opt.get("ichimoku"):
        return

    # Figure MUSS existieren
    fig = go.Figure()

    # Ichimoku-Linien
    lines = [
        ("Tenkan_sen", "Tenkan-sen", "solid", "blue"),
        ("Kijun_sen", "Kijun-sen", "solid", "orange"),
        ("Senkou_Span_A", "Senkou Span A", "dash", "green"),
        ("Senkou_Span_B", "Senkou Span B", "dash", "red"),
        ("Chikou_Span", "Chikou Span", "dot", "purple"),
    ]

    for col, line_name, line_style, line_color in lines:
        if col in data.columns:
            fig.add_trace(go.Scatter(
                x=data.index,
                y=data[col],
                mode="lines",
                line=dict(dash=line_style, color=line_color),
                name=line_name
            ))

    fig.update_layout(
        title=f"Ichimoku – {symbol}",
        xaxis_title="Datum",
        yaxis_title="Preis"
    )

    st.plotly_chart(fig, use_container_width=True)


def plot_macd(data, symbol, opt):
    macd_fig = go.Figure()
    macd_fig.add_trace(go.Scatter(x=data.index, y=data["MACD"], mode="lines", name="MACD"))
    macd_fig.add_trace(go.Scatter(x=data.index, y=data["MACD_Signal"], mode="lines", name="Signal"))
    macd_fig.add_trace(go.Bar(x=data.index, y=data["MACD_Hist"], name="Histogramm"))
    macd_fig.update_layout(title=f"{symbol} MACD", xaxis_title="Datum")
    st.plotly_chart(macd_fig, use_container_width=True)

def plot_rsi(data, symbol, opt):
    rsi_fig = go.Figure()
    rsi_fig.add_trace(go.Scatter(x=data.index, y=data["RSI"], mode="lines", name="RSI"))
    rsi_fig.add_hline(y=30, line_dash="dash", line_color="red", annotation_text="Überverkauft (30)", annotation_position="bottom right")
    rsi_fig.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Überkauft (70)", annotation_position="top right")
    rsi_fig.update_layout(title=f"{symbol} RSI", xaxis_title="Datum", yaxis_range=[0, 100])
    st.plotly_chart(rsi_fig, use_container_width=True)

def plot_stoch(data, symbol, opt):
    stoch_fig = go.Figure()
    stoch_fig.add_trace(go.Scatter(x=data.index, y=data["Stoch_%K"], mode="lines", name="%K"))
    stoch_fig.add_trace(go.Scatter(x=data.index, y=data["Stoch_%D"], mode="lines", name="%D"))
    stoch_fig.update_layout(title=f"{symbol} Stochastic Oscillator", xaxis_title="Datum", yaxis_range=[0, 100])
    st.plotly_chart(stoch_fig, use_container_width=True)

def plot_adx(data, symbol, opt):
    adx_fig = go.Figure()
    adx_fig.add_trace(go.Scatter(x=data.index, y=data["ADX"], mode="lines", name="ADX"))
    adx_fig.add_trace(go.Scatter(x=data.index, y=data["+DI"], mode="lines", name="+DI"))
    adx_fig.add_trace(go.Scatter(x=data.index, y=data["-DI"], mode="lines", name="-DI"))
    adx_fig.update_layout(title=f"{symbol} ADX", xaxis_title="Datum")
    st.plotly_chart(adx_fig, use_container_width=True)

def show_technical_metrics(data, st_output, title="📋 Technische Kennzahlen"):
    """Erstellt eine Tabelle der wichtigsten technischen Kennzahlen."""

    st_output.subheader(title)

    letzte = data.iloc[-1]
    kennzahlen = {}

    # 1️⃣ Erste Gruppe von Indikatoren
    erste_gruppe = [
        "Close", "MA10", "MA50", "RSI", "ATR",
        "BB_Upper", "BB_Lower", "MACD", "MACD_Signal"
    ]

    for key in erste_gruppe:
        if key in data.columns:
            val = letzte[key]
            if key in ["MACD", "MACD_Signal"]:
                kennzahlen[key] = [round(val, 4)]
            else:
                kennzahlen[key] = [round(val, 2)]

    # 2️⃣ Zweite Gruppe von Indikatoren
    zweite_gruppe = [
        "Stoch_%K", "Stoch_%D", "ADX", "+DI", "-DI",
        "Tenkan_sen", "Kijun_sen"
    ]

    for key in zweite_gruppe:
        if key in data.columns:
            val = letzte[key]
            if pd.isna(val):
                kennzahlen[key] = ["N/A"]
            else:
                kennzahlen[key] = [round(val, 2)]

    # 3️⃣ DataFrame erzeugen
    kennzahlen_df = pd.DataFrame.from_dict(
        kennzahlen,
        orient="index",
        columns=["Wert"]
    )

    # String-Konvertierung für saubere Ausgabe
    kennzahlen_df = kennzahlen_df.astype(str)

    # 4️⃣ Anzeige
    st_output.table(kennzahlen_df)

def zeige_fundamentaldaten(symbol):
    """Lädt Fundamentaldaten für ein Symbol und zeigt sie als Tabelle in Streamlit an."""

    st.subheader("🏦 Fundamentaldaten")

    try:
        fundamentaldaten = lade_fundamentaldaten(symbol)

        if fundamentaldaten:
            # In DataFrame umwandeln
            fundamentaldaten_df = pd.DataFrame(
                list(fundamentaldaten.items()),
                columns=["Kennzahl", "Wert"]
            ).astype(str)

            st.table(fundamentaldaten_df)

        else:
            st.warning("Keine Fundamentaldaten gefunden.")

    except Exception as e:
        st.error(f"Fehler beim Laden der Fundamentaldaten: {e}")

def zeige_technische_signale(data):
    """Berechnet technische Signale, zeigt Übersicht und das kombinierte Handelssignal."""

    # Einzel-Signale berechnen
    rsi_sig = RSI_signal(data)
    macd_sig = macd_signal(data)
    adx_sig = adx_signal(data)
    stoch_sig = stochastic_signal(data)
    boll_sig = bollinger_signal(data)

    # Übersichtstabelle der Einzel-Signale
    df_signale = pd.DataFrame({
        "Bollinger": [boll_sig],
        "RSI": [rsi_sig],
        "MACD": [macd_sig],
        "ADX": [adx_sig],
        "Stochastic": [stoch_sig]
    })

    st.table(df_signale)

    # Kombiniertes Signal berechnen
    gesamt_signal, alle_signale = kombiniertes_signal(data)

    st.markdown("---")
    st.subheader("🧩 Kombiniertes Handelssignal")
    st.write(gesamt_signal)

    # Detailansicht
    with st.expander("Details zu den Einzelsignalen"):
        for name, sig in alle_signale.items():
            st.write(f"**{name}**: {sig}")

def zeige_kaufsignal_analyse(data, Auswertung_tage, min_veraenderung):
    """
    Führt die Analyse der Kaufsignal-Perioden durch
    und zeigt die wichtigsten Kennzahlen und Details in Streamlit an.
    """

    # Analyse aus Kernfunktion laden
    analyse_ergebnis = analyse_kaufsignal_perioden(data, Auswertung_tage, min_veraenderung)

    st.write(f"Anzahl Kaufsignale (gesamt): {analyse_ergebnis.get('Anzahl_Kaufsignale', 0)}")

    # Perioden-Bewertung prüfen
    if "Perioden_Bewertung" not in analyse_ergebnis:
        st.info("Keine Perioden-Bewertung verfügbar.")
        return

    df_details = pd.DataFrame(analyse_ergebnis["Perioden_Bewertung"])
    df_details.columns = ["Start", "Ende", "Signal", "Wert1", "Wert2", "Beschreibung", "ExtraInfo"]

    # Signal in Bool umwandeln
    df_details["Signal"] = df_details["Signal"].astype(str).str.upper() == "TRUE"

    # Start-Datum als datetime
    df_details["Start"] = pd.to_datetime(df_details["Start"])

    # Ende-Datum als datetime
    df_details["Ende"] = pd.to_datetime(df_details["Ende"])

    # letztes Kursdatum
    letztes_datum = data.index[-1]

    # Ende + Bewertungsdauer = Zeitpunkt, ab dem man die Periode werten darf
    df_details["Bewertung_fertig_ab"] = df_details["Ende"] + pd.Timedelta(days=Auswertung_tage)

    # Perioden klassifizieren
    df_abgeschlossen = df_details[df_details["Bewertung_fertig_ab"] <= letztes_datum]
    df_offen = df_details[df_details["Bewertung_fertig_ab"] > letztes_datum]

    # Neue korrekte Trefferquote berechnen
    gesamt = len(df_abgeschlossen)
    if gesamt > 0:
        prozent_true = (df_abgeschlossen["Signal"].sum() / gesamt) * 100
    else:
        prozent_true = 0

    st.write(f"Ausgewertete abgeschlossene Perioden: {gesamt}")
    st.metric("Trefferquote (nur abgeschlossene Perioden)", f"{prozent_true:.2f} %")
    
    with st.expander("Details zu den Perioden"):
        st.markdown("### 📘 Abgeschlossene Signalperioden")
        if len(df_abgeschlossen) > 0:
            st.dataframe(df_abgeschlossen)
        else:
            st.info("Es gibt aktuell keine abgeschlossenen Perioden.")

        st.markdown("### ⏳ Laufende Signalperioden")
        if len(df_offen) > 0:
            df_tmp = df_offen.copy()
            df_tmp["Tage_bis_fertig"] = (df_tmp["Bewertung_fertig_ab"] - letztes_datum).dt.days
            st.dataframe(df_tmp)
        else:
            st.success("Alle abgeschlossenen Perioden wurden ausgewertet – keine offenen Perioden vorhanden.")
