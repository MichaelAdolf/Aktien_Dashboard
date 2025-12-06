import pandas as pd
import yfinance as yf
import numpy as np  # nur wenn du numpy Funktionen brauchst

def fundamental_analyse(ticker_symbol):
    stock = yf.Ticker(ticker_symbol)
    info = stock.info
    kgv = info.get("trailingPE")
    kuv = info.get("priceToSalesTrailing12Months")
    kbv = info.get("priceToBook")
    marge = info.get("profitMargins")
    beta = info.get("beta")

    score = 0
    if kgv and kgv < 15: score += 20
    if kuv and kuv < 3: score += 20
    if marge and marge > 0.15: score += 20
    if beta and beta < 1.2: score += 20
    ampel = "🟢" if score >= 60 else "🟡" if score >= 40 else "🔴"

    return {
        "Aktie": ticker_symbol,
        "KGV": f"{kgv:.2f}" if kgv else "n/a",
        "KUV": f"{kuv:.2f}" if kuv else "n/a",
        "KBV": f"{kbv:.2f}" if kbv else "n/a",
        "Marge (%)": f"{marge*100:.1f}%" if marge else "n/a",
        "Beta": f"{beta:.2f}" if beta else "n/a",
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

    # Debug-Ausgabe (optional)
    #print(f"Kombinierter Score: {gesamt_score:.2f} → {finale_entscheidung}")

    return finale_entscheidung, signale

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
        entscheidung, einzelsignale = kombiniertes_signal(fenster)  # Deine Signalgenerierung
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

