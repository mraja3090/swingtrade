# ============================================================
# patterns.py — Candlestick Pattern Detection
#
# Source: Zerodha Varsity — Technical Analysis Module
#   https://zerodha.com/varsity/module/technical-analysis/
#
# Rule 4 of the Grand Checklist: Primary signal for trade.
# "One must look for at least 1 recognised candlestick pattern
#  before initiating a trade." — Zerodha Varsity
#
# Patterns (ranked by reliability per Varsity):
#   ★★★  Morning Star     — strongest 3-day reversal
#   ★★★  Bullish Engulfing — bulls fully engulf prior bear day
#   ★★   Bullish Marubozu  — full-day bull control, no wicks
#   ★★   Hammer            — buyers reject the lows
#   ★★   Dragonfly Doji    — complete lower wick rejection
#   ★    Piercing Line     — moderate 2-day reversal
#   ★    Bullish Harami    — bears losing momentum
#
# All functions accept a full DataFrame and return a boolean Series.
# 100% vectorised — no Python min/max on pandas Series.
# ============================================================

import pandas as pd
import numpy as np
from config import ENGULF_RATIO, HAMMER_WICK_RATIO, MARUBOZU_TOLERANCE


def bullish_engulfing(df: pd.DataFrame) -> pd.Series:
    """
    Day 1 = bearish candle.
    Day 2 = bullish candle whose body FULLY engulfs Day 1 body.
    Varsity: "The prior trend should be a downtrend / pullback."
    """
    o1 = df['Open'].shift(1);  c1 = df['Close'].shift(1)
    o2 = df['Open'];            c2 = df['Close']

    bear_d1  = c1 < o1                       # Day 1 bearish
    bull_d2  = c2 > o2                       # Day 2 bullish
    engulfs  = (c2 > o1) & (o2 < c1)        # D2 body covers D1 body
    body_d1  = (o1 - c1).abs()
    body_d2  = (c2 - o2).abs()
    bigger   = body_d2 >= ENGULF_RATIO * body_d1

    return (bear_d1 & bull_d2 & engulfs & bigger).fillna(False)


def hammer(df: pd.DataFrame) -> pd.Series:
    """
    Small real body at TOP of candle, long lower wick ≥ 2× body.
    Upper wick negligible.
    Varsity: "Hammer is a single candlestick pattern. It indicates
    that the bulls are reversing the market sentiment."
    """
    o  = df['Open'];  c  = df['Close']
    h  = df['High'];  l  = df['Low']

    body     = (c - o).abs()
    hi_body  = pd.concat([o, c], axis=1).max(axis=1)   # top of body
    lo_body  = pd.concat([o, c], axis=1).min(axis=1)   # bottom of body
    lo_wick  = lo_body - l
    up_wick  = h - hi_body
    rng      = (h - l).clip(lower=1e-9)

    small_body    = body / rng < 0.35
    long_lo_wick  = lo_wick >= HAMMER_WICK_RATIO * body.clip(lower=1e-9)
    tiny_up_wick  = up_wick <= 0.15 * rng
    has_body      = body / c > 0.001                   # avoid flat lines

    return (small_body & long_lo_wick & tiny_up_wick & has_body).fillna(False)


def dragonfly_doji(df: pd.DataFrame) -> pd.Series:
    """
    Open ≈ Close ≈ High, very long lower wick.
    Varsity: "Doji at the bottom indicates indecision — when
    combined with a prior downtrend it signals reversal."
    """
    o  = df['Open'];  c  = df['Close']
    h  = df['High'];  l  = df['Low']

    body    = (c - o).abs()
    rng     = (h - l).clip(lower=1e-9)
    lo_body = pd.concat([o, c], axis=1).min(axis=1)
    lo_wick = lo_body - l

    tiny_body  = body / rng < 0.10
    long_lo    = lo_wick / rng > 0.60
    near_high  = (h - pd.concat([o, c], axis=1).max(axis=1)) / rng < 0.10

    return (tiny_body & long_lo & near_high).fillna(False)


def bullish_marubozu(df: pd.DataFrame) -> pd.Series:
    """
    Open ≈ Low, Close ≈ High. No significant wicks.
    Varsity: "Represents a very strong bullish sentiment. The bulls
    are in complete control from open to close."
    """
    o  = df['Open'];  c  = df['Close']
    h  = df['High'];  l  = df['Low']

    rng          = (h - l).clip(lower=1e-9)
    open_near_lo = (o - l)   / rng < (MARUBOZU_TOLERANCE / 100)
    close_near_hi= (h - c)   / rng < (MARUBOZU_TOLERANCE / 100)
    is_bull      = c > o
    big_body     = (c - o).abs() / rng > 0.80

    return (open_near_lo & close_near_hi & is_bull & big_body).fillna(False)


def morning_star(df: pd.DataFrame) -> pd.Series:
    """
    Day 1: Large bearish candle.
    Day 2: Small body (star) — indecision, gaps if possible.
    Day 3: Large bullish candle closing above Day 1 midpoint.
    Varsity: "Morning Star is the strongest 3-candle reversal pattern.
    It requires patience. The reward justifies the wait."
    """
    o1 = df['Open'].shift(2);  c1 = df['Close'].shift(2)
    h1 = df['High'].shift(2);  l1 = df['Low'].shift(2)
    o2 = df['Open'].shift(1);  c2 = df['Close'].shift(1)
    h2 = df['High'].shift(1);  l2 = df['Low'].shift(1)
    o3 = df['Open'];            c3 = df['Close']

    rng1 = (h1 - l1).clip(lower=1e-9)
    rng2 = (h2 - l2).clip(lower=1e-9)

    d1_bear    = c1 < o1
    d1_big     = (o1 - c1).abs() / rng1 > 0.50
    d2_small   = (o2 - c2).abs() / rng2 < 0.30
    d3_bull    = c3 > o3
    d3_over_mid= c3 > (o1 + c1) / 2          # closes above D1 midpoint

    return (d1_bear & d1_big & d2_small & d3_bull & d3_over_mid).fillna(False)


def piercing_line(df: pd.DataFrame) -> pd.Series:
    """
    Day 1: Long bearish candle.
    Day 2: Opens below D1 low, closes above D1 body midpoint.
    Varsity: "Moderate reversal pattern. Less reliable than Morning Star."
    """
    o1 = df['Open'].shift(1);  c1 = df['Close'].shift(1)
    l1 = df['Low'].shift(1)
    o2 = df['Open'];            c2 = df['Close']
    h1 = df['High'].shift(1);  l1h= df['Low'].shift(1)
    rng1 = (df['High'].shift(1) - df['Low'].shift(1)).clip(lower=1e-9)

    d1_bear        = c1 < o1
    d1_big         = (o1 - c1).abs() / rng1 > 0.50
    d2_opens_low   = o2 < l1h
    d2_closes_mid  = c2 > (o1 + c1) / 2
    d2_bull        = c2 > o2

    return (d1_bear & d1_big & d2_opens_low & d2_closes_mid & d2_bull).fillna(False)


def bullish_harami(df: pd.DataFrame) -> pd.Series:
    """
    Day 1: Large bearish candle.
    Day 2: Small bullish candle INSIDE Day 1 body.
    Varsity: "Bears are losing momentum. Weakest reversal signal."
    """
    o1 = df['Open'].shift(1);  c1 = df['Close'].shift(1)
    o2 = df['Open'];            c2 = df['Close']
    rng1 = (df['High'].shift(1) - df['Low'].shift(1)).clip(lower=1e-9)

    d1_bear  = c1 < o1
    d1_big   = (o1 - c1).abs() / rng1 > 0.50
    d2_bull  = c2 > o2
    d2_in_d1 = (o2 > c1) & (c2 < o1)    # D2 body inside D1 body

    return (d1_bear & d1_big & d2_bull & d2_in_d1).fillna(False)


# ── Pattern detection ────────────────────────────────────

PATTERN_PRIORITY = [
    ('Morning Star',      morning_star,      3),
    ('Bullish Engulfing', bullish_engulfing, 3),
    ('Bullish Marubozu',  bullish_marubozu,  2),
    ('Hammer',            hammer,            2),
    ('Dragonfly Doji',    dragonfly_doji,    2),
    ('Piercing Line',     piercing_line,     1),
    ('Bullish Harami',    bullish_harami,    1),
]


def detect_pattern(df: pd.DataFrame) -> pd.Series:
    """
    Run all patterns. Return Series of pattern name per row.
    Higher priority patterns overwrite lower priority ones.
    """
    result = pd.Series('', index=df.index, dtype=str)
    for name, fn, _ in reversed(PATTERN_PRIORITY):
        try:
            mask = fn(df)
            result[mask] = name
        except Exception:
            pass
    return result


def pattern_strength(name: str) -> int:
    """Return reliability score (1=weak, 2=moderate, 3=strong)."""
    for pname, _, strength in PATTERN_PRIORITY:
        if pname == name:
            return strength
    return 0
