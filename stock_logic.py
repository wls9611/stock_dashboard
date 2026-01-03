import yfinance as yf
import pandas as pd
import requests
import config

def get_fear_and_greed():
    """CNN 공포탐욕지수 크롤링 (차단 시 N/A 반환)"""
    try:
        url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
        # 마치 일반 브라우저인 척 헤더를 설정
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.cnn.com/"
        }
        r = requests.get(url, headers=headers, timeout=3)
        
        if r.status_code == 200:
            data = r.json()
            score = int(data['fear_and_greed']['score'])
            rating = data['fear_and_greed']['rating'].capitalize()
            return f"{rating} ({score})"
        else:
            return "데이터 없음"
    except:
        return "데이터 없음"

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
    """시장 지수 가져오기 (나스닥100, S&P500, 다우, VIX, 공탐)"""
    try:
        # 나스닥100(^NDX), S&P500(^GSPC), 다우(^DJI)
        tickers = ["^NDX", "^GSPC", "^DJI"]
        df = yf.download(tickers, period="30d", progress=False)['Close']
        vix = yf.Ticker("^VIX").history(period="1d")['Close'].iloc[-1]
        fng = get_fear_and_greed()
        
        # 각 지수 RSI 계산
        ndx_val = df['^NDX'].iloc[-1]
        spx_val = df['^GSPC'].iloc[-1]
        dji_val = df['^DJI'].iloc[-1]
        
        ndx_rsi = calculate_rsi(df['^NDX']).iloc[-1]
        spx_rsi = calculate_rsi(df['^GSPC']).iloc[-1]
        dji_rsi = calculate_rsi(df['^DJI']).iloc[-1]
            
        return {
            "ndx": {"price": ndx_val, "rsi": ndx_rsi},
            "spx": {"price": spx_val, "rsi": spx_rsi},
            "dji": {"price": dji_val, "rsi": dji_rsi},
            "vix": vix,
            "fng": fng
        }
    except Exception as e:
        print(f"Market Data Error: {e}")
        return None

def analyze_stock(ticker):
    """개별 종목 분석"""
    try:
        df = yf.Ticker(ticker).history(period="3mo")
        if df.empty: return None
        
        # --- 지표 직접 계산 ---
        df['RSI'] = calculate_rsi(df['Close'], 14)
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MFI'] = calculate_mfi(df, 14)
        
        curr = df.iloc[-1]
        price = curr['Close']
        rsi = curr['RSI']
        mfi = curr['MFI']
        ma20 = curr['MA20']
        
        # 값이 NaN이면 기본값 처리
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
    except:
        return None