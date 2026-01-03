# --- 관심 종목 리스트 ---
TICKERS = [
    "PLTR", "META", "NVDA", "GOOGL",
    "MSFT", "AAPL", "AMZN", "TSLA"
]

# --- 매매 타점 기준값 (Thresholds) ---
# RSI 기준
RSI_OVERSOLD = 35    # 강력 매수 기준 (이 이하일 때)
RSI_WATCH = 40       # 매수 관찰 기준
RSI_OVERBOUGHT = 70  # 강력 매도 기준 (이 이상일 때)

# MFI 기준
MFI_STRONG = 40      # 강력 매수 MFI 기준
MFI_WATCH = 55       # 매수 관찰 MFI 기준