import pandas as pd
import yfinance as yf
import numpy as np  # nur wenn du numpy Funktionen brauchst
import plotly.graph_objects as go
import streamlit as st
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import MACD, ADXIndicator
from ta.volatility import BollingerBands

def fundamental_analyse(fundamentaldaten, ticker_symbol):
    sector = fundamentaldaten["sector"]
    kgv = fundamentaldaten["kgv"]
    forward_kgv = fundamentaldaten["forward_kgv"]
    kuv = fundamentaldaten["kuv"]
    kbv = fundamentaldaten["kbv"]
    marge = fundamentaldaten["marge"]
    beta = fundamentaldaten["beta"]
    roe = fundamentaldaten["roe"]
    debt_to_equity = fundamentaldaten["debt_to_equity"]
    revenue_growth = fundamentaldaten["revenue_growth"]
    earnings_growth = fundamentaldaten["earnings_growth"]

    peg = None
    if forward_kgv and earnings_growth and earnings_growth > 0:
        peg = forward_kgv / (earnings_growth * 100)

    sector_thresholds = {
        "Technology":     {"kgv": 30, "kuv": 10, "marge": 0.10, "de_ratio": 150},
        "Financial Services": {"kgv": 15, "kuv": 3, "marge": 0.15, "de_ratio": 300},
        "Industrial":     {"kgv": 20, "kuv": 3, "marge": 0.10, "de_ratio": 200},
        "Healthcare":     {"kgv": 25, "kuv": 6, "marge": 0.10, "de_ratio": 150},
        "Consumer Defensive": {"kgv": 20, "kuv": 4, "marge": 0.08, "de_ratio": 250},
        "Consumer Cyclical": {"kgv": 25, "kuv": 6, "marge": 0.08, "de_ratio": 200},
    }
    sector_config = sector_thresholds.get(sector, {"kgv": 20, "kuv": 4, "marge": 0.10, "de_ratio": 200})

    score = 0
    max_score = 140

    if kgv and kgv < sector_config["kgv"]:
        score += 15
    if forward_kgv and forward_kgv < sector_config["kgv"]:
        score += 10
    if peg and peg < 1.5:
        score += 10
    if kuv and kuv < sector_config["kuv"]:
        score += 15
    if marge and marge > sector_config["marge"]:
        score += 15
    if roe and roe > 0.15:
        score += 15
    if revenue_growth and revenue_growth > 0.07:
        score += 15
    if earnings_growth and earnings_growth > 0.07:
        score += 15
    if debt_to_equity and debt_to_equity < sector_config["de_ratio"]:
        score += 10
    if beta and beta < 1.2:
        score += 10

    ratio = score / max_score
    if ratio >= 0.70:
        ampel = "🟢"
    elif ratio >= 0.45:
        ampel = "🟡"
    else:
        ampel = "🔴"

    return {
        "Aktie": ticker_symbol,
        "Sektor": sector,
        "KGV": kgv,
        "Forward KGV": forward_kgv,
        "KUV": kuv,
        "KBV": kbv,
        "Marge (%)": f"{marge*100:.1f}%" if marge else "n/a",
        "ROE (%)": f"{roe*100:.1f}%" if roe else "n/a",
        "PEG Ratio": peg,
        "Beta": beta,
        "Umsatzwachstum": revenue_growth,
        "Gewinnwachstum": earnings_growth,
        "Debt/Equity": debt_to_equity,
        "Score": score,
        "Ampel": ampel
    }

def bollinger_signal(data: pd.DataFrame) -> str:
    """
    Bollinger-Band-Signal mit Toleranz und Rebound-Logik.

    Logik:
    - 🟢 Kaufsignal, wenn der Schlusskurs maximal 1,5 % über dem unteren Band liegt 
      ODER vorher unter dem Band lag und jetzt darüber schließt (Rebound).
    - 🔴 Verkaufssignal, wenn der Schlusskurs maximal 1,5 % unter dem oberen Band liegt 
      ODER vorher über dem Band lag und jetzt darunter schließt (Rebound).
    - 🟡 Andernfalls Haltesignal.

    Erwartet Spalten: 'Close', 'BB_Upper', 'BB_Lower'
    """
    if len(data) < 2:
        return "🟡 Zu wenige Daten für Bollinger-Signal"

    if not {"Close", "BB_Upper", "BB_Lower"}.issubset(data.columns):
        return "Keine Bollinger-Band-Daten vorhanden"

    if len(data) < 2:
        return "Zu wenige Daten für Signal"

    letzte = data.iloc[-1]
    vorletzte = data.iloc[-2]

    close = letzte["Close"]
    upper = letzte["BB_Upper"]
    lower = letzte["BB_Lower"]

    if pd.isna(upper) or pd.isna(lower):
        return "Keine gültigen Bollinger-Daten"

    # Distanz zum oberen und unteren Band in Prozent
    dist_lower = (close - lower) / lower
    dist_upper = (upper - close) / upper

    # --- Kaufsignal: Nähe zum unteren Band oder Rebound
    if (dist_lower <= 0.015) or (
        vorletzte["Close"] < vorletzte["BB_Lower"] and close > lower
    ):
        return "🟢 Bollinger Signal - Kaufsignal (≤1,5 % vom unteren Band oder Rebound)"

    # --- Verkaufssignal: Nähe zum oberen Band oder Rebound
    elif (dist_upper <= 0.015) or (
        vorletzte["Close"] > vorletzte["BB_Upper"] and close < upper
    ):
        return "🔴 Bollinger Signal - Verkaufssignal (≤1,5 % vom oberen Band oder Rebound)"

    # --- Haltesignal
    else:
        return "🟡 Bollinger Signal - Haltesignal"
    
def berechne_bollinger_abstand(data, window=20, window_dev=2):
    bollinger = BollingerBands(close=data["Close"], window=window, window_dev=window_dev)
    # Abstand Close zum unteren Band, normalisiert: (Close - LowerBand) / Close
    bollinger_lband = bollinger.bollinger_lband()
    return float(((data["Close"].iloc[-1] - bollinger_lband.iloc[-1]) / data["Close"].iloc[-1]))

def RSI_signal(data):
    """
    Einfaches Swingtrading-Signal basierend auf RSI und MA10.
    Rückgabe: String mit Signal und Emoji.
    """
    letzte = data.iloc[-1]
    if letzte["RSI"] < 35:
        return "🟢 RSI Signal - Kaufsignal"
    elif letzte["RSI"] > 60:
        return "🔴 RSI Signal - Verkaufssignal"
    else:
        return "🟡 RSI Signal - Haltesignal"
    
def berechne_rsi(data, window=14):
    rsi = RSIIndicator(close=data["Close"], window=window)
    return float(rsi.rsi().iloc[-1])

def macd_signal(data):
    """
    Verbesserte MACD-Logik:
    - Erkennung von MACD/Signal-Kreuzungen
    - Einbau von Momentum- und Trendfiltern
    - Sanfter: verhindert Fehlsignale in Seitwärtsmärkten
    """

    if len(data) < 3:
        return "🟡 Zu wenige Daten für MACD-Signal"

    # Zeilen
    letzte = data.iloc[-1]
    vorletzte = data.iloc[-2]
    dritte = data.iloc[-3]

    macd = letzte["MACD"]
    signal = letzte["MACD_Signal"]

    # --- 1️⃣ Grundlegende Kreuzungen ---
    bullish_cross = vorletzte["MACD"] < vorletzte["MACD_Signal"] and macd > signal
    bearish_cross = vorletzte["MACD"] > vorletzte["MACD_Signal"] and macd < signal

    # --- 2️⃣ Momentum-Filter ---
    # Verhindert Signale ohne Kraft
    momentum_positive = (letzte["MACD"] - vorletzte["MACD"]) > 0
    momentum_negative = (letzte["MACD"] - vorletzte["MACD"]) < 0

    # --- 3️⃣ Trendfilter (MACD muss mind. leicht getrennt sein) ---
    distance = abs(macd - signal)
    min_dist = 0.1  # Tuning möglich

    # --- 4️⃣ Entscheidung ---
    # Kaufsignal: Kreuzung + Momentum + minimale Distanz
    if bullish_cross and momentum_positive and distance > min_dist:
        return "🟢 MACD Signal - Starkes Kaufsignal (Cross + Momentum)"

    # Verkauf: Kreuzung + Momentum + Distanz
    elif bearish_cross and momentum_negative and distance > min_dist:
        return "🔴 MACD Signal - Starkes Verkaufssignal (Cross + Momentum)"

    # Schwaches Kaufsignal (Cross aber wenig Momentum)
    elif bullish_cross:
        return "🟡 MACD Signal - Schwaches Kaufsignal (Cross ohne Momentum)"

    # Schwaches Verkaufssignal
    elif bearish_cross:
        return "🟡 MACD Signal - Schwaches Verkaufssignal (Cross ohne Momentum)"

    else:
        return "🟡 MACD Signal - Haltesignal"

def berechne_macd(data, window_slow=26, window_fast=12, window_sign=9):
    macd = MACD(close=data["Close"], window_slow=window_slow, window_fast=window_fast, window_sign=window_sign)
    # MACD-Diff als Trend-Impuls (positiv = bullish)
    return float(macd.macd_diff().iloc[-1])

def adx_signal(data, adx_threshold=25):
    """
    ADX-basierte Signale:
    - Trendstärke über Schwelle = Signal
    - Directional Indicator +DI und -DI für Richtung
    """
    letzte = data.iloc[-1]

    if letzte["ADX"] < adx_threshold:
        return "🟡 ADX Signal - Kein klarer Trend (ADX zu niedrig)"
    if letzte["+DI"] > letzte["-DI"]:
        return "🟢 ADX Signal - Aufwärtstrend (ADX stark, +DI > -DI)"
    else:
        return "🔴 ADX Signal - Abwärtstrend (ADX stark, +DI < -DI)"

def berechne_adx(data, window=14):
    adx = ADXIndicator(high=data["High"], low=data["Low"], close=data["Close"], window=window)
    return float(adx.adx().iloc[-1])

def stochastic_signal(data: pd.DataFrame) -> str:
    """
    Generiert Kaufs- oder Verkaufssignal basierend auf Stochastic Oscillator.

    Erwartet, dass die Spalten 'Stoch_%K' und 'Stoch_%D' im DataFrame vorhanden sind.
    """

    if len(data) < 2:
        return "🟡 Zu wenige Daten für Stochastic-Signal"

    if not {"Stoch_%K", "Stoch_%D"}.issubset(data.columns):
        return "Daten für Stochastic Oscillator fehlen"

    letzte = data.iloc[-1]
    vorletzte = data.iloc[-2]

    # Kaufsignal: %K kreuzt %D von unten nach oben und beide unter 20
    if (vorletzte["Stoch_%K"] < vorletzte["Stoch_%D"]) and (letzte["Stoch_%K"] > letzte["Stoch_%D"]) and (letzte["Stoch_%K"] < 20) and (letzte["Stoch_%D"] < 20):
        return "🟢 Stochastic Oscillator - Kaufsignal"

    # Verkaufssignal: %K kreuzt %D von oben nach unten und beide über 80
    elif (vorletzte["Stoch_%K"] > vorletzte["Stoch_%D"]) and (letzte["Stoch_%K"] < letzte["Stoch_%D"]) and (letzte["Stoch_%K"] > 80) and (letzte["Stoch_%D"] > 80):
        return "🔴 Stochastic Oscillator - Verkaufssignal"

    else:
        return "🟡 Stochastic Oscillator - Haltesignal"
    
def berechne_stochastic(data, window=14, smooth_window=3):
    stochastic = StochasticOscillator(high=data["High"], low=data["Low"], close=data["Close"], window=window, smooth_window=smooth_window)
    return float(stochastic.stoch().iloc[-1])

def berechne_alle_signale(data):
    signale = {}
    try:
        signale["RSI"] = berechne_rsi(data)
    except Exception as e:
        print(f"RSI Berechnung fehlgeschlagen: {e}")
        signale["RSI"] = 50  # Neutralwert als Fallback

    try:
        signale["MACD"] = berechne_macd(data)
    except Exception as e:
        print(f"MACD Berechnung fehlgeschlagen: {e}")
        signale["MACD"] = 0

    # ADX
    try:
        signale["ADX"] = berechne_adx(data)
    except Exception as e:
        print(f"ADX Berechnung fehlgeschlagen: {e}")
        signale["ADX"] = 20

    # Bollinger Band Abstand
    try:
        signale["Bollinger"] = berechne_bollinger_abstand(data)
    except Exception as e:
        print(f"Bollinger Berechnung fehlgeschlagen: {e}")
        signale["Bollinger"] = 0.5

    # Stochastic
    try:
        signale["Stochastic"] = berechne_stochastic(data)
    except Exception as e:
        print(f"Stochastic Berechnung fehlgeschlagen: {e}")
        signale["Stochastic"] = 50

    return signale
    
signal_gewichtung = {
    "Growth": {
        "RSI": 1.0,
        "MACD": 1.0,
        "Bollinger": 0.8,
        "ADX": 0.7,
        "Stochastic": 0.8
    },
    "Value": {
        "RSI": 0.7,
        "MACD": 0.5,
        "Bollinger": 1.0,
        "ADX": 0.4,
        "Stochastic": 0.9
    },
    "Zyklisch": {
        "RSI": 0.9,
        "MACD": 1.0,
        "Bollinger": 0.7,
        "ADX": 1.0,
        "Stochastic": 0.6
    },
    "Defensiv": {
        "RSI": 0.6,
        "MACD": 0.5,
        "Bollinger": 1.0,
        "ADX": 0.4,
        "Stochastic": 0.7
    },
        "Keine": {  # Falls keine Kategorie zugewiesen wird
        "RSI": 0.5,
        "MACD": 0.5,
        "Bollinger": 0.5,
        "ADX": 0.5,
        "Stochastic": 0.5
    }
}

trading_status_modifikator = {
    "Momentum": {
        "Trend_Signale": 1.2,   # erhöhe Gewicht für Trend-Indikatoren
        "Volatilitaet_Signale": 0.8
    },
    "Volatil": {
        "Trend_Signale": 0.8,
        "Volatilitaet_Signale": 1.2
    },
    "Keine": {
        "Trend_Signale": 1.0,
        "Volatilitaet_Signale": 1.0
    }
}

def berechne_gewichtete_signale(signale, profil, trading_status):
    """
    Berechnet einen Gesamtwert aus technischen Signalen, gewichtet nach Profil und Trading Status.

    signale: dict, z.B. {"RSI": 30, "MACD": 0.5, "ADX": 25, "Bollinger": 1.1, "Stochastic": 70}
    profil: str, z.B. "Growth"
    trading_status: str, z.B. "Momentum"

    Rückgabe: float, Gesamtbewertung (höher = stärkeres Kaufsignal)
    """

    # Gewichtungen laden, fallback auf "Keine"
    prof_weights = signal_gewichtung.get(profil, signal_gewichtung["Keine"])
    ts_mod = trading_status_modifikator.get(trading_status, trading_status_modifikator["Keine"])

    # Indikatoren nach Typ sortieren
    trend_signale = ["RSI", "MACD", "ADX"]
    volatil_signale = ["Bollinger", "Stochastic"]

    gesamt_score = 0.0

    for signal_name, wert in signale.items():
        gewicht = prof_weights.get(signal_name, 0.5)  # default Gewichtung 0.5

        if signal_name in trend_signale:
            gewicht *= ts_mod["Trend_Signale"]
        elif signal_name in volatil_signale:
            gewicht *= ts_mod["Volatilitaet_Signale"]

        # **Signalwerte müssen normiert / skaliert sein!**
        # Hier ein einfaches Beispiel für Interpretation:
        # RSI: Nähe 30 = Kaufsignal, Nähe 70 = Verkaufssignal
        # MACD: Positiv = Trend nach oben, Negativ = Trend nach unten
        # ADX: Je höher, desto stärker der Trend (positive Richtung kann man gesondert auswerten)
        # Bollinger: Abstand von Mittelwert (z.B. unteres Band = Kauf)
        # Stochastic: ähnlich RSI, Nähe 20 = Kauf, Nähe 80 = Verkauf

        # Für Demo nehmen wir an, dass niedrige Werte bei RSI & Stochastic positiv sind,
        # positive MACD Werte positiv sind und höhere ADX Werte positiv sind,
        # Bollinger als Abstand zum unteren Band (>=1 positiv).

        if signal_name == "RSI":
            # Kaufsignal, wenn RSI < 30
            signal_score = max(0, (30 - wert) / 30)  # 1 wenn RSI=0, 0 wenn RSI=30+
        elif signal_name == "Stochastic":
            signal_score = max(0, (20 - wert) / 20)  # 1 wenn 0, 0 wenn >=20
        elif signal_name == "MACD":
            signal_score = max(0, wert)  # positiv ist gut
        elif signal_name == "ADX":
            signal_score = min(wert / 50, 1)  # ADX max 50, >25 stark
        elif signal_name == "Bollinger":
            # z.B. Abstand unteres Band: wenn <1, dann gut
            # Wir nehmen Wert < 1 als Kaufsignal
            signal_score = max(0, 1 - wert)
        else:
            signal_score = 0.5  # Neutral fallback

        gesamt_score += gewicht * signal_score

    return gesamt_score


    
def kombiniertes_signal(data: pd.DataFrame):
    """
    Kombiniert mehrere technische Signale zu einer Gesamtentscheidung:
    - Gewichtet jedes Signal nach Wichtigkeit
    - Berechnet daraus einen Gesamt-Score
    - Liefert Gesamtentscheidung + Einzelsignale zurück
    """

    # Einzelsignale abrufen
    signale = {
        "Bollinger": bollinger_signal(data),
        "RSI": RSI_signal(data),
        "MACD": macd_signal(data),
        "ADX": adx_signal(data),
        "Stochastic": stochastic_signal(data)
    }

    # --- Nur Kaufsignale herausfiltern
    #kaufsignale = filter_kaufsignale(signale)

    # Gewichtungen (du kannst sie anpassen)
    weights = {
        "Bollinger": 0.25,
        "RSI": 0.3,
        "MACD": 0.2,
        "ADX": 0.1,
        "Stochastic": 0.15
    }

    # Hilfsfunktion: Textsignal in Zahl übersetzen
    def map_signal(sig: str) -> int:
        if "Kauf" in sig:
            return 1
        elif "Verkauf" in sig:
            return -1
        else:
            return 0

    # Gesamtbewertung berechnen
    gesamt_score = sum(map_signal(sig) * weights[name] for name, sig in signale.items())

    # Entscheidung nach Score
    if gesamt_score > 0.2:
        finale_entscheidung = "🟢 Kaufen"
    elif gesamt_score < -0.2:
        finale_entscheidung = "🔴 Verkaufen"
    else:
        finale_entscheidung = "🟡 Halten"

    return finale_entscheidung, signale, gesamt_score

def cluster_buy_signal_periods(kaufsignale_df: pd.DataFrame, max_gap_days: int = 5):
    if "Datum" not in kaufsignale_df.columns:
        kaufsignale_df = kaufsignale_df.reset_index()

    daten = kaufsignale_df.sort_values("Datum").reset_index(drop=True)["Datum"]

    perioden = []
    start = daten[0]
    prev = daten[0]

    for current in daten[1:]:
        diff = (current - prev).days
        if diff <= max_gap_days:
            prev = current
        else:
            perioden.append((start, prev))
            start = current
            prev = current
    perioden.append((start, prev))

    return perioden


def evaluate_buy_periods(perioden, full_data,
                         Auswertung_tage, min_veraenderung):
    bewertungen = []

    for (start_datum, end_datum) in perioden:
        # jetzt sind start_datum und end_datum schon Datumswerte
        try:
            start_kurs = full_data.loc[end_datum, "Close"]
        except KeyError:
            bewertungen.append({
                "Start_Datum": start_datum,
                "End_Datum": end_datum,
                "Bewertung": None,
                "Kommentar": "Datum nicht in Daten gefunden"
            })
            continue

        try:
            end_index = full_data.index.get_loc(end_datum)
            lookahead_index = end_index + Auswertung_tage
            if lookahead_index >= len(full_data):
                lookahead_index = len(full_data) - 1
            max_kurs = full_data.iloc[end_index:lookahead_index+1]["Close"].max()
        except Exception as e:
            bewertungen.append({
                "Start_Datum": start_datum,
                "End_Datum": end_datum,
                "Bewertung": None,
                "Kommentar": f"Fehler beim Kursvergleich: {e}"
            })
            continue

        kurs_diff = (max_kurs - start_kurs) / start_kurs
        getroffen = kurs_diff >= min_veraenderung

        bewertungen.append({
            "Start_Datum": start_datum,
            "End_Datum": end_datum,
            "Bewertung": getroffen,
            "Max_Kurs": max_kurs,
            "Start_Kurs": start_kurs,
            "Kurs_Diff": kurs_diff,
            "Kommentar": f"Kursanstieg >= {min_veraenderung*100:.1f}%: {getroffen}"
        })

    return bewertungen


def evaluate_buy_signals(full_data, kaufsignale_df, Auswertung_tage, min_veraenderung):
    """
    Bewertet einzelne Kaufsignale nach Kursentwicklung.

    Parameter:
    - full_data: kompletter DataFrame mit Kursdaten
    - kaufsignale_df: DataFrame mit Kaufsignalen (mit Spalte 'Datum')
    - kombiniertes_signal: Funktion zur Signalgenerierung (optional für Erweiterungen)
    - Auswertung_tage: Anzahl der Tage, um Kursanstieg zu beobachten
    - min_veraenderung: Mindest-Kursanstieg für Treffer
    - min_len_window, innerhalb_zeitraum: Optional, falls für Erweiterungen

    Rückgabe:
    - Dict mit Trefferquote und Anzahl geprüfter Signale
    """

    treffer = 0
    anzahl = 0

    for _, signal_row in kaufsignale_df.iterrows():
        datum = signal_row["Datum"]

        try:
            start_kurs = full_data.loc[datum, "Close"]
        except KeyError:
            continue  # Datum nicht gefunden, überspringen

        try:
            start_index = full_data.index.get_loc(datum)
            end_index = start_index + Auswertung_tage
            if end_index >= len(full_data):
                end_index = len(full_data) - 1
            max_kurs = full_data.iloc[start_index:end_index+1]["Close"].max()
        except Exception:
            continue

        kurs_diff = (max_kurs - start_kurs) / start_kurs
        if kurs_diff >= min_veraenderung:
            treffer += 1
        anzahl += 1

    trefferquote = (treffer / anzahl * 100) if anzahl > 0 else None

    return {
        "Trefferquote_Kauf (%)": trefferquote,
        "Anzahl_geprüfter_Signale": anzahl,
        "Treffer": treffer
    }

def analyse_kaufsignal_perioden(full_data: pd.DataFrame,
                               Auswertung_tage,
                               min_veraenderung,
                               min_len_window: int = 20,
                               innerhalb_zeitraum: bool = True):
    # 1. Alle Signale über den gesamten Zeitraum generieren
    signale_liste = []

    for i in range(min_len_window, len(full_data)):
        fenster = full_data.iloc[:i+1]
        entscheidung, einzelsignale, gesamtscore = kombiniertes_signal(fenster)  # Deine Signalgenerierung
        datum = fenster.index[-1]
        signale_liste.append({"Datum": datum, "Entscheidung": entscheidung, **einzelsignale})

    signale_df = pd.DataFrame(signale_liste)  # signale_df hier erzeugen!

    # 2. Nur Kaufsignale herausfiltern
    kaufsignale_df = signale_df[signale_df["Entscheidung"].str.contains("Kauf")].copy()

    if kaufsignale_df.empty:
        return {
            "Anzahl_Kaufsignale": 0,
            "Trefferquote_Kauf (%)": None,
            "Gesamt_Signale": 0,
            "Signal_Details": signale_df,
            "Perioden": [],
            "Perioden_Bewertung": None
        }

    # 3. Perioden clustern basierend auf echten Handelstagen
    perioden = cluster_buy_signal_periods(kaufsignale_df, max_gap_days=5)

    # 4. Jede Periode bewerten
    perioden_bewertung = evaluate_buy_periods(perioden, full_data,
                                             Auswertung_tage=Auswertung_tage,
                                             min_veraenderung=min_veraenderung)

    # 5. Einzelbewertung (optional)
    einzelbewertung = evaluate_buy_signals(full_data, kaufsignale_df,
                                           Auswertung_tage=Auswertung_tage,
                                           min_veraenderung=min_veraenderung,
                                           )

    return {
        "Anzahl_Kaufsignale": len(kaufsignale_df),
        "Trefferquote_Kauf (%)": einzelbewertung["Trefferquote_Kauf (%)"],
        "Gesamt_Signale": len(signale_df),
        "Signal_Details": signale_df,
        "Perioden": perioden,
        "Perioden_Bewertung": perioden_bewertung,
        "Einzelbewertung": einzelbewertung
    }

def lade_analystenbewertung(symbol):
    ticker = yf.Ticker(symbol)
    anal_data = {}

    # Analysten-Empfehlungen (Buy/Hold/Sell)
    try:
        summary = ticker.recommendations_summary
        # Falls summary nicht None und kein DataFrame, versuche Umwandlung
        if summary is not None and not isinstance(summary, pd.DataFrame):
            summary = pd.DataFrame(summary)
        anal_data["summary"] = summary
    except Exception as e:
        anal_data["summary"] = None

    # Historische Empfehlungen
    try:
        recs = ticker.recommendations
        if recs is not None and not isinstance(recs, pd.DataFrame):
            recs = pd.DataFrame(recs)
        anal_data["recommendations"] = recs
    except Exception as e:
        anal_data["recommendations"] = None

    # Tiefere Analyse wie Wachstum/Kennzahlen
    try:
        analysis = ticker.analysis
        if analysis is not None and not isinstance(analysis, pd.DataFrame):
            analysis = pd.DataFrame(analysis)
        anal_data["analysis"] = analysis
    except Exception as e:
        anal_data["analysis"] = None

    return anal_data


def berechne_rating_bar(summary_df):
    # Falls dict → zu DataFrame konvertieren
    if isinstance(summary_df, dict):
        summary_df = pd.DataFrame([summary_df])

    # Falls summary_df None ist → sicher abfangen
    if summary_df is None:
        return {"Buy": 0, "Hold": 0, "Sell": 0}

    # Falls DataFrame leer ist → sicher abfangen
    if summary_df.empty:
        return {"Buy": 0, "Hold": 0, "Sell": 0}

    # typischerweise: "strongBuy", "buy", "hold", "sell", "strongSell"
    row = summary_df.iloc[0]

    return {
        "Buy": row.get("buy", 0) + row.get("strongBuy", 0),
        "Hold": row.get("hold", 0),
        "Sell": row.get("sell", 0) + row.get("strongSell", 0),
    }

def zeichne_rating_gauge(rating_counts):
    total = sum(rating_counts.values())
    if total == 0:
        buy_percent = 0
    else:
        buy_percent = rating_counts.get("Buy", 0) / total * 100

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=buy_percent,
        title={'text': "Buy-Empfehlungen in %"},
        delta={'reference': 50, 'increasing': {'color': "green"}, 'decreasing': {'color': "red"}},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': "green"},
            'steps': [
                {'range': [0, 33], 'color': "red"},
                {'range': [33, 66], 'color': "orange"},
                {'range': [66, 100], 'color': "green"}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': buy_percent
            }
        }
    ))

    fig.update_layout(height=300, margin=dict(t=0, b=0, l=0, r=0))

    st.plotly_chart(fig, use_container_width=True)

