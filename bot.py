import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(level=logging.INFO)
TOKEN = os.environ.get("BOT_TOKEN")

# ==================================================
# TRADING ENGINE
# ==================================================

market = {
    "DXY": -1,
    "VIX": 19,
    "FED": "DOVISH",
    "NEWS_RISK": False,
    "COT_GOLD": "BULLISH",
    "COT_BTC": "BULLISH",
    "GOLD_PRICE": 2360,
    "GOLD_DAILY": "BULLISH",
    "GOLD_4H": "BULLISH",
    "GOLD_1H": "BULLISH",
    "BONDS": "DOWN",
    "GOLD_LOSSES": 0,
    "BTC_PRICE": 108000,
    "BTC_DAILY": "BULLISH",
    "BTC_4H": "BULLISH",
    "BTC_1H": "BULLISH",
    "BTC_WHALES": "ACCUMULATION",
}

def timeframe_confirmation(daily, h4, h1):
    if daily == "BULLISH" and h4 == "BULLISH" and h1 == "BULLISH":
        return "BULLISH"
    if daily == "BEARISH" and h4 == "BEARISH" and h1 == "BEARISH":
        return "BEARISH"
    return "MIXED"

def get_signal(score):
    if score >= 80: return "🔥 STRONG BUY"
    if score >= 60: return "🟡 MEDIUM BUY"
    if score <= -80: return "🔥 STRONG SELL"
    if score <= -60: return "🟡 MEDIUM SELL"
    return "🚫 NO TRADE"

def calc_btc():
    score = 0
    reasons = []
    tf = timeframe_confirmation(market["BTC_DAILY"], market["BTC_4H"], market["BTC_1H"])

    if market["DXY"] == -1: score += 25; reasons.append("✅ Weak Dollar +25")
    if market["DXY"] == 1: score -= 25; reasons.append("❌ Strong Dollar -25")
    if market["BTC_WHALES"] == "ACCUMULATION": score += 30; reasons.append("✅ Whale Accumulation +30")
    if market["BTC_WHALES"] == "DISTRIBUTION": score -= 30; reasons.append("❌ Whale Distribution -30")
    if market["VIX"] < 20: score += 15; reasons.append("✅ Low VIX +15")
    if market["VIX"] > 25: score -= 20; reasons.append("❌ High VIX -20")
    if market["FED"] == "DOVISH": score += 15; reasons.append("✅ Dovish Fed +15")
    if market["FED"] == "HAWKISH": score -= 20; reasons.append("❌ Hawkish Fed -20")
    if tf == "BULLISH": score += 25; reasons.append("✅ Bullish Multi TF +25")
    if tf == "BEARISH": score -= 25; reasons.append("❌ Bearish Multi TF -25")
    if market["COT_BTC"] == "BULLISH": score += 10; reasons.append("✅ Bullish COT +10")
    if market["COT_BTC"] == "BEARISH": score -= 10; reasons.append("❌ Bearish COT -10")

    return score, reasons, tf, get_signal(score)

def calc_gold():
    score = 0
    reasons = []
    disabled = False
    disable_reason = ""
    tf = timeframe_confirmation(market["GOLD_DAILY"], market["GOLD_4H"], market["GOLD_1H"])

    if market["GOLD_LOSSES"] >= 2: disabled = True; disable_reason = "REVENGE PROTECTION"
    if market["NEWS_RISK"]: disabled = True; disable_reason = "HIGH IMPACT NEWS"

    if market["DXY"] == -1: score += 30; reasons.append("✅ Weak Dollar +30")
    if market["DXY"] == 1: score -= 35; reasons.append("❌ Strong Dollar -35")
    if market["VIX"] > 25: score += 20; reasons.append("✅ Fear In Market +20")
    if market["VIX"] < 18: score -= 10; reasons.append("❌ Risk On Market -10")
    if market["FED"] == "DOVISH": score += 20; reasons.append("✅ Dovish Fed +20")
    if market["FED"] == "HAWKISH": score -= 30; reasons.append("❌ Hawkish Fed -30")
    if market["BONDS"] == "DOWN": score += 20; reasons.append("✅ Bond Yields Falling +20")
    if market["BONDS"] == "UP": score -= 20; reasons.append("❌ Bond Yields Rising -20")
    if tf == "BULLISH": score += 25; reasons.append("✅ Bullish Multi TF +25")
    if tf == "BEARISH": score -= 25; reasons.append("❌ Bearish Multi TF -25")
    if market["COT_GOLD"] == "BULLISH": score += 15; reasons.append("✅ Bullish COT +15")
    if market["COT_GOLD"] == "BEARISH": score -= 15; reasons.append("❌ Bearish COT -15")

    macro_conflict = (
        (market["DXY"] == 1 and market["FED"] == "HAWKISH") or
        (market["DXY"] == 1 and market["BONDS"] == "UP")
    )

    if disabled:
        signal = f"🚫 GOLD DISABLED ({disable_reason})"
    elif macro_conflict:
        signal = "🚫 GOLD FILTER ACTIVE"
    else:
        signal = get_signal(score)

    return score, reasons, tf, signal

def format_signal_message():
    btc_score, btc_reasons, btc_tf, btc_signal = calc_btc()
    gold_score, gold_reasons, gold_tf, gold_signal = calc_gold()

    btc_entry = market["BTC_PRICE"]
    gold_entry = market["GOLD_PRICE"]

    msg = f"""
🤖 *SMART MACRO TRADING AI v5*
━━━━━━━━━━━━━━━━━━━━

📊 *MACRO*
• DXY: {"WEAK 🟢" if market["DXY"] == -1 else "STRONG 🔴"}
• VIX: {market["VIX"]}
• FED: {market["FED"]}
• NEWS RISK: {"⚠️ YES" if market["NEWS_RISK"] else "✅ NO"}

━━━━━━━━━━━━━━━━━━━━
🟠 *BTC/USD*
Signal: *{btc_signal}*
Score: {btc_score}/100
Trend: {btc_tf}

📌 Trade Setup:
• Entry: {btc_entry:,}
• SL: {btc_entry - 1800:,}
• TP1: {btc_entry + 3000:,}
• TP2: {btc_entry + 6000:,}

Reasons:
{chr(10).join(btc_reasons)}

━━━━━━━━━━━━━━━━━━━━
🥇 *XAU/USD (GOLD)*
Signal: *{gold_signal}*
Score: {gold_score}/100
Trend: {gold_tf}

📌 Trade Setup:
• Entry: {gold_entry}
• SL: {gold_entry - 18}
• TP1: {gold_entry + 35}
• TP2: {gold_entry + 60}

Reasons:
{chr(10).join(gold_reasons)}
━━━━━━━━━━━━━━━━━━━━
⚠️ _For educational purposes only_
"""
    return msg

def get_settings_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(f"DXY: {'WEAK🟢' if market['DXY']==-1 else 'STRONG🔴'}", callback_data="toggle_dxy"),
            InlineKeyboardButton(f"FED: {market['FED']}", callback_data="toggle_fed"),
        ],
        [
            InlineKeyboardButton(f"VIX: {market['VIX']} ➕", callback_data="vix_up"),
            InlineKeyboardButton(f"VIX: {market['VIX']} ➖", callback_data="vix_down"),
        ],
        [
            InlineKeyboardButton(f"NEWS: {'⚠️ON' if market['NEWS_RISK'] else '✅OFF'}", callback_data="toggle_news"),
            InlineKeyboardButton(f"BONDS: {market['BONDS']}", callback_data="toggle_bonds"),
        ],
        [
            InlineKeyboardButton("── BTC ──", callback_data="noop"),
        ],
        [
            InlineKeyboardButton(f"Daily: {market['BTC_DAILY'][:4]}", callback_data="toggle_btc_daily"),
            InlineKeyboardButton(f"4H: {market['BTC_4H'][:4]}", callback_data="toggle_btc_4h"),
            InlineKeyboardButton(f"1H: {market['BTC_1H'][:4]}", callback_data="toggle_btc_1h"),
        ],
        [
            InlineKeyboardButton(f"WHALES: {market['BTC_WHALES'][:5]}", callback_data="toggle_whales"),
            InlineKeyboardButton(f"COT BTC: {market['COT_BTC'][:4]}", callback_data="toggle_cot_btc"),
        ],
        [
            InlineKeyboardButton("── GOLD ──", callback_data="noop"),
        ],
        [
            InlineKeyboardButton(f"Daily: {market['GOLD_DAILY'][:4]}", callback_data="toggle_gold_daily"),
            InlineKeyboardButton(f"4H: {market['GOLD_4H'][:4]}", callback_data="toggle_gold_4h"),
            InlineKeyboardButton(f"1H: {market['GOLD_1H'][:4]}", callback_data="toggle_gold_1h"),
        ],
        [
            InlineKeyboardButton(f"COT GOLD: {market['COT_GOLD'][:4]}", callback_data="toggle_cot_gold"),
            InlineKeyboardButton(f"Losses: {market['GOLD_LOSSES']} ➕", callback_data="losses_up"),
            InlineKeyboardButton(f"➖", callback_data="losses_down"),
        ],
        [
            InlineKeyboardButton("🔄 GET SIGNAL", callback_data="get_signal"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

# ==================================================
# HANDLERS
# ==================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *SMART MACRO TRADING AI v5*\n\nاضغط /signal للحصول على إشارة\nاضغط /settings لتغيير الإعدادات",
        parse_mode="Markdown"
    )

async def signal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = format_signal_message()
    await update.message.reply_text(msg, parse_mode="Markdown")

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚙️ *الإعدادات* — اضغط لتغيير القيم:",
        reply_markup=get_settings_keyboard(),
        parse_mode="Markdown"
    )

def toggle(key, val1, val2):
    market[key] = val2 if market[key] == val1 else val1

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "noop":
        return
    elif data == "toggle_dxy":
        market["DXY"] = 1 if market["DXY"] == -1 else -1
    elif data == "toggle_fed":
        toggle("FED", "DOVISH", "HAWKISH")
    elif data == "vix_up":
        market["VIX"] = min(100, market["VIX"] + 1)
    elif data == "vix_down":
        market["VIX"] = max(0, market["VIX"] - 1)
    elif data == "toggle_news":
        market["NEWS_RISK"] = not market["NEWS_RISK"]
    elif data == "toggle_bonds":
        toggle("BONDS", "DOWN", "UP")
    elif data == "toggle_btc_daily":
        toggle("BTC_DAILY", "BULLISH", "BEARISH")
    elif data == "toggle_btc_4h":
        toggle("BTC_4H", "BULLISH", "BEARISH")
    elif data == "toggle_btc_1h":
        toggle("BTC_1H", "BULLISH", "BEARISH")
    elif data == "toggle_whales":
        toggle("BTC_WHALES", "ACCUMULATION", "DISTRIBUTION")
    elif data == "toggle_cot_btc":
        toggle("COT_BTC", "BULLISH", "BEARISH")
    elif data == "toggle_gold_daily":
        toggle("GOLD_DAILY", "BULLISH", "BEARISH")
    elif data == "toggle_gold_4h":
        toggle("GOLD_4H", "BULLISH", "BEARISH")
    elif data == "toggle_gold_1h":
        toggle("GOLD_1H", "BULLISH", "BEARISH")
    elif data == "toggle_cot_gold":
        toggle("COT_GOLD", "BULLISH", "BEARISH")
    elif data == "losses_up":
        market["GOLD_LOSSES"] = min(10, market["GOLD_LOSSES"] + 1)
    elif data == "losses_down":
        market["GOLD_LOSSES"] = max(0, market["GOLD_LOSSES"] - 1)
    elif data == "get_signal":
        msg = format_signal_message()
        await query.message.reply_text(msg, parse_mode="Markdown")
        return

    await query.edit_message_reply_markup(reply_markup=get_settings_keyboard())

# ==================================================
# MAIN
# ==================================================

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("signal", signal_command))
    app.add_handler(CommandHandler("settings", settings_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("✅ Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
