import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_datareader.data as web
import plotly.graph_objects as go
import requests
from datetime import datetime, timedelta

# -----------------------------------------------------------------------------
# 1. 페이지 및 스타일 설정
# -----------------------------------------------------------------------------
st.set_page_config(layout="wide", page_title="투자 지표 대시보드")
st.title("📊 통합 투자 인사이트 대시보드")
st.caption("5대 지표 실시간 추적 및 매매 기준 가이드")

# -----------------------------------------------------------------------------
# 2. 데이터 정의 (매매 기준표)
# -----------------------------------------------------------------------------
guide_data = {
    "VIX": {
        "매수 (적극/분할)": "30 이상 (공포 피크)",
        "대기 (관망)": "20 ~ 30 (불안정)",
        "매도 (현금확보)": "15 이하 (낙관/과열)"
    },
    "FearGreed": {
        "매수 (적극/분할)": "20 미만 (Extreme Fear)",
        "대기 (관망)": "40 ~ 60 (Neutral)",
        "매도 (현금확보)": "80 이상 (Extreme Greed)"
    },
    "HighYield": {
        "매수 (적극/분할)": "6.0%p 이상 (위기 후 반등)",
        "대기 (관망)": "4.0 ~ 5.5%p (신용 주의)",
        "매도 (현금확보)": "3.5%p 이하 (지나친 안도)"
    },
    "PMI": {
        "매수 (적극/분할)": "45 미만 (침체 바닥 신호)",
        "대기 (관망)": "50 내외 (확장/수축 경계)",
        "매도 (현금확보)": "60 이상 (경기 정점)"
    },
    "Buffett": {
        "매수 (적극/분할)": "80% ~ 100% (저평가/적정)",
        "대기 (관망)": "120% ~ 150% (다소 고평가)",
        "매도 (현금확보)": "200% 이상 (역사적 거품)"
    }
}

# -----------------------------------------------------------------------------
# 3. 데이터 수집 함수
# -----------------------------------------------------------------------------

@st.cache_data(ttl=3600) # 1시간마다 갱신
def get_realtime_fg():
    """CNN 공포와 탐욕 지수 실시간 수집 (요청하신 함수 적용)"""
    try:
        # 헤더를 실제 브라우저처럼 위장
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
            'Referer': 'https://edition.cnn.com/'
        }
        url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata/"
        r = requests.get(url, headers=headers, timeout=5)
        r.raise_for_status()
        
        # 데이터 파싱
        data = r.json()
        score = float(data['fear_and_greed']['score'])
        rating = data['fear_and_greed']['rating']
        timestamp = data['fear_and_greed']['timestamp']
        return score, rating, timestamp
    except Exception as e:
        # 에러 발생 시 (차단 등) None 반환하여 UI에서 처리
        return None, None, None

@st.cache_data
def get_stock_data(ticker, period="5y"):
    """yfinance 데이터 가져오기 (이평선 포함)"""
    df = yf.Ticker(ticker).history(period=period)
    if df.empty: return None
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA60'] = df['Close'].rolling(window=60).mean()
    return df

@st.cache_data
def get_fred_data(series_id):
    """FRED(미국 연준) 데이터 가져오기"""
    try:
        start = datetime.now() - timedelta(days=365*5)
        end = datetime.now()
        df = web.DataReader(series_id, 'fred', start, end)
        return df
    except Exception as e:
        return None

# -----------------------------------------------------------------------------
# 4. 차트 생성 함수
# -----------------------------------------------------------------------------

def create_chart(df, title, is_fred=False):
    """일반 시계열 차트 (라인 + 이평선)"""
    if df is None:
        st.error(f"{title} 데이터를 불러올 수 없습니다.")
        return

    if is_fred:
        target_col = df.columns[0]
        current_val = df[target_col].iloc[-1]
    else:
        target_col = 'Close'
        current_val = df['Close'].iloc[-1]

    end_date = df.index[-1]
    start_date = end_date - timedelta(days=365)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df[target_col], mode='lines', name=title, line=dict(width=2)))
    
    if not is_fred and 'MA20' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], mode='lines', name='20일선', line=dict(color='green', width=1, dash='dot')))
        fig.add_trace(go.Scatter(x=df.index, y=df['MA60'], mode='lines', name='60일선', line=dict(color='orange', width=1, dash='dot')))

    fig.update_layout(
        title=f"{title} (현재: {current_val:.2f})",
        height=350,
        margin=dict(l=10, r=10, t=40, b=10),
        hovermode="x unified",
        xaxis=dict(range=[start_date, end_date], rangeslider=dict(visible=False))
    )
    st.plotly_chart(fig, use_container_width=True)

def create_gauge_chart(score, title):
    """공포와 탐욕 지수 전용 게이지 차트"""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': title},
        gauge = {
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "darkblue"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 25], 'color': '#ff4d4d'},  # Extreme Fear (Red)
                {'range': [25, 45], 'color': '#ff9f43'}, # Fear (Orange)
                {'range': [45, 55], 'color': '#feca57'}, # Neutral (Yellow)
                {'range': [55, 75], 'color': '#c8d6e5'}, # Greed (Light Blue)
                {'range': [75, 100], 'color': '#1dd1a1'} # Extreme Greed (Green)
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': score
            }
        }
    ))
    fig.update_layout(height=300, margin=dict(l=20, r=20, t=30, b=20))
    st.plotly_chart(fig, use_container_width=True)

def show_guide(key_name):
    """매매 기준표 표시"""
    data = guide_data[key_name]
    with st.expander(f"📌 {key_name} 매매 기준 가이드 보기", expanded=False):
        st.table(pd.DataFrame([data]))

# -----------------------------------------------------------------------------
# 5. 메인 화면 구성
# -----------------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(["🌎 거시경제(5대지표)", "🇰🇷 국내지수", "🪙 가상자산", "🏦 금리 & 국채"])

# [Tab 1] 거시경제
with tab1:
    st.info("💡 모바일 가로 모드로 보시면 차트가 더 잘 보입니다.")
    
    # 1. VIX
    st.subheader("1. VIX (공포지수)")
    df_vix = get_stock_data("^VIX")
    create_chart(df_vix, "VIX Index")
    show_guide("VIX")
    st.markdown("---")

    # 2. 공포와 탐욕 지수 (실시간 함수 적용)
    st.subheader("2. 공포와 탐욕 지수 (Fear & Greed)")
    
    fg_score, fg_rating, fg_time = get_realtime_fg()
    
    if fg_score is not None:
        # 데이터 수집 성공 시 게이지 차트 표시
        st.caption(f"Update: {fg_time} / 상태: {fg_rating}")
        create_gauge_chart(fg_score, "현재 점수")
    else:
        # 데이터 수집 실패 시 (CNN 차단 등)
        st.warning("⚠️ 실시간 데이터 수집 실패 (CNN 보안 차단). 아래 링크를 확인하세요.")
        st.metric(label="대체 값 (중립)", value="50")
        st.markdown("[👉 CNN 공식 홈페이지 바로가기](https://edition.cnn.com/markets/fear-and-greed)")
        
    show_guide("FearGreed")
    st.markdown("---")

    # 3. 하이일드 스프레드
    st.subheader("3. 하이일드 스프레드")
    df_high_yield = get_fred_data("BAMLH0A0HYM2")
    if df_high_yield is not None:
        create_chart(df_high_yield, "US High Yield Option-Adjusted Spread", is_fred=True)
    show_guide("HighYield")
    st.markdown("---")

    # 4. PMI
    st.subheader("4. PMI (ISM 제조업 지수)")
    st.caption("※ 실시간 추세 확인용 (미국 산업생산지수)")
    df_pmi = get_fred_data("INDPRO")
    if df_pmi is not None:
        create_chart(df_pmi, "US Industrial Production", is_fred=True)
    show_guide("PMI")
    st.markdown("---")

    # 5. 버핏 지수
    st.subheader("5. 버핏 지수 (시장 과열도)")
    df_mkt = get_fred_data("WILL5000PR")
    df_gdp = get_fred_data("GDP")
    
    if df_mkt is not None and df_gdp is not None:
        df_gdp = df_gdp.resample('D').ffill()
        common_index = df_mkt.index.intersection(df_gdp.index)
        df_buffett = (df_mkt.loc[common_index]['WILL5000PR'] / df_gdp.loc[common_index]['GDP']) * 100
        df_buffett = df_buffett.to_frame(name='Buffett Indicator')
        create_chart(df_buffett, "Buffett Indicator (%)", is_fred=True)
    show_guide("Buffett")

# [Tab 2] 국내 지수
with tab2:
    st.subheader("국내 주요 지수")
    col1, col2 = st.columns(2)
    with col1: create_chart(get_stock_data("^KS11"), "KOSPI")
    with col2: create_chart(get_stock_data("^KQ11"), "KOSDAQ")

# [Tab 3] 가상자산
with tab3:
    st.subheader("주요 코인 시세")
    create_chart(get_stock_data("BTC-USD"), "Bitcoin (BTC)")
    create_chart(get_stock_data("ETH-USD"), "Ethereum (ETH)")

# [Tab 4] 금리 & 국채
with tab4:
    st.subheader("미국 국채 금리")
    col1, col2 = st.columns(2)
    with col1: create_chart(get_stock_data("^TNX"), "10년물 국채 금리")
    with col2: create_chart(get_stock_data("^IRX"), "13주(단기) 국채 금리")
    st.markdown("---")
    st.subheader("원/달러 환율")
    create_chart(get_stock_data("KRW=X"), "USD/KRW")