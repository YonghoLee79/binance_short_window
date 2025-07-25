#!/usr/bin/env python3
"""
트레이딩 봇 설정 파일
"""

import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()


class Config:
    """트레이딩 봇 설정 클래스"""
    
    # API 키 설정
    BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
    BINANCE_SECRET_KEY = os.getenv('BINANCE_SECRET_KEY')
    USE_TESTNET = os.getenv('USE_TESTNET', 'False').lower() == 'true'
    
    # 텔레그램 설정
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    
    # 거래 설정
    INITIAL_BALANCE = 1000.0  # 초기 자금
    SPOT_ALLOCATION = 0.4     # 현물 할당 40% (수익률 최적화)
    FUTURES_ALLOCATION = 0.6  # 선물 할당 60% (레버리지 활용)
    REBALANCE_THRESHOLD = 0.05  # 리밸런싱 임계값 5% (더 빈번한 리밸런싱)
    
    # 거래 심볼 (현물과 선물 모두 지원되는 메이저 코인만)
    TRADING_SYMBOLS = [
        'BTC/USDT',   # 비트코인
        'ETH/USDT',   # 이더리움
        'BNB/USDT',   # 바이낸스 코인
        'XRP/USDT',   # 리플
        'SOL/USDT',   # 솔라나
        'ADA/USDT',   # 카르다노
        'AVAX/USDT',  # 아발란체
        'LINK/USDT',  # 체인링크
        'DOT/USDT',   # 폴카닷 (선물 제외)
        'MATIC/USDT', # 폴리곤 (현재 문제 발생)
        # 'LTC/USDT',   # 라이트코인 (선물 문제로 제외)
        'TRX/USDT'    # 트론
    ]
    
    # 수수료 설정
    FEES = {
        'spot': {
            'maker': 0.001,   # 0.1%
            'taker': 0.001    # 0.1%
        },
        'futures': {
            'maker': 0.0002,  # 0.02%
            'taker': 0.0004   # 0.04%
        }
    }
    
    def get_risk_config(self):
        """리스크 관리 설정 반환"""
        return {
            'max_position_size': 0.15,      # 단일 포지션 최대 15%
            'max_daily_loss': 0.05,         # 일일 손실 한도 5%
            'max_drawdown': 0.20,           # 최대 드로우다운 20%
            'stop_loss_pct': 0.05,          # 스탑로스 5%
            'take_profit_pct': 0.10,        # 테이크프로핏 10%
            'position_timeout_hours': 24,   # 포지션 타임아웃 24시간
            'max_leverage': 3,              # 최대 레버리지 3배
            'risk_per_trade': 0.02,         # 거래당 리스크 2%
            'short_position_limit': 0.3,    # 공매도 포지션 한도 30%
            'short_squeeze_threshold': 0.10,# 숏 스퀴즈 임계값 10%
            'funding_rate_threshold': 0.01  # 펀딩비 임계값 1%
        }
    
    def get_technical_config(self):
        """기술적 분석 설정 반환"""
        return {
            'rsi_period': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            'bb_period': 20,
            'bb_stddev': 2,
            'atr_period': 14,
            'stoch_k_period': 14,
            'stoch_d_period': 3,
            'williams_r_period': 14,
            'ma_short': 10,
            'ma_long': 20
        }
    
    def get_strategy_config(self):
        """전략 설정 반환"""
        return {
            'signal_threshold': 0.3,        # 신호 임계값
            'trend_strength_min': 0.4,      # 최소 트렌드 강도
            'volatility_threshold': 0.02,   # 변동성 임계값
            'volume_threshold': 1.5,        # 거래량 임계값
            'correlation_threshold': 0.7,   # 상관관계 임계값
            'momentum_period': 10,          # 모멘텀 기간
            'reversal_threshold': 0.8       # 반전 신호 임계값
        }
    
    def get_hybrid_config(self):
        """하이브리드 전략 설정 반환 (적극적 거래)"""
        return {
            'spot_allocation': self.SPOT_ALLOCATION,
            'futures_allocation': self.FUTURES_ALLOCATION,
            'arbitrage_threshold': 0.0005,  # 아비트라지 임계값 0.05% (초민감)
            'rebalance_threshold': self.REBALANCE_THRESHOLD,
            'max_leverage': 5,              # 레버리지 증가
            'max_position_size': 0.2,       # 단일 포지션 최대 20%
            'correlation_limit': 0.75,
            'trend_threshold': 0.3,         # 트렌드 신호 임계값 (더 민감)
            'momentum_threshold': 0.5,      # 모멘텀 신호 임계값 (더 민감)
            'hedge_ratio': 0.8,             # 헤지 비율 80%
            'rebalance_interval_hours': 12  # 리밸런싱 간격 12시간
        }


# 전역 설정 인스턴스
config = Config()