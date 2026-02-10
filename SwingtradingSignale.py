import pandas as pd
import numpy as np
import streamlit as st

class RSIAnalysis:
    """
    Professionelle RSI-Regime-Analyse
    ---------------------------------
    Erkennt:
    - Marktregime (Bullish / Bearish / Sideways)
    - Überdehnung
    - Stärke der Aussage
    """

    def __init__(
        self,
        oversold: int = 30,
        overbought: int = 70,
        bullish_floor: int = 40,
        bearish_ceiling: int = 60
    ):
        self.oversold = oversold
        self.overbought = overbought
        self.bullish_floor = bullish_floor
        self.bearish_ceiling = bearish_ceiling

    def analyse(self, data: pd.DataFrame) -> dict:
        if "RSI" not in data.columns or len(data) < 2:
            return self._empty_result("RSI-Daten fehlen")

        rsi = float(data["RSI"].iloc[-1])
        prev_rsi = float(data["RSI"].iloc[-2])

        # -------------------------
        # Regime-Erkennung
        # -------------------------
        if rsi >= self.bullish_floor and prev_rsi >= self.bullish_floor:
            market_regime = "bullish"
        elif rsi <= self.bearish_ceiling and prev_rsi <= self.bearish_ceiling:
            market_regime = "bearish"
        else:
            market_regime = "sideways"

        # -------------------------
        # Überdehnung
        # -------------------------
        if rsi <= self.oversold:
            state = "oversold"
            bias = "mean_reversion_long"
            strength = min(1.0, (self.oversold - rsi) / self.oversold + 0.3)
            interpretation = {
                "headline": "Stark überverkauft",
                "meaning": "Der Kurs wurde stark verkauft und ist technisch überdehnt.",
                "chance": "Kurzfristige technische Erholung möglich.",
                "risk": "In starken Abwärtstrends kann der RSI lange überverkauft bleiben.",
                "typical_action": "Nur für kurzfristige Trades geeignet"
            }

        elif rsi >= self.overbought:
            state = "overbought"
            bias = "mean_reversion_short"
            strength = min(1.0, (rsi - self.overbought) / (100 - self.overbought) + 0.3)
            interpretation = {
                "headline": "Stark überkauft",
                "meaning": "Der Kurs ist kurzfristig stark gestiegen und technisch überdehnt.",
                "chance": "Rücksetzer oder Seitwärtsphase möglich.",
                "risk": "In starken Aufwärtstrends kann der RSI lange überkauft bleiben.",
                "typical_action": "Gewinne absichern oder Teilverkäufe prüfen"
            }

        else:
            if market_regime == "bullish" and rsi >= 55:
                state = "bullish_strength"
                bias = "trend_follow_long"
                strength = (rsi - 50) / 50
                interpretation = {
                    "headline": "Trendstärke im Aufwärtstrend",
                    "meaning": "Der RSI bestätigt einen stabilen Aufwärtstrend.",
                    "chance": "Trendfortsetzung wahrscheinlich.",
                    "risk": "Überhitzung bei sehr schnellem Anstieg möglich.",
                    "typical_action": "Trendfolge – Rücksetzer abwarten"
                }

            elif market_regime == "bearish" and rsi <= 45:
                state = "bearish_weakness"
                bias = "trend_follow_short"
                strength = (50 - rsi) / 50
                interpretation = {
                    "headline": "Abwärtsdruck bestätigt",
                    "meaning": "Der RSI bestätigt einen schwachen Markt.",
                    "chance": "Weitere Abgaben möglich.",
                    "risk": "Plötzliche Gegenbewegungen möglich.",
                    "typical_action": "Short-orientiert oder abwarten"
                }

            else:
                state = "neutral"
                bias = "none"
                strength = 0.0
                interpretation = {
                    "headline": "Neutral",
                    "meaning": "Der RSI zeigt aktuell keine klare Richtung.",
                    "chance": "Ausbruch aus der Range möglich.",
                    "risk": "Fehlsignale bei Seitwärtsmarkt.",
                    "typical_action": "Bestätigung durch andere Indikatoren abwarten"
                }

        return {
            "value": round(rsi, 2),
            "regime": market_regime,
            "state": state,
            "bias": bias,
            "strength": round(float(strength), 2),
            "interpretation": interpretation
        }
    
    def analyze_history(self, data):
        result = {
            "oversold_pct": round((data["RSI"] < self.oversold).mean() * 100, 1),
            "overbought_pct": round((data["RSI"] > self.overbought).mean() * 100, 1),
            "avg_rsi": round(data["RSI"].mean(), 2),
            "min_rsi": round(data["RSI"].min(), 2),
            "max_rsi": round(data["RSI"].max(), 2),
        }
        self.oversold_prozent = result["oversold_pct"]
        self.overbought_prozent = result["overbought_pct"]
        return result

    @staticmethod
    def _empty_result(reason: str) -> dict:
        return {
            "value": None,
            "regime": "unknown",
            "state": "invalid",
            "bias": "none",
            "strength": 0.0,
            "interpretation": reason
        }
    
    """
    rsi_analyser = RSIAnalysis()
    rsi_result = rsi_analyser.analyse(data)

    st.metric("RSI", rsi_result["value"])
    st.write(rsi_result["interpretation"])
    st.progress(rsi_result["strength"])
    """

class MACDAnalysis:
    """
    Professionelle MACD-Regime-Analyse
    ----------------------------------
    Erkennt:
    - Trendrichtung
    - Momentum
    - Übergangsphasen (Reversal / Weakening)
    """

    def __init__(
        self,
        min_hist_strength: float = 0.05
    ):
        self.min_hist_strength = min_hist_strength

    def analyse(self, data: pd.DataFrame) -> dict:
        required = {"MACD", "MACD_Signal", "MACD_Hist"}
        if not required.issubset(data.columns) or len(data) < 3:
            return self._empty_result("MACD-Daten fehlen")

        macd = float(data["MACD"].iloc[-1])
        signal = float(data["MACD_Signal"].iloc[-1])
        hist = float(data["MACD_Hist"].iloc[-1])

        prev_hist = float(data["MACD_Hist"].iloc[-2])
        prev_macd = float(data["MACD"].iloc[-2])

        # -------------------------
        # Grundregime (Trendrichtung)
        # -------------------------
        if macd > signal:
            regime = "bullish"
        elif macd < signal:
            regime = "bearish"
        else:
            regime = "neutral"

        # -------------------------
        # Momentum-Bewertung
        # -------------------------
        hist_trend = hist - prev_hist
        macd_trend = macd - prev_macd

        # -------------------------
        # Zustände
        # -------------------------
        if regime == "bullish":
            if hist > self.min_hist_strength and hist_trend > 0:
                state = "bullish_expansion"
                bias = "trend_follow_long"
                strength = min(1.0, abs(hist) * 5)
                interpretation = {
                    "headline": "Aufwärtstrend beschleunigt sich",
                    "meaning": "Der Markt befindet sich in einem Aufwärtstrend und das Momentum nimmt weiter zu.",
                    "chance": "Trendfortsetzung mit steigender Dynamik wahrscheinlich.",
                    "risk": "Späte Einstiege können zu Rücksetzern führen.",
                    "typical_action": "Trendfolge – Rücksetzer für Einstieg abwarten"
                }

            elif hist_trend < 0:
                state = "bullish_weakening"
                bias = "caution_long"
                strength = min(1.0, abs(hist_trend) * 3)
                interpretation = {
                    "headline": "Aufwärtstrend verliert Momentum",
                    "meaning": "Der übergeordnete Trend ist positiv, aber die Dynamik lässt nach.",
                    "chance": "Seitwärtsphase oder kurze Konsolidierung möglich.",
                    "risk": "Trend kann kippen, wenn Momentum weiter abnimmt.",
                    "typical_action": "Long-Positionen absichern oder Teilgewinne mitnehmen"
                }

            else:
                state = "bullish_neutral"
                bias = "trend_follow_long"
                strength = 0.2
                interpretation = {
                    "headline": "Stabiler Aufwärtstrend",
                    "meaning": "Der Markt steigt, aber ohne zusätzliche Beschleunigung.",
                    "chance": "Solide Trendfortsetzung möglich.",
                    "risk": "Fehlende Dynamik kann zu Seitwärtsbewegung führen.",
                    "typical_action": "Trend halten – auf Momentum-Zunahme achten"
                }

        elif regime == "bearish":
            if hist < -self.min_hist_strength and hist_trend < 0:
                state = "bearish_expansion"
                bias = "trend_follow_short"
                strength = min(1.0, abs(hist) * 5)
                interpretation = {
                    "headline": "Abwärtstrend verstärkt sich",
                    "meaning": "Der Markt befindet sich in einem klaren Abwärtstrend mit zunehmendem Verkaufsdruck.",
                    "chance": "Weitere Kursverluste wahrscheinlich.",
                    "risk": "Technische Gegenbewegungen können abrupt auftreten.",
                    "typical_action": "Short-Trades bevorzugen oder Longs meiden"
                }

            elif hist_trend > 0:
                state = "bearish_weakening"
                bias = "caution_short"
                strength = min(1.0, abs(hist_trend) * 3)
                interpretation = {
                    "headline": "Abwärtsdruck lässt nach",
                    "meaning": "Der Abwärtstrend verliert an Dynamik.",
                    "chance": "Erholung oder Seitwärtsphase möglich.",
                    "risk": "Trend kann nach kurzer Pause weiterlaufen.",
                    "typical_action": "Short-Gewinne sichern – Bestätigung abwarten"
                }

            else:
                state = "bearish_neutral"
                bias = "trend_follow_short"
                strength = 0.2
                interpretation = {
                    "headline": "Stabiler Abwärtstrend",
                    "meaning": "Der Markt fällt gleichmäßig ohne zusätzliche Beschleunigung.",
                    "chance": "Weiterer Abwärtsverlauf wahrscheinlich.",
                    "risk": "Plötzliche Gegenbewegungen möglich.",
                    "typical_action": "Short-orientiert bleiben, Stops beachten"
                }

        else:
            state = "transition"
            bias = "wait"
            strength = 0.0
            interpretation = {
                "headline": "Trendwechselphase",
                "meaning": "Der MACD zeigt aktuell keine klare Trendrichtung.",
                "chance": "Neuer Trend kann sich entwickeln.",
                "risk": "Erhöhte Fehlsignale in Übergangsphasen.",
                "typical_action": "Abwarten und andere Indikatoren nutzen"
            }

        return {
            "macd": round(macd, 4),
            "signal": round(signal, 4),
            "histogram": round(hist, 4),
            "regime": regime,
            "state": state,
            "bias": bias,
            "strength": round(float(strength), 2),
            "interpretation": interpretation
        }


    @staticmethod
    def _empty_result(reason: str) -> dict:
        return {
            "macd": None,
            "signal": None,
            "histogram": None,
            "regime": "unknown",
            "state": "invalid",
            "bias": "none",
            "strength": 0.0,
            "interpretation": reason
        }
    

class ADXAnalysis:
    """
    ADX Regime Analyse
    ------------------
    Erkennt:
    - Trendstärke
    - Trendrichtung (nur wenn valide)
    - Trading-Umfeld (Trend vs. Range)
    """

    def __init__(
        self,
        weak_trend: float = 20,
        strong_trend: float = 25,
        extreme_trend: float = 40
    ):
        self.weak_trend = weak_trend
        self.strong_trend = strong_trend
        self.extreme_trend = extreme_trend

    def analyse(self, data: pd.DataFrame) -> dict:
        required = {"ADX", "+DI", "-DI"}
        if not required.issubset(data.columns) or len(data) < 2:
            return self._empty_result("ADX-Daten fehlen")

        adx = float(data["ADX"].iloc[-1])
        pdi = float(data["+DI"].iloc[-1])
        mdi = float(data["-DI"].iloc[-1])

        prev_adx = float(data["ADX"].iloc[-2])
        adx_trend = adx - prev_adx

        # -------------------------
        # Trendrichtung (nur sekundär!)
        # -------------------------
        if pdi > mdi:
            direction = "bullish"
        elif mdi > pdi:
            direction = "bearish"
        else:
            direction = "neutral"

        # -------------------------
        # Regime & State
        # -------------------------
        if adx < self.weak_trend:
            regime = "range"
            state = "no_trend"
            bias = "mean_reversion"
            strength = 0.0
            summary = "Seitwärtsmarkt"
            interpretation_short = "Kein klarer Trend – Trendstrategien meiden"
            interpretation_long = (
                "Der ADX liegt unterhalb der Trend-Schwelle. "
                "Der Markt bewegt sich überwiegend seitwärts. "
                "Trendfolgestrategien sind in solchen Phasen meist ineffektiv, "
                "während kurzfristige Gegenbewegungen häufiger auftreten."
            )
            chance = "Kurzfristige Gegenbewegungen bieten Trading-Gelegenheiten."
            risk = "Trendfolgestrategien sind ineffektiv, Risiko von Fehlsignalen."
            action_hint = "Abwarten / Range-Strategien"
        elif self.weak_trend <= adx < self.strong_trend:
            regime = "emerging_trend"
            state = f"{direction}_emerging"
            bias = "wait_for_confirmation"
            strength = (adx - self.weak_trend) / (self.strong_trend - self.weak_trend)
            summary = "Trend im Aufbau"
            interpretation_short = "Möglicher Trend – noch unbestätigt"
            interpretation_long = (
                "Der ADX steigt, hat aber noch keinen stabilen Trendbereich erreicht. "
                "Das deutet auf einen entstehenden Trend hin, der sich jedoch noch "
                "als Fehlsignal entpuppen kann."
            )
            chance = "Trend entsteht, mögliche frühe Einstiege."
            risk = "Trend ist noch unsicher, Fehlsignale möglich."
            action_hint = "Beobachten"

        elif self.strong_trend <= adx < self.extreme_trend:
            regime = "strong_trend"
            state = f"{direction}_trend"
            bias = f"trend_follow_{direction}"
            strength = min(1.0, adx / self.extreme_trend)
            summary = "Starker Trend"
            interpretation_short = "Stabiler Trend – gute Trendfolge"
            interpretation_long = (
                "Der ADX signalisiert einen klaren und stabilen Trend. "
                "In solchen Marktphasen haben Trendfolgestrategien eine erhöhte "
                "Erfolgswahrscheinlichkeit, da sich Bewegungen oft fortsetzen."
            )
            chance = "Klare Trendrichtung, Trendfolgestrategien erfolgversprechend."
            risk = "Markt kann plötzliche Gegenbewegungen zeigen."
            action_hint = "Trend handeln"

        else:
            regime = "extreme_trend"
            state = f"{direction}_exhaustion"
            bias = "risk_of_reversal"
            strength = 1.0
            summary = "Überdehnter Trend"
            interpretation_short = "Sehr starker Trend – Rücksetzer möglich"
            interpretation_long = (
                "Der ADX liegt auf extrem hohem Niveau. "
                "Solche Phasen gehen häufig mit einer Überdehnung einher. "
                "Neueinstiege bergen ein erhöhtes Risiko für plötzliche Rücksetzer "
                "oder Trendwenden."
            )
            chance = "Trend hat viel Kraft, Gewinnmitnahmen können sinnvoll sein."
            risk = "Hohe Gefahr von Trendwende oder plötzlichen Rücksetzern."
            action_hint = "Gewinne sichern / Vorsicht"

        # -------------------------
        # Trendbeschleunigung
        # -------------------------
        if adx_trend > 0:
            trend_acceleration = " Trend nimmt an Stärke zu"
        elif adx_trend < 0:
            trend_acceleration = " Trend verliert an Stärke"

        return {
            "adx": round(adx, 2),
            "pdi": round(pdi, 2),
            "mdi": round(mdi, 2),
            "regime": regime,
            "state": state,
            "bias": bias,
            "strength": round(float(strength), 2),
            "summary": summary,
            "interpretation_short": interpretation_short,
            "trend_acceleration": trend_acceleration,
            "interpretation_long": interpretation_long,
            "chance": chance,
            "risk": risk,
            "action_hint": action_hint
        }

    @staticmethod
    def _empty_result(reason: str) -> dict:
        return {
            "adx": None,
            "pdi": None,
            "mdi": None,
            "regime": "unknown",
            "state": "invalid",
            "bias": "none",
            "strength": 0.0,
            "interpretation": reason
        }
    
class BollingerAnalysis:
    def analyze(self, data):
        last = data.iloc[-1]

        close = last["Close"]
        upper = last["BB_Upper"]
        lower = last["BB_Lower"]
        mid = last["BB_Middle"]

        width = (upper - lower) / mid

        if close <= lower:
            state = "Below_Lower"
            score = +1
            summary = "Preis am unteren Band"
            interpretation_short = "Preis liegt am unteren Band"
            interpretation_long = (
                "Der Kurs notiert am unteren Bollinger-Band, was auf eine starke Unterbewertung "
                "und erhöhte Volatilität hinweist. Dies kann eine attraktive Einstiegszone für Long-Positionen darstellen, "
                "jedoch besteht das Risiko weiterer Abwärtsbewegungen."
            )
            action_hint = "Mögliches Kaufsignal – Risiko beachten"
            chance = "Attraktiver Einstiegszeitpunkt bei potenzieller Bodenbildung."
            risk = "Markt könnte weiter fallen, trotz Überverkauftheit."

        elif close < mid:
            state = "Lower_Half"
            score = +0.5
            state = "Lower_Half"
            score = +0.5
            summary = "Preis in der unteren Hälfte"
            interpretation_short = "Preis in der unteren Hälfte"
            interpretation_long = (
                "Der Kurs bewegt sich in der unteren Hälfte der Bollinger-Bänder, was auf eine potenziell "
                "günstige Long-Position hinweist. Die Volatilität ist moderat, und der Markt zeigt keine extremen Bewegungen."
            )
            action_hint = "Long-Position möglich, Trend beobachten"
            chance = "Preis in günstiger Zone, moderates Aufwärtspotenzial."
            risk = "Trend könnte seitwärts oder schwach bleiben."

        elif close > upper:
            state = "Above_Upper"
            score = -1
            summary = "Preis über dem oberen Band"
            interpretation_short = "Preis über dem oberen Band"
            interpretation_long = (
                "Der Kurs notiert oberhalb des oberen Bollinger-Bandes und gilt als überdehnt. "
                "Dies weist auf eine mögliche technische Gegenreaktion hin, und es besteht ein erhöhtes Risiko für Rücksetzer."
            )
            action_hint = "Vorsicht bei Neueinstiegen – Gewinnmitnahmen erwägen"
            chance = "Starke Aufwärtsdynamik vorhanden."
            risk = "Hohe Wahrscheinlichkeit für technische Gegenreaktion."

        else:
            state = "Neutral"
            score = 0
            summary = "Preis nahe Mittelband"
            interpretation_short = "Preis nahe Mittelband"
            interpretation_long = (
                "Der Kurs befindet sich nahe dem mittleren Bollinger-Band, was auf eine stabile Marktphase "
                "ohne ausgeprägte Über- oder Unterbewertung hindeutet."
            )
            action_hint = "Abwarten oder Seitwärtsstrategie nutzen"
            chance = "Markt zeigt Stabilität ohne Extreme."
            risk = "Keine klaren Signale, mögliche Seitwärtsbewegung."

        return {
            "state": state,
            "score": score,
            "bandwidth": round(width, 3),
            "interpretation_short": interpretation_short,
            "summary": summary,
            "interpretation_long": interpretation_long,
            "action_hint": action_hint,
            "chance": chance,
            "risk": risk
        }

class StochasticAnalysis:
    def analyze(self, data):
        last = data.iloc[-1]
        prev = data.iloc[-2]

        k = last["Stoch_%K"]
        d = last["Stoch_%D"]

        bullish_cross = prev["Stoch_%K"] < prev["Stoch_%D"] and k > d
        bearish_cross = prev["Stoch_%K"] > prev["Stoch_%D"] and k < d

        if k < 20 and bullish_cross:
            regime = "Oversold_Reversal"
            score = +1
            summary = "Überverkauftes bullishes Signal"
            interpretation_short = "Überverkauft und günstiges Kaufsignal"
            interpretation_long = (
                "Der Stochastic-Oszillator zeigt eine Überverkauft-Situation zusammen mit "
                "einem bullischen Kreuz (K % über D %). Das kann eine gute Gelegenheit für eine technische "
                "Gegenbewegung oder Trendwende sein."
            )
            action_hint = "Long-Position erwägen, Stop-Loss setzen"
            chance = "Hohe Wahrscheinlichkeit für Erholung oder Trendwende."
            risk = "Signal kann in starkem Abwärtstrend versagen, weitere Bestätigung nötig."

        elif k > 80 and bearish_cross:
            regime = "Overbought_Reversal"
            score = -1
            summary = "Überkauftes bearishes Signal"
            interpretation_short = "Überkauft mit Verkaufsignal"
            interpretation_long = (
                "Der Indikator signalisiert eine Überkauft-Situation mit einem bearischen Kreuz. "
                "Das weist auf eine mögliche Trendwende nach unten oder einen Rücksetzer hin."
            )
            action_hint = "Gewinne sichern, Short-Position prüfen"
            chance = "Potenzial für kurzfristige Korrektur oder Trendwende."
            risk = "Signal könnte ein Fehlausbruch sein, Trend könnte anhalten."

        elif k > d and k < 80:
            regime = "Bullish_Momentum"
            score = +0.5
            summary = "Positives Momentum"
            interpretation_short = "Bullishes Momentum, aber nicht überkauft"
            interpretation_long = (
                "Der Stochastic zeigt, dass das Momentum auf der Long-Seite liegt, "
                "jedoch ohne extreme Überkauft-Signale. Eine moderate Aufwärtsbewegung ist wahrscheinlich."
            )
            action_hint = "Positionen halten oder ausbauen"
            chance = "Fortsetzung des Aufwärtstrends mit moderatem Risiko."
            risk = "Markt kann kurzfristig konsolidieren oder korrigieren."

        elif k < d and k > 20:
            regime = "Bearish_Momentum"
            score = -0.5
            summary = "Negatives Momentum"
            interpretation_short = "Bearishes Momentum ohne Überverkauft"
            interpretation_long = (
                "Das Momentum liegt auf der Short-Seite, aber ohne eine ausgeprägte Überverkauft-Situation. "
                "Der Trend könnte sich abschwächen oder eine Korrektur einleiten."
            )
            action_hint = "Vorsicht walten lassen, Stopp beachten"
            chance = "Möglichkeit für Trendwende oder kurzfristige Erholung."
            risk = "Abschwächung könnte nur eine Pause sein, Abwärtstrend bleibt intakt."

        else:
            regime = "Neutral"
            score = 0
            summary = "Kein klares Timing"
            interpretation_short = "Neutraler Zustand"
            interpretation_long = (
                "Der Stochastic-Indikator liefert derzeit keine klaren Signale für eine Trendwende oder ein "
                "starkes Momentum. Marktbewegungen sind eher unentschlossen."
            )
            action_hint = "Abwarten und Markt beobachten"
            chance = "Markt könnte sich bald entscheiden, gute Einstiegsgelegenheiten möglich."
            risk = "Unklare Marktphase birgt Unsicherheit und erhöhtes Risiko."

        return {
            "regime": regime,
            "score": score,
            "k": round(k, 2),
            "d": round(d, 2),
            "summary": summary,
            "interpretation_short": interpretation_short,
            "interpretation_long": interpretation_long,
            "action_hint": action_hint,
            "chance": chance,
            "risk": risk
        }

class MarketRegimeAnalysis:
    """
    Kombiniert RSI, MACD und ADX zu einem übergeordneten Market-Regime
    """

    def analyse(
        self,
        rsi: dict,
        macd: dict,
        adx: dict
    ) -> dict:

        # Default-Werte setzen, damit Variablen immer definiert sind
        market_regime = "unknown"
        trade_bias = "none"
        confidence = 0.0
        summary = "Unbekanntes Regime"
        interpretation_short = "Keine klare Marktlage erkennbar"
        interpretation_long = (
            "Die Kombination der Indikatoren liefert kein eindeutiges Bild "
            "des Marktregimes."
        )
        action_hint = "Abwarten und weitere Signale beobachten"

        # --------------------------------------------------
        # 1️⃣ RANGE / MEAN REVERSION
        # --------------------------------------------------
        if adx["regime"] == "range":

            market_regime = "range_market"
            trade_bias = "mean_reversion"
            confidence = 0.4

            summary = "Seitwärtsmarkt"
            if rsi["state"] == "oversold":
                interpretation_short = "RSI überverkauft im Seitwärtsmarkt"
                interpretation_long = (
                    "Der Markt befindet sich in einer Seitwärtsphase mit "
                    "überverkauftem RSI. Dies kann eine Chance für technische "
                    "Gegenbewegungen (Long-Reversal) bieten."
                )
                action_hint = "Long-Reversal möglich, aber vorsichtig agieren"
            elif rsi["state"] == "overbought":
                interpretation_short = "RSI überkauft im Seitwärtsmarkt"
                interpretation_long = (
                    "Der Markt ist seitwärts mit überkaufter RSI-Situation, "
                    "was auf Short-Reversal Chancen hinweist."
                )
                action_hint = "Short-Reversal möglich, Risiko beachten"
            else:
                interpretation_short = "Seitwärtsmarkt ohne Überdehnung"
                interpretation_long = (
                    "Der Markt zeigt keine starke Über- oder Unterbewertung "
                    "und befindet sich in einer neutralen Seitwärtsphase."
                )
                action_hint = "Range-Strategien oder Abwarten"

        # --------------------------------------------------
        # 2️⃣ EMERGING TREND
        # --------------------------------------------------
        elif adx["regime"] == "emerging_trend":

            market_regime = "transition_phase"
            trade_bias = "wait_for_confirmation"
            confidence = 0.5

            summary = "Trend im Aufbau"
            interpretation_short = "Trend entsteht, noch unsicher"
            interpretation_long = (
                "Der ADX signalisiert den Beginn eines neuen Trends. "
                "Eine Bestätigung ist jedoch noch ausstehend, daher sollten "
                "Positionen vorsichtig aufgebaut oder zunächst abgewartet werden."
            )
            action_hint = "Kleine Positionen oder abwarten"

        # --------------------------------------------------
        # 3️⃣ STRONG TREND
        # --------------------------------------------------
        elif adx["regime"] == "strong_trend":

            market_regime = "trend_market"
            trade_bias = macd["bias"]
            confidence = 0.75

            summary = "Starker Trend"
            if macd["bias"] == "bullish":
                if rsi["state"] in ["neutral", "bullish"]:
                    interpretation_short = "Starker Aufwärtstrend"
                    interpretation_long = (
                        "Markt zeigt einen stabilen Aufwärtstrend, unterstützt "
                        "durch MACD und RSI. Trendfolgestrategien haben gute Erfolgschancen."
                    )
                    action_hint = "Trend folgen, Long-Positionen bevorzugen"
                else:
                    interpretation_short = "Aufwärtstrend mit kurzfristiger Überdehnung"
                    interpretation_long = (
                        "Trend ist intakt, jedoch weist der RSI auf eine mögliche "
                        "kurzfristige Überdehnung hin. Vorsicht bei Neueinstiegen."
                    )
                    action_hint = "Gewinne sichern, Vorsicht bei Einstiegen"
            elif macd["bias"] == "bearish":
                if rsi["state"] in ["neutral", "bearish"]:
                    interpretation_short = "Starker Abwärtstrend"
                    interpretation_long = (
                        "Markt zeigt einen stabilen Abwärtstrend, unterstützt "
                        "durch MACD und RSI. Short-Positionen sind bevorzugt."
                    )
                    action_hint = "Trend folgen, Short-Positionen bevorzugen"
                else:
                    interpretation_short = "Abwärtstrend mit kurzfristiger Überdehnung"
                    interpretation_long = (
                        "Trend ist intakt, aber RSI weist auf mögliche kurzfristige "
                        "Erholung oder Überdehnung hin. Vorsicht bei Neueinstiegen."
                    )
                    action_hint = "Gewinne sichern, Vorsicht bei Einstiegen"

        # --------------------------------------------------
        # 4️⃣ EXTREMER TREND / ERSCHÖPFUNG
        # --------------------------------------------------
        elif adx["regime"] == "extreme_trend":

            market_regime = "late_trend"
            trade_bias = "risk_management"
            confidence = 0.6

            summary = "Extremer Trend"
            interpretation_short = "Sehr starker Trend mit Erschöpfungsrisiko"
            interpretation_long = (
                "Der Markt befindet sich in einem extrem starken Trend, der "
                "weiterlaufen kann, aber das Risiko einer Trendwende oder "
                "starker Rücksetzer stark gestiegen ist."
            )
            action_hint = "Gewinne sichern, Stop-Loss anpassen, vorsichtig handeln"

        else:
            summary = "Unbekanntes Regime"
            interpretation_short = "Keine klare Marktlage erkennbar"
            interpretation_long = (
                "Die Kombination der Indikatoren liefert kein eindeutiges Bild "
                "des Marktregimes."
            )
            action_hint = "Abwarten und weitere Signale beobachten"

        return {
            "market_regime": market_regime,
            "trade_bias": trade_bias,
            "confidence": round(confidence, 2),
            "summary": summary,
            "interpretation_short": interpretation_short,
            "interpretation_long": interpretation_long,
            "action_hint": action_hint
        }
    
class EntryQualityAnalysis:
    """
    Bewertet die Qualität des Einstiegs (Timing & Preis)
    unabhängig von der Trade-Entscheidung
    """

    def analyse(
        self,
        bollinger: dict,
        stochastic: dict,
        market: dict
    ) -> dict:

        score = 0.0
        quality = "poor"
        interpretation_list = []

        # ---------------------------------------
        # Bollinger Bewertung (Preisniveau)
        # ---------------------------------------
        score += bollinger.get("score", 0)

        if bollinger["state"] in ["Below_Lower", "Lower_Half"]:
            interpretation_list.append("Preis attraktiv (Bollinger)")
        elif bollinger["state"] == "Above_Upper":
            interpretation_list.append("Preis überdehnt (Bollinger)")

        # ---------------------------------------
        # Stochastic Bewertung (Timing)
        # ---------------------------------------
        score += stochastic.get("score", 0)

        if stochastic["regime"] == "Oversold_Reversal":
            interpretation_list.append("Gutes Reversal-Timing")
        elif stochastic["regime"] == "Overbought_Reversal":
            interpretation_list.append("Ungünstiges Timing")

        # ---------------------------------------
        # Markt-Kontext-Gewichtung
        # ---------------------------------------
        if market["market_regime"] == "trend_market":
            score *= 1.1
        elif market["market_regime"] == "late_trend":
            score *= 0.8

        # ---------------------------------------
        # Qualitätsstufe
        # ---------------------------------------
        if score >= 1.5:
            quality = "excellent"
            summary = "Exzellenter Einstiegszeitpunkt"
            interpretation_short = "Sehr gute Kombination aus Preis und Timing"
            interpretation_long = (
                "Die Bewertung zeigt eine ausgezeichnete Einstiegsqualität mit "
                "attraktivem Preisniveau und gutem Timing. Die Marktbedingungen unterstützen "
                "diesen Einstieg, wodurch eine hohe Wahrscheinlichkeit für einen erfolgreichen Trade besteht."
            )
            action_hint = "Einstieg klar empfohlen"
        elif score >= 0.5:
            quality = "good"
            summary = "Guter Einstiegszeitpunkt"
            interpretation_short = "Attraktives Setup mit geringem Risiko"
            interpretation_long = (
                "Die Einstiegsqualität ist gut mit positiven Signalen sowohl beim Preis als auch beim Timing. "
                "Der Markt zeigt unterstützende Tendenzen, dennoch sollten mögliche Risiken berücksichtigt werden."
            )
            action_hint = "Einstieg erwägen"
        elif score >= 0:
            quality = "neutral"
            summary = "Neutrales Einstiegs-Setup"
            interpretation_short = "Weder besonders gut noch schlecht"
            interpretation_long = (
                "Die Analyse ergibt weder eindeutige Kauf- noch Verkaufssignale. "
                "Es besteht Unsicherheit bezüglich des Einstiegszeitpunkts, daher ist Vorsicht geboten."
            )
            action_hint = "Abwarten oder kleine Positionen"
        else:
            quality = "poor"
            summary = "Schlechter Einstiegszeitpunkt"
            interpretation_short = "Ungünstiges Setup"
            interpretation_long = (
                "Die Bewertung deutet auf ungünstige Bedingungen für einen Einstieg hin. "
                "Preis und Timing sprechen gegen einen Trade, daher sollte auf bessere Chancen gewartet werden."
            )
            action_hint = "Einstieg vermeiden"

        return {
            "score": round(score, 2),
            "quality": quality,
            "summary": summary,
            "interpretation_short": interpretation_short,
            "interpretation_long": interpretation_long,
            "action_hint": action_hint,
            "interpretation": " | ".join(interpretation_list)
        }

    
class TradeDecisionEngine:
    """
    Trifft eine konkrete Kauf-/Nicht-Kauf-Entscheidung
    basierend auf Market-Regime, RSI, MACD und ADX
    """

    def decide(
        self,
        market: dict,
        rsi: dict,
        macd: dict,
        adx: dict
    ) -> dict:

        action = "NO_TRADE"
        position_type = None
        confidence = 0.0
        risk_level = "high"
        reason = ""

        interpretation_short = ""
        interpretation_long = ""
        summary = ""
        action_hint = ""

        # --------------------------------------------------
        # 1️⃣ RANGE-MARKT → Mean Reversion
        # --------------------------------------------------
        if market["market_regime"] == "range_market":

            summary = "Seitwärtsmarkt mit Mean Reversion Chancen"

            if rsi["state"] == "oversold":
                action = "BUY"
                position_type = "mean_reversion"
                confidence = 0.55
                risk_level = "moderate"
                reason = "Seitwärtsmarkt + RSI überverkauft"
                interpretation_short = "Kauf wegen Überverkauft-Signal"
                interpretation_long = (
                    "Der Markt bewegt sich seitwärts, während der RSI einen überverkauften Zustand signalisiert. "
                    "Dies deutet auf eine potenzielle Gegenbewegung hin, die Kaufgelegenheiten bietet. "
                    "Das Risiko ist moderat, da keine starken Trends vorliegen."
                )
                action_hint = "Long-Position eingehen, Stopp-Loss beachten"

            elif rsi["state"] == "overbought":
                action = "SELL"
                position_type = "mean_reversion"
                confidence = 0.55
                risk_level = "moderate"
                reason = "Seitwärtsmarkt + RSI überkauft"
                interpretation_short = "Verkauf wegen Überkauft-Signal"
                interpretation_long = (
                    "Der Markt zeigt seitwärts Bewegungen, während der RSI einen überkauften Zustand anzeigt. "
                    "Dies könnte eine kurzfristige Korrektur oder Gegenbewegung einleiten, "
                    "die Verkaufsgelegenheiten eröffnet."
                )
                action_hint = "Short-Position erwägen oder Gewinne sichern"

            else:
                reason = "Range-Markt ohne Extrem"
                interpretation_short = "Keine eindeutige Signalwirkung"
                interpretation_long = (
                    "Der Markt bewegt sich in einer Range ohne signifikante Über- oder Unterbewertung. "
                    "Handlungen sollten zurückhaltend erfolgen, da klare Signale fehlen."
                )
                action_hint = "Abwarten oder Range-Trading"

        # --------------------------------------------------
        # 2️⃣ TRANSITION → Abwarten
        # --------------------------------------------------
        elif market["market_regime"] == "transition_phase":

            action = "WAIT"
            confidence = 0.4
            risk_level = "high"
            reason = "Trend im Aufbau → keine Bestätigung"
            summary = "Trendbildungsphase – unsichere Marktlage"
            interpretation_short = "Warten auf klare Trendbestätigung"
            interpretation_long = (
                "Der Markt befindet sich in einer Übergangsphase, in der ein Trend entsteht, "
                "aber noch keine klare Richtung bestätigt ist. "
                "In solchen Phasen sind Investitionen riskant und sollten mit Vorsicht behandelt werden."
            )
            action_hint = "Positionen offen halten oder zurückhaltend agieren"

        # --------------------------------------------------
        # 3️⃣ TREND-MARKT → Trend-Follow
        # --------------------------------------------------
        elif market["market_regime"] == "trend_market":

            summary = "Ausgeprägter Trendmarkt – Trendfolge empfohlen"

            if macd["bias"] == "bullish" and rsi["value"] > 50:
                action = "BUY"
                position_type = "trend_follow"
                confidence = market["confidence"]
                risk_level = "low"
                reason = "Starker Aufwärtstrend + Momentum bestätigt"
                interpretation_short = "Kaufen im starken Aufwärtstrend"
                interpretation_long = (
                    "Der Markt zeigt einen klaren Aufwärtstrend mit unterstützendem Momentum "
                    "laut MACD und RSI. Dies erhöht die Wahrscheinlichkeit für eine Fortsetzung des Trends."
                )
                action_hint = "Long-Position eröffnen und Trend folgen"

            elif macd["bias"] == "bearish" and rsi["value"] < 50:
                action = "SELL"
                position_type = "trend_follow"
                confidence = market["confidence"]
                risk_level = "low"
                reason = "Starker Abwärtstrend + Momentum bestätigt"
                interpretation_short = "Verkaufen im starken Abwärtstrend"
                interpretation_long = (
                    "Der Markt befindet sich in einem Abwärtstrend mit bestätigtem negativen Momentum. "
                    "Trendfolgestrategien sind hier sinnvoll."
                )
                action_hint = "Short-Position eröffnen und Trend folgen"

            else:
                action = "HOLD"
                confidence = 0.5
                reason = "Trend intakt, aber Timing ungünstig"
                interpretation_short = "Trend vorhanden, aber kein klarer Einstieg"
                interpretation_long = (
                    "Obwohl ein Trend existiert, sind die Signale nicht eindeutig für einen Einstieg. "
                    "Es empfiehlt sich daher, die Position zu halten und auf bessere Gelegenheiten zu warten."
                )
                action_hint = "Position halten, auf günstigeres Timing achten"

        # --------------------------------------------------
        # 4️⃣ LATE TREND → Risiko-Management
        # --------------------------------------------------
        elif market["market_regime"] == "late_trend":

            action = "REDUCE"
            confidence = 0.6
            risk_level = "moderate"
            reason = "Späte Trendphase → Risiko reduzieren"
            summary = "Späte Trendphase mit erhöhter Vorsicht"
            interpretation_short = "Risiko minimieren"
            interpretation_long = (
                "Der Trend ist weit fortgeschritten und es besteht eine erhöhte Wahrscheinlichkeit "
                "für eine Trenderschöpfung oder Umkehr. Daher ist es sinnvoll, bestehende Positionen zu verkleinern "
                "und Gewinne zu sichern."
            )
            action_hint = "Positionen reduzieren, Stopp-Loss enger setzen"

        else:
            summary = "Keine klare Marktlage"
            interpretation_short = "Keine eindeutige Handlungsempfehlung"
            interpretation_long = (
                "Die Marktlage ist unklar, daher sollten neue Positionen vermieden werden, "
                "bis bessere Signale vorliegen."
            )
            action_hint = "Abwarten"

        return {
            "action": action,
            "position_type": position_type,
            "confidence": round(confidence, 2),
            "risk_level": risk_level,
            "reason": reason,
            "summary": summary,
            "interpretation_short": interpretation_short,
            "interpretation_long": interpretation_long,
            "action_hint": action_hint
        }
    
class TradePlanBuilder:

    def build(self, decision: dict, entry: dict) -> dict:

        if decision["action"] not in ["BUY", "SELL"]:
            return {"execute": False, "reason": "Kein Handelssignal"}

        if entry["quality"] == "poor":
            return {
                "execute": False,
                "reason": "Entry-Qualität zu schlecht"
            }

        size_factor = {
            "excellent": 1.0,
            "good": 0.7,
            "neutral": 0.4
        }.get(entry["quality"], 0)

        return {
            "execute": True,
            "direction": decision["action"],
            "size_factor": size_factor,
            "risk_level": decision["risk_level"],
            "confidence": decision["confidence"]
        }


class PositionSizer:
    def __init__(self, konto_groesse: float):
        """
        Initialisiert den Positionsgrößen-Rechner.

        Args:
            konto_groesse (float): Gesamtes Kapital (z.B. 10.000 €)
        """
        self.konto_groesse = konto_groesse  # z.B. 10000 €

    def berechne_positionsgroesse(
        self,
        einstiegskurs: float,
        stop_loss_kurs: float,
        risiko_prozent: float = 1.0,       # Prozentualer Risikoanteil am Konto, z.B. 1%
        confidence: float = 1.0,           # Vertrauen in die Trade-Entscheidung (0 bis 1)
        risiko_level: str = "moderate"     # Risikokategorie: low, moderate, high
    ) -> dict:

        # Berechnung des absoluten Risikobetrags in Euro
        risk_amount = self.konto_groesse * (risiko_prozent / 100)

        # Abstand zwischen Einstiegs- und Stop-Loss-Kurs
        stop_loss_abstand = abs(einstiegskurs - stop_loss_kurs)

        if stop_loss_abstand == 0:
            return {
                "error": "Stop-Loss Abstand darf nicht 0 sein",
                "message": "Der Abstand zwischen Einstiegs- und Stop-Loss-Kurs darf nicht null sein, "
                           "da sonst keine Positionsgröße berechnet werden kann."
            }

        # Berechnung der Basis-Positionsgröße (Anzahl Aktien, Kontrakte etc.)
        base_position_size = risk_amount / stop_loss_abstand

        # Multiplikator für Risiko-Level (z.B. konservativer bei hohem Risiko)
        risiko_faktoren = {
            "low": 1.2,       # Leicht größere Position bei geringem Risiko möglich
            "moderate": 1.0,  # Standard
            "high": 0.8       # Position wird verkleinert bei hohem Risiko
        }
        risiko_faktor = risiko_faktoren.get(risiko_level, 1.0)

        # Adjustierte Positionsgröße unter Berücksichtigung des Konfidenzwerts
        position_size = base_position_size * risiko_faktor * confidence

        # Interpretationstexte für UI und Nutzerfreundlichkeit
        summary = f"Empfohlene Positionsgröße basiert auf einem Risiko von {risiko_prozent}% " \
                  f"des Kontos ({risk_amount} €) und einem Stop-Loss-Abstand von {round(stop_loss_abstand, 4)}."

        interpretation_short = f"Positionsgröße: {round(position_size, 2)} Einheiten"

        interpretation_long = (
            f"Das Risiko pro Trade wird auf {round(risiko_prozent, 2)}% des Kontos begrenzt, "
            f"was {round(risk_amount, 2)} € entspricht. Die Positionsgröße wird anhand des Abstandes "
            f"zwischen Einstieg ({einstiegskurs}) und Stop-Loss ({stop_loss_kurs}) berechnet, "
            f"um das Risiko zu steuern. Ein Risiko-Level '{risiko_level}' "
            f"passt die Positionsgröße entsprechend an, ebenso wie das Vertrauen in den Trade "
            f"mit einem Faktor von {round(confidence, 2)} berücksichtigt wird."
        )

        action_hint = (
            "Stelle sicher, dass Stop-Loss und Einstiegsniveau sinnvoll gesetzt sind, "
            "um unerwartete Verluste zu vermeiden. Diese Positionsgröße soll das Risiko "
            "kontrollieren und ist kein Garant für Gewinn."
        )

        return {
            "position_size": round(position_size, 2),
            "risk_amount": round(risk_amount, 2),
            "stop_loss_abstand": round(stop_loss_abstand, 4),
            "confidence": round(confidence, 2),
            "risiko_level": risiko_level,
            "summary": summary,
            "interpretation_short": interpretation_short,
            "interpretation_long": interpretation_long,
            "action_hint": action_hint
        }


"""
🛑 Stop-Loss & 🎯 Take-Profit je Market-Regime
Regime	Stop-Loss Abstand (in %)	Take-Profit Abstand (in %)	Erklärung
Bullish	3 % unter Einstieg	6 % über Einstieg	Etwas enger Stop-Loss, da Markt klar im Aufwärtstrend
Bearish	2 % über Einstieg (für Short)	4 % unter Einstieg (für Short)	Strenger Stop-Loss, um Risiko zu begrenzen
Sideways	1.5 % unter/über Einstieg	3 % über/unter Einstieg	Engere Stops wegen Seitwärtsbewegung, Take-Profit kleiner
"""

class TradeRiskManager:
    def __init__(self, einstiegskurs: float, regime: str):
        self.einstiegskurs = einstiegskurs
        self.regime = regime.lower()

    def stop_loss_take_profit(self, position_typ="long") -> dict:
        """
        position_typ: 'long' oder 'short'
        """

        # Default Werte (in Prozent)
        stop_loss_pct = 0.03
        take_profit_pct = 0.06

        if self.regime == "bullish":
            stop_loss_pct = 0.03
            take_profit_pct = 0.06
        elif self.regime == "bearish":
            stop_loss_pct = 0.02
            take_profit_pct = 0.04
        elif self.regime == "sideways":
            stop_loss_pct = 0.015
            take_profit_pct = 0.03
        else:
            # Fallback, falls Regime unbekannt
            stop_loss_pct = 0.03
            take_profit_pct = 0.05

        if position_typ == "long":
            stop_loss = self.einstiegskurs * (1 - stop_loss_pct)
            take_profit = self.einstiegskurs * (1 + take_profit_pct)
        elif position_typ == "short":
            stop_loss = self.einstiegskurs * (1 + stop_loss_pct)
            take_profit = self.einstiegskurs * (1 - take_profit_pct)
        else:
            raise ValueError("position_typ muss 'long' oder 'short' sein")

        return {
            "stop_loss": round(stop_loss, 4),
            "take_profit": round(take_profit, 4),
            "stop_loss_pct": stop_loss_pct,
            "take_profit_pct": take_profit_pct,
            "regime": self.regime,
            "position_typ": position_typ
        }
    
class SignalGenerator:

    def __init__(self):
        self.engine = TradeDecisionEngine()

    def generate_signals(
        self,
        full_data: pd.DataFrame,
        min_len_window: int = 20
    ) -> pd.DataFrame:

        signale = []
        rsi_analysis = RSIAnalysis()
        macd_analysis = MACDAnalysis()
        adx_analysis = ADXAnalysis()
        market_analysis = MarketRegimeAnalysis()

        for i in range(min_len_window, len(full_data)):
            datum = full_data.index[i]
            fenster = full_data.iloc[:i+1]  # Nur bis zum aktuellen Tag i

            rsi_result = rsi_analysis.analyse(fenster)
            macd_result = macd_analysis.analyse(fenster)
            adx_result = adx_analysis.analyse(fenster)
            market_result = market_analysis.analyse(rsi_result, macd_result, adx_result)

            decision = self.engine.decide(
                market_result, rsi_result, macd_result, adx_result
            )

            action_map = {
                "BUY": "🟢 Kaufen",
                "SELL": "🔴 Verkaufen",
                "HOLD": "🟡 Halten",
                "WAIT": "🟡 Halten",
                "NO_TRADE": "🟡 Halten",
                "REDUCE": "🟡 Halten",
            }

            signale.append({
                "Datum": datum,
                "Entscheidung": action_map.get(decision["action"], "🟡 Halten"),
                "confidence": decision["confidence"],
                "market_regime": market_result.get("market_regime"),
                "rsi_state": rsi_result.get("state"),
                "rsi_value": rsi_result.get("value"),
                "macd_bias": macd_result.get("bias"),
                "adx_value": adx_result.get("value"),
            })

        return pd.DataFrame(signale)


class BuySignalEvaluator:

    @staticmethod
    def filter_buy_signals(signals_df: pd.DataFrame) -> pd.DataFrame:
        return signals_df[
            signals_df["Entscheidung"].str.contains("Kaufen")
        ].copy()

    @staticmethod
    def cluster_periods(kaufsignale_df, max_gap_days=5):
        # ⛔ Edge Case: keine Kaufsignale
        if kaufsignale_df is None or kaufsignale_df.empty:
            return []
        daten = kaufsignale_df.sort_values("Datum")["Datum"].tolist()
        # ⛔ zusätzliche Sicherheit (z.B. falls Datum-Spalte leer ist)
        if not daten:
            return []
        perioden = []

        start = prev = daten[0]
        for d in daten[1:]:
            if (d - prev).days <= max_gap_days:
                prev = d
            else:
                perioden.append((start, prev))
                start = prev = d

        perioden.append((start, prev))
        return perioden

    @staticmethod
    def evaluate_periods(perioden, full_data, Auswertung_tage, min_veraenderung):
        bewertungen = []

        for start, end in perioden:
            start_kurs = full_data.loc[end, "Close"]
            idx = full_data.index.get_loc(end)
            max_kurs = full_data.iloc[idx:idx+Auswertung_tage+1]["Close"].max()

            diff = (max_kurs - start_kurs) / start_kurs

            bewertungen.append({
                "Start": start,
                "Ende": end,
                "Signal": diff >= min_veraenderung,
                "Kurs_Diff": diff,
            })

        return pd.DataFrame(bewertungen)

class SwingSignalService:

    def __init__(self):
        self.generator = SignalGenerator()
        self.evaluator = BuySignalEvaluator()

    def run_analysis(
        self,
        full_data,
        Auswertung_tage,
        min_veraenderung,
        market,
        rsi,
        macd,
        adx
    ):
        signals = self.generator.generate_signals(
            full_data
        )

        buys = self.evaluator.filter_buy_signals(signals)

        if buys.empty:
            return {"signals": signals}

        perioden = self.evaluator.cluster_periods(buys)
        bewertung = self.evaluator.evaluate_periods(
            perioden, full_data, Auswertung_tage, min_veraenderung
        )

        return {
            "signals": signals,
            "buy_signals": buys,
            "perioden_bewertung": bewertung,
            "trefferquote": bewertung["Signal"].mean() * 100
        }
