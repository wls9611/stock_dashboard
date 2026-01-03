import streamlit as st
import config

def set_page_style():
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
    c1, c2 = st.columns([3, 1])
    with c1:
        st.title("🇺🇸 스나이퍼 Bot")
        st.caption(f"Update: {datetime_str}")
    with c2:
        if st.button("🔄 갱신"):
            refresh_func()

def display_logic_expander():
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
    st.subheader("🌍 Market Index")
    
    if not data:
        st.warning("⚠️ 시장 데이터를 가져오는 중이거나 실패했습니다.")
        return
        
    st.caption(f"📅 데이터 기준: {data.get('date', '-')}")

    cols = st.columns(5)
    
    # 지표 리스트 정의 (키 이름, 표시 이름)
    metrics = [("ndx", "NDX(100)"), ("spx", "S&P 500"), ("dji", "Dow")]
    
    for i, (key, label) in enumerate(metrics):
        with cols[i]:
            if key in data and data[key]:
                val = data[key]['price']
                rsi = data[key]['rsi']
                st.metric(label, f"{val:,.0f}")
                c = "red" if rsi > 70 else "blue" if rsi < 30 else "gray"
                st.markdown(f"RSI :{c}[{rsi:.0f}]")
            else:
                st.metric(label, "-")

    with cols[3]:
        vix = data.get('vix', 0)
        st.metric("VIX", f"{vix:.1f}")
        st.caption("🔴위험" if vix > 25 else "🟢안정")

    with cols[4]:
        st.metric("공탐지수", "심리")
        st.caption(f"{data.get('fng', '-')}")

    st.markdown("---")

def display_stock_cards(tickers, logic_func):
    st.subheader("🚀 실시간 종목 모니터링")
    
    if not tickers:
        st.error("설정 파일(config.py)에 종목(TICKERS)이 없습니다.")
        return

    c1, c2 = st.columns(2)
    
    for i, ticker in enumerate(tickers):
        current_col = c1 if i % 2 == 0 else c2
        with current_col:
            # logic_func 실행 결과가 None일 경우를 대비
            data = logic_func(ticker)
            
            if data:
                score = data['score']
                change = data['change']
                
                if score == -99:
                    bg = "#ff4b4b" 
                    txt = "🚨 매도 (과열)"
                elif score >= 90:
                    bg = "#21c354"
                    txt = f"🔥 강력 매수 ({score})"
                elif score >= 50:
                    bg = "#ffbd45"
                    txt = f"🟡 매수 관찰 ({score})"
                else:
                    bg = "#808495"
                    txt = f"⚪ 관망 ({score})"

                with st.container(border=True):
                    top_c1, top_c2 = st.columns([2, 1.2])
                    with top_c1:
                        st.subheader(ticker)
                        cc = "red" if change > 0 else "blue"
                        icon = "▲" if change > 0 else "▼"
                        st.markdown(f"<div style='font-weight:bold; font-size:1.05rem;'>${data['price']:.2f} <span style='color:{cc}; font-size:0.8rem;'>({icon}{abs(change):.2f}%)</span></div>", unsafe_allow_html=True)
                        st.caption(f"RSI:{data['rsi']:.0f} / MFI:{data['mfi']:.0f}")
                        
                        gc = "red" if data['ma20_gap'] > 0 else "blue"
                        st.caption(f"20일선: :{gc}[{data['ma20_gap']:.1f}%]")
                        
                    with top_c2:
                        st.markdown(f"<div style='background-color:{bg}; color:white; padding:10px 2px; border-radius:8px; text-align:center; font-size:0.8rem; font-weight:bold; height:100%; display:flex; align-items:center; justify-content:center;'>{txt}</div>", unsafe_allow_html=True)
            else:
                st.error(f"{ticker} 로딩 실패")