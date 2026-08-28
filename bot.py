import os
import time
import telebot
import pandas as pd
import numpy as np
import ta
from threading import Thread

# 1. Initialize Bot configuration
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

# 🚀 Your linked live Telegram Channel
CHANNEL_ID = "@madmo_gold_signals" 

def get_mock_gold_data():
    """Simulates live 15-minute candlestick data for XAU/USD."""
    np.random.seed(int(time.time()) % 1000) # Ensure dynamic price shifts over time
    dates = pd.date_range(end=pd.Timestamp.now(), periods=50, freq='15min')
    prices = np.sin(np.linspace(0, 10, 50)) * 15 + 2520 + np.random.normal(0, 4, 50)
    return pd.DataFrame(index=dates, data={'Close': prices})

def get_economic_calendar():
    """
    Simulates real-time global economic data feeds.
    In live deployment, replace this with a dynamic API fetch loop.
    """
    now = pd.Timestamp.now()
    return [
        {
            "time": now + pd.Timedelta(minutes=15), # Alert set to trigger exactly 15 mins prior
            "event": "US Core Retail Sales MoM",
            "impact": "HIGH",
            "usd_bias": "USD_BULLISH"
        }
    ]

def analyze_market_state():
    """Analyzes market for manual queries and returns a response string."""
    df = get_mock_gold_data()
    news_list = get_economic_calendar()
    
    df['EMA_20'] = ta.trend.ema_indicator(close=df['Close'], window=20)
    df['EMA_50'] = ta.trend.ema_indicator(close=df['Close'], window=50)
    df['RSI'] = ta.momentum.rsi(close=df['Close'], window=14)
    
    current_time = df.index[-1]
    current_price = round(df['Close'].iloc[-1], 2)
    rsi_now = df['RSI'].iloc[-1]
    rsi_prev = df['RSI'].iloc[-2]
    
    # Structural News Safeguard check
    for item in news_list:
        time_diff = (item['time'] - current_time).total_seconds() / 60.0
        if item['impact'] == 'HIGH' and -30 <= time_diff <= 30:
            return (
                f"⚠️ *STAY AWAY WARNING* ⚠️\n\n"
                f"High impact event: *{item['event']}* occurs soon.\n"
                f"Market execution halted to prevent spread expansion."
            )
            
    is_uptrend = df['EMA_20'].iloc[-1] > df['EMA_50'].iloc[-1]
    is_downtrend = df['EMA_20'].iloc[-1] < df['EMA_50'].iloc[-1]
    rsi_crossed_up = (rsi_prev <= 40) and (rsi_now > 40)
    rsi_crossed_down = (rsi_prev >= 60) and (rsi_now < 60)
    
    if is_uptrend and rsi_crossed_up:
        return (
            f"🚀 *XAU/USD HIGH PROBABILITY BUY* 🚀\n\n"
            f"▪️ *Entry Price:* ${current_price}\n"
            f"▪️ *Take Profit (TP):* ${round(current_price + 24.0, 2)}\n"
            f"▪️ *Stop Loss (SL):* ${round(current_price - 12.0, 2)}\n\n"
            f"_Trend alignment validated via 20/50 EMA overlap._"
        )
        
    if is_downtrend and rsi_crossed_down:
        return (
            f"📉 *XAU/USD HIGH PROBABILITY SELL* 📉\n\n"
            f"▪️ *Entry Price:* ${current_price}\n"
            f"▪️ *Take Profit (TP):* ${round(current_price - 24.0, 2)}\n"
            f"▪️ *Stop Loss (SL):* ${round(current_price + 12.0, 2)}\n\n"
            f"_Trend alignment validated via 20/50 EMA overlap._"
        )
        
    return None

def automated_background_scanner():
    """Continuous automated scanning engine running every 15 minutes on a separate thread layer."""
    print("Automated channel broadcast thread initialized...")
    last_processed_signal = None
    alerted_events = set()
    
    while True:
        try:
            now = pd.Timestamp.now()
            
            # --- 1. PROACTIVE PUSH NEWS ALERTS (15 Mins Before Event) ---
            news_list = get_economic_calendar()
            for item in news_list:
                time_diff = (item['time'] - now).total_seconds() / 60.0
                event_key = f"{item['event']}_{item['time'].strftime('%H:%M')}"
                
                # Broadcast warning if event is within 15 minutes and hasn't been sent yet
                if item['impact'] == 'HIGH' and 0 <= time_diff <= 15 and event_key not in alerted_events:
                    news_warning = (
                        f"🚨 *AUTOMATED RISK ALERT* 🚨\n\n"
                        f"High-Impact event *{item['event']}* starts in *{round(time_diff)} minutes*!\n"
                        f"⚠️ *Recommendation:* Protect capital, adjust trailing stops, or STAY AWAY."
                    )
                    bot.send_message(CHANNEL_ID, news_warning, parse_mode='Markdown')
                    alerted_events.add(event_key)
            
            # --- 2. AUTOMATED MARKET SIGNAL BROADCASTER ---
            current_signal = analyze_market_state()
            
            # Broadcast signals when a valid setup presents itself
            if current_signal and "STAY AWAY" not in current_signal and current_signal != last_processed_signal:
                bot.send_message(CHANNEL_ID, current_signal, parse_mode='Markdown')
                last_processed_signal = current_signal
                
            elif "STAY AWAY" in str(current_signal) and current_signal != last_processed_signal:
                bot.send_message(CHANNEL_ID, current_signal, parse_mode='Markdown')
                last_processed_signal = current_signal

        except Exception as e:
            print(f"Loop scanning error encountered: {e}")
            
        # Check market indicators exactly every 15 minutes (900 seconds)
        time.sleep(900)

# --- TELEGRAM USER COMMAND HANDLERS ---
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Welcome to the High Probability XAU/USD Signal Bot. The bot is actively scanning markets and broadcasting live to your channel.")

@bot.message_handler(commands=['signal'])
def send_signal(message):
    status_msg = analyze_market_state()
    if status_msg is None:
        df = get_mock_gold_data()
        status_msg = f"📊 *XAU/USD Market Status:* No clean setup found. Price: ${round(df['Close'].iloc[-1],2)}."
    bot.reply_to(message, status_msg, parse_mode='Markdown')

if __name__ == "__main__":
    # Initialize the background automated engine thread
    scanner_thread = Thread(target=automated_background_scanner)
    scanner_thread.daemon = True
    scanner_thread.start()
    
    # Run user interaction listener loop
    bot.infinity_polling()
