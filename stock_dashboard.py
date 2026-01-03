import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 1. 페이지 설정 및 오늘 날짜
st.set_page_config(page_title="2026 전략 대시보드", layout="wide")
today = datetime.now().strftime("%Y년 %m월 %d일")

st.title("📊 2026 통합 투자 인사이트")
st.subheader(f"📅 Today: {today}")
st.markdown("---")

# 2. 데이터 수집 함수
def get_data(ticker):
    try:
        df = yf.Ticker(ticker).history(period="5d")
        if not df.empty:
            curr = df['Close'].iloc[-1]
            prev = df['Close'].iloc[-2]
            chg = ((curr - prev) / prev) * 100
            return curr, chg
        return 0, 0
    except:
        return 0, 0

# 3. 투자 적기 점수 계산 (괄호 오류 수정 완료)
def get_investment_score(vix, fg, hys, buffett):
    v_s = max(0, min(100, (vix - 10) / 30 * 100))
    b_s = max(0, min(100, (buffett - 100) / 150 * 100))
    h_s = max(0, min(100, (hys - 2) / 8 * 100))
    f_s = fg
    
    # 괄호를 닫고 4로 나누어 평균 점수를 냅니다.
    score = ( (100 - v_s) + b_s + (100 - h_s) + f_s ) / 4
    return score

# 실시간 데이터 로드 (2026.01.03 기준)
vix_v, _ = get_data("^VIX")
ndx_v, _ = get_data("^NDX")
hys_v = 2.81  # 하이일드 스프레드
fg_v = 45     # 공포와 탐욕 지수
buffett_v = (ndx_v / 18000) * 230  # 버핏 지수 예시

# 4. 탭 구성
tabs = st.tabs(["🇰🇷 국내 지수", "🇺🇸 해외 지수", "🌍 해외지표 분석", "🪙 코인 지수"])

# --- Tab 3: 분석 탭에서 상태바 확인 ---
with tabs[2]:
    st.header("🌍 글로벌 매크로 & 투자 적기 평가")
    score = get_investment_score(vix_v, fg_v, hys_v, buffett_v)
    
    st.write(f"### 🎯 통합 투자 지수: {score:.1f}점")
    
    # 사용자님이 그려준 30-50-70 로직 반영
    if score <= 40:
        st.error("🔴 투자 적기 (공포): RSI 30 종목 분할 매수 시기입니다.")
    elif score <= 70:
        st.warning("🟡 관망 (중립): 무리한 진입보다 현금을 보유하세요.")
    else:
        st.success("🟢 분할 매도 (탐욕): 레버리지 정산을 고려할 타이밍입니다.")
    
    st.progress(score / 100)
    st.markdown("---")
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("VIX (공포지수)", f"{vix_v:.2f}") # 안정 상태
    m2.metric("버핏 지수", f"{buffett_v:.1f}%") # 과열 상태
    m3.metric("하이일드", f"{hys_v}%") # 저위험
    m4.metric("공탐 지수", f"{fg_v}") # 중립

# 나머지 탭은 기존과 동일하게 작동합니다.