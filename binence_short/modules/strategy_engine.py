"""
거래 전략 엔진 모듈
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from utils.logger import logger
from utils.decorators import log_execution_time, cache_result
from .technical_analysis import TechnicalAnalyzer
from .exchange_interface import ExchangeInterface


class StrategyEngine:
    """거래 전략 엔진 클래스"""
    
    def __init__(self, config: Dict[str, Any], exchange: ExchangeInterface):
        self.config = config
        self.exchange = exchange
        self.technical_analyzer = TechnicalAnalyzer(config.get('technical_config', {}))
        
        # 전략 설정
        self.spot_allocation = config.get('spot_allocation', 0.6)
        self.futures_allocation = config.get('futures_allocation', 0.4)
        self.hedge_ratio = config.get('hedge_ratio', 0.3)
        self.rebalance_threshold = config.get('rebalance_threshold', 0.05)
        self.max_leverage = config.get('max_leverage', 5)
        self.risk_per_trade = config.get('risk_per_trade', 0.02)
        
        # 거래 상태
        self.positions = {}
        self.last_signals = {}
        self.last_rebalance = None
        
        logger.info("전략 엔진 초기화 완료")
    
    @log_execution_time
    def analyze_market(self, symbol: str) -> Dict[str, Any]:
        """시장 분석"""
        try:
            # 캔들 데이터 수집
            spot_df = self.exchange.get_ohlcv(symbol, '1h', 100, 'spot')
            futures_df = self.exchange.get_ohlcv(symbol, '1h', 100, 'future')
            
            if spot_df.empty or futures_df.empty:
                logger.warning(f"데이터 부족: {symbol}")
                return {}
            
            # 기술적 분석
            spot_indicators = self.technical_analyzer.get_all_indicators(spot_df)
            futures_indicators = self.technical_analyzer.get_all_indicators(futures_df)
            
            # 거래 신호 생성
            spot_signals = self.technical_analyzer.generate_signals(spot_indicators)
            futures_signals = self.technical_analyzer.generate_signals(futures_indicators)
            
            # 시장 강도 분석
            spot_strength = self.technical_analyzer.get_market_strength(spot_indicators)
            futures_strength = self.technical_analyzer.get_market_strength(futures_indicators)
            
            # 프리미엄 분석
            spot_price = spot_df['close'].iloc[-1]
            futures_price = futures_df['close'].iloc[-1]
            premium = (futures_price - spot_price) / spot_price
            
            return {
                'symbol': symbol,
                'spot_price': spot_price,
                'futures_price': futures_price,
                'premium': premium,
                'spot_signals': spot_signals,
                'futures_signals': futures_signals,
                'spot_strength': spot_strength,
                'futures_strength': futures_strength,
                'timestamp': datetime.now()
            }
        except Exception as e:
            logger.error(f"시장 분석 실패 ({symbol}): {e}")
            return {}
    
    @log_execution_time
    def generate_trade_decision(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """거래 결정 생성"""
        try:
            symbol = market_data['symbol']
            spot_signals = market_data.get('spot_signals', {})
            futures_signals = market_data.get('futures_signals', {})
            premium = market_data.get('premium', 0)
            
            # 기본 거래 결정
            spot_decision = self._get_spot_decision(spot_signals, premium)
            futures_decision = self._get_futures_decision(futures_signals, premium)
            
            # 하이브리드 전략 적용
            hybrid_decision = self._apply_hybrid_strategy(spot_decision, futures_decision, premium)
            
            # 리스크 조정
            final_decision = self._apply_risk_management(hybrid_decision, symbol)
            
            return {
                'symbol': symbol,
                'spot_decision': spot_decision,
                'futures_decision': futures_decision,
                'hybrid_decision': hybrid_decision,
                'final_decision': final_decision,
                'timestamp': datetime.now()
            }
        except Exception as e:
            logger.error(f"거래 결정 생성 실패: {e}")
            return {}
    
    def _get_spot_decision(self, signals: Dict[str, float], premium: float) -> Dict[str, Any]:
        """현물 거래 결정"""
        try:
            combined_signal = signals.get('combined_signal', 0)
            
            # 신호 강도에 따른 거래 결정
            if combined_signal > 0.5:
                action = 'buy'
                confidence = min(combined_signal, 1.0)
            elif combined_signal < -0.5:
                action = 'sell'
                confidence = min(abs(combined_signal), 1.0)
            else:
                action = 'hold'
                confidence = 0
            
            # 프리미엄 고려
            if premium > 0.02:  # 2% 이상 프리미엄
                if action == 'buy':
                    confidence *= 0.8  # 매수 신호 약화
            elif premium < -0.02:  # 2% 이상 디스카운트
                if action == 'sell':
                    confidence *= 0.8  # 매도 신호 약화
            
            return {
                'action': action,
                'confidence': confidence,
                'size': confidence * self.spot_allocation,
                'signals': signals
            }
        except Exception as e:
            logger.error(f"현물 거래 결정 실패: {e}")
            return {'action': 'hold', 'confidence': 0, 'size': 0}
    
    def _get_futures_decision(self, signals: Dict[str, float], premium: float) -> Dict[str, Any]:
        """선물 거래 결정"""
        try:
            combined_signal = signals.get('combined_signal', 0)
            
            # 신호 강도에 따른 거래 결정
            if combined_signal > 0.5:
                action = 'buy'
                confidence = min(combined_signal, 1.0)
            elif combined_signal < -0.5:
                action = 'sell'
                confidence = min(abs(combined_signal), 1.0)
            else:
                action = 'hold'
                confidence = 0
            
            # 프리미엄 기회 활용
            if premium > 0.03:  # 3% 이상 프리미엄
                if action == 'sell':
                    confidence *= 1.2  # 매도 신호 강화
            elif premium < -0.03:  # 3% 이상 디스카운트
                if action == 'buy':
                    confidence *= 1.2  # 매수 신호 강화
            
            return {
                'action': action,
                'confidence': min(confidence, 1.0),
                'size': min(confidence, 1.0) * self.futures_allocation,
                'leverage': min(int(confidence * self.max_leverage), self.max_leverage),
                'signals': signals
            }
        except Exception as e:
            logger.error(f"선물 거래 결정 실패: {e}")
            return {'action': 'hold', 'confidence': 0, 'size': 0, 'leverage': 1}
    
    def _apply_hybrid_strategy(self, spot_decision: Dict[str, Any], 
                              futures_decision: Dict[str, Any], premium: float) -> Dict[str, Any]:
        """하이브리드 전략 적용"""
        try:
            # 아비트라지 기회 탐지
            arbitrage_opportunity = self._detect_arbitrage_opportunity(premium)
            
            if arbitrage_opportunity:
                return self._execute_arbitrage_strategy(spot_decision, futures_decision, premium)
            
            # 트렌드 following 전략
            if spot_decision['action'] == futures_decision['action']:
                return self._execute_trend_following(spot_decision, futures_decision)
            
            # 헤지 전략
            if spot_decision['action'] != 'hold' and futures_decision['action'] != 'hold':
                return self._execute_hedge_strategy(spot_decision, futures_decision)
            
            # 단일 시장 전략
            if spot_decision['confidence'] > futures_decision['confidence']:
                return {'strategy': 'spot_only', 'decision': spot_decision}
            else:
                return {'strategy': 'futures_only', 'decision': futures_decision}
        
        except Exception as e:
            logger.error(f"하이브리드 전략 적용 실패: {e}")
            return {'strategy': 'hold', 'decision': {'action': 'hold', 'size': 0}}
    
    def _detect_arbitrage_opportunity(self, premium: float) -> bool:
        """아비트라지 기회 탐지"""
        return abs(premium) > 0.05  # 5% 이상 가격차이
    
    def _execute_arbitrage_strategy(self, spot_decision: Dict[str, Any], 
                                  futures_decision: Dict[str, Any], premium: float) -> Dict[str, Any]:
        """아비트라지 전략 실행"""
        try:
            if premium > 0.05:  # 선물 가격이 높음
                return {
                    'strategy': 'arbitrage',
                    'spot_action': 'buy',
                    'futures_action': 'sell',
                    'size': min(spot_decision['size'], futures_decision['size']),
                    'expected_profit': premium
                }
            elif premium < -0.05:  # 현물 가격이 높음
                return {
                    'strategy': 'arbitrage',
                    'spot_action': 'sell',
                    'futures_action': 'buy',
                    'size': min(spot_decision['size'], futures_decision['size']),
                    'expected_profit': abs(premium)
                }
            else:
                return {'strategy': 'hold', 'decision': {'action': 'hold', 'size': 0}}
        except Exception as e:
            logger.error(f"아비트라지 전략 실행 실패: {e}")
            return {'strategy': 'hold', 'decision': {'action': 'hold', 'size': 0}}
    
    def _execute_trend_following(self, spot_decision: Dict[str, Any], 
                               futures_decision: Dict[str, Any]) -> Dict[str, Any]:
        """트렌드 추종 전략"""
        try:
            combined_confidence = (spot_decision['confidence'] + futures_decision['confidence']) / 2
            
            return {
                'strategy': 'trend_following',
                'spot_action': spot_decision['action'],
                'futures_action': futures_decision['action'],
                'spot_size': spot_decision['size'],
                'futures_size': futures_decision['size'],
                'combined_confidence': combined_confidence
            }
        except Exception as e:
            logger.error(f"트렌드 추종 전략 실행 실패: {e}")
            return {'strategy': 'hold', 'decision': {'action': 'hold', 'size': 0}}
    
    def _execute_hedge_strategy(self, spot_decision: Dict[str, Any], 
                              futures_decision: Dict[str, Any]) -> Dict[str, Any]:
        """헤지 전략"""
        try:
            # 주요 포지션 결정
            if spot_decision['confidence'] > futures_decision['confidence']:
                main_decision = spot_decision
                hedge_decision = futures_decision
                main_market = 'spot'
            else:
                main_decision = futures_decision
                hedge_decision = spot_decision
                main_market = 'futures'
            
            # 헤지 비율 적용
            hedge_size = main_decision['size'] * self.hedge_ratio
            
            return {
                'strategy': 'hedge',
                'main_market': main_market,
                'main_action': main_decision['action'],
                'main_size': main_decision['size'],
                'hedge_action': 'sell' if main_decision['action'] == 'buy' else 'buy',
                'hedge_size': hedge_size,
                'hedge_ratio': self.hedge_ratio
            }
        except Exception as e:
            logger.error(f"헤지 전략 실행 실패: {e}")
            return {'strategy': 'hold', 'decision': {'action': 'hold', 'size': 0}}
    
    def _apply_risk_management(self, decision: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """리스크 관리 적용"""
        try:
            # 포지션 크기 조정
            if 'size' in decision:
                decision['size'] = min(decision['size'], self.risk_per_trade)
            
            # 최대 레버리지 제한
            if 'leverage' in decision:
                decision['leverage'] = min(decision['leverage'], self.max_leverage)
            
            # 기존 포지션 고려
            if symbol in self.positions:
                current_position = self.positions[symbol]
                decision = self._adjust_for_existing_position(decision, current_position)
            
            return decision
        except Exception as e:
            logger.error(f"리스크 관리 적용 실패: {e}")
            return decision
    
    def _adjust_for_existing_position(self, decision: Dict[str, Any], 
                                    current_position: Dict[str, Any]) -> Dict[str, Any]:
        """기존 포지션에 따른 조정"""
        try:
            # 포지션 크기 제한
            total_exposure = current_position.get('size', 0) + decision.get('size', 0)
            if total_exposure > self.risk_per_trade * 3:  # 최대 3배까지
                decision['size'] = max(0, self.risk_per_trade * 3 - current_position.get('size', 0))
            
            return decision
        except Exception as e:
            logger.error(f"기존 포지션 조정 실패: {e}")
            return decision
    
    @log_execution_time
    def should_rebalance(self) -> bool:
        """리밸런싱 필요 여부 확인"""
        try:
            if not self.last_rebalance:
                return True
            
            # 시간 기준 리밸런싱 (6시간마다)
            if datetime.now() - self.last_rebalance > timedelta(hours=6):
                return True
            
            # 포트폴리오 비율 변화 확인
            spot_balance = self.exchange.get_spot_balance()
            futures_balance = self.exchange.get_futures_balance()
            
            total_balance = spot_balance.get('total', {}).get('USDT', 0) + \
                           futures_balance.get('total', {}).get('USDT', 0)
            
            if total_balance > 0:
                current_spot_ratio = spot_balance.get('total', {}).get('USDT', 0) / total_balance
                target_spot_ratio = self.spot_allocation
                
                if abs(current_spot_ratio - target_spot_ratio) > self.rebalance_threshold:
                    return True
            
            return False
        except Exception as e:
            logger.error(f"리밸런싱 확인 실패: {e}")
            return False
    
    def update_position(self, symbol: str, position_data: Dict[str, Any]):
        """포지션 업데이트"""
        try:
            self.positions[symbol] = position_data
            logger.info(f"포지션 업데이트: {symbol} - {position_data}")
        except Exception as e:
            logger.error(f"포지션 업데이트 실패: {e}")
    
    def get_strategy_performance(self) -> Dict[str, Any]:
        """전략 성과 조회"""
        try:
            total_pnl = 0
            winning_trades = 0
            losing_trades = 0
            
            for symbol, position in self.positions.items():
                pnl = position.get('unrealized_pnl', 0) + position.get('realized_pnl', 0)
                total_pnl += pnl
                
                if pnl > 0:
                    winning_trades += 1
                elif pnl < 0:
                    losing_trades += 1
            
            total_trades = winning_trades + losing_trades
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            return {
                'total_pnl': total_pnl,
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate,
                'active_positions': len(self.positions)
            }
        except Exception as e:
            logger.error(f"전략 성과 조회 실패: {e}")
            return {}
    
    def reset_strategy(self):
        """전략 상태 초기화"""
        try:
            self.positions.clear()
            self.last_signals.clear()
            self.last_rebalance = None
            logger.info("전략 상태 초기화 완료")
        except Exception as e:
            logger.error(f"전략 상태 초기화 실패: {e}")