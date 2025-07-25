"""
리스크 관리 모듈
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from utils.logger import logger
from utils.decorators import log_execution_time


class RiskManager:
    """리스크 관리 클래스"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # 리스크 관리 파라미터
        self.max_position_size = config.get('max_position_size', 0.2)  # 최대 포지션 크기 (20%)
        self.max_daily_loss = config.get('max_daily_loss', 0.05)  # 최대 일일 손실 (5%)
        self.max_drawdown = config.get('max_drawdown', 0.20)  # 최대 드로우다운 (20%)
        self.stop_loss_pct = config.get('stop_loss_pct', 0.05)  # 스탑로스 (5%)
        self.take_profit_pct = config.get('take_profit_pct', 0.10)  # 테이크프로핏 (10%)
        self.position_timeout_hours = config.get('position_timeout_hours', 24)  # 포지션 타임아웃 (24시간)
        self.max_leverage = config.get('max_leverage', 5)  # 최대 레버리지
        self.risk_per_trade = config.get('risk_per_trade', 0.02)  # 거래당 리스크 (2%)
        
        # 공매도 특화 리스크 관리
        self.short_position_limit = config.get('short_position_limit', 0.3)  # 공매도 포지션 한도 (30%)
        self.short_squeeze_threshold = config.get('short_squeeze_threshold', 0.10)  # 숏 스퀴즈 임계값 (10%)
        self.funding_rate_threshold = config.get('funding_rate_threshold', 0.01)  # 펀딩비 임계값 (1%)
        
        # 리스크 상태 추적
        self.daily_pnl = 0.0
        self.peak_balance = 0.0
        self.current_drawdown = 0.0
        self.positions = {}
        self.risk_alerts = []
        
        logger.info("리스크 관리자 초기화 완료")
    
    @log_execution_time
    def validate_trade(self, symbol: str, side: str, size: float, price: float, 
                      current_balance: float, exchange_type: str = 'spot') -> Dict[str, Any]:
        """거래 유효성 검증"""
        try:
            validation_result = {
                'is_valid': True,
                'warnings': [],
                'errors': [],
                'adjusted_size': size
            }
            
            # 포지션 크기 검증
            position_value = size * price
            max_position_value = current_balance * self.max_position_size
            
            if position_value > max_position_value:
                validation_result['warnings'].append(f"포지션 크기 초과: {position_value:.2f} > {max_position_value:.2f}")
                validation_result['adjusted_size'] = max_position_value / price
            
            # 일일 손실 한도 검증
            if self.daily_pnl < -current_balance * self.max_daily_loss:
                validation_result['is_valid'] = False
                validation_result['errors'].append(f"일일 손실 한도 초과: {self.daily_pnl:.2f}")
            
            # 드로우다운 검증
            if self.current_drawdown > self.max_drawdown:
                validation_result['is_valid'] = False
                validation_result['errors'].append(f"최대 드로우다운 초과: {self.current_drawdown:.2%}")
            
            # 공매도 특화 검증
            if side == 'sell' and exchange_type == 'futures':
                short_validation = self._validate_short_position(symbol, size, price, current_balance)
                validation_result['warnings'].extend(short_validation['warnings'])
                validation_result['errors'].extend(short_validation['errors'])
                if not short_validation['is_valid']:
                    validation_result['is_valid'] = False
            
            # 레버리지 검증
            if exchange_type == 'futures':
                leverage_validation = self._validate_leverage(size, price, current_balance)
                validation_result['warnings'].extend(leverage_validation['warnings'])
                validation_result['errors'].extend(leverage_validation['errors'])
            
            return validation_result
        except Exception as e:
            logger.error(f"거래 검증 실패: {e}")
            return {
                'is_valid': False,
                'warnings': [],
                'errors': [f"검증 오류: {e}"],
                'adjusted_size': 0
            }
    
    def _validate_short_position(self, symbol: str, size: float, price: float, 
                               current_balance: float) -> Dict[str, Any]:
        """공매도 포지션 검증"""
        try:
            validation_result = {
                'is_valid': True,
                'warnings': [],
                'errors': []
            }
            
            # 공매도 포지션 한도 검증
            current_short_value = sum(
                pos['size'] * pos['price'] for pos in self.positions.values()
                if pos['side'] == 'sell' and pos['exchange_type'] == 'futures'
            )
            new_short_value = current_short_value + (size * price)
            max_short_value = current_balance * self.short_position_limit
            
            if new_short_value > max_short_value:
                validation_result['is_valid'] = False
                validation_result['errors'].append(
                    f"공매도 포지션 한도 초과: {new_short_value:.2f} > {max_short_value:.2f}"
                )
            
            # 숏 스퀴즈 위험 검증
            if symbol in self.positions:
                recent_price_change = self._calculate_recent_price_change(symbol)
                if recent_price_change > self.short_squeeze_threshold:
                    validation_result['warnings'].append(
                        f"숏 스퀴즈 위험: 최근 가격 상승 {recent_price_change:.2%}"
                    )
            
            return validation_result
        except Exception as e:
            logger.error(f"공매도 포지션 검증 실패: {e}")
            return {
                'is_valid': False,
                'warnings': [],
                'errors': [f"공매도 검증 오류: {e}"]
            }
    
    def _validate_leverage(self, size: float, price: float, current_balance: float) -> Dict[str, Any]:
        """레버리지 검증"""
        try:
            validation_result = {
                'is_valid': True,
                'warnings': [],
                'errors': []
            }
            
            position_value = size * price
            required_margin = position_value / self.max_leverage
            
            if required_margin > current_balance * 0.8:  # 잔고의 80% 이상 사용
                validation_result['warnings'].append(
                    f"높은 레버리지 사용: 필요 마진 {required_margin:.2f}"
                )
            
            return validation_result
        except Exception as e:
            logger.error(f"레버리지 검증 실패: {e}")
            return {
                'is_valid': True,
                'warnings': [],
                'errors': []
            }
    
    def _calculate_recent_price_change(self, symbol: str) -> float:
        """최근 가격 변화 계산"""
        try:
            if symbol in self.positions:
                position = self.positions[symbol]
                entry_price = position['price']
                current_price = position.get('current_price', entry_price)
                return (current_price - entry_price) / entry_price
            return 0.0
        except Exception as e:
            logger.error(f"가격 변화 계산 실패: {e}")
            return 0.0
    
    @log_execution_time
    def calculate_position_size(self, symbol: str, signal_strength: float, 
                               current_balance: float, current_price: float, 
                               volatility: float = 0.02) -> float:
        """기존 포지션 크기 계산 (하위 호환성 유지)"""
        try:
            # 기본 시장 조건 설정
            market_conditions = {
                'volatility': volatility,
                'regime': 'neutral',
                'liquidity': 'normal'
            }
            
            return self.adaptive_position_sizing(symbol, signal_strength, current_balance, 
                                               current_price, market_conditions)
        except Exception as e:
            logger.error(f"포지션 크기 계산 실패: {e}")
            return 0.0

    @log_execution_time
    def adaptive_position_sizing(self, symbol: str, signal_strength: float, 
                                current_balance: float, current_price: float,
                                market_conditions: Dict[str, Any]) -> float:
        """시장 상황 적응형 포지션 크기 계산"""
        try:
            # 1. 실시간 승률 계산
            recent_win_rate = self._calculate_recent_win_rate(symbol, days=30)
            
            # 2. 동적 Kelly Criterion 적용
            dynamic_kelly = self._calculate_dynamic_kelly(symbol, recent_win_rate, market_conditions)
            
            # 3. 변동성 조정
            volatility_adj = self._calculate_volatility_adjustment(market_conditions['volatility'])
            
            # 4. 시장 체제별 조정
            regime_multiplier = self._get_regime_multiplier(market_conditions['regime'])
            
            # 5. 유동성 조정
            liquidity_adj = self._calculate_liquidity_adjustment(market_conditions['liquidity'])
            
            # 6. 상관관계 리스크 조정
            correlation_adj = self._calculate_correlation_adjustment(symbol)
            
            # 7. 최종 포지션 크기 계산
            base_size = dynamic_kelly * signal_strength
            adjusted_size = (base_size * volatility_adj * regime_multiplier * 
                           liquidity_adj * correlation_adj)
            
            # 8. 안전 장치 적용
            final_size = self._apply_safety_limits(adjusted_size, current_balance, current_price)
            
            logger.debug(f"적응형 포지션 크기: {symbol} - {final_size:.6f} "
                        f"(신호: {signal_strength:.2f}, 승률: {recent_win_rate:.2f})")
            
            return final_size
            
        except Exception as e:
            logger.error(f"적응형 포지션 사이징 실패: {e}")
            return self._fallback_position_size(current_balance, current_price)

    def _calculate_recent_win_rate(self, symbol: str, days: int = 30) -> float:
        """최근 거래 승률 계산"""
        try:
            # 실제 구현에서는 데이터베이스에서 최근 거래 기록을 가져와야 함
            # 현재는 시뮬레이션된 값 사용
            
            # 심볼별 기본 승률 (과거 데이터 기반 추정)
            base_win_rates = {
                'BTC/USDT': 0.58,
                'ETH/USDT': 0.56,
                'BNB/USDT': 0.54,
                'XRP/USDT': 0.52,
                'SOL/USDT': 0.55,
                'ADA/USDT': 0.53,
                'AVAX/USDT': 0.54,
                'LINK/USDT': 0.56,
                'TRX/USDT': 0.51
            }
            
            base_rate = base_win_rates.get(symbol, 0.52)
            
            # 최근 시장 상황에 따른 조정 (실제로는 DB 쿼리 결과 사용)
            # 여기서는 간단한 변동을 시뮬레이션
            import random
            adjustment = random.uniform(-0.05, 0.05)  # ±5% 변동
            
            recent_rate = max(0.3, min(0.8, base_rate + adjustment))
            return recent_rate
            
        except Exception as e:
            logger.error(f"승률 계산 실패: {e}")
            return 0.52  # 기본값

    def _calculate_dynamic_kelly(self, symbol: str, win_rate: float, 
                                market_conditions: Dict[str, Any]) -> float:
        """동적 Kelly Criterion 계산"""
        try:
            # 시장 조건에 따른 수익/손실 비율 조정
            if market_conditions['regime'] == 'trending':
                avg_win = 0.18   # 트렌드 시장에서 더 큰 수익 기대
                avg_loss = 0.09
            elif market_conditions['regime'] == 'volatile':
                avg_win = 0.12   # 변동성 시장에서 작은 수익
                avg_loss = 0.12
            else:  # ranging 또는 neutral
                avg_win = 0.15
                avg_loss = 0.08
            
            # Kelly 공식: f = (bp - q) / b
            # f = fraction to bet, b = odds received, p = win probability, q = lose probability
            if avg_win <= 0:
                return 0.0
                
            kelly_fraction = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
            
            # Kelly 값이 음수면 0으로, 너무 크면 제한
            kelly_fraction = max(0, min(kelly_fraction, 0.25))  # 최대 25%
            
            return kelly_fraction
            
        except Exception as e:
            logger.error(f"동적 Kelly 계산 실패: {e}")
            return 0.02  # 보수적 기본값

    def _calculate_volatility_adjustment(self, volatility: float) -> float:
        """변동성 기반 조정"""
        try:
            # 변동성이 높을수록 포지션 크기 감소
            if volatility > 0.05:  # 5% 이상 고변동성
                return 0.5
            elif volatility > 0.03:  # 3-5% 중변동성
                return 0.7
            elif volatility > 0.01:  # 1-3% 저변동성
                return 1.0
            else:  # 1% 미만 극저변동성
                return 1.2  # 약간 증가
                
        except Exception as e:
            logger.error(f"변동성 조정 계산 실패: {e}")
            return 0.8

    def _get_regime_multiplier(self, regime: str) -> float:
        """시장 체제별 배수"""
        regime_multipliers = {
            'trending': 1.3,    # 트렌드 시장: 포지션 크기 증가
            'ranging': 0.8,     # 횡보 시장: 포지션 크기 감소
            'volatile': 0.6,    # 변동성 시장: 포지션 크기 대폭 감소
            'neutral': 1.0      # 중립: 기본값
        }
        return regime_multipliers.get(regime, 1.0)

    def _calculate_liquidity_adjustment(self, liquidity: str) -> float:
        """유동성 조정"""
        liquidity_adjustments = {
            'high': 1.1,      # 높은 유동성: 약간 증가
            'normal': 1.0,    # 보통 유동성: 기본값
            'low': 0.7        # 낮은 유동성: 감소
        }
        return liquidity_adjustments.get(liquidity, 1.0)

    def _calculate_correlation_adjustment(self, symbol: str) -> float:
        """포트폴리오 상관관계 조정"""
        try:
            # 현재 포지션들과의 상관관계 계산
            correlation_risk = 0.0
            
            for existing_symbol, position in self.positions.items():
                if existing_symbol != symbol:
                    # 심볼 간 상관관계 추정 (실제로는 과거 가격 데이터 기반 계산)
                    correlation = self._estimate_correlation(symbol, existing_symbol)
                    position_weight = abs(position['size'] * position['current_price'])
                    correlation_risk += correlation * position_weight
            
            # 상관관계 리스크가 높을수록 포지션 크기 감소
            if correlation_risk > 0.8:
                return 0.5
            elif correlation_risk > 0.6:
                return 0.7
            elif correlation_risk > 0.3:
                return 0.9
            else:
                return 1.0
                
        except Exception as e:
            logger.error(f"상관관계 조정 계산 실패: {e}")
            return 0.9

    def _estimate_correlation(self, symbol1: str, symbol2: str) -> float:
        """두 심볼 간 상관관계 추정"""
        try:
            # 메이저 코인들 간의 대략적인 상관관계
            major_coins = ['BTC/USDT', 'ETH/USDT']
            
            if symbol1 in major_coins and symbol2 in major_coins:
                return 0.8  # BTC-ETH 높은 상관관계
            elif symbol1 in major_coins or symbol2 in major_coins:
                return 0.6  # 메이저 코인과 알트코인
            else:
                return 0.4  # 알트코인들 간 중간 상관관계
                
        except Exception as e:
            logger.error(f"상관관계 추정 실패: {e}")
            return 0.5

    def _apply_safety_limits(self, calculated_size: float, current_balance: float, 
                           current_price: float) -> float:
        """안전 제한 적용"""
        try:
            position_value = calculated_size * current_price
            
            # 1. 최대 포지션 크기 제한
            max_position_value = current_balance * self.max_position_size
            if position_value > max_position_value:
                calculated_size = max_position_value / current_price
            
            # 2. 최대 리스크 제한
            max_risk_amount = current_balance * self.risk_per_trade
            if position_value > max_risk_amount:
                calculated_size = max_risk_amount / current_price
            
            # 3. 최소 포지션 크기 (거래 수수료 고려)
            min_position_value = 10.0  # 최소 $10
            if position_value < min_position_value:
                return 0.0
            
            return calculated_size
            
        except Exception as e:
            logger.error(f"안전 제한 적용 실패: {e}")
            return 0.0

    def _fallback_position_size(self, current_balance: float, current_price: float) -> float:
        """폴백 포지션 크기 (에러 시 사용)"""
        try:
            # 매우 보수적인 포지션 크기
            conservative_amount = current_balance * 0.01  # 1%
            return conservative_amount / current_price
        except Exception as e:
            logger.error(f"폴백 포지션 크기 계산 실패: {e}")
            return 0.0
    
    @log_execution_time
    def calculate_stop_loss(self, symbol: str, side: str, entry_price: float, 
                           volatility: float = 0.02) -> float:
        """스탑로스 가격 계산"""
        try:
            # 기본 스탑로스
            basic_stop_loss = self.stop_loss_pct
            
            # 변동성 기반 조정
            volatility_adjustment = max(volatility * 2, basic_stop_loss)
            
            # ATR 기반 스탑로스 (더 정교한 방법)
            atr_multiplier = 2.0
            atr_stop_loss = volatility * atr_multiplier
            
            # 최종 스탑로스 거리 결정
            stop_loss_distance = max(basic_stop_loss, min(volatility_adjustment, atr_stop_loss))
            
            if side == 'buy':
                stop_loss_price = entry_price * (1 - stop_loss_distance)
            else:  # sell
                stop_loss_price = entry_price * (1 + stop_loss_distance)
            
            logger.debug(f"스탑로스 계산: {symbol} {side} - {stop_loss_price:.6f}")
            return stop_loss_price
        except Exception as e:
            logger.error(f"스탑로스 계산 실패: {e}")
            return entry_price
    
    @log_execution_time
    def calculate_take_profit(self, symbol: str, side: str, entry_price: float, 
                            signal_strength: float = 0.5) -> float:
        """테이크프로핏 가격 계산"""
        try:
            # 기본 테이크프로핏
            basic_take_profit = self.take_profit_pct
            
            # 신호 강도 기반 조정
            strength_adjustment = basic_take_profit * (1 + signal_strength)
            
            # 리스크 대비 수익 비율 (Risk-Reward Ratio)
            risk_reward_ratio = 2.0  # 2:1 비율
            stop_loss_distance = self.stop_loss_pct
            take_profit_distance = stop_loss_distance * risk_reward_ratio
            
            # 최종 테이크프로핏 거리 결정
            final_take_profit_distance = min(strength_adjustment, take_profit_distance)
            
            if side == 'buy':
                take_profit_price = entry_price * (1 + final_take_profit_distance)
            else:  # sell
                take_profit_price = entry_price * (1 - final_take_profit_distance)
            
            logger.debug(f"테이크프로핏 계산: {symbol} {side} - {take_profit_price:.6f}")
            return take_profit_price
        except Exception as e:
            logger.error(f"테이크프로핏 계산 실패: {e}")
            return entry_price
    
    @log_execution_time
    def update_position_risk(self, symbol: str, current_price: float, 
                           unrealized_pnl: float = 0.0):
        """포지션 리스크 업데이트"""
        try:
            if symbol not in self.positions:
                return
            
            position = self.positions[symbol]
            position['current_price'] = current_price
            position['unrealized_pnl'] = unrealized_pnl
            position['last_update'] = datetime.now()
            
            # 스탑로스 체크
            if self._should_stop_loss(position, current_price):
                self.risk_alerts.append({
                    'type': 'stop_loss',
                    'symbol': symbol,
                    'message': f"스탑로스 발생: {symbol} 현재가 {current_price:.6f}",
                    'timestamp': datetime.now()
                })
            
            # 테이크프로핏 체크
            if self._should_take_profit(position, current_price):
                self.risk_alerts.append({
                    'type': 'take_profit',
                    'symbol': symbol,
                    'message': f"테이크프로핏 발생: {symbol} 현재가 {current_price:.6f}",
                    'timestamp': datetime.now()
                })
            
            # 포지션 타임아웃 체크
            if self._is_position_timeout(position):
                self.risk_alerts.append({
                    'type': 'timeout',
                    'symbol': symbol,
                    'message': f"포지션 타임아웃: {symbol} 보유시간 초과",
                    'timestamp': datetime.now()
                })
            
        except Exception as e:
            logger.error(f"포지션 리스크 업데이트 실패: {e}")
    
    def _should_stop_loss(self, position: Dict[str, Any], current_price: float) -> bool:
        """스탑로스 여부 확인"""
        try:
            side = position['side']
            stop_loss_price = position.get('stop_loss_price', 0)
            
            if stop_loss_price == 0:
                return False
            
            if side == 'buy':
                return current_price <= stop_loss_price
            else:  # sell
                return current_price >= stop_loss_price
        except Exception as e:
            logger.error(f"스탑로스 확인 실패: {e}")
            return False
    
    def _should_take_profit(self, position: Dict[str, Any], current_price: float) -> bool:
        """테이크프로핏 여부 확인"""
        try:
            side = position['side']
            take_profit_price = position.get('take_profit_price', 0)
            
            if take_profit_price == 0:
                return False
            
            if side == 'buy':
                return current_price >= take_profit_price
            else:  # sell
                return current_price <= take_profit_price
        except Exception as e:
            logger.error(f"테이크프로핏 확인 실패: {e}")
            return False
    
    def _is_position_timeout(self, position: Dict[str, Any]) -> bool:
        """포지션 타임아웃 확인"""
        try:
            entry_time = position.get('entry_time', datetime.now())
            timeout_threshold = timedelta(hours=self.position_timeout_hours)
            return datetime.now() - entry_time > timeout_threshold
        except Exception as e:
            logger.error(f"포지션 타임아웃 확인 실패: {e}")
            return False
    
    def update_daily_pnl(self, realized_pnl: float):
        """일일 손익 업데이트"""
        try:
            self.daily_pnl += realized_pnl
            logger.debug(f"일일 손익 업데이트: {self.daily_pnl:.2f}")
        except Exception as e:
            logger.error(f"일일 손익 업데이트 실패: {e}")
    
    def update_drawdown(self, current_balance: float):
        """드로우다운 업데이트"""
        try:
            if current_balance > self.peak_balance:
                self.peak_balance = current_balance
                self.current_drawdown = 0.0
            else:
                self.current_drawdown = (self.peak_balance - current_balance) / self.peak_balance
            
            logger.debug(f"드로우다운 업데이트: {self.current_drawdown:.2%}")
        except Exception as e:
            logger.error(f"드로우다운 업데이트 실패: {e}")
    
    def add_position(self, symbol: str, side: str, size: float, price: float, 
                    exchange_type: str = 'spot', stop_loss_price: float = 0, 
                    take_profit_price: float = 0):
        """포지션 추가"""
        try:
            self.positions[symbol] = {
                'symbol': symbol,
                'side': side,
                'size': size,
                'price': price,
                'exchange_type': exchange_type,
                'stop_loss_price': stop_loss_price,
                'take_profit_price': take_profit_price,
                'entry_time': datetime.now(),
                'unrealized_pnl': 0.0,
                'current_price': price
            }
            logger.info(f"포지션 추가: {symbol} {side} {size} @ {price}")
        except Exception as e:
            logger.error(f"포지션 추가 실패: {e}")
    
    def remove_position(self, symbol: str):
        """포지션 제거"""
        try:
            if symbol in self.positions:
                del self.positions[symbol]
                logger.info(f"포지션 제거: {symbol}")
        except Exception as e:
            logger.error(f"포지션 제거 실패: {e}")
    
    def get_risk_alerts(self) -> List[Dict[str, Any]]:
        """리스크 알림 조회"""
        try:
            alerts = self.risk_alerts.copy()
            self.risk_alerts.clear()  # 조회 후 클리어
            return alerts
        except Exception as e:
            logger.error(f"리스크 알림 조회 실패: {e}")
            return []
    
    def get_risk_summary(self) -> Dict[str, Any]:
        """리스크 요약 정보"""
        try:
            total_position_value = sum(
                pos['size'] * pos['current_price'] for pos in self.positions.values()
            )
            
            total_unrealized_pnl = sum(
                pos['unrealized_pnl'] for pos in self.positions.values()
            )
            
            short_position_value = sum(
                pos['size'] * pos['current_price'] for pos in self.positions.values()
                if pos['side'] == 'sell' and pos['exchange_type'] == 'futures'
            )
            
            return {
                'daily_pnl': self.daily_pnl,
                'current_drawdown': self.current_drawdown,
                'peak_balance': self.peak_balance,
                'total_positions': len(self.positions),
                'total_position_value': total_position_value,
                'total_unrealized_pnl': total_unrealized_pnl,
                'short_position_value': short_position_value,
                'risk_alerts_count': len(self.risk_alerts)
            }
        except Exception as e:
            logger.error(f"리스크 요약 정보 조회 실패: {e}")
            return {}
    
    def reset_daily_metrics(self):
        """일일 메트릭 초기화"""
        try:
            self.daily_pnl = 0.0
            logger.info("일일 메트릭 초기화 완료")
        except Exception as e:
            logger.error(f"일일 메트릭 초기화 실패: {e}")
    
    def emergency_stop(self, reason: str = "Emergency stop triggered"):
        """비상 정지"""
        try:
            self.risk_alerts.append({
                'type': 'emergency_stop',
                'symbol': 'ALL',
                'message': f"비상 정지: {reason}",
                'timestamp': datetime.now()
            })
            logger.critical(f"비상 정지 발생: {reason}")
        except Exception as e:
            logger.error(f"비상 정지 실패: {e}")

    def real_time_risk_monitoring(self) -> Dict[str, Any]:
        """실시간 리스크 모니터링 및 자동 대응"""
        try:
            monitoring_result = {
                'risk_level': 'low',  # low, medium, high, critical
                'actions_taken': [],
                'warnings': [],
                'portfolio_health': {},
                'recommendations': []
            }
            
            # 1. 포지션별 실시간 손익 추적
            position_risks = self._monitor_position_risks()
            
            # 2. 포트폴리오 상관관계 리스크 체크
            correlation_risks = self._monitor_correlation_risks()
            
            # 3. 시장 체제 변화 감지
            regime_changes = self._detect_regime_changes()
            
            # 4. 유동성 리스크 모니터링
            liquidity_risks = self._monitor_liquidity_risks()
            
            # 5. 레버리지 및 마진 리스크 체크
            leverage_risks = self._monitor_leverage_risks()
            
            # 6. 종합 리스크 레벨 결정
            overall_risk = self._calculate_overall_risk_level([
                position_risks, correlation_risks, regime_changes, 
                liquidity_risks, leverage_risks
            ])
            
            monitoring_result['risk_level'] = overall_risk['level']
            monitoring_result['actions_taken'] = overall_risk['actions']
            monitoring_result['warnings'] = overall_risk['warnings']
            monitoring_result['recommendations'] = overall_risk['recommendations']
            
            # 7. 자동 대응 실행
            if overall_risk['level'] in ['high', 'critical']:
                self._execute_automatic_responses(overall_risk)
            
            return monitoring_result
            
        except Exception as e:
            logger.error(f"실시간 리스크 모니터링 실패: {e}")
            return {'risk_level': 'unknown', 'actions_taken': [], 'warnings': [str(e)]}

    def _monitor_position_risks(self) -> Dict[str, Any]:
        """포지션별 리스크 모니터링"""
        try:
            position_alerts = []
            actions_taken = []
            
            for symbol, position in self.positions.items():
                current_price = position.get('current_price', position['price'])
                entry_price = position['price']
                size = position['size']
                side = position['side']
                
                # 미실현 손익 계산
                if side == 'buy':
                    unrealized_pnl_pct = (current_price - entry_price) / entry_price
                else:
                    unrealized_pnl_pct = (entry_price - current_price) / entry_price
                
                # 1. 동적 스탑로스 조정
                if unrealized_pnl_pct > 0.05:  # 5% 수익시
                    new_stop_loss = self._update_trailing_stop(position, profit_ratio=0.02)
                    if new_stop_loss:
                        actions_taken.append(f"{symbol}: 트레일링 스탑 업데이트 → {new_stop_loss:.6f}")
                
                # 2. 큰 손실 경고
                if unrealized_pnl_pct < -0.08:  # 8% 손실시
                    position_alerts.append({
                        'symbol': symbol,
                        'type': 'large_loss',
                        'pnl_pct': unrealized_pnl_pct,
                        'message': f"{symbol} 큰 손실 발생: {unrealized_pnl_pct:.2%}"
                    })
                
                # 3. 포지션 타임아웃 체크
                entry_time = position.get('entry_time', datetime.now())
                holding_hours = (datetime.now() - entry_time).total_seconds() / 3600
                
                if holding_hours > self.position_timeout_hours:
                    position_alerts.append({
                        'symbol': symbol,
                        'type': 'timeout',
                        'holding_hours': holding_hours,
                        'message': f"{symbol} 포지션 타임아웃: {holding_hours:.1f}시간 보유"
                    })
            
            return {
                'risk_level': 'high' if len(position_alerts) > 2 else 'medium' if position_alerts else 'low',
                'alerts': position_alerts,
                'actions': actions_taken
            }
            
        except Exception as e:
            logger.error(f"포지션 리스크 모니터링 실패: {e}")
            return {'risk_level': 'unknown', 'alerts': [], 'actions': []}

    def _monitor_correlation_risks(self) -> Dict[str, Any]:
        """포트폴리오 상관관계 리스크 모니터링"""
        try:
            if len(self.positions) < 2:
                return {'risk_level': 'low', 'correlation': 0.0, 'actions': []}
            
            # 포지션들 간 상관관계 계산
            total_correlation_risk = 0.0
            position_count = 0
            actions_taken = []
            
            symbols = list(self.positions.keys())
            for i, symbol1 in enumerate(symbols):
                for symbol2 in symbols[i+1:]:
                    correlation = self._estimate_correlation(symbol1, symbol2)
                    
                    # 포지션 가중치 고려
                    weight1 = abs(self.positions[symbol1]['size'] * self.positions[symbol1]['current_price'])
                    weight2 = abs(self.positions[symbol2]['size'] * self.positions[symbol2]['current_price'])
                    weighted_correlation = correlation * (weight1 + weight2)
                    
                    total_correlation_risk += weighted_correlation
                    position_count += 1
            
            avg_correlation = total_correlation_risk / position_count if position_count > 0 else 0
            
            # 상관관계가 너무 높으면 포지션 축소
            if avg_correlation > 0.8:
                actions_taken.append("높은 상관관계 감지 - 포지션 축소 권장")
                return {'risk_level': 'high', 'correlation': avg_correlation, 'actions': actions_taken}
            elif avg_correlation > 0.6:
                return {'risk_level': 'medium', 'correlation': avg_correlation, 'actions': actions_taken}
            else:
                return {'risk_level': 'low', 'correlation': avg_correlation, 'actions': actions_taken}
                
        except Exception as e:
            logger.error(f"상관관계 리스크 모니터링 실패: {e}")
            return {'risk_level': 'unknown', 'correlation': 0.0, 'actions': []}

    def _detect_regime_changes(self) -> Dict[str, Any]:
        """시장 체제 변화 감지"""
        try:
            # 실제 구현시에는 최근 가격 데이터를 기반으로 체제 변화를 감지
            # 현재는 시뮬레이션
            
            import random
            regimes = ['trending', 'ranging', 'volatile', 'neutral']
            current_regime = random.choice(regimes)
            
            # 이전 체제와 비교 (실제로는 저장된 값과 비교)
            previous_regime = getattr(self, '_previous_regime', 'neutral')
            
            actions_taken = []
            if current_regime != previous_regime:
                actions_taken.append(f"시장 체제 변화 감지: {previous_regime} → {current_regime}")
                self._previous_regime = current_regime
                
                # 체제 변화에 따른 리스크 레벨 조정
                if current_regime == 'volatile':
                    return {'risk_level': 'high', 'regime': current_regime, 'actions': actions_taken}
                elif current_regime == 'ranging':
                    return {'risk_level': 'medium', 'regime': current_regime, 'actions': actions_taken}
            
            return {'risk_level': 'low', 'regime': current_regime, 'actions': actions_taken}
            
        except Exception as e:
            logger.error(f"체제 변화 감지 실패: {e}")
            return {'risk_level': 'unknown', 'regime': 'neutral', 'actions': []}

    def _monitor_liquidity_risks(self) -> Dict[str, Any]:
        """유동성 리스크 모니터링"""
        try:
            liquidity_alerts = []
            
            for symbol, position in self.positions.items():
                # 간단한 유동성 체크 (실제로는 주문장 깊이 분석 필요)
                position_size = abs(position['size'] * position['current_price'])
                
                # 대형 포지션은 유동성 리스크가 높음
                if position_size > 10000:  # $10,000 이상
                    liquidity_alerts.append({
                        'symbol': symbol,
                        'position_size': position_size,
                        'risk': 'high_impact'
                    })
                elif position_size > 5000:  # $5,000 이상
                    liquidity_alerts.append({
                        'symbol': symbol,
                        'position_size': position_size,
                        'risk': 'medium_impact'
                    })
            
            if len(liquidity_alerts) > 0:
                risk_level = 'high' if any(alert['risk'] == 'high_impact' for alert in liquidity_alerts) else 'medium'
            else:
                risk_level = 'low'
            
            return {'risk_level': risk_level, 'alerts': liquidity_alerts, 'actions': []}
            
        except Exception as e:
            logger.error(f"유동성 리스크 모니터링 실패: {e}")
            return {'risk_level': 'unknown', 'alerts': [], 'actions': []}

    def _monitor_leverage_risks(self) -> Dict[str, Any]:
        """레버리지 및 마진 리스크 모니터링"""
        try:
            total_position_value = 0
            futures_position_value = 0
            
            for position in self.positions.values():
                position_value = abs(position['size'] * position['current_price'])
                total_position_value += position_value
                
                if position.get('exchange_type') == 'futures':
                    futures_position_value += position_value
            
            # 전체 잔고 대비 포지션 비중 (가상의 잔고 사용)
            estimated_balance = 10000  # 실제로는 현재 잔고를 가져와야 함
            total_exposure_ratio = total_position_value / estimated_balance
            
            actions_taken = []
            
            if total_exposure_ratio > 0.8:  # 80% 이상 노출
                actions_taken.append("높은 포지션 노출도 감지 - 레버리지 축소 필요")
                return {'risk_level': 'critical', 'exposure_ratio': total_exposure_ratio, 'actions': actions_taken}
            elif total_exposure_ratio > 0.6:  # 60% 이상 노출
                actions_taken.append("중간 수준 포지션 노출도")
                return {'risk_level': 'medium', 'exposure_ratio': total_exposure_ratio, 'actions': actions_taken}
            else:
                return {'risk_level': 'low', 'exposure_ratio': total_exposure_ratio, 'actions': actions_taken}
                
        except Exception as e:
            logger.error(f"레버리지 리스크 모니터링 실패: {e}")
            return {'risk_level': 'unknown', 'exposure_ratio': 0.0, 'actions': []}

    def _calculate_overall_risk_level(self, risk_components: List[Dict[str, Any]]) -> Dict[str, Any]:
        """종합 리스크 레벨 계산"""
        try:
            risk_scores = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4, 'unknown': 2}
            
            total_score = 0
            valid_components = 0
            all_actions = []
            all_warnings = []
            recommendations = []
            
            for component in risk_components:
                if 'risk_level' in component:
                    total_score += risk_scores.get(component['risk_level'], 2)
                    valid_components += 1
                
                if 'actions' in component:
                    all_actions.extend(component['actions'])
                
                if 'alerts' in component:
                    all_warnings.extend([alert.get('message', str(alert)) for alert in component['alerts']])
            
            if valid_components == 0:
                return {'level': 'unknown', 'actions': [], 'warnings': [], 'recommendations': []}
            
            avg_score = total_score / valid_components
            
            # 점수를 레벨로 변환
            if avg_score >= 3.5:
                risk_level = 'critical'
                recommendations.extend([
                    "즉시 포지션 축소 검토",
                    "레버리지 대폭 감소",
                    "상관관계 높은 포지션 정리"
                ])
            elif avg_score >= 2.5:
                risk_level = 'high'
                recommendations.extend([
                    "포지션 크기 조정 검토",
                    "스탑로스 강화",
                    "시장 모니터링 강화"
                ])
            elif avg_score >= 1.5:
                risk_level = 'medium'
                recommendations.append("현재 리스크 모니터링 지속")
            else:
                risk_level = 'low'
                recommendations.append("안정적인 리스크 수준 유지")
            
            return {
                'level': risk_level,
                'score': avg_score,
                'actions': all_actions,
                'warnings': all_warnings,
                'recommendations': recommendations
            }
            
        except Exception as e:
            logger.error(f"종합 리스크 레벨 계산 실패: {e}")
            return {'level': 'unknown', 'actions': [], 'warnings': [str(e)], 'recommendations': []}

    def _execute_automatic_responses(self, risk_assessment: Dict[str, Any]):
        """자동 대응 실행"""
        try:
            risk_level = risk_assessment['level']
            
            if risk_level == 'critical':
                # 위험 포지션 자동 축소
                self._reduce_risky_positions(reduction_ratio=0.5)
                logger.critical("위험 수준 최고 - 포지션 50% 자동 축소 실행")
                
            elif risk_level == 'high':
                # 스탑로스 강화
                self._tighten_stop_losses()
                logger.warning("위험 수준 높음 - 스탑로스 강화 실행")
                
        except Exception as e:
            logger.error(f"자동 대응 실행 실패: {e}")

    def _update_trailing_stop(self, position: Dict[str, Any], profit_ratio: float = 0.02) -> Optional[float]:
        """트레일링 스탑 업데이트"""
        try:
            current_price = position.get('current_price', position['price'])
            side = position['side']
            
            # 트레일링 스탑 계산
            if side == 'buy':
                new_stop_loss = current_price * (1 - profit_ratio)
                current_stop_loss = position.get('stop_loss_price', 0)
                
                # 기존 스탑로스보다 높을 때만 업데이트
                if new_stop_loss > current_stop_loss:
                    position['stop_loss_price'] = new_stop_loss
                    return new_stop_loss
            else:  # sell
                new_stop_loss = current_price * (1 + profit_ratio)
                current_stop_loss = position.get('stop_loss_price', float('inf'))
                
                # 기존 스탑로스보다 낮을 때만 업데이트
                if new_stop_loss < current_stop_loss:
                    position['stop_loss_price'] = new_stop_loss
                    return new_stop_loss
            
            return None
            
        except Exception as e:
            logger.error(f"트레일링 스탑 업데이트 실패: {e}")
            return None

    def _reduce_risky_positions(self, reduction_ratio: float = 0.3):
        """위험 포지션 축소"""
        try:
            for symbol, position in self.positions.items():
                current_price = position.get('current_price', position['price'])
                entry_price = position['price']
                side = position['side']
                
                # 손실 포지션 우선 축소
                if side == 'buy':
                    pnl_pct = (current_price - entry_price) / entry_price
                else:
                    pnl_pct = (entry_price - current_price) / entry_price
                
                if pnl_pct < -0.05:  # 5% 이상 손실 포지션
                    original_size = position['size']
                    new_size = original_size * (1 - reduction_ratio)
                    position['size'] = new_size
                    
                    logger.info(f"포지션 자동 축소: {symbol} {original_size:.6f} → {new_size:.6f}")
                    
        except Exception as e:
            logger.error(f"위험 포지션 축소 실패: {e}")

    def _tighten_stop_losses(self):
        """스탑로스 강화"""
        try:
            for symbol, position in self.positions.items():
                current_price = position.get('current_price', position['price'])
                side = position['side']
                
                # 더 엄격한 스탑로스 설정
                if side == 'buy':
                    new_stop_loss = current_price * 0.97  # 3% 스탑로스
                else:
                    new_stop_loss = current_price * 1.03  # 3% 스탑로스
                
                position['stop_loss_price'] = new_stop_loss
                logger.info(f"스탑로스 강화: {symbol} → {new_stop_loss:.6f}")
                
        except Exception as e:
            logger.error(f"스탑로스 강화 실패: {e}")