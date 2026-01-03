import yfinance as yf
import pandas as pd
import requests
import config

def get_fear_and_greed():
    """CNN 공포탐욕지수 크롤링"""
    try:
        url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        r = requests.get(url, headers=headers, timeout=5)
        data = r.json()
        score = int(data['fear_and_greed']['score'])
        rating = data['fear_and_greed']['rating'].capitalize()
        return f"{rating} ({score})"
    except:
        return "N/A"

def calculate_rsi(series, period=14):
    """RSI 직접 계산 함수"""
    delta = series.diff(1)
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_mfi(df, period=14):
    """MFI 직접 계산 함수"""
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    money_flow = typical_price * df['Volume']
    
    positive_flow = money_flow.where(typical_price > typical_price.shift(1), 0)
    negative_flow = money_flow.where(typical_price < typical_price.shift(1), 0)
    
    positive_mf = positive_flow.rolling(window=period).sum()
    negative_mf = negative_flow.rolling(window=period).sum()
    
    mfi = 100 - (100 / (1 + (positive_mf / negative_mf)))
    return mfi

def get_market_data():
    """시장 지수 가져오기"""
    try:
        df = yf.download("^IXIC ^GSPC", period="30d", progress=False)['Close']
        vix = yf.Ticker("^VIX").history(period="1d")['Close'].iloc[-1]
        fng = get_fear_and_greed()
        
        # 시장 지수 RSI 계산
        ndx_rsi = calculate_rsi(df['^IXIC']).iloc[-1]
        spx_rsi = calculate_rsi(df['^GSPC']).iloc[-1]
            
        return df['^IXIC'].iloc[-1], df['^GSPC'].iloc[-1], vix, fng
    except:
        return 0, 0, 0, "-"

def analyze_stock(ticker):
    """개별 종목 분석"""
    try:
        df = yf.Ticker(ticker).history(period="3mo")
        if df.empty: return None
        
        # --- 지표 직접 계산 ---
        # 1. RSI
        df['RSI'] = calculate_rsi(df['Close'], 14)
        # 2. MA20
        df['MA20'] = df['Close'].rolling(window=20).mean()
        # 3. MFI
        df['MFI'] = calculate_mfi(df, 14)
        
        curr = df.iloc[-1]
        price = curr['Close']
        rsi = curr['RSI']
        mfi = curr['MFI']
        ma20 = curr['MA20']
        
        # 값이 NaN(계산불가)이면 50으로 처리
        if pd.isna(rsi): rsi = 50
        if pd.isna(mfi): mfi = 50
        if pd.isna(ma20): ma20 = price

        ma20_gap = ((price - ma20) / ma20) * 100
        
        # --- 점수 계산 ---
        score = 0
        
        if rsi < config.RSI_OVERSOLD: score += 40
        elif rsi < config.RSI_WATCH: score += 20
        
        if mfi < config.MFI_STRONG: score += 30
        elif mfi < config.MFI_WATCH: score += 10
        
        if price < ma20: score += 30
        
        if rsi > config.RSI_OVERBOUGHT: score = -99
        
        return {
            "price": price, "rsi": rsi, "mfi": mfi, 
            "ma20_gap": ma20_gap, "score": score
        }
    except Exception as e:
        return None