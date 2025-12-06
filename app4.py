# ------------------------------------------------------
# Dies ist die Haupt-App, welche die ganze Magie triggert
# ------------------------------------------------------

import streamlit as st
import plotly.graph_objects as go
from pathlib import Path
import yfinance as yf
import pandas as pd
from ta.trend import ADXIndicator
from ta.momentum import StochasticOscillator

# ------------------------------------------------------
# Funktionen Import von weiterem Skript
# ------------------------------------------------------
from core_magic import (
    lade_aktien
)

from streamlit_visualization_6 import (
    go_to,
    home_page,
    aktienseite
)

THEMEN = lade_aktien()
if not THEMEN:
    st.warning("Datei Watchlist.txt wurde nicht gefunden oder ist leer.")

# ------------------------------------------------------
# Navigation
# ------------------------------------------------------
if "page" not in st.session_state:
    st.session_state.page = "home"

# ------------------------------------------------------
# Home
# ------------------------------------------------------
if st.session_state.page == "home":
    home_page(THEMEN)

# ------------------------------------------------------
# Aktienseite
# ------------------------------------------------------
else:
    symbol = st.session_state.page
    aktienseite(symbol)

    # Navigation zurück
    if st.button("⬅️ Zurück zur Startseite"):
        go_to("home")
