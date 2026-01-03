import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests
from datetime import datetime, timedelta

# -----------------------------------------------------------------------------
# 1. 페이지 및 스타일 설정
# -----------------------------------------------------------------------------
st.set_page_config(layout="wide", page_title="투자 지표 대시보드")
st.title("📊 통합 투자 인사이트 대시보드")
st.caption("주요 지표 실시간 추적 및 매매 기준 가이드")

# -----------------------------------------------------------------------------
# 2. 데이터 정의 (매매 기준표) - 하이일드, PMI 삭제됨
# -----------------------------------------------------------------------------
guide_data = {
    "VIX": {
        "desc": "공포지수 (VIX)",
        "매수": "30 이상 (공포)",
        "중립": "15 ~ 30",
        "매도": "15 이하 (탐욕)",
        "unit": ""
    },
    "FearGreed": {
        "desc": "공포와 탐욕 지수",
        "매수": "20 미만 (Extreme Fear)",
        "중립": "40 ~ 60",
        "매도": "80 이상 (Extreme Greed)",
        "unit": "점"
    },
    "Buffett": {
        "desc": "버핏 지수 (시총/GDP)",
        "매수": "80% ~ 100% (저평가)",
        "중립": "100% ~ 120%",
        "매도": "140% 이상 (고평가)", # 기준 단순화
        "unit": "%"
    }
}

# -----------------------------------------------------------------------------
# 3. 데이터 수집 함수
# -----------------------------------------------------------------------------

@st.cache_data(ttl=3600)
def get_realtime_fg():
    """CNN 공포와 탐욕 지수 실시간 수집"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
            'Referer': 'https://edition.cnn.com/'
        }
        url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata/"
        r = requests.get(url, headers=headers, timeout=5)
        r.raise_for_status()
        data = r.json()
        score = float(data['fear_and_greed']['score'])
        rating = data['fear_and_greed']['rating']
        timestamp = data['fear_and_greed']['timestamp']
        return score, rating, timestamp
    except Exception:
        return None, None, None

@st.cache_data
def get_stock_data(ticker, period="5y", include_ma=True):
    """yfinance 데이터 가져오기 (이평선 4개 포함: 20, 60, 120, 200)"""
    try:
        df = yf.Ticker(ticker).history(period=period)
        if df.empty: return None
        
        if include_ma:
            df['MA20'] = df['Close'].rolling(window=20).mean()
            df['MA60'] = df['Close'].rolling(window=60).mean()
            df['MA120'] = df['Close'].rolling(window=120).mean()
            df['MA200'] = df['Close'].rolling(window=200).mean()
        return df
    except Exception:
        return None

@st.cache_data
def get_fred_data(series_id):
    """FRED 데이터 가져오기"""
    try:
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
        df = pd.read_csv(url, index_col='DATE', parse_dates=True)
        start_date = datetime.now() - timedelta(days=365*5)
        df = df[df.index >= start_date]
        return df
    except Exception as e:
        return None

# -----------------------------------------------------------------------------
# 4. 차트 및 UI 생성 함수
# -----------------------------------------------------------------------------

def create_chart(df, title, is_fred=False, show_ma=True):
    """차트 그리기 (이평선 20, 60, 120, 200 표시)"""
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
    start_date = df.index[0]

    fig = go.Figure()
    # 메인 차트
    fig.add_trace(go.Scatter(x=df.index, y=df[target_col], mode='lines', name=title, line=dict(width=2, color='black')))
    
    # 이평선 표시 (show_ma=True 일 때만)
    if not is_fred and show_ma:
        if 'MA20' in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], mode='lines', name='20일선', line=dict(color='green', width=1)))
        if 'MA60' in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df['MA60'], mode='lines', name='60일선', line=dict(color='orange', width=1)))
        if 'MA120' in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df['MA120'], mode='lines', name='120일선', line=dict(color='red', width=1)))
        if 'MA200' in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df['MA200'], mode='lines', name='200일선', line=dict(color='purple', width=1)))

    fig.update_layout(
        title=f"{title} (현재: {current_val:,.2f})",
        height=350,
        margin=dict(l=10, r=10, t=40, b=10),
        hovermode="x unified",
        xaxis=dict(range=[start_date, end_date], rangeslider=dict(visible=False)),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)

def render_indicator_text(key, current_value):
    """지표를 텍스트로만 표시 (막대 그래프 제거)"""
    meta = guide_data[key]
    
    # UI 렌더링
    st.markdown(f"### {meta['desc']}")
    
    col_val, col_guide = st.columns([1, 2])
    
    with col_val:
        st.metric(label="현재 값", value=f"{current_value:.2f} {meta['unit']}")
    
    with col_guide:
        st.markdown("**📋 매매 기준 가이드**")
        st.markdown(f"""
        - 🔵 **매수:** {meta['매수']}
        - ⚪ **중립:** {meta['중립']}
        - 🔴 **매도:** {meta['매도']}
        """)
    
    st.markdown("---")

# -----------------------------------------------------------------------------
# 5. 메인 화면 구성
# -----------------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs(["해외지표", "🇺🇸 해외지수", "🇰🇷 국내지수", "💎 가상자산", "금리 & 환율"])

# [Tab 1] 해외지표 (VIX, FearGreed, Buffett 만 남김, 텍스트 표시)
with tab1:
    st.subheader("🌐 글로벌 시장 핵심 지표")
    st.info("현재 수치와 매매 기준을 확인하세요.")
    st.markdown("---")

    # 1. VIX
    df_vix = get_stock_data("^VIX", period="1mo", include_ma=False)
    if df_vix is not None:
        val = df_vix['Close'].iloc[-1]
        render_indicator_text("VIX", val)

    # 2. Fear & Greed
    fg_score, _, _ = get_realtime_fg()
    if fg_score is not None:
        render_indicator_text("FearGreed", fg_score)
    else:
        st.warning("Fear & Greed 지수 로딩 실패 (CNN 연결 확인 필요)")

    # 3. 버핏 지수
    df_mkt = get_fred_data("WILL5000PR")
    df_gdp = get_fred_data("GDP")
    if df_mkt is not None and df_gdp is not None:
        df_gdp = df_gdp.resample('D').ffill()
        common_index = df_mkt.index.intersection(df_gdp.index)
        if not common_index.empty:
            current_buffett = (df_mkt.loc[common_index]['WILL5000PR'][-1] / df_gdp.loc[common_index]['GDP'][-1]) * 100
            render_indicator_text("Buffett", current_buffett)

# [Tab 2] 해외 지수 (이평선 4개 적용)
with tab2:
    st.subheader("🇺🇸 미국 3대 지수")
    col1, col2, col3 = st.columns(3)
    with col1: create_chart(get_stock_data("^GSPC"), "S&P 500")
    with col2: create_chart(get_stock_data("^IXIC"), "NASDAQ")
    with col3: create_chart(get_stock_data("^DJI"), "Dow Jones")

# [Tab 3] 국내 지수 (이평선 4개 적용)
with tab3:
    st.subheader("🇰🇷 국내 주요 지수")
    col1, col2 = st.columns(2)
    with col1: create_chart(get_stock_data("^KS11"), "KOSPI")
    with col2: create_chart(get_stock_data("^KQ11"), "KOSDAQ")

# [Tab 4] 가상자산 (이평선 4개 적용)
with tab4:
    st.subheader("💎 주요 코인 시세")
    col1, col2 = st.columns(2)
    with col1: create_chart(get_stock_data("BTC-USD"), "Bitcoin (BTC)")
    with col2: create_chart(get_stock_data("ETH-USD"), "Ethereum (ETH)")

# [Tab 5] 금리 & 환율 (이평선 없음 유지)
with tab5:
    st.subheader("🏦 기준 금리 현황")
    
    # 금리 데이터 수집
    df_fed = get_fred_data("FEDFUNDS") # 미국 연방기금금리
    
    def format_date(date_obj):
        return date_obj.strftime("%Y-%m-%d")

    col_us, col_kr = st.columns(2)
    
    with col_us:
        if df_fed is not None:
            us_rate = df_fed.iloc[-1, 0]
            us_date = format_date(df_fed.index[-1])
            st.metric(label="🇺🇸 미국 기준금리", value=f"{us_rate}%", delta=f"발표: {us_date}")
        else:
            st.metric(label="🇺🇸 미국 기준금리", value="로딩 중")

    with col_kr:
        # 한국 금리 예시값
        kr_rate = 3.00 
        kr_date = "최근 금통위"
        st.metric(label="🇰🇷 한국 기준금리", value=f"{kr_rate}%", delta=kr_date, delta_color="off")
        st.caption("※ 한국 금리는 수동 설정 값입니다.")

    st.markdown("---")
    
    st.subheader("📈 주요 시장 지표 (5년 추이)")
    
    # 10년물 국채 금리 & 환율 (여기는 선이 많으면 복잡하므로 이평선 제외 설정 유지)
    col1, col2 = st.columns(2)
    with col1:
        st.write("##### 🇺🇸 미국 10년물 국채 금리")
        df_tnx = get_stock_data("^TNX", period="5y", include_ma=False)
        create_chart(df_tnx, "US 10Y Treasury", show_ma=False)

    with col2:
        st.write("##### 🇰🇷 원/달러 환율 (USD/KRW)")
        df_krw = get_stock_data("KRW=X", period="5y", include_ma=False)
        create_chart(df_krw, "USD/KRW Exchange Rate", show_ma=False)