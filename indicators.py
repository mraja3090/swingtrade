# ============================================================
# indicators.py — Technical Indicator Calculations
# Pure math. No ML. Every value verifiable on any charting tool.
# ============================================================

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

from config import (
    NIFTY_EMA_PERIOD, STOCK_EMA_FAST, STOCK_EMA_SLOW,
    ADX_PERIOD, MACD_FAST, MACD_SLOW, MACD_SIGNAL_PERIOD,
    STOCH_PERIOD, ATR_PERIOD
)


# ── Core math ─────────────────────────────────────────────

def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(period).mean()


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain  = delta.clip(lower=0).ewm(com=period-1, min_periods=period).mean()
    loss  = (-delta.clip(upper=0)).ewm(com=period-1, min_periods=period).mean()
    rs    = gain / loss.replace(0, 1e-9)
    return 100 - 100 / (1 + rs)


def atr(df: pd.DataFrame, period: int = ATR_PERIOD) -> pd.Series:
    hl  = df['High'] - df['Low']
    hc  = (df['High'] - df['Close'].shift(1)).abs()
    lc  = (df['Low']  - df['Close'].shift(1)).abs()
    tr  = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def macd(close: pd.Series):
    """Returns (macd_line, signal_line, histogram)"""
    fast     = ema(close, MACD_FAST)
    slow     = ema(close, MACD_SLOW)
    macd_ln  = fast - slow
    signal   = macd_ln.ewm(span=MACD_SIGNAL_PERIOD, adjust=False).mean()
    hist     = macd_ln - signal
    return macd_ln, signal, hist


def stochastic(df: pd.DataFrame, period: int = STOCH_PERIOD):
    """Returns (%K, %D)"""
    low_min  = df['Low'].rolling(period).min()
    high_max = df['High'].rolling(period).max()
    denom    = (high_max - low_min).replace(0, np.nan)
    k        = 100 * (df['Close'] - low_min) / denom
    d        = k.rolling(3).mean()
    return k.fillna(50), d.fillna(50)


def adx(df: pd.DataFrame, period: int = ADX_PERIOD) -> pd.Series:
    """
    ADX — Average Directional Index
    Measures trend STRENGTH (not direction).
    ADX > 20: trend is real. ADX < 20: choppy sideways market.
    Zerodha Varsity: ADX helps filter out sideways markets.
    """
    high  = df['High']
    low   = df['Low']
    close = df['Close']

    # True Range
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low  - close.shift(1)).abs()
    tr  = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    # Directional movement
    dm_plus  = high.diff().clip(lower=0)
    dm_minus = (-low.diff()).clip(lower=0)
    dm_plus  = dm_plus.where(dm_plus > dm_minus, 0)
    dm_minus = dm_minus.where(dm_minus > dm_plus, 0)

    # Smoothed
    atr_smooth    = tr.ewm(span=period, adjust=False).mean()
    di_plus       = 100 * dm_plus.ewm(span=period, adjust=False).mean()  / atr_smooth.replace(0, 1e-9)
    di_minus      = 100 * dm_minus.ewm(span=period, adjust=False).mean() / atr_smooth.replace(0, 1e-9)
    dx            = 100 * (di_plus - di_minus).abs() / (di_plus + di_minus).replace(0, 1e-9)
    adx_val       = dx.ewm(span=period, adjust=False).mean()
    return adx_val.fillna(0)


def support_resistance(df: pd.DataFrame, lookback: int = 20):
    """
    Rolling support (recent low) and resistance (recent high).
    Zerodha Varsity: S&R are key price levels where price tends to reverse.
    """
    support    = df['Low'].rolling(lookback).min()
    resistance = df['High'].rolling(lookback).max()
    return support, resistance


def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add all indicators to a stock DataFrame. Returns enriched copy."""
    df = df.copy()
    c = df['Close']

    # Trend
    df['ema_20']    = ema(c, STOCK_EMA_FAST)
    df['ema_50']    = ema(c, STOCK_EMA_SLOW)
    df['ema_200']   = ema(c, NIFTY_EMA_PERIOD)
    df['adx']       = adx(df)

    # Momentum
    df['rsi']       = rsi(c)
    ml, sl, hl      = macd(c)
    df['macd']      = ml
    df['macd_sig']  = sl
    df['macd_hist'] = hl

    # Oscillator
    k, d            = stochastic(df)
    df['stoch_k']   = k
    df['stoch_d']   = d

    # Volatility
    df['atr']       = atr(df)
    df['atr_pct']   = df['atr'] / c * 100

    # Volume
    df['vol_avg']   = df['Volume'].rolling(10).mean()
    df['vol_ratio'] = df['Volume'] / df['vol_avg'].replace(0, 1e-9)

    # Support / Resistance
    df['support']   ,  df['resistance']    = support_resistance(df, 20)
    df['support_10'],  df['resistance_10'] = support_resistance(df, 10)

    # Returns
    df['ret_5d']    = c.pct_change(5) * 100
    df['ret_20d']   = c.pct_change(20)* 100

    # 52-week high
    df['high_52w']  = df['High'].rolling(252).max()
    df['pct_from_52w_high'] = (c - df['high_52w']) / df['high_52w'] * 100

    return df.dropna(subset=['ema_50','rsi','adx'])
