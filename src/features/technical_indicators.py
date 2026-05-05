"""Technical indicators for feature engineering."""

import pandas as pd
import numpy as np
from typing import Optional


def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index (RSI)."""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)  # Neutral RSI for initial values


def calculate_macd(
    prices: pd.Series,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate MACD (Moving Average Convergence Divergence)."""
    ema_fast = prices.ewm(span=fast_period, adjust=False).mean()
    ema_slow = prices.ewm(span=slow_period, adjust=False).mean()
    
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    histogram = macd_line - signal_line
    
    return macd_line.fillna(0), signal_line.fillna(0), histogram.fillna(0)


def calculate_bollinger_bands(
    prices: pd.Series,
    period: int = 20,
    num_std: float = 2.0
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate Bollinger Bands."""
    sma = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    
    upper_band = sma + (std * num_std)
    lower_band = sma - (std * num_std)
    
    return upper_band.fillna(prices), sma.fillna(prices), lower_band.fillna(prices)


def calculate_moving_averages(
    prices: pd.Series,
    periods: list[int] = [5, 10, 20, 50, 200]
) -> dict[str, pd.Series]:
    """Calculate multiple Simple Moving Averages (SMA)."""
    mas = {}
    for period in periods:
        ma = prices.rolling(window=period).mean()
        mas[f"sma_{period}"] = ma.fillna(prices)
    return mas


def calculate_ema(prices: pd.Series, period: int = 20) -> pd.Series:
    """Calculate Exponential Moving Average (EMA)."""
    ema = prices.ewm(span=period, adjust=False).mean()
    return ema.fillna(prices)


def calculate_stochastic(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14
) -> tuple[pd.Series, pd.Series]:
    """Calculate Stochastic Oscillator (%K and %D)."""
    lowest_low = low.rolling(window=period).min()
    highest_high = high.rolling(window=period).max()
    
    k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
    d_percent = k_percent.rolling(window=3).mean()
    
    return k_percent.fillna(50), d_percent.fillna(50)


def calculate_atr(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14
) -> pd.Series:
    """Calculate Average True Range (ATR)."""
    high_low = high - low
    high_close = np.abs(high - close.shift())
    low_close = np.abs(low - close.shift())
    
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = true_range.rolling(window=period).mean()
    
    return atr.fillna(0)


def calculate_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """Calculate On-Balance Volume (OBV)."""
    obv = (np.sign(close.diff()) * volume).fillna(0).cumsum()
    return obv


def calculate_vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
    """Calculate Volume Weighted Average Price (VWAP)."""
    typical_price = (high + low + close) / 3
    vwap = (typical_price * volume).cumsum() / volume.cumsum()
    return vwap.fillna(close)


def calculate_williams_r(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14
) -> pd.Series:
    """Calculate Williams %R."""
    highest_high = high.rolling(window=period).max()
    lowest_low = low.rolling(window=period).min()
    
    williams_r = -100 * ((highest_high - close) / (highest_high - lowest_low))
    return williams_r.fillna(-50)


def calculate_momentum(prices: pd.Series, period: int = 10) -> pd.Series:
    """Calculate Price Momentum."""
    momentum = prices.diff(period)
    return momentum.fillna(0)


def calculate_roc(prices: pd.Series, period: int = 10) -> pd.Series:
    """Calculate Rate of Change (ROC)."""
    roc = ((prices - prices.shift(period)) / prices.shift(period)) * 100
    return roc.fillna(0)


def add_all_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add all technical indicators to a dataframe.
    
    Expected columns: open, high, low, close, volume
    """
    df = df.copy()
    
    # Ensure column names are lowercase
    df.columns = [col.lower() for col in df.columns]
    
    # RSI
    df["rsi_14"] = calculate_rsi(df["close"], period=14)
    
    # MACD
    macd, signal, histogram = calculate_macd(df["close"])
    df["macd"] = macd
    df["macd_signal"] = signal
    df["macd_histogram"] = histogram
    
    # Bollinger Bands
    bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(df["close"])
    df["bb_upper"] = bb_upper
    df["bb_middle"] = bb_middle
    df["bb_lower"] = bb_lower
    df["bb_width"] = (bb_upper - bb_lower) / bb_middle
    df["bb_position"] = (df["close"] - bb_lower) / (bb_upper - bb_lower)
    
    # Moving Averages
    mas = calculate_moving_averages(df["close"], periods=[5, 10, 20, 50])
    for name, values in mas.items():
        df[name] = values
    
    # EMA
    df["ema_20"] = calculate_ema(df["close"], period=20)
    
    # Stochastic
    stoch_k, stoch_d = calculate_stochastic(df["high"], df["low"], df["close"])
    df["stoch_k"] = stoch_k
    df["stoch_d"] = stoch_d
    
    # ATR
    df["atr_14"] = calculate_atr(df["high"], df["low"], df["close"])
    
    # OBV
    df["obv"] = calculate_obv(df["close"], df["volume"])
    
    # VWAP
    df["vwap"] = calculate_vwap(df["high"], df["low"], df["close"], df["volume"])
    
    # Williams %R
    df["williams_r"] = calculate_williams_r(df["high"], df["low"], df["close"])
    
    # Momentum
    df["momentum_10"] = calculate_momentum(df["close"], period=10)
    
    # ROC
    df["roc_10"] = calculate_roc(df["close"], period=10)
    
    # Volume indicators
    df["volume_sma_20"] = df["volume"].rolling(window=20).mean().fillna(df["volume"])
    df["volume_ratio"] = df["volume"] / df["volume_sma_20"]
    
    # Price position relative to moving averages
    df["price_to_sma_5"] = (df["close"] - df["sma_5"]) / df["sma_5"]
    df["price_to_sma_20"] = (df["close"] - df["sma_20"]) / df["sma_20"]
    
    # Trend strength
    df["trend_strength"] = (df["sma_5"] - df["sma_20"]) / df["sma_20"]
    
    return df


def get_technical_feature_columns() -> list[str]:
    """Return list of all technical indicator column names."""
    return [
        "rsi_14",
        "macd", "macd_signal", "macd_histogram",
        "bb_upper", "bb_middle", "bb_lower", "bb_width", "bb_position",
        "sma_5", "sma_10", "sma_20", "sma_50",
        "ema_20",
        "stoch_k", "stoch_d",
        "atr_14",
        "obv",
        "vwap",
        "williams_r",
        "momentum_10",
        "roc_10",
        "volume_sma_20", "volume_ratio",
        "price_to_sma_5", "price_to_sma_20",
        "trend_strength",
    ]
