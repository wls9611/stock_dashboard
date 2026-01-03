import yfinance as yf
import pandas as pd
import requests
import config

def get_fear_and_greed():
    """CNN 공포탐욕지수 크롤링"""
    try:
        url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
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
    delta = series.diff(1)
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_mfi(df, period=14):
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    money_flow = typical_price * df['Volume']
    positive_flow = money_flow.where(typical_price > typical_price.shift(1), 0)
    negative_flow = money_flow.where(typical_price < typical_price.shift(1), 0)
    positive_mf = positive_flow.rolling(window=period).sum()
    negative_mf = negative_flow.rolling(window=period).sum()
    mfi = 100 - (100 / (1 + (positive_mf / negative_mf)))
    return mfi

def get_market_data():
    """시장 지수 및 기준 날짜 가져오기"""
    try:
        # 나스닥100(^NDX), S&P500(^GSPC), 다우(^DJI)
        tickers = ["^NDX", "^GSPC", "^DJI"]
        # 주말 이슈 방지를 위해 넉넉히 50일치 가져와서 마지막(최신) 데이터 사용
        df = yf.download(tickers, period="50d", progress=False)['Close']
        
        # 데이터가 있는 마지막 날짜 확인 (기준 날짜용)
        last_date = df.index[-1].strftime("%Y-%m-%d")
        
        vix = yf.Ticker("^VIX").history(period="5d")['Close'].iloc[-1]
        fng = get_fear_and_greed()
        
        # 각 지수 최신값 (NaN 제거 후 마지막 값 사용)
        ndx_series = df['^NDX'].dropna()
        spx_series = df['^GSPC'].dropna()
        dji_series = df['^DJI'].dropna()

        # 지수별 RSI 계산
        ndx_rsi = calculate_rsi(ndx_series).iloc[-1]
        spx_rsi = calculate_rsi(spx_series).iloc[-1]
        dji_rsi = calculate_rsi(dji_series).iloc[-1]
            
        return {
            "date": last_date,
            "ndx": {"price": ndx_series.iloc[-1], "rsi": ndx_rsi},
            "spx": {"price": spx_series.iloc[-1], "rsi": spx_rsi},
            "dji": {"price": dji_series.iloc[-1], "rsi": dji_rsi},
            "vix": vix,
            "fng": fng
        }
    except Exception as e:
        print(f"Market Data Error: {e}")