import streamlit as st
from datetime import datetime
import config
import stock_logic as logic
import ui_components as ui

# 1. 페이지 설정
st.set_page_config(
    page_title="Stock Sniper", 
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)
ui.set_page_style()

# 2. 헤더
now_str = datetime.now().strftime('%H:%M:%S')
ui.display_header(now_str, st.rerun)
ui.display_logic_expander()

# 3. 시장 지수 (데이터 날짜 포함)
market_data = logic.get_market_data()
ui.display_market_summary(market_data)

# 4. 종목 리스트
ui.display_stock_cards(config.TICKERS, logic.analyze_stock)