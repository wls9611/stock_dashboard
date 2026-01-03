import streamlit as st
from datetime import datetime
import config
import stock_logic as logic
import ui_components as ui

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="Stock Sniper", 
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)
ui.set_page_style()

# 2. 헤더 및 로직 설명바
now_str = datetime.now().strftime('%H:%M:%S')
ui.display_header(now_str, st.rerun)
ui.display_logic_expander()

# 3. 시장 지수 요약
ndx, spx, vix, fng = logic.get_market_data()
ui.display_market_summary(ndx, spx, vix, fng)

# 4. 메인 종목 카드 그리드 표시
ui.display_stock_cards(config.TICKERS, logic.analyze_stock)