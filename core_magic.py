from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import streamlit as st
import plotly.graph_objects as go
from ta.trend import ADXIndicator
from ta.momentum import StochasticOscillator

# ------------------------------------------------------
# Themen aus der definierten Watchlist laden
# ------------------------------------------------------
@st.cache_data(show_spinner=False)
def lade_aktien(pfad="Watchlist.txt"):
    file = Path(pfad)
    if not file.exists():
        st.warning(f"Datei {pfad} wurde nicht gefunden.")
        return []
    with open(file, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]
    
# ------------------------------------------------------
# Lade Daten
# ------------------------------------------------------
@st.cache_data(show_spinner=False)
def lade_daten_aktie(symbol: str, period="3y") -> pd.DataFrame:
    ticker = yf.Ticker(symbol)
    data = ticker.history(period=period)
    if data.empty:
        raise ValueError(f"Keine Daten für {symbol} gefunden.")
    return data

# ------------------------------------------------------
# Fundamentaldaten laden
# ------------------------------------------------------
def lade_fundamentaldaten(ticker_symbol):
    ticker = yf.Ticker(ticker_symbol)
    info = ticker.info
    fundamentaldaten = {
        "KGV": info.get("trailingPE", "N/A"),
        "Dividendenrendite": info.get("dividendYield", "N/A"),
        "Marktkapitalisierung": info.get("marketCap", "N/A"),
        "Gewinn je Aktie (EPS)": info.get("trailingEps", "N/A")
    }
    # Optional: Formatieren der Werte
    if fundamentaldaten["Dividendenrendite"] != "N/A":
        fundamentaldaten["Dividendenrendite (%)"] = fundamentaldaten.pop("Dividendenrendite") * 100
    if fundamentaldaten["Marktkapitalisierung"] != "N/A":
        mkt = fundamentaldaten["Marktkapitalisierung"]
        if isinstance(mkt, (int, float)):
            if mkt > 1e12:
                fundamentaldaten["Marktkapitalisierung"] = f"{mkt / 1e12:.2f} Bio."
            elif mkt > 1e9:
                fundamentaldaten["Marktkapitalisierung"] = f"{mkt / 1e9:.2f} Mrd."
            elif mkt > 1e6:
                fundamentaldaten["Marktkapitalisierung"] = f"{mkt / 1e6:.2f} Mio."
    return fundamentaldaten

# ------------------------------------------------------
# Indikatoren berechnen
# ------------------------------------------------------
@st.cache_data(show_spinner=False)
def berechne_indikatoren(data: pd.DataFrame) -> pd.DataFrame:
    # Berechne technische Indikatoren hier, z.B.:
    data = data.copy()
    data["MA10"] = data["Close"].rolling(window=10).mean()
    data["MA50"] = data["Close"].rolling(window=50).mean()

    # Bollinger Bänder
    ma20 = data["Close"].rolling(window=20).mean()
    std20 = data["Close"].rolling(window=20).std()
    data["BB_Upper"] = ma20 + 2 * std20
    data["BB_Lower"] = ma20 - 2 * std20

    # MACD Beispiel (schnell/ langsam/ signal)
    exp1 = data["Close"].ewm(span=12, adjust=False).mean()
    exp2 = data["Close"].ewm(span=26, adjust=False).mean()
    data["MACD"] = exp1 - exp2
    data["MACD_Signal"] = data["MACD"].ewm(span=9, adjust=False).mean()
    data["MACD_Hist"] = data["MACD"] - data["MACD_Signal"]

    # RSI (14 Tage)
    delta = data["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    data["RSI"] = 100 - (100 / (1 + rs))

    # ATR (Average True Range) 14 Tage
    high_low = data["High"] - data["Low"]
    high_close = (data["High"] - data["Close"].shift()).abs()
    low_close = (data["Low"] - data["Close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    data["ATR"] = tr.rolling(window=14).mean()

    # Beispiel Support/Resistance - hier Dummywerte (besser mit echter Methode berechnen)
    data["Support1"] = data["Close"].rolling(window=20).min()
    data["Support2"] = data["Close"].rolling(window=50).min()
    data["Resistance1"] = data["Close"].rolling(window=20).max()
    data["Resistance2"] = data["Close"].rolling(window=50).max()

    # Stochastic Oscillator
    stoch = StochasticOscillator(data['High'], data['Low'], data['Close'], window=14, smooth_window=3)
    data['Stoch_%K'] = stoch.stoch()
    data['Stoch_%D'] = stoch.stoch_signal()

    # ADX
    adx_ind = ADXIndicator(data['High'], data['Low'], data['Close'], window=14)
    data['ADX'] = adx_ind.adx()
    data['+DI'] = adx_ind.adx_pos()
    data['-DI'] = adx_ind.adx_neg()


    # Ichimoku Cloud berechnen 
    high_9 = data['High'].rolling(window=9).max()
    low_9 = data['Low'].rolling(window=9).min()
    data['Tenkan_sen'] = (high_9 + low_9) / 2
    
    high_26 = data['High'].rolling(window=26).max()
    low_26 = data['Low'].rolling(window=26).min()
    data['Kijun_sen'] = (high_26 + low_26) / 2
    
    data['Senkou_Span_A'] = ((data['Tenkan_sen'] + data['Kijun_sen']) / 2).shift(26)
    
    high_52 = data['High'].rolling(window=52).max()
    low_52 = data['Low'].rolling(window=52).min()
    data['Senkou_Span_B'] = ((high_52 + low_52) / 2).shift(26)
    
    data['Chikou_Span'] = data['Close'].shift(-26)

    return data