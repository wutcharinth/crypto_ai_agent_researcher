import ccxt
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD
import feedparser
from datetime import datetime

def fetch_crypto_data(symbol: str, timeframe: str = '1h', limit: int = 100):
    """
    Fetches OHLCV data for a given symbol from Binance (or other exchange).
    """
    try:
        exchange = ccxt.binance()
        # CCXT uses 'BTC/USDT' format
        formatted_symbol = symbol.upper() + '/USDT'
        ohlcv = exchange.fetch_ohlcv(formatted_symbol, timeframe, limit=limit)
        
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return pd.DataFrame()

def calculate_technicals(df: pd.DataFrame):
    """
    Adds RSI and MACD to the dataframe.
    """
    if df.empty:
        return df
    
    # RSI
    rsi_indicator = RSIIndicator(close=df['close'], window=14)
    df['rsi'] = rsi_indicator.rsi()
    
    # MACD
    macd_indicator = MACD(close=df['close'])
    df['macd'] = macd_indicator.macd()
    
    return df

def fetch_crypto_news(query: str = "crypto"):
    """
    Fetches top news from Coindesk via RSS.
    """
    rss_url = "https://www.coindesk.com/arc/outboundfeeds/rss/"
    feed = feedparser.parse(rss_url)
    
    news_items = []
    for entry in feed.entries[:5]:
        news_items.append({
            "title": entry.title,
            "link": entry.link,
            "published": entry.published,
            "summary": entry.summary
        })
    return news_items

if __name__ == "__main__":
    # Test
    df = fetch_crypto_data('BTC')
    df = calculate_technicals(df)
    print("Technicals:\n", df.tail(1))
    
    news = fetch_crypto_news()
    print("\nNews:\n", news[0]['title'])
