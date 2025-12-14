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
    lade_fundamentaldaten,
    klassifiziere_aktie,
    erklaere_kategorien
)

from signals import (
    fundamental_analyse,
    RSI_signal, 
    macd_signal, 
    adx_signal, 
    stochastic_signal, 
    bollinger_signal,
    berechne_alle_signale,
    berechne_gewichtete_signale,
    kombiniertes_signal,
    analyse_kaufsignal_perioden,
    lade_analystenbewertung,
    berechne_rating_bar,
    zeichne_rating_gauge
)

def go_to(page_name):
    st.session_state.page = page_name

def home_page(watchlist):
    st.title("📈 Aktien-Dashboard")
    st.write("Wähle eine Aktie:")

    for name, symbol in watchlist:
        if st.button(f"{name} ({symbol})"):
            st.session_state.page = (name, symbol) #Touple speichern

def aktienseite(): 
    name, symbol = st.session_state.page

    st.set_page_config(
    page_title="Aktien Dashboard",
    layout="wide"  # 💥 macht Seite 100% breit
    )
    
    st.title(f"📊 {name} – Analyse")

    max_period = "4y"
    try:
        data_full = lade_daten_aktie(symbol, period=max_period)
        data_full = berechne_indikatoren(data_full)
    except Exception as e:
        st.error(f"Fehler beim Laden der Daten: {e}")
        return
    fundamentaldaten = lade_fundamentaldaten(symbol)
    data_fund = fundamental_analyse(fundamentaldaten, symbol)
    analysten_daten = lade_analystenbewertung(symbol)
    summary_df = analysten_daten["summary"]
    rating_counts = berechne_rating_bar(summary_df)
    klassifikation = klassifiziere_aktie(symbol, data_full, fundamentaldaten)
    erklaerung = erklaere_kategorien(klassifikation["Profil"], klassifikation["Trading_Status"])

    
    # Sidebar-Parameter laden
    tage, min_veraenderung, Auswertung_tage = lade_sidebar_parameter()
    opt = anzeige_optionen_main()
        
    # Startdatum berechnen (heute minus tage)
    startdatum = pd.Timestamp.today(tz=data_full.index.tz) - pd.Timedelta(days=tage)
    # Daten filtern, nur Daten ab Startdatum behalten
    data = data_full.loc[data_full.index >= startdatum]
    
    # Tabs definieren
    tab_overview, tab_signaldetail, tab_charts, tab_ichimoku, tab_fundamentals = st.tabs(
        ["📈 Übersicht", "🔔Signaldetails", "📊 Charts", "🌥️ Ichimoku", "🏦 Fundamentaldaten"]
    )

    with tab_overview:
        # --- 2 Spalten Layout ---
        col1, col2 = st.columns([2, 1])

        # ---------------------------------------------------------
        # 1️⃣ LINKE SPALTE
        # ---------------------------------------------------------
        with col1:
            with st.container(border=True):
                plot_hautpchart(data, name, opt, 1)

        # ---------------------------------------------------------
        # 2️⃣ RECHTE SPALTE
        # ---------------------------------------------------------
        with col2:
            with st.container(border=True):
                st.subheader("Experteneinschätzung:")
                if summary_df is not None:
                    zeichne_rating_gauge(rating_counts)

                st.subheader("📌 Klassifizierung der Aktie:")
                st.metric("Profil:", klassifikation["Profil"])
                st.metric("Trading Status:", klassifikation["Trading_Status"])
                with st.expander("Details zur Aktuen-Kathegorie:"):
                    st.write(erklaerung)
         # --- 2 Spalten Layout ---
        col1, col2 = st.columns([2, 1])

        # ---------------------------------------------------------
        # 1️⃣ LINKE SPALTE
        # ---------------------------------------------------------
        with col1:
            with st.container(border=True):
                st.subheader("Beispiel-Übersicht:")
                signals = berechne_alle_signale(data)
                trading_sig = berechne_gewichtete_signale(signals, klassifikation["Profil"], klassifikation["Trading_Status"])
                st.metric("Trading Signal:", trading_sig)

                st.subheader("🏦 Fundamental Übersicht:")
                fundamental_summary(data_fund)

                st.subheader("🔄 Swingtrading Übersicht:")
                zeige_swingtrading_signal(data)
                zeige_swingtrading_signalauswertung(data, Auswertung_tage, min_veraenderung)

        # ---------------------------------------------------------
        # 2️⃣ RECHTE SPALTE
        # ---------------------------------------------------------
        with col2:
            beispiel_kachel()

    with tab_signaldetail:
        # ---------------------------------------------------------
        # Unten drunter
        # ---------------------------------------------------------
        with st.container(border=True):
            st.subheader("Analyse der Signale")
            zeige_kaufsignal_analyse(data, Auswertung_tage, min_veraenderung)

        with st.container(border=True):
            analyse_ergebnis = analyse_kaufsignal_perioden(data, Auswertung_tage, min_veraenderung)
            # macht es nicht Sinn, die folgende Formatierung in die Funktion mit aufzunehmen?
            df_details = pd.DataFrame(analyse_ergebnis["Perioden_Bewertung"])
            df_details.columns = ["Start", "Ende", "Signal", "Wert1", "Wert2", "Beschreibung", "ExtraInfo"]
            df_details["Signal"] = df_details["Signal"].astype(str).str.upper() == "TRUE"
            df_details["Start"] = pd.to_datetime(df_details["Start"])
            df_details["Ende"] = pd.to_datetime(df_details["Ende"])
            st.subheader("Kennzeichnung der Perioden")
            plot_priodenchart(data, name, opt, 1, kaufperioden=df_details)

        with st.container(border=True):
            st.subheader("📊 Übersicht der technischen Signale")
            zeige_technische_signale(data)

        with st.container(border=True):
            st.subheader("🏦 Übersicht des Fundamentalsignals")
            fundamental_interpretation(data_fund)
    
        if summary_df is not None:
            with st.container(border=True):
                zeichne_rating_bar(rating_counts)

        else:
            st.info("Keine Analystenbewertungen verfügbar.")

        rating_counts = berechne_rating_bar(summary_df)

        with st.container(border=True):
                    st.subheader("Übersicht der Analystenbewertung")
                    zeige_analystenbewertung(symbol)

    with tab_charts:
        with st.container(border=True):
            st.subheader("Gesamtübersicht")
            plot_hautpchart(data, name, opt, 2)

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
        plot_Ichimoku(data, name, opt)


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

# ------------------------------
# Sidebar: Parameter laden
# ------------------------------
def lade_sidebar_parameter():
    zeitraum = st.sidebar.selectbox("Zeitraum wählen", ["6 Monate", "1 Jahr", "3 Jahre"])
    period_map = {
        "6 Monate": 180,
        "1 Jahr": 365,
        "3 Jahre": 1095
    }
    tage = period_map[zeitraum]

    min_veraenderung = st.sidebar.slider(
        "📈 Mindestkursanstieg (%)",
        min_value=0.0,
        max_value=0.3,
        value=0.08,
        step=0.01
    )

    auswertung_tage = st.sidebar.slider(
        "📅 Auswertung-Tage für Performance-Auswertung",
        min_value=10,
        max_value=200,
        value=61,
        step=1
    )

    return tage, min_veraenderung, auswertung_tage

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

def plot_hautpchart (data, name, opt, version):
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
    fig.update_layout(
        xaxis_title="Datum",
        yaxis_title="Preis (USD)",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.05,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255,255,255,0.3)",
            bordercolor="rgba(0,0,0,0.15)",
            borderwidth=1
        )
    )
    st.subheader(f"{name} Kurs")
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
        yaxis_title="Preis",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.05,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255,255,255,0.3)",
            bordercolor="rgba(0,0,0,0.15)",
            borderwidth=1
        )
    )

    st.plotly_chart(fig, use_container_width=True)


def plot_macd(data, symbol, opt):
    macd_fig = go.Figure()
    macd_fig.add_trace(go.Scatter(x=data.index, y=data["MACD"], mode="lines", name="MACD"))
    macd_fig.add_trace(go.Scatter(x=data.index, y=data["MACD_Signal"], mode="lines", name="Signal"))
    macd_fig.add_trace(go.Bar(x=data.index, y=data["MACD_Hist"], name="Histogramm"))
    macd_fig.update_layout(title=f"{symbol} MACD", xaxis_title="Datum", legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.05,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255,255,255,0.3)",
            bordercolor="rgba(0,0,0,0.15)",
            borderwidth=1
        ))
    st.plotly_chart(macd_fig, use_container_width=True)

def plot_rsi(data, symbol, opt):
    rsi_fig = go.Figure()
    rsi_fig.add_trace(go.Scatter(x=data.index, y=data["RSI"], mode="lines", name="RSI"))
    rsi_fig.add_hline(y=30, line_dash="dash", line_color="red", annotation_text="Überverkauft (30)", annotation_position="bottom right")
    rsi_fig.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Überkauft (70)", annotation_position="top right")
    rsi_fig.update_layout(title=f"{symbol} RSI", xaxis_title="Datum", yaxis_range=[0, 100], 
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.05,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255,255,255,0.3)",
            bordercolor="rgba(0,0,0,0.15)",
            borderwidth=1
        ))
    st.plotly_chart(rsi_fig, use_container_width=True)

def plot_stoch(data, symbol, opt):
    stoch_fig = go.Figure()
    stoch_fig.add_trace(go.Scatter(x=data.index, y=data["Stoch_%K"], mode="lines", name="%K"))
    stoch_fig.add_trace(go.Scatter(x=data.index, y=data["Stoch_%D"], mode="lines", name="%D"))
    stoch_fig.update_layout(title=f"{symbol} Stochastic Oscillator", xaxis_title="Datum", yaxis_range=[0, 100], 
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.05,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255,255,255,0.3)",
            bordercolor="rgba(0,0,0,0.15)",
            borderwidth=1
        ))
    st.plotly_chart(stoch_fig, use_container_width=True)

def plot_adx(data, symbol, opt):
    adx_fig = go.Figure()
    adx_fig.add_trace(go.Scatter(x=data.index, y=data["ADX"], mode="lines", name="ADX"))
    adx_fig.add_trace(go.Scatter(x=data.index, y=data["+DI"], mode="lines", name="+DI"))
    adx_fig.add_trace(go.Scatter(x=data.index, y=data["-DI"], mode="lines", name="-DI"))
    adx_fig.update_layout(title=f"{symbol} ADX", xaxis_title="Datum",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.05,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255,255,255,0.3)",
            bordercolor="rgba(0,0,0,0.15)",
            borderwidth=1
        ))
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

# ------------------------------------------------------------
# Fundamentaldaten: Summary
# ------------------------------------------------------------
def fundamental_summary(result):
    ampel = result["Ampel"]
    score = result["Score"]

    # Ampel-Interpretation
    if ampel == "🟢":
        st.markdown(
            f"""
            **{ampel} Sehr solide Fundamentaldaten (Score: {score}/100)**  
            Die Aktie zeigt in mehreren zentralen Bereichen überzeugende Werte.  
            Dies spricht für eine **attraktive Bewertung** und ein **günstiges Risiko-Rendite-Verhältnis**.
            """
        )
    elif ampel == "🟡":
        st.markdown(
            f"""
            **{ampel} Neutrale Fundamentaldaten (Score: {score}/100)**  
            Die Kennzahlen sind gemischt. Einige Bereiche schneiden gut ab, andere schwächer.  
            Eine **Beobachtung** oder **Einstieg bei besserer Bewertung** kann sinnvoll sein.
            """
        )
    else:
        st.markdown(
            f"""
            **{ampel} Schwache Fundamentaldaten (Score: {score}/100)**  
            Die Aktie weist mehrere kritische Bewertungs- oder Risikofaktoren auf.  
            Eine Investition sollte nur nach tieferer Analyse erwogen werden.
            """
        )

# ------------------------------------------------------------
# Fundamentaldaten: Score Interpretation
# ------------------------------------------------------------
def fundamental_interpretation(result):
    aktie = result["Aktie"]
    ampel = result["Ampel"]

    kgv = result["KGV"]
    kuv = result["KUV"]
    kbv = result["KBV"]
    marge = result["Marge (%)"]
    beta = result["Beta"]
    score = result["Score"]

    st.subheader(f"Fundamentale Einschätzung:")

    # Ampel-Interpretation
    if ampel == "🟢":
        st.markdown(
            f"""
            **{ampel} Sehr solide Fundamentaldaten (Score: {score}/100)**  
            Die Aktie zeigt in mehreren zentralen Bereichen überzeugende Werte.  
            Dies spricht für eine **attraktive Bewertung** und ein **günstiges Risiko-Rendite-Verhältnis**.
            """
        )
    elif ampel == "🟡":
        st.markdown(
            f"""
            **{ampel} Neutrale Fundamentaldaten (Score: {score}/100)**  
            Die Kennzahlen sind gemischt. Einige Bereiche schneiden gut ab, andere schwächer.  
            Eine **Beobachtung** oder **Einstieg bei besserer Bewertung** kann sinnvoll sein.
            """
        )
    else:
        st.markdown(
            f"""
            **{ampel} Schwache Fundamentaldaten (Score: {score}/100)**  
            Die Aktie weist mehrere kritische Bewertungs- oder Risikofaktoren auf.  
            Eine Investition sollte nur nach tieferer Analyse erwogen werden.
            """
        )

    # Detailanalyse
    st.markdown("### Detailanalyse der Kennzahlen")

    def bullet(text, value):
        return f"- **{text}:** {value}"

    st.markdown(
        "\n".join([
            bullet("KGV (Bewertung Gewinn)", kgv),
            bullet("KUV (Bewertung Umsatz)", kuv),
            bullet("KBV (Bewertung Substanz)", kbv),
            bullet("Gewinnmarge", marge),
            bullet("Beta (Risiko/Volatilität)", beta),
        ])
    )

    # Einordnung der Kennzahlen
    st.markdown("### Kurzinterpretation der Faktoren")

    interpretation = []

    # KGV
    try:
        kgv_val = float(kgv)
        if kgv_val < 15:
            interpretation.append("• **KGV niedrig:** Die Aktie ist im Vergleich zum Gewinn günstig bewertet.")
        elif kgv_val > 35:
            interpretation.append("• **KGV sehr hoch:** Markt erwartet starkes Wachstum – oder Aktie ist überbewertet.")
        else:
            interpretation.append("• **KGV neutral:** Bewertung im marktüblichen Bereich.")
    except:
        pass

    # KUV
    try:
        kuv_val = float(kuv)
        if kuv_val < 3:
            interpretation.append("• **KUV attraktiv:** Umsatzbewertung spricht für solide Bewertung.")
        else:
            interpretation.append("• **KUV erhöht:** Markt zahlt Aufpreis für Wachstum oder Marke.")
    except:
        pass

    # Marge
    try:
        marge_val = float(marge.replace("%",""))
        if marge_val > 15:
            interpretation.append("• **Hohe Marge:** Starkes, profitables Geschäftsmodell.")
        else:
            interpretation.append("• **Niedrige Marge:** Wettbewerb hoch oder Geschäftsmodell wenig profitabel.")
    except:
        pass

    # Beta
    try:
        beta_val = float(beta)
        if beta_val < 1:
            interpretation.append("• **Niedriges Beta:** Aktie schwankt weniger als der Markt (geringeres Risiko).")
        else:
            interpretation.append("• **Hohes Beta:** Überdurchschnittliche Schwankung → höheres Risiko.")
    except:
        pass

    st.markdown("\n".join(interpretation))

def zeige_technische_signale(data):
    # Übersichtstabelle der Einzel-Signale
    df_signale = pd.DataFrame({
        "Bollinger": [bollinger_signal(data)],
        "RSI": [RSI_signal(data)],
        "MACD": [macd_signal(data)],
        "ADX": [adx_signal(data)],
        "Stochastic": [stochastic_signal(data)]
    })

    st.table(df_signale)

    # Kombiniertes Signal berechnen
    gesamt_signal, alle_signale, gesamtscore = kombiniertes_signal(data)

    st.markdown("---")
    st.subheader("🧩 Kombiniertes Handelssignal")
    st.write(gesamt_signal)

    # Detailansicht
    with st.expander("Details zu den Einzelsignalen"):
        st.write(gesamtscore)
        for name, sig in alle_signale.items():
            st.write(f"**{name}**: {sig}")

def zeige_swingtrading_signal(data):
    # Kombiniertes Signal berechnen
    gesamt_signal, alle_signale, geasmtscore = kombiniertes_signal(data)

    st.write(gesamt_signal)

def zeige_swingtrading_signalauswertung(data, Auswertung_tage, min_veraenderung):
    """
    Führt die Analyse der Kaufsignal-Perioden durch
    und zeigt nur die prozentzele trefferquote in Streamlit an.
    """

    # Analyse aus Kernfunktion laden
    analyse_ergebnis = analyse_kaufsignal_perioden(data, Auswertung_tage, min_veraenderung)

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

    # Neue korrekte Trefferquote berechnen
    gesamt = len(df_abgeschlossen)
    if gesamt > 0:
        prozent_true = (df_abgeschlossen["Signal"].sum() / gesamt) * 100
    else:
        prozent_true = 0

    st.metric("Trefferquote (nur abgeschlossene Perioden)", f"{prozent_true:.2f} %")

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

def plot_priodenchart(data, symbol, opt, version, kaufperioden=None):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=data["Close"], mode="lines", name="Schlusskurs", line=dict(color="blue")))

    if opt["bollinger"]:
        fig.add_trace(go.Scatter(x=data.index, y=data["BB_Upper"], mode="lines", line=dict(dash='dash'), name="BB Oberband"))
        fig.add_trace(go.Scatter(x=data.index, y=data["BB_Lower"], mode="lines", line=dict(dash='dash'), name="BB Unterband"))

    # Kaufperioden als grüne Bereiche einzeichnen
    if kaufperioden is not None and not kaufperioden.empty:
        for _, row in kaufperioden.iterrows():
                # Farbe je nach Signal
                if row["Signal"]:
                    fill_color = "green"
                    line_color = "green"
                else:
                    fill_color = "lightgrey"  # hellgrau für "false"
                    line_color = "grey"
                fig.add_vrect(
                    x0=row["Start"],
                    x1=row["Ende"],
                    fillcolor=fill_color,
                    opacity=0.2,
                    layer="below",
                    line_width=0,
                )
                # Optional: Kursverlauf in der Kaufperiode grün färben
                periode_mask = (data.index >= row["Start"]) & (data.index <= row["Ende"])
                fig.add_trace(go.Scatter(
                    x=data.index[periode_mask],
                    y=data["Close"][periode_mask],
                    mode="lines",
                    line=dict(color=line_color, width=3),
                    name="Kaufperiode",
                    showlegend=False
                ))

    fig.update_layout(xaxis_title="Datum", yaxis_title="Preis (USD)", 
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.05,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255,255,255,0.3)",
            bordercolor="rgba(0,0,0,0.15)",
            borderwidth=1
        ))
    st.plotly_chart(fig, use_container_width=True, key=f"Periodenchart_{version}")

def zeige_analystenbewertung(symbol):
    data = lade_analystenbewertung(symbol)

    st.markdown("<div class='kachel'>", unsafe_allow_html=True)
    st.markdown("### 🧠 Analystenbewertungen")

    # 🟦 Zusammenfassung (Buy/Hold/Sell)
    if data["summary"] is not None:
        st.markdown("#### 📊 Rating-Übersicht")
        st.table(data["summary"])
    else:
        st.info("Keine Rating-Übersicht verfügbar.")

    # 🟪 Historische Empfehlungen (Buy/Hold/Sell)
    if data["recommendations"] is not None:
        st.markdown("#### 🕒 Historische Empfehlungen")
        st.dataframe(data["recommendations"].tail(20))
    else:
        st.info("Keine historischen Empfehlungen verfügbar.")

    # 🟧 EPS & Wachstumsprognosen
    if data["analysis"] is not None:
        st.markdown("#### 📈 Analysten-Prognosen (EPS, Revenue, Growth)")
        st.dataframe(data["analysis"])
    else:
        st.info("Keine detaillierten Analystenanalysen verfügbar.")

    st.markdown("</div>", unsafe_allow_html=True)

def zeichne_rating_bar(rating_counts):
    if rating_counts is None: 
        return

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=list(rating_counts.keys()),
        y=list(rating_counts.values()),
        text=list(rating_counts.values()),
        textposition="auto"
    ))

    fig.update_layout(
        title="Analysten Rating-Verteilung",
        xaxis_title="Kategorie",
        yaxis_title="Anzahl"
    )

    st.plotly_chart(fig, use_container_width=True)

def beispiel_kachel():
    st.subheader("📊 Beispiel-Kachel mit Grafik")
    # Container für die Kachel mit etwas Styling
    with st.container():
        st.markdown("""
        <div style="
            background-color: #f0f2f6;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 3px 3px 10px rgba(0,0,0,0.1);
            max-width: 400px;
            margin: auto;
            ">
            <h3 style="color:#333; font-weight:700;">Aktien Kursverlauf</h3>
            <p style="color:#666;">Hier ein Beispielchart mit Zufallsdaten.</p>
        """, unsafe_allow_html=True)

        # Plotly Beispielchart
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=[1, 2, 3, 4, 5],
            y=[10, 15, 13, 17, 14],
            mode='lines+markers',
            line=dict(color='royalblue', width=3),
            marker=dict(size=8)
        ))
        fig.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            height=250,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(255,255,255,1)',
        )

        st.markdown("</div>", unsafe_allow_html=True)


