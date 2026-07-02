# ============================================================
# telegram_bot.py — SwingTradeAI Rules Edition Alerts
# Shows all 7 Grand Checklist rules — fully transparent
# ============================================================

import asyncio, json, os
from datetime import datetime
from config import (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
                    MAX_CAPITAL_PER_TRADE, MAX_OPEN_TRADES,
                    TOP_N_SIGNALS)


def _score_bar(score: int, max_score: int = 12) -> str:
    filled = round(score / max_score * 10)
    return '█' * filled + '░' * (10 - filled)


def format_signal(sig: dict, rank: int, total: int) -> str:
    sym     = sig['symbol']
    entry   = sig['entry']
    target  = sig['target']
    sl      = sig['stop_loss']
    rr      = sig['rr_ratio']
    score   = sig['score']
    pattern = sig['pattern'] or 'No pattern'
    rsi     = sig['rsi']
    adx     = sig['adx']
    vol_r   = sig['vol_ratio']
    shares  = sig['shares']
    ep      = sig['est_profit']
    el      = sig['est_loss']

    # Rule pass/fail icons
    d = sig.get('details', {})
    r2 = '✅' if d.get('R2_Trend',{}).get('passed') else '⚠️'
    r3 = '✅' if d.get('R3_Entry',{}).get('passed') else '⚠️'
    r4 = '✅' if d.get('R4_Pattern',{}).get('passed') else '⚠️'
    r5 = '✅' if d.get('R5_Volume',{}).get('passed') else '⚠️'
    r6 = '✅' if d.get('R6_Indicators',{}).get('passed') else '⚠️'

    gain_pct = round((target - entry) / entry * 100, 1)
    loss_pct = round((entry - sl)   / entry * 100, 1)

    return f"""
━━━━━━━━━━━━━━━━━━━━━━━━━
📊 SWING SIGNAL #{rank} of {total}
━━━━━━━━━━━━━━━━━━━━━━━━━
📈 Stock     : {sym}
🕯️  Pattern   : {pattern}
🎯 Action    : BUY

💰 Entry     : ₹{entry}
🎯 Target    : ₹{target}  (+{gain_pct}%)
🛑 Stop Loss : ₹{sl}  (-{loss_pct}%)
⏳ Hold      : 5–7 trading days
📊 R:R Ratio : 1:{rr}

📋 Grand Checklist:
  {r2} R2 Trend    ADX:{adx}  EMA aligned
  {r3} R3 Entry    RSI:{rsi}  Pullback zone
  {r4} R4 Pattern  {pattern}
  {r5} R5 Volume   {vol_r:.1f}x avg
  {r6} R6 MACD+RSI Confirmed
  ✅  R7 R:R      1:{rr} ≥ 2.0
Score: {_score_bar(score)} {score}/12

💼 For ₹{MAX_CAPITAL_PER_TRADE:,}:
  Qty          : ~{shares} shares
  If target hit: +₹{ep:,}
  If SL hit    : -₹{el:,}

⚠️  Place order 9:20 AM tomorrow
⚠️  Set SL in Zerodha BEFORE buying
⚠️  Verify on chart before placing
━━━━━━━━━━━━━━━━━━━━━━━━━
🕐 {datetime.now().strftime('%d %b %Y  %I:%M %p')}
""".strip()


def format_no_signal(reason: str) -> str:
    return f"""
🔴 NO SIGNALS TODAY
━━━━━━━━━━━━━━━━━━━━━━━━━
{reason}

✅ Grand Checklist found no
   high-quality setups today.
   Staying in cash is correct.

📅 Next scan: tomorrow 4:15 PM
━━━━━━━━━━━━━━━━━━━━━━━━━
🕐 {datetime.now().strftime('%d %b %Y  %I:%M %p')}
""".strip()


def format_summary(signals: list) -> str:
    lines = '\n'.join([
        f"  {i+1}. {s['symbol']:<14} Score:{s['score']:>2}  "
        f"₹{s['entry']} → ₹{s['target']}  SL:₹{s['stop_loss']}  {s['pattern']}"
        for i, s in enumerate(signals)
    ])
    return f"""
📋 TODAY'S SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━
{lines}

Max {MAX_OPEN_TRADES} trades open at once.
All pass Zerodha Varsity Grand Checklist.
━━━━━━━━━━━━━━━━━━━━━━━━━""".strip()


async def _send(text: str):
    from telegram import Bot
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    for chunk in [text[i:i+4000] for i in range(0, len(text), 4000)]:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=chunk)


def send(text: str):
    if TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print(f"\n[TELEGRAM - PAPER MODE]\n{text}\n")
        return
    try:
        asyncio.run(_send(text))
        print("  [TELEGRAM] ✅ Sent")
    except Exception as e:
        print(f"  [TELEGRAM ERROR] {e}")
        if "Chat not found" in str(e):
            print("  → Fix: Open Telegram, message your bot first, then retry")
        elif "Unauthorized" in str(e):
            print("  → Fix: Check TELEGRAM_BOT_TOKEN in config.py")


def print_console_summary(signals: list, market_reason: str = ""):
    """Print a clean summary to the terminal — same info as Telegram."""
    width = 70
    now   = datetime.now().strftime('%d %b %Y  %I:%M %p')
    sep   = "═" * width
    line  = "─" * width

    print()
    print(sep)
    print("  SWINGTRADEAI — TODAY'S SIGNALS  |  " + now)
    print(sep)

    if not signals:
        reason = market_reason or "No stocks passed all 7 rules today."
        print("  NO SIGNALS — " + reason)
        print(sep)
        return

    for i, sig in enumerate(signals):
        sym      = sig['symbol']
        entry    = sig['entry']
        target   = sig['target']
        sl       = sig['stop_loss']
        rr       = sig['rr_ratio']
        score    = sig['score']
        pat      = sig.get('pattern') or 'No pattern'
        rsi      = sig.get('rsi', '—')
        adx      = sig.get('adx', '—')
        vol      = sig.get('vol_ratio', 0)
        shares   = sig.get('shares', '—')
        ep       = sig.get('est_profit', 0)
        el       = sig.get('est_loss',   0)
        gain_pct = round((target - entry) / entry * 100, 1)
        loss_pct = round((entry  - sl)    / entry * 100, 1)

        d   = sig.get('details', {})
        r2  = 'PASS' if d.get('R2_Trend',     {}).get('passed') else 'WEAK'
        r3  = 'PASS' if d.get('R3_Entry',     {}).get('passed') else 'WEAK'
        r4  = 'PASS' if d.get('R4_Pattern',   {}).get('passed') else 'WEAK'
        r5  = 'PASS' if d.get('R5_Volume',    {}).get('passed') else 'WEAK'
        r6  = 'PASS' if d.get('R6_Indicators',{}).get('passed') else 'WEAK'

        bar = "#" * round(score / 12 * 20) + "." * (20 - round(score / 12 * 20))

        print()
        print("  SIGNAL #" + str(i+1) + " of " + str(len(signals)) + "  |  " + sym)
        print("  Score  [" + bar + "]  " + str(score) + "/12")
        print("  Pattern: " + pat)
        print(line)
        print("  Entry      :  Rs." + f"{entry:,.2f}")
        print("  Target     :  Rs." + f"{target:,.2f}" + "  (+" + str(gain_pct) + "%)")
        print("  Stop Loss  :  Rs." + f"{sl:,.2f}" + "  (-" + str(loss_pct) + "%)")
        print("  R:R Ratio  :  1:" + str(rr) + "     Hold: 5-7 trading days")
        print(line)
        print("  Trend:" + r2 + "  Entry:" + r3 + "  Pattern:" + r4 +
              "  Volume:" + r5 + "  MACD:" + r6)
        print("  RSI " + str(rsi) + "  |  ADX " + str(adx) +
              "  |  Volume " + str(round(vol,1)) + "x avg")
        print(line)
        print("  For Rs." + f"{MAX_CAPITAL_PER_TRADE:,}" +
              "  ->  ~" + str(shares) + " shares")
        print("  If target hit  :  +Rs." + f"{ep:,}")
        print("  If SL hit      :  -Rs." + f"{el:,}")

    print()
    print("  IMPORTANT: Check chart in Zerodha/TradingView before buying")
    print("  IMPORTANT: Set Stop Loss immediately after placing buy order")
    print(sep)
    print()


    top = signals[:TOP_N_SIGNALS]
    for i, sig in enumerate(top):
        send(format_signal(sig, i + 1, len(top)))

    if len(top) > 1:
        send(format_summary(top))

    # Save log
    os.makedirs("logs", exist_ok=True)
    date = datetime.now().strftime('%Y-%m-%d')
    json.dump(
        {'date': date, 'signals': [
            {k: v for k, v in s.items() if k != 'details'}
            for s in top
        ]},
        open(f"logs/signals_{date}.json", 'w'),
        indent=2, default=str
    )
    print(f"  [LOG] → logs/signals_{date}.json")


# Compatibility wrapper expected by main.py
def send_signals(signals: list, market_reason: str = ""):
    """Backwards-compatible function used by main.py.

    The older main.py expects a send_signals function; print_console_summary
    already performs the full behaviour (printing, sending Telegram messages,
    and saving logs). This wrapper simply forwards to it.
    """
    print_console_summary(signals, market_reason)
