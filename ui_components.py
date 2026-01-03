import streamlit as st
import config

def set_page_style():
    """모바일 최적화 CSS"""
    st.markdown("""
    <style>
        .block-container {padding-top: 1rem; padding-bottom: 2rem;}
        h1 {font-size: 1.5rem !important;}
        h3 {font-size: 1.1rem !important; margin-bottom: 0px;}
        .stButton>button {width: 100%;}
        [data-testid="stMetricLabel"] {font-size: 0.8rem;}
        [data-testid="stMetricValue"] {font-size: 1.1rem;}
    </style>
    """, unsafe_allow_html=True)

def display_header(datetime_str, refresh_func):
    """상단 헤더 및 새로고침"""
    c1, c2 = st.columns([3, 1])
    with c1:
        st.title("🇺🇸 스나이퍼 Bot")
        st.caption(f"Update: {datetime_str}")
    with c2:
        if st.button("🔄 갱신"):
            refresh_func()

def display_logic_expander():
    """로직 설명 접이식 박스"""
    with st.expander("ℹ️ 점수 산출: RSI + MFI + 20일선"):
        st.markdown(f"""
        **💯 총 100점 만점 기준**
        
        1.  **RSI ({config.RSI_OVERSOLD}미만 40점 / {config.RSI_WATCH}미만 20점)**
        2.  **MFI ({config.MFI_STRONG}미만 30점 / {config.MFI_WATCH}미만 10점)**
        3.  **이평선 (20일선 아래 30점)**
        
        ---
        🚨 **RSI {config.RSI_OVERBOUGHT} 이상은 강제 매도 신호(-99점)**
        """)

def display_market_summary(ndx, spx, vix, fng):
    """시장 지수 요약바"""
    st.subheader("🌍 Market Index")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Nasdaq", f"{ndx:,.0f}")
    m2.metric("S&P", f"{spx:,.0f}")
    m3.metric("VIX", f"{vix:.1f}", delta_color="inverse")
    m4.metric("Fear/Greed", f"{fng}")
    st.markdown("---")

def display_stock_cards(tickers, logic_func):
    """2열 종목 카드 그리드"""
    st.subheader("🚀 실시간 타점 모니터")
    
    # 2열 배치를 위한 컬럼 생성
    c1, c2 = st.columns(2)
    
    for i, ticker in enumerate(tickers):
        # 인덱스에 따라 좌/우 컬럼 배정
        current_col = c1 if i % 2 == 0 else c2
        
        with current_col:
            data = logic_func(ticker)
            if data:
                score = data['score']
                
                # 색상 및 상태 결정
                if score == -99:
                    bg_color = "#ff4b4b" # Red
                    status_text = "Sell (과열)"
                elif score >= 90:
                    bg_color = "#21c354" # Green
                    status_text = f"Strong Buy ({score})"
                elif score >= 50:
                    bg_color = "#ffbd45" # Orange
                    status_text = f"Watch ({score})"
                else:
                    bg_color = "#808495" # Gray
                    status_text = f"Neutral ({score})"

                # 카드 디자인 (좌측 데이터, 우측 시그널 박스)
                with st.container(border=True):
                    top_c1, top_c2 = st.columns([2, 1.2])
                    
                    with top_c1:
                        st.subheader(ticker)
                        st.write(f"**Price: ${data['price']:.2f}**")
                        st.caption(f"RSI: {data['rsi']:.1f}")
                        st.caption(f"MFI: {data['mfi']:.1f}")
                        
                        gap_color = "red" if data['ma20_gap'] > 0 else "green"
                        st.caption(f"MA20 gap: :{gap_color}[{data['ma20_gap']:.2f}%]")
                        
                    with top_c2:
                        # 시그널 박스 CSS
                        box_style = f"""
                        <div style='
                            background-color: {bg_color};
                            color: white;
                            padding: 15px 5px;
                            border-radius: 10px;
                            text-align: center;
                            font-weight: bold;
                            font-size: 0.9rem;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            height: 100%;
                        '>
                            {status_text}<br>Signal
                        </div>
                        """
                        st.markdown(box_style, unsafe_allow_html=True)
            else:
                st.error(f"{ticker} Error")