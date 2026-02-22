# 한국어 종목명을 영어 티커로 변환하는 매핑
STOCK_MAP = {
    # 미국 주식
    "테슬라": "TSLA",
    "애플": "AAPL", 
    "마이크로소프트": "MSFT",
    "엔비디아": "NVDA",
    "구글": "GOOGL",
    "아마존": "AMZN",
    "메타": "META",
    "넷플릭스": "NFLX",
    
    # 한국 주식
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS", 
    "에스케이하이닉스": "000660.KS",
    "현대차": "005380.KS",
    "카카오": "035720.KS",
    "네이버": "035420.KS",
    "NAVER": "035420.KS",
    
    # 암호화폐
    "비트코인": "KRW-BTC",
    "이더리움": "KRW-ETH"
}

import streamlit as st
import yfinance as yf
import pyupbit
import pandas as pd
import pandas_ta as ta
import numpy as np
from datetime import datetime

# 페이지 설정
st.set_page_config(
    page_title="AI 투자 분석 시스템 Ver.3.0", 
    page_icon="📈",
    layout="wide"
)

# 제목
st.title("🚀 확장형 AI 투자 운영 시스템 Ver.3.0")
st.markdown("---")

# 핵심 함수 정의
def get_market_regime():
    """VIX 지수로 시장 환경 진단"""
    try:
        vix = yf.Ticker("^VIX").history(period="5d")['Close'].iloc[-1]
        if vix < 20:
            return "Risk-On (공격 투자)", "🟢"
        elif vix > 25:
            return "Risk-Off (보수 투자)", "🔴"
        else:
            return "Neutral (중립)", "🟡"
    except Exception:
        return "데이터 조회 중...", "⚪"

def analyze_asset(user_query):
    """종목 분석 함수 - STOCK_MAP을 우선 사용"""
    
    # 입력값 정리
    query = user_query.strip()
    
    # STOCK_MAP에서 우선 검색 (대소문자 무관)
    ticker = None
    for key, value in STOCK_MAP.items():
        if key.lower() == query.lower():
            ticker = value
            break
    
    # STOCK_MAP에 없으면 입력값 그대로 사용 (이미 티커인 경우)
    if ticker is None:
        ticker = query.upper()
    
    st.subheader(f"📊 {query} 정밀 분석")
    
    # 암호화폐 여부 판별
    is_crypto = ticker.startswith("KRW-")
    
    try:
        with st.spinner(f"📡 {query} 데이터 수집 중..."):
            
            if is_crypto:
                # 암호화폐 데이터 (Upbit)
                current_price = pyupbit.get_current_price(ticker)
                df = pyupbit.get_ohlcv(ticker, interval="day", count=100)
                price_col = 'close'
            else:
                # 주식 데이터 (Yahoo Finance)
                stock = yf.Ticker(ticker)
                df = stock.history(period="6mo")
                if df is None or df.empty:
                    st.error(f"❌ '{query}' 데이터를 불러올 수 없습니다. 올바른 종목명인지 확인해주세요.")
                    st.info("💡 **지원 종목:** 테슬라, 애플, 삼성전자, AAPL, TSLA, 005930 등")
                    return
                current_price = df['Close'].iloc[-1]
                price_col = 'Close'
            
            # 기술적 지표 계산
            df['RSI'] = ta.rsi(df[price_col], length=14)
            df['MA20'] = df[price_col].rolling(20).mean()
            df['MA60'] = df[price_col].rolling(60).mean()
            
            # MACD 계산
            macd_data = ta.macd(df[price_col])
            df['MACD'] = macd_data['MACD_12_26_9']
            df['MACD_signal'] = macd_data['MACDs_12_26_9']
            
            # 현재 지표값
            current_rsi = df['RSI'].iloc[-1]
            current_ma20 = df['MA20'].iloc[-1]
            current_macd = df['MACD'].iloc[-1]
            current_signal = df['MACD_signal'].iloc[-1]
            
            # 지표 대시보드
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if is_crypto or ".KS" in ticker:
                    st.metric("현재가", f"{current_price:,.0f}원")
                else:
                    st.metric("현재가", f"${current_price:.2f}")
            
            with col2:
                rsi_status = "과열" if current_rsi > 70 else "침체" if current_rsi < 30 else "중립"
                st.metric("RSI(14)", f"{current_rsi:.1f}", rsi_status)
            
            with col3:
                trend = "상승" if current_price > current_ma20 else "하락"
                st.metric("추세(MA20)", trend)
            
            with col4:
                macd_signal = "매수" if current_macd > current_signal else "매도"
                st.metric("MACD", macd_signal)
            
            # 차트
            st.subheader("📈 가격 차트 (최근 60일)")
            chart_data = df[price_col].tail(60)
            st.line_chart(chart_data)
            
            # 투자 전략
            st.subheader("💡 투자 전략")
            
            support_level = current_price * 0.95
            resistance_level = current_price * 1.05
            
            strategy_col1, strategy_col2 = st.columns(2)
            
            with strategy_col1:
                st.write("**분할매수 전략**")
                st.write(f"• 1차 진입: {current_price * 0.98:,.0f}원")
                st.write(f"• 2차 진입: {support_level:,.0f}원")
                st.write(f"• 손절라인: {current_price * 0.92:,.0f}원")
            
            with strategy_col2:
                st.write("**목표 설정**")
                st.write(f"• 1차 목표: {resistance_level:,.0f}원")
                st.write(f"• 2차 목표: {current_price * 1.08:,.0f}원")
                st.write(f"• 최대 손실: -8%")
            
            st.success(f"✅ {query} 분석 완료!")
            
    except Exception as e:
        st.error(f"❌ 오류 발생: {str(e)}")
        st.info("💡 올바른 종목 코드인지 확인해주세요")

# 사이드바
with st.sidebar:
    st.header("📋 사용 가이드")
    st.info("""
**직접 입력 가능:**
• 테슬라, 애플, 삼성전자
• AAPL, TSLA, 005930
• 비트코인, 이더리움

**명령어:**
• 종목추천
• 배당주추천
""")
    
    st.markdown("### 💡 인기 종목")
    
    popular_stocks = {
        "🇺🇸 미국": ["AAPL", "TSLA", "NVDA", "GOOGL"],
        "🇰🇷 한국": ["삼성전자", "SK하이닉스", "카카오", "네이버"],
        "₿ 암호화폐": ["비트코인", "이더리움"]
    }
    
    for category, stocks in popular_stocks.items():
        st.markdown(f"**{category}**")
        for stock in stocks:
            if st.button(stock, key=f"quick_{stock}"):
                st.session_state.selected_stock = stock

# 메인 입력 인터페이스
col1, col2 = st.columns([5, 1])

with col1:
    # 세션 상태에서 선택된 종목 가져오기
    default_value = st.session_state.get('selected_stock', '')
    
    user_input = st.text_input(
        "종목명, 티커 또는 명령어 입력",
        value=default_value,
        placeholder="예: 테슬라, AAPL, 삼성전자, 종목추천",
        help="한글 종목명이나 영문 티커 모두 지원"
    )

with col2:
    st.write("")
    st.write("")
    analyze_btn = st.button("🔍 실행하기", type="primary", use_container_width=True)

# 실행 로직
if analyze_btn and user_input:
    command = user_input.strip()
    
    # "분석:" 접두어 자동 제거 (기존 사용자 습관 고려)
    if "분석:" in command:
        command = command.replace("분석:", "").strip()
    
    # 명령어 처리
    if "종목추천" in command:
        regime, emoji = get_market_regime()
        st.subheader(f"{emoji} 현재 시장 환경: {regime}")
        
        recommendations = {
            "순위": [1, 2, 3, 4, 5],
            "종목명": ["삼성전자", "TIGER 미국S&P500", "비트코인", "KT", "현대차"],
            "구분": ["성장주", "ETF", "암호화폐", "배당주", "가치주"],
            "현재가": ["72,300원", "15,400원", "업비트 시세", "38,500원", "240,000원"],
            "점수": [92, 89, 85, 82, 80],
            "선정사유": [
                "반도체 업황 회복 기대",
                "S&P500 지수 추종 안정성",
                "디지털 자산 상승 모멘텀",
                "고배당 수익률 6%+",
                "저평가 해소 가능성"
            ]
        }
        
        df_rec = pd.DataFrame(recommendations)
        st.dataframe(df_rec, use_container_width=True)
        
    elif "배당주" in command:
        st.subheader("💰 안정형 배당주 포트폴리오")
        
        dividend_data = {
            "종목명": ["KT", "SK텔레콤", "맥쿼리인프라", "LG유플러스", "한국전력"],
            "배당수익률": ["5.2%", "4.8%", "6.1%", "4.5%", "3.8%"],
            "안정성": ["High", "High", "Medium", "High", "Medium"],
            "추천비중": ["25%", "20%", "20%", "20%", "15%"]
        }
        
        df_div = pd.DataFrame(dividend_data)
        st.dataframe(df_div, use_container_width=True)
        
    else:
        # 종목 분석 실행
        analyze_asset(command)
        
elif analyze_btn:
    st.warning("⚠️ 종목명이나 명령어를 입력해주세요.")

# 세션 상태 초기화 (빠른 선택 후)
if 'selected_stock' in st.session_state and st.session_state.selected_stock:
    st.session_state.selected_stock = ""

# 면책조항
st.markdown("---")
st.caption("⚠️ **면책조항**: 본 시스템은 정보 제공 목적이며, 투자 결정의 책임은 사용자에게 있습니다. 실시간 데이터에는 지연이 있을 수 있습니다.")
