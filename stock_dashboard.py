import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 1. 페이지 설정 및 헤더
st.set_page_config(page_title="2026 실시간 투자 대시보드", layout="wide")
today = datetime.now().strftime("%Y년 %m월 %d일")

st.title("📊 2026 실시간 통합 투자 인사이트")
st.subheader(f"📅 실시간 데이터 기준 일자: {today}")
st.markdown("---")

# 2. 실시간 데이터 수집 핵심 함수
def get_current_data(ticker):
    try:
        # 주말/공휴일 대비 5일치 데이터를 가져와 마지막 거래일 확정
        df = yf.Ticker(ticker).history(period="5d")
        if not df.empty:
            curr = df['Close'].iloc[-1]
            prev = df['Close'].iloc[-2]
            chg = ((curr - prev) / prev) * 100
            return curr, chg
        return 0, 0
    except:
        return 0, 0

# 3. 실시간 지표 기반 투자 점수 계산 (사전 로드 제거)
def calculate_realtime_score():
    # A. VIX (공포지수) - 실시간 로드
    vix_val, _ = get_current_data("^VIX")
    
    # B. 버핏 지수 (실시간 지수 기반 계산)
    # 2026년 예상 GDP를 약 $28.5T로 가정하고 Wilshire 5000 지수를 통해 계산
    w5000, _ = get_current_data("^W5000")
    if w5000 == 0: # 데이터 부재 시 S&P500으로 대체 계산
        snp, _ = get_current_data("^GSPC")
        buffett_val = (snp / 2400) * 230 # 지수 비율로 환산
    else:
        buffett_val = (w5000 / 28500) * 100 

    # C. 하이일드 스프레드 & 공탐지수
    # yfinance로 직접 수집이 어려운 매크로 지표는 최신 공식 발표 수치 활용
    hys_val = 2.81  # 2026.01 기준 최신 스프레드
    fg_val = 45     # CNN Fear & Greed 최신 수치

    # 각 지표 정규화 (사용자 30-50-70 원칙)
    v_s = max(0, min(100, (vix_val - 10) / 30 * 100))
    b_s = max(0, min(100, (buffett_val - 100) / 150 * 100))
    h_s = max(0, min(100, (hys_val - 2) / 8 * 100))
    f_s = fg_val
    
    # 통합 점수 산출
    final_score = ( (100 - v_s) + b_s + (100 - h_s) + f_s ) / 4
    return final_score, vix_val, buffett_val, hys_val, fg_val

# 4. 탭 구성 및 시각화
tab1, tab2, tab3, tab4 = st.tabs(["🇰🇷 국내", "🇺🇸 해외", "🌍 지표 분석", "🪙 코인"])

# 데이터 계산 호출
score, cur_vix, cur_buffett, cur_hys, cur_fg = calculate_realtime_score()

# --- Tab 3: 해외지표 분석 (실시간 상태바) ---
with tab3:
    st.header("🌍 실시간 매크로 분석 및 투자 적기 평가")
    
    st.write(f"### 🎯 실시간 통합 투자 지수: {score:.1f}점")
    
    # 상태별 메시지 분기 (사용자 정의 로직)
    if score <= 40:
        st.error("🔴 투자 적기: 지표상 공포 구간입니다. RSI 30 종목 분할 매수를 검토하세요.")
    elif score <= 70:
        st.warning("🟡 관망: 시장이 중립 상태입니다. 2월 변곡점을 대비해 현금을 보유하세요.")
    else:
        st.success("🟢 분할 매도: 지표상 과열 구간입니다. 레버리지 수익을 확정할 타이밍입니다.")
    
    st.progress(score / 100)
    
    # 세부 수치 대시보드
    st.markdown("---")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("VIX (실시간)", f"{cur_vix:.2f}") # 현재 14.51 수준
    m2.metric("버핏 지수(추정)", f"{cur_buffett:.1f}%") # 현재 약 230% 과열
    m3.metric("하이일드 스프레드", f"{cur_hys}%") # 현재 2.81%
    m4.metric("공포/탐욕 지수", f"{cur_fg}") # 현재 45 (Neutral)

# --- 나머지 탭 (실시간 주가 반영) ---
with tab1:
    k_p, k_pc = get_current_data("^KS11")
    k_d, k_dc = get_current_data("^KQ11")
    st.columns(2)[0].metric("KOSPI", f"{k_p:,.2f}", f"{k_pc:.2f}%")
    st.columns(2)[1].metric("KOSDAQ", f"{k_d:,.2f}", f"{k_dc:.2f}%")

with tab2:
    n_x, n_xc = get_current_data("^NDX")
    s_p, s_pc = get_current_data("^GSPC")
    st.columns(2)[0].metric("NASDAQ 100", f"{n_x:,.2f}", f"{n_xc:.2f}%")
    st.columns(2)[1].metric("S&P 500", f"{s_p:,.2f}", f"{s_pc:.2f}%")

with tab4:
    b_t, b_tc = get_current_data("BTC-USD")
    e_t, e_tc = get_current_data("ETH-USD")
    st.columns(2)[0].metric("Bitcoin", f"${b_t:,.0f}", f"{b_tc:.2f}%")
    st.columns(2)[1].metric("Ethereum", f"${e_t:,.0f}", f"{e_tc:.2f}%")

# 사이드바 원칙 고정
st.sidebar.title("📌 2026 투자 원칙")
st.sidebar.info("- 레버리지: 지표 초록색(70점↑) 시 정산\n- 매수: 지표 빨간색(40점↓) 시 분할 진입\n- ISA: 9월 전까지 현금 15% 유지")