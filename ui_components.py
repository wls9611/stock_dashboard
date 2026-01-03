import streamlit as st
import config

def set_page_style():
    """모바일 최적화 및 CSS 설정"""
    st.markdown("""
    <style>
        /* 기본 여백 조정 */
        .block-container {padding-top: 1rem; padding-bottom: 3rem;}
        
        /* 시장 지표 카드 디자인 */
        .market-card {
            background-color: #f0f2f6;
            border-radius: 10px;
            padding: 10px 5px; /* 내부 여백 조정 */
            text-align: center;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
            height: 100%; /* 높이 채우기 */
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        
        /* 다크모드 대응 */
        @media (prefers-color-scheme: dark) {
            .market-card {
                background-color: #262730;
                color: white;
            }
        }

        /* 종목 카드 그리드 (모바일 2열 강제) */
        .stock-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr); 
            gap: 10px;
            margin-top: 15px;
        }

        /* 개별 종목 카드 */
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
        
        /* 텍스트 크기 미세 조정 */
        .small-label { font-size: 0.75rem; color: gray; font-weight: bold; }
        .big-value { font-size: 1.0rem; font-weight: 900; margin: 3px 0; }
        .change-text { font-size: 0.8rem; font-weight: bold; }
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
    with st.expander("ℹ️ 점수 산출 공식 (클릭)"):
        st.markdown(f"""
        **💯 총 100점 만점**
        - RSI < {config.RSI_OVERSOLD}: **40점**
        - MFI < {config.MFI_STRONG}: **30점**
        - Price < MA20: **30점**
        - (RSI > {config.RSI_OVERBOUGHT}: **-99점**)
        """)

def create_market_card_html(label, val, change, rsi=None, is_vix=False, is_fng=False):
    """시장 지표 카드 HTML 생성 헬퍼 함수"""
    if is_fng:
        # 공탐지수 전용
        return f"""
        <div class="market-card">