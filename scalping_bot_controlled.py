import time
import threading
import requests
import telegram
import pandas as pd
from telegram.ext import Updater, CommandHandler
from datetime import datetime

# بيانات البوت
TOKEN = "7615175244:AAFa_XsGIttwH-Ka3xLzh8sHOzwEoD_tN5k"
OWNER_ID = 1403010427
running = False

def get_ohlcv():
    url = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=100"
    data = requests.get(url).json()
    df = pd.DataFrame(data, columns=[
        'time', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'qv', 'trades', 'tbv', 'tqv', 'ignore'
    ])
    df['close'] = df['close'].astype(float)
    return df

def calculate_rsi(data, period=14):
    delta = data.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def analyze():
    df = get_ohlcv()
    df['EMA5'] = df['close'].ewm(span=5, adjust=False).mean()
    df['EMA10'] = df['close'].ewm(span=10, adjust=False).mean()
    df['RSI'] = calculate_rsi(df['close'])

    current_price = df['close'].iloc[-1]
    prev_price = df['close'].iloc[-2]
    ema5 = df['EMA5'].iloc[-1]
    ema10 = df['EMA10'].iloc[-1]
    rsi = df['RSI'].iloc[-1]

    signal = "⏸ استقرار"
    if current_price > prev_price and ema5 > ema10 and rsi < 70:
        signal = "🔼 شراء"
    elif current_price < prev_price and ema5 < ema10 and rsi > 30:
        signal = "🔽 بيع"

    confidence = round(abs(current_price - prev_price) / prev_price * 100, 2)
    msg = f"""
📊 سكالبينغ بيتكوين | BTC/USDT
🕒 {datetime.now().strftime('%H:%M:%S')}

📉 السعر الحالي: {current_price:.2f}
📈 السعر السابق: {prev_price:.2f}

EMA 5: {ema5:.2f}
EMA 10: {ema10:.2f}
RSI: {rsi:.2f}

📍 الإشارة: {signal}
📊 نسبة التغير: {confidence}%
"""
    return msg

def send_signals(context):
    global running
    while running:
        try:
            msg = analyze()
            context.bot.send_message(chat_id=OWNER_ID, text=msg)
            time.sleep(30)
        except Exception as e:
            context.bot.send_message(chat_id=OWNER_ID, text=f"🚨 خطأ: {str(e)}")
            time.sleep(10)

def start_command(update, context):
    global running
    if update.effective_user.id != OWNER_ID:
        return
    if not running:
        running = True
        threading.Thread(target=send_signals, args=(context,), daemon=True).start()
        context.bot.send_message(chat_id=OWNER_ID, text="🚀 تم تشغيل إشارات السكالبينغ.")
    else:
        context.bot.send_message(chat_id=OWNER_ID, text="✅ البوت يعمل بالفعل.")

def stop_command(update, context):
    global running
    if update.effective_user.id != OWNER_ID:
        return
    running = False
    context.bot.send_message(chat_id=OWNER_ID, text="🛑 تم إيقاف البوت مؤقتًا.")

def status_command(update, context):
    if update.effective_user.id != OWNER_ID:
        return
    status = "✅ يعمل" if running else "⛔ متوقف"
    context.bot.send_message(chat_id=OWNER_ID, text=f"📡 الحالة الحالية: {status}")

def signal_command(update, context):
    if update.effective_user.id != OWNER_ID:
        return
    msg = analyze()
    context.bot.send_message(chat_id=OWNER_ID, text=msg)

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start_command))
    dp.add_handler(CommandHandler("stop", stop_command))
    dp.add_handler(CommandHandler("status", status_command))
    dp.add_handler(CommandHandler("signal", signal_command))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
