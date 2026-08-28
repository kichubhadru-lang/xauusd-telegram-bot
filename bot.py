import os
import telebot
import pandas as pd
import numpy as np
import ta

# Initialize Bot using GitHub Environment Secret
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

def get_mock_gold_data():
    np.random.seed(42)
    dates = pd.date_range(end=pd.Timestamp.now(), periods=50, freq='15min')
    prices = np.sin(np.linspace(0, 10, 50)) * 15 + 2500 + np.random.normal(0, 3, 50)
    return pd.DataFrame(index=dates, data={'Close': prices})

def get_economic_calendar():
    now = pd.Timestamp.now()
    return {
        now + pd.Timedelta(minutes=15): {
            "event": "US Core Retail Sales MoM",
            "impact": "HIGH",
            "usd_bias": "USD_BULLISH"
        }
    }

def analyze_market():
    df = get_mock_gold_data()
    news = get_economic_calendar()
    
    df['EMA_20'] = ta.trend.ema_indicator(close=df['Close'], window=20)
    df['EMA_50'] = ta.trend.ema_indicator(close=df['Close'], window=50)
    df['RSI'] = ta.momentum.rsi(close=df['Close'], window=14)
    
    current_time = df.index[-1]
    current_price = round(df['Close'].iloc[-1], 2)
    rsi_now = df['RSI'].iloc[-1]
    rsi_prev = df['RSI'].iloc[-2]
    
    for event_time, details in news.items():
        time_diff = abs((current_time - event_time).total_seconds()) / 60.0
        if details['impact'] == 'HIGH' and time_diff <= 30:
            return (
                f"⚠️ *STAY AWAY WARNING* ⚠️\n\n"
                f"High impact event: *{details['event']}* occurs soon.\n"
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
        
    return f"📊 *XAU/USD Market Status:* No clean setup found. Price: ${current_price}. RSI: {round(rsi_now, 2)}."

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Welcome to the High Probability XAU/USD Signal Bot. Use /signal to run an audit analysis.")

@bot.message_handler(commands=['signal'])
def send_signal(message):
    status_msg = analyze_market()
    bot.reply_to(message, status_msg, parse_mode='Markdown')

if __name__ == "__main__":
    bot.infinity_polling()
              
