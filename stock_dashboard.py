import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# --- 페이지 기본 설정 (모바일 최적화 포함) ---
st.set_page_config(
    page_title="Investment Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 1. 데이터 생성 (Mock Data Generation)
# ==========================================
np.random.seed(42)

# (1) 금리 & 환율 데이터 (최근 5년치 - 요청 8번)
# 5년 = 365 * 5 = 1825일
dates_5y = pd.date_range(end=datetime.today(), periods=1825, freq='D')
df_rates = pd.DataFrame({
    'date': dates_5y,
    # 1.5 ~ 5.5 사이 변동
    'us_10y': np.linspace(1.5, 5.0, len(dates_5y)) + np.random.normal(0, 0.15, len(dates_5y)), 
    # 1100 ~ 1400 사이 변동
    'usdkrw': np.linspace(1100, 1350, len(dates_5y)) + np.random.normal(0, 15, len(dates_5y))
})

# (2) 주식 데이터 (해외지수용)
dates_stock = pd.date_range(end=datetime.today(), periods=300, freq='D')
price_data = 150 + np.cumsum(np.random.randn(300))
df_stock = pd.DataFrame({'date': dates_stock, 'price': price_data})

# 이동평균선 계산 (요청 10번: 120일, 200일선 추가)
df_stock['ma20'] = df_stock['price'].rolling(window=20).mean()
df_stock['ma60'] = df_stock['price'].rolling(window=60).mean()
df_stock['ma120'] = df_stock['price'].rolling(window=120).mean()
df_stock['ma200'] = df_stock['price'].rolling(window=200).mean()

# ==========================================
# 2. 헬퍼 함수: 가로 막대 바 (Bullet Chart)
# ==========================================
# 요청 2, 3번: 그래프 삭제 후 숫자와 매매기준 위치만 표시 (Bullet Chart 활용)
def create_bullet_chart(title, current_val, min_val, max_val, unit, threshold=None):
    fig = go.Figure(go.Indicator(
        mode = "number+gauge",
        value = current_val,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': f"<b>{title}</b>", 'font': {'size': 16}},
        number = {'suffix': unit, 'font': {'size': 20}},
        gauge = {
            'shape': "bullet",
            'axis': {'range': [min_val, max_val]},
            'bar': {'color': "#2563eb"},  # 파란색 바
            'bgcolor': "white",
            'borderwidth': 0,
            # 매매 기준선 (옵션)
            'threshold': {
                'line': {'color': "red", 'width': 2},
                'thickness': 0.75,
                'value': threshold if threshold else (min_val + max_val) / 2
            },
            # 배경 구간 색상 (심리적 안정/위험 구간 예시)
            'steps': [
                {'range': [min_val, (min_val+max_val)/2], 'color': "#f3f4f6"},
                {'range': [(min_val+max_val)/2, max_val], 'color': "#e5e7eb"}
            ],
        }
    ))
    # 모바일에서 너무 높지 않게 설정
    fig.update_layout(height=100, margin={'t':20, 'b':10, 'l':25, 'r':25})
    return fig

# ==========================================
# 3. 메인 대시보드 UI
# ==========================================

# (요청 9번: 상단바 현재투자지표 복구)
st.title("📊 My Investment Dashboard")
st.markdown(f"Last Updated: **{datetime.today().strftime('%Y-%m-%d')}**")

# 상단 지표 (Metric)
m_col1, m_col2, m_col3 = st.columns(3)
with m_col1:
    st.metric(label="공포/탐욕 지수", value="65", delta="Greed", delta_color="normal")
with m_col2:
    st.metric(label="VIX (변동성)", value="14.5", delta="-1.2%", delta_color="inverse")
with m_col3:
    st.metric(label="달러 인덱스", value="102.4", delta="0.1%")

st.divider()

# 탭 구성 (요청 1번: 명칭 수정)
tab1, tab2, tab3 = st.tabs(["해외지표", "금리&환율", "해외지수"])

# --- TAB 1: 해외지표 ---
# (요청 1번: 거시경제 -> 해외지표)
# (요청 2, 3번: 그래프 삭제, 가로 막대바 표시)
with tab1:
    st.subheader("🌐 해외지표 (매매기준 위치)")
    st.caption("각 지표의 현재 수치가 역사적 범위(Low-High) 내 어디에 있는지 보여줍니다.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # ISM 제조업 지수 (기준선 50)
        st.plotly_chart(create_bullet_chart("ISM 제조업 지수", 47.5, 40, 65, "pt", threshold=50), use_container_width=True)
        # CPI (목표 2%)
        st.plotly_chart(create_bullet_chart("CPI (소비자물가)", 3.1, 0, 9.0, "%", threshold=2.0), use_container_width=True)
        
    with col2:
        # 실업률 (자연실업률 4% 부근)
        st.plotly_chart(create_bullet_chart("미국 실업률", 3.7, 2.5, 10.0, "%", threshold=4.0), use_container_width=True)
        # 하이일드 스프레드 (위험 기준 5% 부근)
        st.plotly_chart(create_bullet_chart("하이일드 스프레드", 3.5, 2.0, 10.0, "%", threshold=5.0), use_container_width=True)

# --- TAB 2: 금리 & 환율 ---
# (요청 6번: 명칭 변경)
with tab2:
    st.subheader("💵 금리 & 환율")
    
    # (요청 7번: 현재 금리 숫자만 표기 + 발표일자)
    kpi_col1, kpi_col2 = st.columns(2)
    with kpi_col1:
        st.info(f"🇺🇸 미국 기준금리 (Fed)\n\n### **5.50%**\n(최근 발표: 2023.12.14)")
    with kpi_col2:
        st.success(f"🇰🇷 한국 기준금리 (BOK)\n\n### **3.50%**\n(최근 발표: 2023.11.30)")
    
    # (요청 8번: 5년치 데이터 사용)
    # (요청 7번: 20일/60일 이평선 삭제 -> 원본 데이터만 표시)
    st.markdown("#### 📉 미국 10년물 국채 & 원/달러 환율 (최근 5년)")
    
    fig_rates = make_subplots(specs=[[{"secondary_y": True}]])
    
    # 왼쪽 축: 미국 10년물 국채
    fig_rates.add_trace(
        go.Scatter(
            x=df_rates['date'], y=df_rates['us_10y'], 
            name="미국 10년물 국채", 
            line=dict(color='#2563eb', width=2)
        ),
        secondary_y=False
    )
    
    # 오른쪽 축: 원/달러 환율
    fig_rates.add_trace(
        go.Scatter(
            x=df_rates['date'], y=df_rates['usdkrw'], 
            name="원/달러 환율", 
            line=dict(color='#dc2626', width=2, dash='dot')
        ),
        secondary_y=True
    )
    
    # 차트 레이아웃 설정
    fig_rates.update_layout(
        hovermode="x unified",
        legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center"),
        margin=dict(l=20, r=20, t=40, b=20)
    )
    fig_rates.update_yaxes(title_text="국채 금리 (%)", secondary_y=False, showgrid=True)
    fig_rates.update_yaxes(title_text="환율 (KRW)", secondary_y=True, showgrid=False)
    
    st.plotly_chart(fig_rates, use_container_width=True)

# --- TAB 3: 해외지수 ---
# (요청 4번: 해외지수 탭 복구)
with tab3:
    st.subheader("📈 해외지수 추세 (S&P 500 Proxy)")
    
    # (요청 10번: 120일선, 200일선 추가)
    fig_stock = go.Figure()
    
    # 주가
    fig_stock.add_trace(go.Scatter(x=df_stock['date'], y=df_stock['price'], name="Price", line=dict(color='black', width=2)))
    
    # 이평선들
    fig_stock.add_trace(go.Scatter(x=df_stock['date'], y=df_stock['ma20'], name="20일선", line=dict(color='#facc15', width=1.5))) # 노랑
    fig_stock.add_trace(go.Scatter(x=df_stock['date'], y=df_stock['ma60'], name="60일선", line=dict(color='#16a34a', width=1.5))) # 초록
    fig_stock.add_trace(go.Scatter(x=df_stock['date'], y=df_stock['ma120'], name="120일선", line=dict(color='#9333ea', width=1.5))) # 보라 (추가됨)
    fig_stock.add_trace(go.Scatter(x=df_stock['date'], y=df_stock['ma200'], name="200일선", line=dict(color='#dc2626', width=1.5))) # 빨강 (추가됨)
    
    fig_stock.update_layout(
        hovermode="x unified",
        legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center"),
        xaxis_title="Date", 
        yaxis_title="Price",
        margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(fig_stock, use_container_width=True)

# --- 하단: 가상자산 섹션 ---
# (요청 5번: X 아이콘 문제 해결 -> 텍스트 심볼 또는 이모지 사용)
st.divider()
c_col1, c_col2 = st.columns([0.1, 0.9])

with c_col1:
    # 텍스트로 비트코인 심볼 표시 (아이콘 로딩 문제 원천 차단)
    st.markdown("<h2 style='text-align: center; margin: 0;'>₿</h2>", unsafe_allow_html=True)
with c_col2:
    st.subheader("Crypto Assets")
    st.write("Bitcoin: **$45,230** (▲ 2.5%)")