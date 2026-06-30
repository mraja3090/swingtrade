# ============================================================
# scanner.py — 7-Rule Grand Checklist Scanner
#
# Based on Zerodha Varsity Technical Analysis Grand Checklist:
#   Rule 1: Market Health         (Dow Theory — primary trend)
#   Rule 2: Stock Trend           (EMA crossover + ADX strength)
#   Rule 3: Pullback Entry Zone   (buy on dip, not at highs)
#   Rule 4: Candlestick Pattern   (primary signal per Varsity)
#   Rule 5: Volume Confirmation   (smart money participation)
#   Rule 6: Indicator Confirmation (MACD + RSI + Stochastic)
#   Rule 7: Risk:Reward Ratio     (minimum 2:1)
#
# Each rule contributes to a SCORE. Signal fired if score >= MIN_SCORE.
# This prevents no-signal days when one minor condition fails.
# Target win rate: 65-70%
# ============================================================

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

from config import (
    NIFTY_EMA_PERIOD, NIFTY_MAX_5DAY_DROP,
    STOCK_EMA_FAST, STOCK_EMA_SLOW, ADX_MINIMUM, MAX_DROP_30D,
    PULLBACK_EMA_TOLERANCE, RSI_MIN_ENTRY, RSI_MAX_ENTRY, MAX_FROM_52W_HIGH,
    VOLUME_SURGE_MIN, STOCH_K_MAX, MIN_RRR,
    SL_ATR_MULT, TARGET_ATR_MULT, MIN_SCORE_TO_SIGNAL, MIN_AVG_VOLUME,
    MAX_CAPITAL_PER_TRADE, R2_MIN_SUBRULES, R3_MIN_SUBRULES
)
from indicators import add_all_indicators, ema
from patterns import detect_pattern, pattern_strength


# ─────────────────────────────────────────────────────────
# RULE 1 — MARKET HEALTH
# ─────────────────────────────────────────────────────────

def check_market_health(nifty_df: pd.DataFrame) -> tuple[bool, str]:
    """
    Zerodha Varsity: Dow Theory — establish primary trend first.
    Never fight the primary trend.

    FIX: Hard binary cutoff at EMA200 caused total silence when Nifty
    was only 1% below the line (noise, not a real bear market).
    Now uses a 2% buffer zone + EMA50 as secondary confirmation —
    matches how Dow Theory is actually applied (broad trend, not
    single-day exact crossover).

    Returns (is_healthy, reason)
    """
    if nifty_df is None or len(nifty_df) < NIFTY_EMA_PERIOD:
        return True, "Nifty data insufficient — proceeding"

    df = add_all_indicators(nifty_df)
    latest = df.iloc[-1]

    ema200   = latest['ema_200']
    ema50    = latest['ema_50']
    close    = latest['Close']
    ret_5d   = latest['ret_5d']

    pct_vs_ema200 = (close - ema200) / ema200 * 100

    # Hard crash guard — always blocks regardless of EMA position
    if ret_5d <= NIFTY_MAX_5DAY_DROP:
        return False, f"Nifty fell {ret_5d:.1f}% in 5 days — Market crash mode"

    # Clear bull market — well above EMA200
    if pct_vs_ema200 >= -2.0:
        # Within 2% of EMA200 or above it — healthy enough to trade
        # (Dow Theory primary trend doesn't flip on 1% daily noise)
        status = "above" if close > ema200 else "near"
        return True, (f"Nifty {status} 200 EMA ({close:.0f} vs {ema200:.0f}, "
                       f"{pct_vs_ema200:+.1f}%) | 5d return: {ret_5d:+.1f}%")

    # More than 2% below EMA200 — check EMA50 for early recovery signal
    if close > ema50:
        return True, (f"Nifty below 200 EMA but above 50 EMA "
                       f"({close:.0f} vs EMA50 {ema50:.0f}) — early recovery, proceeding cautiously")

    return False, (f"Nifty {pct_vs_ema200:.1f}% below 200 EMA "
                    f"({close:.0f} < {ema200:.0f}) — Bear market")


# ─────────────────────────────────────────────────────────
# CORE SCANNER — PER STOCK
# ─────────────────────────────────────────────────────────

def scan_stock(symbol: str, df: pd.DataFrame) -> dict | None:
    """
    Run all 7 rules on one stock.
    Returns signal dict if score >= MIN_SCORE, else None.
    """
    if len(df) < 60:
        return None

    # Liquidity filter
    if df['Volume'].tail(20).mean() < MIN_AVG_VOLUME:
        return None

    try:
        df = add_all_indicators(df)
    except Exception:
        return None

    if len(df) < 5:
        return None

    latest   = df.iloc[-1]
    prev     = df.iloc[-2]
    score    = 0
    details  = {}

    close  = latest['Close']
    e20    = latest['ema_20']
    e50    = latest['ema_50']
    adx_v  = latest['adx']
    rsi_v  = latest['rsi']
    macd_h = latest['macd_hist']
    prev_h = prev['macd_hist']
    stoch_k= latest['stoch_k']
    vol_r  = latest['vol_ratio']
    atr_v  = latest['atr']
    ret_20 = latest['ret_20d']
    pct_52w= latest['pct_from_52w_high']

    # ── RULE 2: STOCK TREND ──────────────────────────────
    # Zerodha Varsity: Stock must be in uptrend (EMA crossover)
    r2_uptrend  = close > e50                          # Price above slow EMA
    r2_ema_cross= e20 > e50                            # Fast > slow = uptrend confirmed
    r2_not_knife= ret_20 > -MAX_DROP_30D               # Not a falling knife
    r2_adx      = adx_v >= ADX_MINIMUM                 # Actual trend, not sideways chop

    r2_score = sum([r2_uptrend, r2_ema_cross, r2_not_knife, r2_adx])

    if r2_score < R2_MIN_SUBRULES:
        return None    # Hard reject — no trend = no trade

    score += 2 if r2_score == 4 else 1
    details['R2_Trend'] = {
        'passed': r2_score >= 3,
        'uptrend': r2_uptrend,
        'ema_cross': r2_ema_cross,
        'adx': round(adx_v, 1),
        'ret_20d': round(ret_20, 1),
    }

    # ── RULE 3: PULLBACK / ENTRY ZONE ────────────────────
    # Zerodha Varsity: Buy during retracement, not at highs
    # FIXED: A strong uptrend stock (passing R2) is normally near its high —
    # that is healthy trend behaviour, not "chasing a top". We only reject
    # the extreme blow-off-top case: price within MAX_FROM_52W_HIGH% of a
    # brand new fresh high made TODAY with no pullback at all.
    pct_from_ema20 = abs(close - e20) / e20 * 100
    r3_pullback    = pct_from_ema20 <= PULLBACK_EMA_TOLERANCE     # Near 20 EMA
    r3_rsi_zone    = RSI_MIN_ENTRY <= rsi_v <= RSI_MAX_ENTRY       # RSI not extreme
    r3_not_blowoff = pct_52w < -MAX_FROM_52W_HIGH or pct_52w == 0  # Allow normal uptrend proximity to high

    r3_score = sum([r3_pullback, r3_rsi_zone, r3_not_blowoff])

    if r3_score < R3_MIN_SUBRULES:
        return None

    score += 2 if r3_score == 3 else 1
    details['R3_Entry'] = {
        'passed': r3_score >= 2,
        'pct_from_ema20': round(pct_from_ema20, 1),
        'rsi': round(rsi_v, 1),
        'pct_from_52w_high': round(pct_52w, 1),
    }

    # ── RULE 4: CANDLESTICK PATTERN ──────────────────────
    # Zerodha Varsity: Primary signal for trade
    patterns      = detect_pattern(df)
    pattern_today = patterns.iloc[-1]
    p_strength    = pattern_strength(pattern_today)

    if p_strength == 0:
        # No pattern today — check if yesterday had a strong one (next-day entry)
        pattern_yest = patterns.iloc[-2]
        p_strength   = max(0, pattern_strength(pattern_yest) - 1)
        pattern_today = pattern_yest + " (prev day)" if p_strength > 0 else ''

    score += p_strength
    details['R4_Pattern'] = {
        'pattern': pattern_today,
        'strength': p_strength,
        'passed': p_strength > 0,
    }

    # ── RULE 5: VOLUME CONFIRMATION ──────────────────────
    # Zerodha Varsity: High volume = smart money participation
    r5_volume = vol_r >= VOLUME_SURGE_MIN

    if r5_volume:
        score += 2
    details['R5_Volume'] = {
        'passed': r5_volume,
        'vol_ratio': round(vol_r, 2),
        'required': VOLUME_SURGE_MIN,
    }

    # ── RULE 6: INDICATOR CONFIRMATION ───────────────────
    # Zerodha Varsity: MACD + RSI confirm the candlestick signal
    r6_macd = (macd_h > 0) or (macd_h > prev_h and macd_h > -0.5)  # MACD improving
    r6_rsi  = rsi_v < 65                                             # RSI has room
    r6_stoch= stoch_k < STOCH_K_MAX                                  # Stochastic not overbought

    r6_score = sum([r6_macd, r6_rsi, r6_stoch])
    score   += min(2, r6_score)   # Max 2 points from indicators
    details['R6_Indicators'] = {
        'macd_ok': r6_macd,
        'rsi': round(rsi_v, 1),
        'stoch_k': round(stoch_k, 1),
        'passed': r6_score >= 2,
    }

    # ── RULE 7: RISK : REWARD ────────────────────────────
    # Zerodha Varsity: Minimum RRR must justify the trade
    entry    = round(close, 2)
    sl       = round(entry - SL_ATR_MULT   * atr_v, 2)
    target   = round(entry + TARGET_ATR_MULT * atr_v, 2)
    risk     = entry - sl
    reward   = target - entry
    rr       = round(reward / risk, 2) if risk > 0 else 0

    r7_rr = rr >= MIN_RRR
    if not r7_rr:
        return None   # Hard reject — poor R:R, never trade

    score += 1
    details['R7_RR'] = {
        'entry': entry,
        'target': target,
        'stop_loss': sl,
        'rr_ratio': rr,
        'atr': round(atr_v, 2),
        'passed': True,
    }

    # ── SIGNAL DECISION ──────────────────────────────────
    if score < MIN_SCORE_TO_SIGNAL:
        return None

    shares     = int(MAX_CAPITAL_PER_TRADE / entry)
    est_profit = round(shares * (target - entry))
    est_loss   = round(shares * (entry - sl))

    return {
        'symbol'     : symbol.replace('.NS',''),
        'symbol_ns'  : symbol,
        'score'      : score,
        'entry'      : entry,
        'target'     : target,
        'stop_loss'  : sl,
        'rr_ratio'   : rr,
        'pattern'    : details['R4_Pattern']['pattern'],
        'rsi'        : round(rsi_v, 1),
        'adx'        : round(adx_v, 1),
        'vol_ratio'  : round(vol_r, 2),
        'macd_hist'  : round(macd_h, 4),
        'shares'     : shares,
        'est_profit' : est_profit,
        'est_loss'   : est_loss,
        'details'    : details,
    }


# ─────────────────────────────────────────────────────────
# SCAN ALL STOCKS
# ─────────────────────────────────────────────────────────

def scan_all(all_data: dict, nifty_healthy: bool) -> list:
    """
    Run Grand Checklist on all stocks.
    Returns top signals sorted by score (highest first).
    """
    if not nifty_healthy:
        print("[SCAN] Market in downtrend. No signals today. Capital protected.")
        return []

    stock_keys = [k for k in all_data if not k.startswith('__')]
    print(f"[SCAN] Scanning {len(stock_keys)} stocks with Grand Checklist...")

    signals  = []
    rejected = {'R2_Trend':0, 'R3_Entry':0, 'R4_Pattern':0, 'R5_Volume':0, 'R7_RR':0, 'Score':0}

    for sym in stock_keys:
        result = scan_stock(sym, all_data[sym].copy())
        if result:
            signals.append(result)
        # (rejection tracking simplified for readability)

    signals.sort(key=lambda x: x['score'], reverse=True)

    print(f"\n{'Rank':<5}{'Stock':<16}{'Score':>6}{'Pattern':<22}{'RSI':>5}{'ADX':>5}{'Vol':>6}{'R:R':>5}")
    print("─" * 70)
    for i, s in enumerate(signals[:10], 1):
        pat = s['pattern'][:20] if s['pattern'] else 'None'
        print(f"{i:<5}{s['symbol']:<16}{s['score']:>6}  {pat:<20}{s['rsi']:>5.1f}{s['adx']:>5.1f}{s['vol_ratio']:>5.1f}x{s['rr_ratio']:>5.1f}")

    print(f"\n[SCAN] {len(signals)} stocks passed all rules.")
    return signals


# ─────────────────────────────────────────────────────────
# DIAGNOSTIC MODE — see exactly why each stock passes/fails
# ─────────────────────────────────────────────────────────

def diagnose_stock(symbol: str, df: pd.DataFrame) -> dict:
    """
    Run all rules WITHOUT early-exit, so you can see exactly
    which sub-checks pass/fail for any stock on any day.
    Used by: python main.py diagnose
    """
    out = {'symbol': symbol.replace('.NS', ''), 'error': None}

    if len(df) < 60:
        out['error'] = f"Insufficient data ({len(df)} rows, need 60+)"
        return out

    avg_vol = df['Volume'].tail(20).mean()
    if avg_vol < MIN_AVG_VOLUME:
        out['error'] = f"Low liquidity (avg vol {avg_vol:,.0f} < {MIN_AVG_VOLUME:,})"
        return out

    try:
        df = add_all_indicators(df)
    except Exception as e:
        out['error'] = f"Indicator error: {e}"
        return out

    if len(df) < 5:
        out['error'] = "Not enough rows after indicator warmup"
        return out

    latest = df.iloc[-1]
    prev   = df.iloc[-2]

    close   = latest['Close']
    e20     = latest['ema_20']
    e50     = latest['ema_50']
    adx_v   = latest['adx']
    rsi_v   = latest['rsi']
    macd_h  = latest['macd_hist']
    prev_h  = prev['macd_hist']
    stoch_k = latest['stoch_k']
    vol_r   = latest['vol_ratio']
    atr_v   = latest['atr']
    ret_20  = latest['ret_20d']
    pct_52w = latest['pct_from_52w_high']

    r2_uptrend   = close > e50
    r2_ema_cross = e20 > e50
    r2_not_knife = ret_20 > -MAX_DROP_30D
    r2_adx       = adx_v >= ADX_MINIMUM
    r2_score     = sum([r2_uptrend, r2_ema_cross, r2_not_knife, r2_adx])

    pct_from_ema20 = abs(close - e20) / e20 * 100
    r3_pullback    = pct_from_ema20 <= PULLBACK_EMA_TOLERANCE
    r3_rsi_zone    = RSI_MIN_ENTRY <= rsi_v <= RSI_MAX_ENTRY
    r3_not_blowoff = pct_52w < -MAX_FROM_52W_HIGH or pct_52w == 0
    r3_score       = sum([r3_pullback, r3_rsi_zone, r3_not_blowoff])

    patterns      = detect_pattern(df)
    pattern_today = patterns.iloc[-1]
    p_strength    = pattern_strength(pattern_today)
    if p_strength == 0 and len(patterns) > 1:
        pattern_yest = patterns.iloc[-2]
        p_strength   = max(0, pattern_strength(pattern_yest) - 1)

    r5_volume = vol_r >= VOLUME_SURGE_MIN

    r6_macd  = (macd_h > 0) or (macd_h > prev_h and macd_h > -0.5)
    r6_rsi   = rsi_v < 65
    r6_stoch = stoch_k < STOCH_K_MAX
    r6_score = sum([r6_macd, r6_rsi, r6_stoch])

    sl     = round(close - SL_ATR_MULT * atr_v, 2)
    target = round(close + TARGET_ATR_MULT * atr_v, 2)
    risk   = close - sl
    rr     = round((target - close) / risk, 2) if risk > 0 else 0
    r7_rr  = rr >= MIN_RRR

    total_score = (
        (2 if r2_score == 4 else (1 if r2_score >= R2_MIN_SUBRULES else 0)) +
        (2 if r3_score == 3 else (1 if r3_score >= R3_MIN_SUBRULES else 0)) +
        p_strength +
        (2 if r5_volume else 0) +
        min(2, r6_score) +
        (1 if r7_rr else 0)
    )

    out.update({
        'close': round(close, 2),
        'r2_score': f"{r2_score}/4", 'r2_pass': r2_score >= R2_MIN_SUBRULES,
        'r3_score': f"{r3_score}/3", 'r3_pass': r3_score >= R3_MIN_SUBRULES,
        'pattern': pattern_today or 'none', 'pattern_pts': p_strength,
        'vol_ratio': round(vol_r, 2), 'r5_pass': r5_volume,
        'r6_score': f"{r6_score}/3",
        'rr': rr, 'r7_pass': r7_rr,
        'total_score': total_score,
        'would_signal': (r2_score >= R2_MIN_SUBRULES and r3_score >= R3_MIN_SUBRULES
                          and r7_rr and total_score >= MIN_SCORE_TO_SIGNAL),
        'rsi': round(rsi_v, 1), 'adx': round(adx_v, 1),
        'pct_from_ema20': round(pct_from_ema20, 1),
    })
    return out