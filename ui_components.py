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
        [data-testid="stMetricValue"] {font-size: 1.0rem;}
    </style>
    """, unsafe_allow_html=True)

def display_header(datetime_str, refresh_func):
    """상단 헤더"""
    c1, c2 = st.columns([3, 1])
    with c1:
        st.title("🇺🇸 스나이퍼 Bot")
        st.caption(f"Update: {datetime_str}")
    with c2:
        if st.button("🔄 갱신"):
            refresh_func()

def display_logic_expander():
    """로직 설명"""
    with st.expander("ℹ️ 점수 산출: RSI + MFI + 20일선"):
        st.markdown(f"""
        **💯 총 100점 만점 기준**
        1. **RSI ({config.RSI_OVERSOLD}미만 40점 / {config.RSI_WATCH}미만 20점)**
        2. **MFI ({config.MFI_STRONG}미만 30점 / {config.MFI_WATCH}미만 10점)**
        3. **이평선 (20일선 아래 30점)**
        ---
        🚨 **RSI {config.RSI_OVERBOUGHT} 이상은 강제 매도 신호(-99점)**
        """)

def display_market_summary(data):
    """시장 지수 요약"""
    st.subheader("🌍 Market Index")
    
    if data is None:
        st.error("시장 데이터 로딩 실패")
        return
        
    # [추가] 데이터 기준 날짜 표시
    st.caption(f"📅 데이터 기준: {data['date']}")

    cols = st.columns(5)
    
    # 1. Nasdaq 100
    with cols[0]:
        st.metric("NDX(100)", f"{data['ndx']['price']:,.0f}")
        rsi = data['ndx']['rsi']
        c = "red" if rsi > 70 else "blue" if rsi < 30 else "gray"
        st.markdown(f"RSI :{c}[{rsi:.0f}]")

    # 2. S&P 500
    with cols[1]:
        st.metric("S&P 500", f"{data['spx']['price']:,.0f}")
        rsi = data['spx']['rsi']
        c = "red" if rsi > 70 else "blue" if rsi < 30 else "gray"
        st.markdown(f"RSI :{c}[{rsi:.0f}]")

    # 3. Dow Jones
    with cols[2]:
        st.metric("Dow", f"{data['dji']['price']:,.0f}")
        rsi = data['dji']['rsi']
        c = "red" if rsi > 70 else "blue" if rsi < 30 else "gray"
        st.markdown(f"RSI :{c}[{rsi:.0f}]")
        
    # 4. VIX
    with cols[3]:
        st.metric("VIX", f"{data['vix']:.1f}")
        st.caption("🔴위험" if data['vix'] > 25 else "🟢안정")

    # 5. Fear & Greed
    with cols[4]:
        st.metric("공탐지수", "심리")
        st.caption(f"{data['fng']}")

    st.markdown("---")

def display_stock_cards(tickers, logic_func):
    """종목 카드 그리드 (수정됨)"""
    # 1. 제목 변경
    st.subheader("🚀 실시간 종목 모니터링")
    
    c1, c2 = st.columns(2)
    
    for i, ticker in enumerate(tickers):
        current_col = c1 if i % 2 == 0 else c2
        
        with current_col:
            data = logic_func(ticker)
            if data:
                score = data['score']
                change = data['change']
                
                # 상태바 색상
                if score == -99:
                    bg_color = "#ff4b4b" 
                    status_text = "🚨 매도 (과열)"
                elif score >= 90:
                    bg_color = "#21c354"
                    status_text = f"🔥 강력 매수 ({score})"
                elif score >= 50:
                    bg_color = "#ffbd45"
                    status_text = f"🟡 매수 관찰 ({score})"
                else:
                    bg_color = "#808495"
                    status_text = f"⚪ 관망 ({score})"

                with st.container(border=True):
                    top_c1, top_c2 = st.columns([2, 1.2])
                    
                    with top_c1:
                        st.subheader(ticker)
                        
                        # 2. 가격 및 등락률 표시 (상승=빨강, 하락=파랑)
                        change_color = "red" if change > 0 else "blue"
                        change_icon = "▲" if change > 0 else "▼"
                        
                        st.markdown(f"""
                        <div style='font-size: 1.05rem; font-weight: bold;'>
                            ${data['price']:.2f} 
                            <span style='color: {change_color}; font-size: 0.8rem;'>
                                ({change_icon}{abs(change):.2f}%)
                            </span>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.caption(f"RSI: {data['rsi']:.1f} / MFI: {data['mfi']:.1f}")
                        
                        # 3. 이평선 명칭 변경
                        gap_color = "red" if data['ma20_gap'] > 0 else "blue"
                        st.caption(f"20일평균선 기준: :{gap_color}[{data['ma20_gap']:.1f}%]")
                        
                    with top_c2:
                        box_style = f"""
                        <div style='
                            background-color: {bg_color};
                            color: white;
                            padding: 10px 2px;
                            border-radius: 8px;
                            text-align: center;
                            font-weight: bold;
                            font-size: 0.85rem;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            height: 100%;
                            word-break: keep-all;
                        '>
                            {status_text}
                        </div>
                        """
                        st.markdown(box_style, unsafe_allow_html=True)
            else:
                st.error(f"{ticker} 로딩 실패")