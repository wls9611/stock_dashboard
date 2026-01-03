# --- 관심 종목 리스트 (TICKERS 변수가 반드시 있어야 함) ---
TICKERS = [
    "PLTR", "NVDA", "GOOGL", "META", 
    "AMZN", "TSLA", "AAPL", "MSFT"
]

# --- 매매 타점 기준값 ---
RSI_OVERSOLD = 35    # 강력 매수 기준
RSI_WATCH = 40       # 매수 관찰 기준
RSI_OVERBOUGHT = 70  # 강력 매도 기준

MFI_STRONG = 40      # 강력 매수 MFI
MFI_WATCH = 55       # 매수 관찰 MFI