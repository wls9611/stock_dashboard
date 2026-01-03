import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import yfinance as yf  # [필수] 야후 파이낸스 라이브러리
import requests        # [필수] 데이터 요청 라이브러리

# --- 1. 페이지 설정 ---
st.set_page_config(
    page_title="Investment Dashboard Pro",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 2. 실시간 데이터 가져오기 (수정됨: 오류 방지 로직 추가)
# ==========================================
@st.cache_data(ttl=600)  # 10분마다 갱신
def get_realtime_indicators():
    # 기본값 설정 (API 실패 시 사용될 값)
    data = {
        'vix': 15.0,
        'fg': 50,
        'buffett': 185.0,
        'nasdaq_rsi': 50.0,
        'nasdaq_price': 15000
    }
    
    # 변수 미리 초기화 (UnboundLocalError 방지)
    hist_ndx = pd.DataFrame()

    # 1. Yahoo Finance 데이터 (VIX, 나스닥)
    try:
        # ^VIX: 공포지수, ^NDX: 나스닥100
        tickers = yf.tickers("^VIX ^NDX")
        
        # 데이터 가져오기 (오류 발생 가능성 있는 구간)
        hist_vix = tickers.tickers['^VIX'].history(period="1d")
        hist_ndx = tickers.tickers['^NDX'].history(period="3mo")

        # VIX 현재가 업데이트
        if not hist_vix.empty:
            data['vix'] = round(hist_vix['Close'].iloc[-1], 2)

        # 나스닥 RSI 계산
        if not hist_ndx.empty:
            data['nasdaq_price'] = hist_ndx['Close'].iloc[-1]
            delta = hist_ndx['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            data['nasdaq_rsi'] = round(rsi.iloc[-1], 1)
            
    except Exception as e:
        print(f"Yahoo Finance Error: {e}") 
        # 에러가 나도 기본값(data)을 반환하므로 앱이 멈추지 않음

    # 2. 공포 & 탐욕 지수 (CNN)
    try:
        url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            fg_data = r.json()
            score = fg_data['fear_and_greed']['score']
            data['fg'] = int(score)
    except Exception:
        # CNN 실패 시 VIX 기반 추정치 사용
        data['fg'] = max(0, min(100, int(110 - data['vix'] * 2.5)))

    # 3. 버핏 지수 (나스닥 변동폭 반영 근사치)
    base_buffett = 185.0
    change_rate = 0
    if not hist_ndx.empty:
        change_rate = (hist_ndx['Close'].iloc[-1] - hist_ndx['Close'].iloc[-2]) / hist_ndx['Close'].iloc[-2]
    data['buffett'] = round(base_buffett * (1 + change_rate), 1)

    return data

# ==========================================
# 3. 차트용 과거 데이터 생성 (Mock Data + Trend)
# ==========================================
np.random.seed(42)
days_5y = 365 * 5
dates = pd.date_range(end=datetime.today(), periods=days_5y, freq='D')

def generate_market_data(start_price, volatility, trend=0.02):
    changes = np.random.normal(trend, volatility, days_5y)
    price = start_price + np.cumsum(changes)
    df = pd.DataFrame({'date': dates, 'price': price})
    
    for window in [20, 60, 120, 200]:
        df[f'ma{window}'] = df['price'].rolling(window=window).mean()
    
    delta = df['price'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    return df

# 데이터셋 생성
df_nasdaq = generate_market_data(15000, 150, 0.05)
df_snp = generate_market_data(4500, 30, 0.03)
df_dow = generate_market_data(35000, 200, 0.02)
df_kospi = generate_market_data(2500, 15, 0.01)
df_kosdaq = generate_market_data(850, 8, 0.015)
df_btc = generate_market_data(40000, 800, 0.1)
df_eth = generate_market_data(2500, 60, 0.1)
df_fx = generate_market_data(1200, 5, 0.005)

# --- 실시간 지표 로드 ---
real_data = get_realtime_indicators()
current_vix = real_data['vix']
current_fg = real_data['fg']
current_buffett = real_data['buffett']
last_rsi_nasdaq = real_data['nasdaq_rsi']

# ==========================================
# 4. 헬퍼 함수: 점수 로직 & 차트
# ==========================================
def calculate_score(rsi, vix, fg):
    score_rsi = max(0, (70 - rsi)) * 2.5
    score_vix = min(100, vix * 2)
    score_fg = (100 - fg)
    total = (score_rsi + score_vix + score_fg) / 3
    return min(100, max(0, total))

invest_score = calculate_score(last_rsi_nasdaq, current_vix, current_fg)

def get_action(score):
    if score >= 70: return "🔥 적극 매수 (Strong Buy)", "bg-red-50 text-red-700 border-red-200"
    elif score >= 40: return "✋ 관망 / 대기 (Hold)", "bg-yellow-50 text-yellow-700 border-yellow-200"
    else: return "⚠️ 리스크 관리 (Sell/Wait)", "bg-blue-50 text-blue-700 border-blue-200"

action_text, action_style = get_action(invest_score)

def create_main_chart(df, title, color_main='black'):
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
    fig.add_trace(go.Scatter(x=df['date'], y=df['price'], name=title, line=dict(color=color_main, width=2)), row=1, col=1)
    
    ma_colors = {'ma20': '#facc15', 'ma60': '#16a34a', 'ma120': '#9333ea', 'ma200': '#dc2626'}
    for ma, color in ma_colors.items():
        label = ma.replace('ma', '') + '일선'
        fig.add_trace(go.Scatter(x=df['date'], y=df[ma], name=label, line=dict(color=color, width=1, dash='dot')), row=1, col=1)
        
    fig.add_trace(go.Scatter(x=df['date'], y=df['rsi'], name="RSI", line=dict(color='#3b82f6', width=1.5)), row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    
    one_year_ago = datetime.today() - timedelta(days=365)
    fig.update_layout(
        title=dict(text=f"<b>{title}</b>", x=0.01),
        height=500, hovermode="x unified",
        xaxis_range=[one_year_ago, datetime.today()],
        legend=dict(orientation="h", y=1.02),
        margin=dict(l=10, r=10, t=40, b=10)
    )
    return fig

def create_gauge(title, val, min_v, max_v, suffix="", threshold=None):
    fig = go.Figure(go.Indicator(
        mode="number+gauge", value=val,
        title={'text': f"<b>{title}</b>", 'font':{'size':14}},
        number={'suffix': suffix},
        gauge={
            'shape': "bullet", 'axis': {'range': [min_v, max_v]},
            'bar': {'color': "#4f46e5"},
            'threshold': {'line': {'color': "red", 'width': 2}, 'thickness': 0.75, 'value': threshold} if threshold else None
        }
    ))
    fig.update_layout(height=110, margin={'t':30, 'b':10, 'l':20, 'r':20})
    return fig

# ==========================================
# 5. UI 구성
# ==========================================
st.title("📊 Investment Dashboard")

with st.container():
    st.markdown("### 🎯 Market Timing Score")
    c1, c2 = st.columns([3, 1])
    with c1:
        st.progress(int(invest_score))
        st.caption("Score Logic: RSI + VIX + Fear&Greed Combined")
    with c2:
        st.metric("종합 점수", f"{int(invest_score)}점")
    
    st.markdown(f"""
    <div class="{action_style}" style="padding: 15px; border-radius: 8px; border-width: 1px; margin-bottom: 20px;">
        <h4 style="margin:0;">📢 Action: {action_text}</h4>
        <p style="margin:5px 0 0 0; font-size:0.9em; opacity:0.8;">📌 원칙: 주요 지수 RSI <b>30 미만</b> 도달 시 분할 매수 시작</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

tabs = st.tabs(["해외지표", "해외지수", "국내지수", "가상자산", "환율"])

with tabs[0]:
    st.subheader("🌐 주요 시장 지표 (실시간 반영)")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.plotly_chart(create_gauge("VIX (변동성지수)", current_vix, 10, 60, "", 20), use_container_width=True)
    with col2:
        st.plotly_chart(create_gauge("공포 & 탐욕 지수", current_fg, 0, 100, "", 50), use_container_width=True)
    with col3:
        st.plotly_chart(create_gauge("버핏 지수 (GDP대비)", current_buffett, 50, 200, "%", 100), use_container_width=True)

with tabs[1]:
    st.subheader("🇺🇸 미국 3대 지수")
    st.plotly_chart(create_main_chart(df_nasdaq, "Nasdaq 100 (NDX)", "#000000"), use_container_width=True)
    st.plotly_chart(create_main_chart(df_snp, "S&P 500 (SPX)", "#4b5563"), use_container_width=True)
    st.plotly_chart(create_main_chart(df_dow, "Dow Jones (DJI)", "#1f2937"), use_container_width=True)

with tabs[2]:
    st.subheader("🇰🇷 한국 주요 지수")
    st.plotly_chart(create_main_chart(df_kospi, "KOSPI", "#0f172a"), use_container_width=True)
    st.plotly_chart(create_main_chart(df_kosdaq, "KOSDAQ", "#334155"), use_container_width=True)

with tabs[3]:
    st.subheader("🪙 Crypto Assets")
    st.plotly_chart(create_main_chart(df_btc, "Bitcoin (BTC)", "#f59e0b"), use_container_width=True)
    st.plotly_chart(create_main_chart(df_eth, "Ethereum (ETH)", "#6366f1"), use_container_width=True)

with tabs[4]:
    st.subheader("💱 Exchange Rate")
    current_rate = df_fx['price'].iloc[-1]
    st.metric("USD/KRW", f"{current_rate:.1f} 원", delta="0.3%")
    st.plotly_chart(create_main_chart(df_fx, "원/달러 환율", "#dc2626"), use_container_width=True)