import pandas as pd
import numpy as np
from typing import Dict, Any, List


class IndicatorManager:
    """
    Calculates key technical indicators (RSI, MACD, Moving Averages, Bollinger Bands, ATR).
    """

    @staticmethod
    def calculate_sma(df: pd.DataFrame, column: str = "close", period: int = 20) -> pd.Series:
        return df[column].rolling(window=period).mean()

    @staticmethod
    def calculate_ema(df: pd.DataFrame, column: str = "close", period: int = 20) -> pd.Series:
        return df[column].ewm(span=period, adjust=False).mean()

    @staticmethod
    def calculate_rsi(df: pd.DataFrame, column: str = "close", period: int = 14) -> pd.Series:
        delta = df[column].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50.0)

    @staticmethod
    def calculate_macd(
        df: pd.DataFrame,
        column: str = "close",
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> Dict[str, pd.Series]:
        fast_ema = IndicatorManager.calculate_ema(df, column, fast_period)
        slow_ema = IndicatorManager.calculate_ema(df, column, slow_period)
        macd_line = fast_ema - slow_ema
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        histogram = macd_line - signal_line

        return {
            "macd": macd_line,
            "signal": signal_line,
            "histogram": histogram
        }

    @staticmethod
    def calculate_bollinger_bands(
        df: pd.DataFrame,
        column: str = "close",
        period: int = 20,
        std_dev: float = 2.0
    ) -> Dict[str, pd.Series]:
        sma = IndicatorManager.calculate_sma(df, column, period)
        std = df[column].rolling(window=period).std()
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)

        return {
            "upper": upper,
            "middle": sma,
            "lower": lower
        }
