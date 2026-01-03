import streamlit as st
from datetime import datetime
import sys

# 1. 페이지 설정
st.set_page_config(page_title="Stock Sniper", layout="wide", initial_sidebar_state="collapsed")

# 2. 파일 로딩 시도 (config 에러 방지)
try:
    import config
    import stock_logic as logic
    import ui_components as ui
except ImportError as e:
    st.error(f"필수 파일을 찾을 수 없습니다: {e}")
    st.stop()
except AttributeError as e:
    st.error(f"설정 파일(config.py) 오류: {e}")
    st.stop()

# 3. UI 적용
ui.set_page_style()
now_str = datetime.now().strftime('%H:%M:%S')
ui.display_header(now_str, st.rerun)
ui.display_logic_expander()

# 4. 데이터 로딩
market_data = logic.get_market_data()
ui.display_market_summary(market_data)

# 5. 종목 카드 표시 (config.TICKERS가 없으면 에러 처리됨)
if hasattr(config, 'TICKERS'):
    ui.display_stock_cards(config.TICKERS, logic.analyze_stock)
else:
    st.error("config.py 파일에 'TICKERS' 리스트가 없습니다.")