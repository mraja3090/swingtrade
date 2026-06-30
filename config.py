# ============================================================
# config.py — SwingTradeAI Rules Edition
# Pure rule-based system. No ML. No black box.
# Every signal can be verified on a chart in 30 seconds.
# Edit ONLY this file to customise the system.
# ============================================================

# --- TELEGRAM ---
TELEGRAM_BOT_TOKEN = "YOUR token"
TELEGRAM_CHAT_ID   = "your id"

# --- STOCK UNIVERSE ---
# Combined: 40 Nifty 50 (large-cap) + 50 Nifty Midcap 150 = 90 stocks
# Large-caps: high liquidity, strong trend signals on Rule 1/2
# Mid-caps: less efficient, patterns persist longer, higher win rate on Rules 3-6
# Together: wider opportunity set, scanner picks best setup regardless of cap
MIDCAP_STOCKS = [
    # ── NIFTY 50 — Large Cap ──────────────────────────────────────────────
    # Banking & Finance
    "HDFCBANK.NS","ICICIBANK.NS","SBIN.NS","KOTAKBANK.NS","AXISBANK.NS",
    "BAJFINANCE.NS","BAJAJFINSV.NS",
    # IT
    "TCS.NS","INFY.NS","WIPRO.NS","HCLTECH.NS","TECHM.NS",
    # Consumer
    "HINDUNILVR.NS","ITC.NS","ASIANPAINT.NS","NESTLEIND.NS","TITAN.NS",
    # Energy & Industrial
    "RELIANCE.NS","ONGC.NS","NTPC.NS","POWERGRID.NS","LT.NS",
    # Auto
    "MARUTI.NS","TATAMOTORS.NS","EICHERMOT.NS","HEROMOTOCO.NS","BAJAJ-AUTO.NS",
    # Pharma
    "SUNPHARMA.NS","DRREDDY.NS","DIVISLAB.NS",
    # Metals & Materials
    "TATASTEEL.NS","JSWSTEEL.NS","HINDALCO.NS","GRASIM.NS","ULTRACEMCO.NS",
    # Diversified
    "ADANIENT.NS","BHARTIARTL.NS","INDUSINDBK.NS","SBILIFE.NS",
    "TATACONSUM.NS","UPL.NS",

    # ── NIFTY MIDCAP 150 — Mid Cap ───────────────────────────────────────
    # IT / Tech Midcap
    "PERSISTENT.NS","COFORGE.NS","MPHASIS.NS","LTTS.NS","TATAELXSI.NS","KPITTECH.NS",
    # Finance / NBFC
    "CHOLAFIN.NS","MFSL.NS","ABCAPITAL.NS","MUTHOOTFIN.NS",
    # Banking (midcap)
    "FEDERALBNK.NS","IDFCFIRSTB.NS","BANDHANBNK.NS","RBLBANK.NS","INDIANB.NS","CANBK.NS",
    # Consumer Durables / Electricals
    "VOLTAS.NS","CROMPTON.NS","POLYCAB.NS","DIXON.NS","HAVELLS.NS",
    # Pharma / Healthcare
    "TORNTPHARM.NS","ALKEM.NS","ZYDUSLIFE.NS","LAURUSLABS.NS","AUROPHARMA.NS","FORTIS.NS",
    # Chemicals
    "PIIND.NS","DEEPAKNTR.NS","AARTIIND.NS","VINATIORGA.NS",
    # Infrastructure / Industrial
    "CUMMINSIND.NS","THERMAX.NS","IRCTC.NS","CONCOR.NS","BHEL.NS",
    # Cement
    "RAMCOCEM.NS","JKCEMENT.NS",
    # Consumer / Retail
    "TRENT.NS","JUBLFOOD.NS","PAGEIND.NS",
    # Auto Ancillary
    "BALKRISIND.NS","APOLLOTYRE.NS","MOTHERSON.NS","EXIDEIND.NS",
    # Metals / Mining
    "NMDC.NS","NATIONALUM.NS","HINDZINC.NS",
    # Pipes / Building Materials
    "ASTRAL.NS","SUPREMEIND.NS",
    # Platform / Internet
    "NAUKRI.NS","INDIAMART.NS",
]

NIFTY_INDEX = "^NSEI"

# --- RULE 1: MARKET HEALTH ---
# Zerodha Varsity: Dow Theory — establish primary trend first
NIFTY_EMA_PERIOD         = 200    # Nifty must be above this EMA
NIFTY_MAX_5DAY_DROP      = -3.0   # Skip all if Nifty fell >3% in 5 days

# --- RULE 2: STOCK TREND ---
# Zerodha Varsity: Moving Average Crossover system
STOCK_EMA_FAST           = 20     # Fast EMA
STOCK_EMA_SLOW           = 50     # Slow EMA — price must be above this
ADX_PERIOD               = 14     # ADX for trend strength
ADX_MINIMUM              = 18     # ADX > 18 = actual trend (was 20, slightly loosened)
MAX_DROP_30D             = 20.0   # Skip if stock fell >20% in 30 days (avoid falling knives)

# --- RULE 3: PULLBACK / ENTRY ZONE ---
# Buy on pullback to moving average — not at highs
# Zerodha Varsity: Buy during secondary trend retracement
PULLBACK_EMA_TOLERANCE   = 6.0    # Price within 6% of 20 EMA = in pullback zone (was 4%)
RSI_MIN_ENTRY            = 38     # RSI not oversold (broken stock)
RSI_MAX_ENTRY            = 68     # RSI not overbought (too extended)
# FIXED LOGIC: stock should NOT be making a brand new fresh 52-week high
# TODAY (chasing the exact top), but a strong uptrend stock is normally
# WITHIN a few % of its high — that is what a healthy trend looks like.
# Old version required >8% BELOW the high, which contradicts Rule 2's
# requirement of a strong uptrend. Fixed to only reject the most extreme
# 1.5% blow-off top zone, not normal trending price action.
MAX_FROM_52W_HIGH        = 1.5    # Reject only if within 1.5% of fresh 52w high (blow-off top)

# --- RULE 4: CANDLESTICK PATTERN ---
# Zerodha Varsity: Primary signal for trade
# Must be a recognised bullish reversal pattern at the pullback zone
MIN_BODY_PCT             = 0.3    # Minimum candle body as % of price (avoid doji noise)
ENGULF_RATIO             = 1.0    # Engulfing candle must fully cover previous body
HAMMER_WICK_RATIO        = 2.0    # Lower wick must be ≥ 2x body (hammer)
MARUBOZU_TOLERANCE       = 1.5    # Body must be >98.5% of range (marubozu)

# --- RULE 5: VOLUME CONFIRMATION ---
# Zerodha Varsity: Above average volume = smart money participation
VOLUME_LOOKBACK          = 10     # Compare to 10-day average
VOLUME_SURGE_MIN         = 1.3    # Today's volume ≥ 1.3x 10-day average (was 1.5x)

# --- RULE 6: INDICATOR CONFIRMATION ---
# Zerodha Varsity: MACD + RSI as confirmation (not primary signal)
MACD_FAST                = 12
MACD_SLOW                = 26
MACD_SIGNAL_PERIOD       = 9
STOCH_K_MAX              = 80     # Stochastic %K < 80 (room to run up)
STOCH_PERIOD             = 14

# --- RULE 7: RISK : REWARD ---
# Zerodha Varsity: Minimum RRR must justify the trade
MIN_RRR                  = 2.0    # Minimum reward:risk ratio

# --- HARD-GATE MINIMUMS (how many sub-checks must pass within each rule) ---
R2_MIN_SUBRULES           = 2      # Trend: need 2 of 4 sub-checks (was hardcoded 3 of 4)
R3_MIN_SUBRULES           = 1      # Entry zone: need 1 of 3 sub-checks (was hardcoded 2 of 3)
ATR_PERIOD               = 14
SL_ATR_MULT              = 1.0    # Stop loss = entry - 1x ATR
TARGET_ATR_MULT          = 2.5    # Target = entry + 2.5x ATR → R:R = 2.5:1

# --- SIGNAL SCORING ---
# Each rule passed adds to score. Signal sent only if score ≥ threshold.
# This allows partial passes on less critical rules.
MIN_SCORE_TO_SIGNAL      = 6      # Must score at least 6 out of 12 points (was 7)
TOP_N_SIGNALS            = 3      # Send top 3 by score daily

# --- LIQUIDITY ---
MIN_AVG_VOLUME           = 200000  # Minimum 2-lakh avg daily volume

# --- CAPITAL ---
TOTAL_CAPITAL            = 100000
MAX_CAPITAL_PER_TRADE    = 20000
MAX_OPEN_TRADES          = 3

# --- SCHEDULE ---
SCAN_TIME                = "16:15"
DATA_PERIOD              = "2y"    # 2 years sufficient for rules (no ML training needed)
DATA_INTERVAL            = "1d"
DATA_PATH                = "data/stock_data.pkl"