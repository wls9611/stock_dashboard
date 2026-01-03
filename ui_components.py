import yfinance as yf
import pandas as pd
import requests
import config
import streamlit as st
import time # 시간 지연을 위해 추가

def get_fear_and_greed():
    """CNN 공포탐욕지수 크롤링 (재시도 로직 추가)"""
    url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
    
    # 진짜 크롬 브라우저처럼 보이는 헤더 정보
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.cnn.com/"
    }

    # 최대 3번 시도 (한 번 실패해도 다시 시도)
    for _ in range(3):
        try:
            r = requests.get(url, headers=headers, timeout=10) # 타임아웃 10초로 연장
            if r.status_code == 200:
                data = r.json()
                score = int(data['fear_and_greed']['score'])
                rating = data['fear_and_greed']['rating'].capitalize()
                return f"{rating} ({score})"
            time.sleep(1) # 실패 시 1초 쉬고 재시도
        except:
            time.sleep(1)
            continue
            
    return "N/A (접속차단)"

# ... (나머지 calculate_rsi, calculate_mfi, get_market_data, analyze_stock 함수는 그대로 유지) ...
# 아래는 기존 코드와 동일하게 유지하면 됩니다.

def calculate_rsi(series, period=14):
    try:
        delta = series.diff(1)
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    except:
        return pd.Series([50]*len(series))

def calculate_mfi(df, period=14):
    try:
        typical_price = (df['High'] + df['Low'] + df['Close']) / 3
        money_flow = typical_price * df['Volume']
        positive_flow = money_flow.where(typical_price > typical_price.shift(1), 0)
        negative_flow = money_flow.where(typical_price < typical_price.shift(1), 0)
        positive_mf = positive_flow.rolling(window=period).sum()
        negative_mf = negative_flow.rolling(window=period).sum()
        mfi = 100 - (100 / (1 + (positive_mf / negative_mf)))
        return mfi
    except:
        return pd.Series([50]*len(df))

@st.cache_data(ttl=300)
def get_market_data():
    try:
        tickers = ["^NDX", "^GSPC", "^DJI"]
        df = yf.download(tickers, period="50d", progress=False)['Close']
        
        if df.empty: return None
            
        last_date = df.index[-1].strftime("%Y-%m-%d")
        
        vix_df = yf.Ticker("^VIX").history(period="5d")
        vix = vix_df['Close'].iloc[-1] if not vix_df.empty else 0
        
        # 여기서 위에서 만든 강력해진 크롤링 함수 호출
        fng = get_fear_and_greed()
        
        result = {"date": last_date, "vix": vix, "fng": fng}
        
        for t, name in zip(["^NDX", "^GSPC", "^DJI"], ["ndx", "spx", "dji"]):
            if t in df.columns:
                series = df[t].dropna()
                if len(series) >= 2:
                    curr = series.iloc[-1]
                    prev = series.iloc[-2]
                    change = ((curr - prev) / prev) * 100
                    rsi = calculate_rsi(series).iloc[-1]
                    
                    result[name] = {
                        "price": curr, 
                        "change": change,
                        "rsi": rsi
                    }
                else:
                    result[name] = {"price": series.iloc[-1], "change": 0, "rsi": 50}
            else:
                result[name] = {"price": 0, "change": 0, "rsi": 50}
                
        return result
    except Exception as e:
        print(f"Market Data Error: {e}")
        return None

@st.cache_data(ttl=300)
def analyze_stock(ticker):
    try:
        df = yf.Ticker(ticker).history(period="6mo")
        if df.empty or len(df) < 20: return None
        
        df['RSI'] = calculate_rsi(df['Close'], 14)
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MFI'] = calculate_mfi(df, 14)
        
        curr = df.iloc[-1]
        
        if len(df) >= 2:
            prev = df.iloc[-2]
            change = ((curr['Close'] - prev['Close']) / prev['Close']) * 100
        else:
            change = 0
            
        price = curr['Close']
        rsi = curr['RSI'] if not pd.isna(curr['RSI']) else 50
        mfi = curr['MFI'] if not pd.isna(curr['MFI']) else 50
        ma20 = curr['MA20'] if not pd.isna(curr['MA20']) else price
        
        ma20_gap = ((price - ma20) / ma20) * 100
        
        score = 0
        if rsi < config.RSI_OVERSOLD: score += 40
        elif rsi < config.RSI_WATCH: score += 20
        
        if mfi < config.MFI_STRONG: score += 30
        elif mfi < config.MFI_WATCH: score += 10
        
        if price < ma20: score += 30
        if rsi > config.RSI_OVERBOUGHT: score = -99
        
        return {
            "price": price, "change": change,
            "rsi": rsi, "mfi": mfi, 
            "ma20_gap": ma20_gap, "score": score
        }
    except:
        return None