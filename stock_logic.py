import yfinance as yf
import pandas_ta as ta
import config
from fear_greed_index.CNNFearAndGreedIndex import CNNFearAndGreedIndex

def get_market_data():
    """시장 지수(나스닥, S&P, VIX, 공탐지수) 가져오기"""
    try:
        df = yf.download("^IXIC ^GSPC", period="5d", progress=False)['Close']
        vix = yf.Ticker("^VIX").history(period="1d")['Close'].iloc[-1]
        
        try:
            cnn = CNNFearAndGreedIndex()
            fng = cnn.index_summary.split(':')[-1].strip()
        except:
            fng = "-"
            
        return df['^IXIC'].iloc[-1], df['^GSPC'].iloc[-1], vix, fng
    except:
        return 0, 0, 0, "-"

def analyze_stock(ticker):
    """개별 종목 데이터 분석 및 점수 계산"""
    try:
        # 최근 3개월 데이터 (MFI 계산 위해 Volume 필요)
        df = yf.Ticker(ticker).history(period="3mo")
        if df.empty: return None
        
        # 보조지표 계산
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['MA20'] = ta.sma(df['Close'], length=20)
        df['MFI'] = ta.mfi(df['High'], df['Low'], df['Close'], df['Volume'], length=14)
        
        curr = df.iloc[-1]
        price = curr['Close']
        rsi = curr['RSI']
        mfi = curr['MFI']
        ma20 = curr['MA20']
        
        # 이평선 괴리율 계산 (%)
        ma20_gap = ((price - ma20) / ma20) * 100
        
        # --- 💯 가중치 점수 계산 (Hybrid Scoring) ---
        score = 0
        
        # 1. RSI 점수 (40점)
        if rsi < config.RSI_OVERSOLD: score += 40
        elif rsi < config.RSI_WATCH: score += 20
        
        # 2. MFI 점수 (30점)
        if mfi < config.MFI_STRONG: score += 30
        elif mfi < config.MFI_WATCH: score += 10
        
        # 3. 이평선 점수 (30점)
        if price < ma20: score += 30
        
        # 매도 시그널 (과열 시 강제 -99점)
        if rsi > config.RSI_OVERBOUGHT: score = -99
        
        return {
            "price": price, "rsi": rsi, "mfi": mfi, 
            "ma20_gap": ma20_gap, "score": score
        }
    except:
        return None