import streamlit as st
import config

def set_page_style():
    """모바일 최적화 및 CSS 설정"""
    st.markdown("""
    <style>
        .block-container {padding-top: 1rem; padding-bottom: 3rem;}
        
        /* 시장 지표 카드 디자인 */
        .market-card {
            background-color: #f0f2f6;
            border-radius: 10px;
            padding: 10px 5px;
            text-align: center;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        @media (prefers-color-scheme: dark) {
            .market-card {
                background-color: #262730;
                color: white;
            }
        }

        /* 종목 카드 그리드 (모바일 2열 강제 적용) */
        .stock-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr); 
            gap: 10px;
            margin-top: 15px;
        }

        /* 개별 종목 카드 디자인 */
        .stock-card {
            border: 1px solid #e0e0e0;
            border-radius: 10px;
            padding: 12px;
            background-color: white;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        @media (prefers-color-scheme: dark) {
            .stock-card {
                background-color: #262730;
                border: 1px solid #444;
            }
        }
        
        /* 폰트 스타일 */
        .small-label { font-size: 0.75rem; color: gray; font-weight: bold; }
        .big-value { font-size: 1.0rem; font-weight: 900; margin: 3px 0; }
        .change-text { font-size: 0.8rem; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

def display_header(datetime_str, refresh_func):
    """헤더 표시 (제목 변경됨)"""
    c1, c2 = st.columns([3, 1])
    with c1:
        # [수정] 제목 변경: US 스나이퍼 Bot -> 해외주식 리포트
        st.title("🇺🇸 해외주식 리포트")
        st.caption(f"Update: {datetime_str}")
    with c2:
        if st.button("🔄 갱신"):
            refresh_func()

def display_logic_expander():
    """점수 산출 공식 설명"""
    with st.expander("ℹ️ 점수 산출 공식 (클릭)"):
        st.markdown(f"""
        **💯 총 100점 만점**
        - RSI < {config.RSI_OVERSOLD}: **40점**
        - MFI < {config.MFI_STRONG}: **30점**
        - Price < MA20: **30점**
        - (RSI > {config.RSI_OVERBOUGHT}: **-99점**)
        """)

def create_market_card_html(label, val, change, rsi=None, is_vix=False, is_fng=False):
    """HTML 카드 생성 헬퍼 함수"""
    
    # 1. 공탐지수 (FNG)
    if is_fng:
        return f"""
        <div class="market-card">
            <div class="small-label">{label}</div>
            <div class="big-value">{val}</div>
            <div class="change-text" style="color:gray;">투자심리</div>
        </div>
        """
    
    # 2. VIX 지수
    if is_vix:
        try:
            v_val = float(val)
            badge = "🔴 위험" if v_val > 25 else "🟢 안정"
        except:
            v_val = 0
            badge = "-"
            
        return f"""
        <div class="market-card">
            <div class="small-label">{label}</div>
            <div class="big-value">{v_val:.1f}</div>
            <div class="change-text">{badge}</div>
        </div>
        """

    # 3. 일반 지수 (나스닥, S&P, 다우)
    color = "#ff4b4b" if change > 0 else "#1c83e1"
    icon = "▲" if change > 0 else "▼"
    
    if rsi is None: rsi = 50
    rsi_c = "#ff4b4b" if rsi > 70 else "#1c83e1" if rsi < 30 else "gray"
    
    return f"""
    <div class="market-card">
        <div class="small-label">{label}</div>
        <div class="big-value">{val:,.0f}</div>
        <div class="change-text" style="color:{color};">
            {icon}{abs(change):.1f}%
        </div>
        <div style="font-size:0.7rem; margin-top:2px;">
            RSI <span style="color:{rsi_c}">{rsi:.0f}</span>
        </div>
    </div>
    """

def display_market_summary(data):
    """시장 지표 요약 (2줄 레이아웃)"""
    st.subheader("🌍 Market Index")
    
    if not data:
        st.warning("데이터 로딩 중...")
        return

    # 1열: 주요 지수 (3개)
    c1, c2, c3 = st.columns(3)
    
    # 나스닥
    with c1:
        d = data.get('ndx', {})
        if d:
            st.markdown(create_market_card_html("Nasdaq", d['price'], d['change'], d['rsi']), unsafe_allow_html=True)
        else:
            st.markdown(create_market_card_html("Nasdaq", 0, 0, 50), unsafe_allow_html=True)
            
    # S&P 500
    with c2:
        d = data.get('spx', {})
        if d:
            st.markdown(create_market_card_html("S&P 500", d['price'], d['change'], d['rsi']), unsafe_allow_html=True)
        else:
            st.markdown(create_market_card_html("S&P 500", 0, 0, 50), unsafe_allow_html=True)

    # 다우존스
    with c3:
        d = data.get('dji', {})