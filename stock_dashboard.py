import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="2026 통합 투자 대시보드", layout="wide", initial_sidebar_state="collapsed")

# 2. RSI 계산 함수 (신규 추가)
def calculate_rsi(series, period=14):
    delta = series.diff(1)
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1] # 가장 최근 RSI 값 반환

# 3. 데이터 수집 함수 (RSI 포함)
def get_market_data(ticker, period="1y"):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
        if not df.empty:
            curr = df['Close'].iloc[-1]
            prev = df['Close'].iloc[-2]
            change = ((curr - prev) / prev) * 100
            date = df.index[-1].strftime('%Y-%m-%d')
            rsi = calculate_rsi(df['Close']) # RSI 계산
            return curr, change, df['Close'], date, rsi
        return 0, 0, pd.Series(), "N/A", 0
    except:
        return 0, 0, pd.Series(), "N/A", 0

# 4. CNN 공포와 탐욕 지수 수집
def get_realtime_fg():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata/"
        r = requests.get(url, headers=headers, timeout=5)
        return float(r.json()['fear_and_greed']['score'])
    except:
        return 45.0 # 에러 시 중립값

# --- 데이터 로드 ---
vix_v, _, _, update_date, _ = get_market_data("^VIX")
snp_v, snp_c, snp_h, _, snp_rsi = get_market_data("^GSPC")
ndx_v, ndx_c, ndx_h, _, ndx_rsi = get_market_data("^NDX")
dji_v, dji_c, dji_h, _, dji_rsi = get_market_data("^DJI")
w5000_v, _, _, _, _ = get_market_data("^W5000")

# 국내 지수 데이터 로드 (추가됨)
ks_v, ks_c, ks_h, _, ks_rsi = get_market_data("^KS11")
kq_v, kq_c, kq_h, _, kq_rsi = get_market_data("^KQ11")

# 코인 데이터 로드
btc_v, btc_c, btc_h, _, btc_rsi = get_market_data("BTC-USD")
eth_v, eth_c, eth_h, _, eth_rsi = get_market_data("ETH-USD")

# [지표 계산]
realtime_buffett = (w5000_v * 1.05 / 30770) * 100 if w5000_v > 0 else (snp_v / 2400) * 230
realtime_fg = get_realtime_fg()

# [종합 지수]
v_score = max(0, min(100, (vix_v - 10) / 30 * 100))
b_score = max(0, min(100, (realtime_buffett - 100) / 150 * 100))
total_score = ((100 - v_score) + b_score + realtime_fg) / 3

# 상태에 따른 색상 결정
if total_score >= 70:
    status_color = "#f87171" # 빨강 (위험/매도)
    status_msg = "🔥 과열 (매도 관점)"
elif total_score <= 40:
    status_color = "#34d399" # 초록 (기회/매수)
    status_msg = "💧 침체 (매수 기회)"
else:
    status_color = "#fbbf24" # 노랑 (중립)
    status_msg = "⚖️ 중립 (관망)"

# ---------------------------------------------------------
# UI 구성
# ---------------------------------------------------------
st.title("📊 2026 통합 투자 전략 대시보드")
st.caption(f"📅 데이터 기준: {update_date} | ⚡ RSI(14) 자동 계산 포함")

# 상단 배너 (동적 색상 적용)
st.markdown(f"""
<div style="background-color: #0f172a; padding: 25px; border-radius: 15px; border-left: 10px solid {status_color}; margin-bottom: 30px; color: white;">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
        <div>
            <h2 style="margin: 0; color: #60a5fa;">🌍 해외총합 지표: {total_score:.1f}점</h2>
            <span style="font-size: 1.2em; font-weight: bold; color: {status_color};">{status_msg}</span>
        </div>
    </div>
    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; text-align: center;">
        <div style="background-color: #1e293b; padding: 15px; border-radius: 10px;">
            <p style="color: #f87171; font-weight:bold;">⚠️ 지표 70점 이상</p>
            <p style="margin:0;">레버리지 포지션 주의</p>
        </div>
        <div style="background-color: #1e293b; padding: 15px; border-radius: 10px;">
            <p style="color: #fbbf24; font-weight:bold;">💰 지표 40점 이하</p>
            <p style="margin:0;">현금 10~15% 유지</p>
        </div>
        <div style="background-color: #1e293b; padding: 15px; border-radius: 10px;">
            <p style="color: #34d399; font-weight:bold;">📉 매수 원칙</p>
            <p style="margin:0;">RSI 30 부근 분할매도</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

tabs = st.tabs(["🌍 해외지표 분석", "🇺🇸 해외 지수", "🇰🇷 국내 지수", "🪙 코인 지수"])

# 탭 1: 지표 분석
with tabs[0]:
    st.header("🌍 실시간 매크로 지표")
    c1, c2, c3 = st.columns(3)
    c1.metric("VIX (공포지수)", f"{vix_v:.2f}")
    c1.progress(max(0.0, min(1.0, (vix_v-10)/30)))
    
    c2.metric("버핏 지수 (추정)", f"{realtime_buffett:.1f}%")
    c2.progress(max(0.0, min(1.0, (realtime_buffett-100)/150)))
    
    c3.metric("공포/탐욕 (CNN)", f"{realtime_fg:.0f}")
    c3.progress(realtime_fg / 100.0)

# 탭 2: 해외 지수 (RSI 추가)
with tabs[1]:
    st.subheader("🇺🇸 미국 3대 지수")
    c1, c2, c3 = st.columns(3)
    
    c1.metric("NASDAQ 100", f"{ndx_v:,.2f}", f"{ndx_c:.2f}%", delta_color="normal")
    c1.info(f"RSI: {ndx_rsi:.1f}")
    c1.line_chart(ndx_h)
    
    c2.metric("S&P 500", f"{snp_v:,.2f}", f"{snp_c:.2f}%", delta_color="normal")
    c2.info(f"RSI: {snp_rsi:.1f}")
    c2.line_chart(snp_h)
    
    c3.metric("DOW JONES", f"{dji_v:,.2f}", f"{dji_c:.2f}%", delta_color="normal")
    c3.info(f"RSI: {dji_rsi:.1f}")
    c3.line_chart(dji_h)

# 탭 3: 국내 지수 (복구됨)
with tabs[2]:
    st.subheader("🇰🇷 국내 양대 지수")
    k1, k2 = st.columns(2)
    
    k1.metric("KOSPI", f"{ks_v:,.2f}", f"{ks_c:.2f}%")
    k1.info(f"RSI: {ks_rsi:.1f}")
    k1.line_chart(ks_h)
    
    k2.metric("KOSDAQ", f"{kq_v:,.2f}", f"{kq_c:.2f}%")
    k2.info(f"RSI: {kq_rsi:.1f}")
    k2.line_chart(kq_h)

# 탭 4: 코인 지수
with tabs[3]:
    st.subheader("🪙 가상자산")
    cc1, cc2 = st.columns(2)
    
    cc1.metric("Bitcoin", f"${btc_v:,.0f}", f"{btc_c:.2f}%")
    cc1.info(f"RSI: {btc_rsi:.1f}")
    cc1.line_chart(btc_h)
    
    cc2.metric("Ethereum", f"${eth_v:,.0f}", f"{eth_c:.2f}%")
    cc2.info(f"RSI: {eth_rsi:.1f}")
    cc2.line_chart(eth_h)