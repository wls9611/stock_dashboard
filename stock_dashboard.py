import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 1. 페이지 설정 및 오늘 날짜
st.set_page_config(page_title="2026 통합 투자 대시보드", layout="wide")
today = datetime.now().strftime("%Y년 %m월 %d일")

# 헤더 구성
st.title("📊 2026 전략 투자 인사이트")
st.subheader(f"📅 Today: {today}")
st.markdown("---")

# 2. 데이터 수집 함수 (주말 데이터 부재 방지)
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

# 3. 투자 적기 점수 계산 (4가지 핵심 지표 조합)
def get_investment_score(vix, fg, hys, buffett):
    # 각 지표 정규화 (사용자님의 30-50-70 로직 기반)
    # VIX: 높을수록 공포(매수), 낮을수록 안정(매도)
    v_s = max(0, min(100, (vix - 10) / 30 * 100))
    # 버핏지수: 낮을수록 저평가(매수), 높을수록 고평가(매도)
    b_s = max(0, min(100, (buffett - 100) / 150 * 100))
    # 하이일드: 높을수록 위험(매수), 낮을수록 안정(매도)
    h_s = max(0, min(100, (hys - 2) / 8 * 100))
    # 공탐지수: 낮을수록 공포(매수), 높을수록 탐욕(매도)
    f_s = fg
    
    # 종합 점수 (높을수록 매도/탐욕 구간)
    score = ( (100 - v_s) + b_s + (100 - h_s) + f_s