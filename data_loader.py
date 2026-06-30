# ============================================================
# data_loader.py — Download NSE mid-cap stock data (free)
# ============================================================

import yfinance as yf
import pandas as pd
import pickle, os, warnings
warnings.filterwarnings('ignore')

from config import MIDCAP_STOCKS, NIFTY_INDEX, DATA_PERIOD, DATA_INTERVAL, DATA_PATH


def download_stock(symbol: str, period: str = DATA_PERIOD) -> pd.DataFrame:
    try:
        df = yf.Ticker(symbol).history(period=period, interval=DATA_INTERVAL)
        if df.empty or len(df) < 60:
            return pd.DataFrame()
        df.index = pd.to_datetime(df.index).tz_localize(None)
        df = df[['Open','High','Low','Close','Volume']].copy()
        df = df[df['Volume'] > 0].dropna()
        return df
    except:
        return pd.DataFrame()


def download_all() -> dict:
    symbols = MIDCAP_STOCKS + [NIFTY_INDEX]
    print(f"\n[DATA] Downloading {len(MIDCAP_STOCKS)} mid-cap stocks + Nifty...")
    data = {}
    for sym in symbols:
        df = download_stock(sym)
        if not df.empty:
            key = '__NIFTY__' if sym == NIFTY_INDEX else sym
            data[key] = df
            label = 'Nifty' if sym == NIFTY_INDEX else sym
            print(f"  ✓ {label}: {len(df)} rows")
        else:
            print(f"  ✗ {sym}: skipped")
    print(f"[DATA] {len(data)-1} stocks + Nifty loaded.\n")
    return data


def save(data: dict):
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    pickle.dump(data, open(DATA_PATH, 'wb'))
    print(f"[DATA] Saved → {DATA_PATH}")


def load() -> dict:
    if not os.path.exists(DATA_PATH):
        data = download_all()
        save(data)
        return data
    data = pickle.load(open(DATA_PATH, 'rb'))
    n = len([k for k in data if not k.startswith('__')])
    print(f"[DATA] Loaded {n} stocks from cache.")
    return data


def refresh(data: dict) -> dict:
    """
    Pull whatever is missing since the last cached candle, for EVERY
    stock, every time this is called — designed for ad-hoc runs.

    FIX: Old version always fetched period="2d", which only works if
    you run daily without gaps. For ad-hoc use (run once every few
    days or weeks), that left a hole between the cache and "2 days
    ago" — corrupting rolling indicators (RSI/ADX/EMA) exactly when
    you need them most: today.

    Now: for each stock, compute days since its last cached date and
    fetch exactly that gap (+5 day safety buffer for weekends/holidays),
    capped at DATA_PERIOD so a very stale cache just re-downloads fully.
    """
    sym_map  = {'__NIFTY__': NIFTY_INDEX}
    today    = pd.Timestamp.now().normalize()
    refreshed, full_redownload = 0, 0

    for key in list(data.keys()):
        yahoo_sym = sym_map.get(key, key)
        try:
            existing = data[key]
            if existing is None or existing.empty:
                period = DATA_PERIOD          # no cache at all — full pull
                full_redownload += 1
            else:
                last_date = existing.index[-1]
                gap_days  = (today - last_date).days
                if gap_days <= 0:
                    continue                  # already up to date
                # Trading days are ~5/7 → add buffer for weekends/holidays
                period = f"{max(5, gap_days + 5)}d"

            new = yf.Ticker(yahoo_sym).history(period=period, interval=DATA_INTERVAL)
            if new.empty:
                continue
            new.index = pd.to_datetime(new.index).tz_localize(None)
            new = new[['Open','High','Low','Close','Volume']].copy()
            new = new[new['Volume'] > 0].dropna()

            if existing is None or existing.empty:
                data[key] = new
            else:
                combined  = pd.concat([existing, new])
                data[key] = combined[~combined.index.duplicated(keep='last')].sort_index()
            refreshed += 1
        except Exception:
            pass

    print(f"[DATA] Refresh complete: {refreshed} stocks updated"
          + (f" ({full_redownload} fresh pulls)" if full_redownload else ""))
    return data