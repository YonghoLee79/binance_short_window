#!/usr/bin/env python3
"""
현물 + 선물 하이브리드 포트폴리오 전략
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import logger


class HybridPortfolioStrategy:
    """현물 + 선물 하이브리드 포트폴리오 전략 클래스"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # 포트폴리오 할당
        self.spot_allocation = config.get('spot_allocation', 0.4)  # 현물 40%
        self.futures_allocation = config.get('futures_allocation', 0.6)  # 선물 60%
        
        # 전략 설정 (매우 적극적 거래를 위한 초 민감 설정)
        self.arbitrage_threshold = config.get('arbitrage_threshold', 0.0005)  # 0.05% 프리미엄 (초민감)
        self.rebalance_threshold = config.get('REBALANCE_THRESHOLD', 0.03)  # 3% 편차시 리밸런싱
        self.rebalance_interval_minutes = config.get('REBALANCE_INTERVAL_MINUTES', 15)  # 15분 간격
        self.auto_transfer_enabled = config.get('AUTO_TRANSFER_ENABLED', True)  # 자동 이체 활성화
        self.balance_check_before_trade = config.get('BALANCE_CHECK_BEFORE_TRADE', True)  # 거래 전 잔고 확인
        self.max_leverage = config.get('max_leverage', 5)  # 최대 5배 레버리지
        
        # 리스크 관리
        self.max_position_size = config.get('max_position_size', 0.2)  # 단일 포지션 최대 20%
        self.correlation_limit = config.get('correlation_limit', 0.7)  # 상관관계 한계
        
        # 상태 추적
        self.current_positions = {'spot': {}, 'futures': {}}
        self.portfolio_history = []
        self.last_rebalance = datetime.now()
        
        # 선물 거래 지원 심볼 (바이낸스 기준)
        self.futures_supported_symbols = [
            'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'XRP/USDT', 
            'SOL/USDT', 'ADA/USDT', 'AVAX/USDT', 'LINK/USDT', 
            'TRX/USDT'  # LTC, DOT, MATIC 제외
        ]
        
        # 현물 심볼 -> 선물 심볼 매핑 (바이낸스 USDT-M 선물 형식)
        self.futures_symbol_mapping = {
            'BTC/USDT': 'BTC/USDT:USDT',
            'ETH/USDT': 'ETH/USDT:USDT', 
            'BNB/USDT': 'BNB/USDT:USDT',
            'XRP/USDT': 'XRP/USDT:USDT',
            'SOL/USDT': 'SOL/USDT:USDT',
            'ADA/USDT': 'ADA/USDT:USDT',
            'AVAX/USDT': 'AVAX/USDT:USDT',
            'LINK/USDT': 'LINK/USDT:USDT',
            'TRX/USDT': 'TRX/USDT:USDT'
        }
        
        logger.info("하이브리드 포트폴리오 전략 초기화 완료")
    
    def analyze_market_opportunity(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """시장 기회 분석"""
        try:
            opportunities = {
                'arbitrage': [],
                'trend_following': [],
                'hedging': [],
                'momentum': []
            }
            
            for symbol in market_data.keys():
                if symbol not in market_data:
                    continue
                
                data = market_data[symbol]
                spot_price = data.get('spot_ticker', {}).get('last', 0)
                futures_price = data.get('futures_ticker', {}).get('last', 0)
                
                # Null 체크 및 타입 검증
                if spot_price is None:
                    spot_price = 0
                if futures_price is None:
                    futures_price = 0
                
                # 숫자가 아닌 경우 0으로 설정
                try:
                    spot_price = float(spot_price)
                    futures_price = float(futures_price)
                except (TypeError, ValueError):
                    spot_price = 0
                    futures_price = 0
                
                if spot_price <= 0 or futures_price <= 0:
                    logger.debug(f"[DEBUG] 가격 데이터 부족으로 스킵: {symbol} - spot: {spot_price}, futures: {futures_price}")
                    continue
                
                logger.debug(f"[DEBUG] 처리 중인 심볼: {symbol} - spot: {spot_price}, futures: {futures_price}")
                
                # 1. 아비트라지 기회 분석
                premium = (futures_price - spot_price) / spot_price
                if abs(premium) > self.arbitrage_threshold:
                    opportunities['arbitrage'].append({
                        'symbol': symbol,
                        'premium': premium,
                        'spot_price': spot_price,
                        'futures_price': futures_price,
                        'opportunity_type': 'long_spot_short_futures' if premium > 0 else 'short_spot_long_futures',
                        'expected_profit': abs(premium),
                        'confidence': min(abs(premium) / self.arbitrage_threshold, 1.0)
                    })
                
                # 2. 트렌드 추종 기회
                spot_signals = data.get('spot_signals', {})
                futures_signals = data.get('futures_signals', {})
                
                # 시그널 강도 초기화 (범위 밖에서도 사용되므로)
                spot_strength = 0
                futures_strength = 0
                
                if spot_signals and futures_signals:
                    spot_strength = spot_signals.get('combined_signal', 0)
                    futures_strength = futures_signals.get('combined_signal', 0)
                    
                    # Null 체크 및 타입 검증
                    if spot_strength is None:
                        spot_strength = 0
                    if futures_strength is None:
                        futures_strength = 0
                    
                    try:
                        spot_strength = float(spot_strength)
                        futures_strength = float(futures_strength)
                    except (TypeError, ValueError):
                        spot_strength = 0
                        futures_strength = 0
                    
                    # 현물과 선물 신호가 같은 방향이면 트렌드 추종 (매우 민감하게)
                    if abs(spot_strength) > 0.1 and abs(futures_strength) > 0.1:
                        if (spot_strength > 0 and futures_strength > 0) or (spot_strength < 0 and futures_strength < 0):
                            opportunities['trend_following'].append({
                                'symbol': symbol,
                                'direction': 'bullish' if spot_strength > 0 else 'bearish',
                                'spot_strength': spot_strength,
                                'futures_strength': futures_strength,
                                'confidence': (abs(spot_strength) + abs(futures_strength)) / 2
                            })
                
                # 3. 헤징 기회 (현물 보유시 선물로 헤지) - 매우 민감하게
                current_spot_position = self.current_positions['spot'].get(symbol, {})
                if current_spot_position and abs(futures_strength) > 0.2:
                    if (current_spot_position.get('side') == 'buy' and futures_strength < -0.2) or \
                       (current_spot_position.get('side') == 'sell' and futures_strength > 0.2):
                        opportunities['hedging'].append({
                            'symbol': symbol,
                            'hedge_type': 'protective_short' if current_spot_position.get('side') == 'buy' else 'protective_long',
                            'spot_position': current_spot_position,
                            'futures_strength': futures_strength,
                            'confidence': abs(futures_strength)
                        })
                
                # 4. 모멘텀 기회 (급격한 가격 변동 활용)
                spot_indicators = data.get('spot_indicators', {})
                futures_indicators = data.get('futures_indicators', {})
                
                if spot_indicators and futures_indicators:
                    spot_rsi = spot_indicators.get('rsi', {}).get('current', 50)
                    futures_rsi = futures_indicators.get('rsi', {}).get('current', 50)
                    
                    # Null 체크 및 타입 검증
                    if spot_rsi is None:
                        spot_rsi = 50
                    if futures_rsi is None:
                        futures_rsi = 50
                    
                    try:
                        spot_rsi = float(spot_rsi)
                        futures_rsi = float(futures_rsi)
                    except (TypeError, ValueError):
                        spot_rsi = 50
                        futures_rsi = 50
                    
                    # RSI 극값에서 모멘텀 기회 (매우 민감하게)
                    if (spot_rsi < 40 and futures_rsi < 40) or (spot_rsi > 60 and futures_rsi > 60):
                        opportunities['momentum'].append({
                            'symbol': symbol,
                            'type': 'oversold_bounce' if spot_rsi < 30 else 'overbought_correction',
                            'spot_rsi': spot_rsi,
                            'futures_rsi': futures_rsi,
                            'confidence': abs(50 - spot_rsi) / 50
                        })
            
            return opportunities
            
        except Exception as e:
            logger.error(f"시장 기회 분석 실패: {e}")
            return {'arbitrage': [], 'trend_following': [], 'hedging': [], 'momentum': []}
    
    def generate_portfolio_signals(self, opportunities: Dict[str, Any], 
                                 portfolio_state: Dict[str, Any], 
                                 market_data: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """포트폴리오 전략 신호 생성"""
        try:
            signals = []
            
            # 실제 사용 가능한 잔고 사용
            spot_free_balance = portfolio_state.get('spot_free_balance', 0)
            futures_free_balance = portfolio_state.get('futures_free_balance', 0)
            
            logger.info(f"사용 가능한 잔고 - 현물: ${spot_free_balance:.2f}, 선물: ${futures_free_balance:.2f}")
            
            # 잔고가 부족하면 신호 생성 중단
            if spot_free_balance < 5 and futures_free_balance < 5:  # 바이낸스 최소 $5 필요
                logger.warning(f"거래 가능한 잔고가 부족합니다 - 현물: ${spot_free_balance:.2f}, 선물: ${futures_free_balance:.2f}")
                return []
            
            # 1. 아비트라지 신호 (최우선)
            arbitrage_opportunities = opportunities.get('arbitrage', [])
            logger.info(f"아비트라지 기회 분석: {len(arbitrage_opportunities)}개 발견")
            
            for i, arb in enumerate(sorted(arbitrage_opportunities, key=lambda x: x['expected_profit'], reverse=True)):
                logger.info(f"아비트라지 #{i+1}: {arb['symbol']} - 신뢰도: {arb['confidence']:.3f}, 수익률: {arb['expected_profit']:.4f}")
                
                if arb['confidence'] >= 0.25:  # 임계값을 25% 이상으로 수정 (경계값 포함)
                    # 사용 가능한 잔고에 맞춰 동적 조정
                    if spot_free_balance < 5:
                        max_spot_amount = 0  # 잔고 부족 시 현물 거래 중단
                    else:
                        max_spot_amount = min(spot_free_balance * 0.8, 100)  # 잔고의 80% 또는 최대 $100
                    
                    if futures_free_balance < 5:
                        max_futures_amount = 0  # 잔고 부족 시 선물 거래 중단
                    else:
                        max_futures_amount = min(futures_free_balance * 0.8, 100)  # 잔고의 80% 또는 최대 $100
                    
                    logger.debug(f"계산된 투자 금액 - 현물: ${max_spot_amount:.2f}, 선물: ${max_futures_amount:.2f}")
                    
                    # 최소 거래 금액 확인 ($5 이상으로 낮춤)
                    min_trade_amount = 5.0
                    if max_spot_amount < min_trade_amount and max_futures_amount < min_trade_amount:
                        logger.warning(f"투자 금액 부족으로 스킵: {arb['symbol']} - 필요: ${min_trade_amount}, 가능: ${max(max_spot_amount, max_futures_amount):.2f}")
                        continue
                    
                    # 실제 거래 가능한 수량 계산 (최소 정밀도 준수)
                    spot_quantity = self._calculate_safe_quantity(arb['symbol'], max_spot_amount, arb['spot_price'], 'spot')
                    futures_quantity = self._calculate_safe_quantity(arb['symbol'], max_futures_amount, arb['futures_price'], 'futures')
                    
                    logger.debug(f"계산된 수량 - 현물: {spot_quantity:.6f}, 선물: {futures_quantity:.6f}")
                    
                    # 수량이 0이면 거래 불가
                    if spot_quantity <= 0 or futures_quantity <= 0:
                        logger.warning(f"수량 부족으로 아비트라지 기회 스킵: {arb['symbol']} - 현물: {spot_quantity:.6f}, 선물: {futures_quantity:.6f}")
                        continue
                    
                    logger.info(f"아비트라지 신호 생성 중: {arb['symbol']} - 현물: {spot_quantity:.6f}, 선물: {futures_quantity:.6f}")
                else:
                    logger.debug(f"신뢰도 부족으로 스킵: {arb['symbol']} - 신뢰도: {arb['confidence']:.3f} < 0.3")
                    
                    # 선물 지원 여부 확인
                    if arb['symbol'] in self.futures_supported_symbols:
                        futures_symbol = self.futures_symbol_mapping.get(arb['symbol'], arb['symbol'])
                        
                        if arb['opportunity_type'] == 'long_spot_short_futures':
                            signals.extend([
                                {
                                    'strategy': 'arbitrage',
                                    'symbol': arb['symbol'],
                                    'exchange_type': 'spot',
                                    'action': 'buy',
                                    'size': spot_quantity,
                                    'confidence': arb['confidence'],
                                    'expected_return': arb['expected_profit'],
                                    'priority': 1
                                },
                                {
                                    'strategy': 'arbitrage',
                                    'symbol': futures_symbol,  # 올바른 선물 심볼 사용
                                    'exchange_type': 'futures',
                                    'action': 'sell',
                                    'size': futures_quantity,
                                    'confidence': arb['confidence'],
                                    'expected_return': arb['expected_profit'],
                                    'priority': 1
                                }
                            ])
                        else:
                            signals.extend([
                                {
                                    'strategy': 'arbitrage',
                                    'symbol': arb['symbol'],
                                    'exchange_type': 'spot',
                                    'action': 'sell',
                                    'size': spot_quantity,
                                    'confidence': arb['confidence'],
                                    'expected_return': arb['expected_profit'],
                                    'priority': 1
                                },
                                {
                                    'strategy': 'arbitrage',
                                    'symbol': futures_symbol,  # 올바른 선물 심볼 사용
                                    'exchange_type': 'futures',
                                    'action': 'buy',
                                    'size': futures_quantity,
                                    'confidence': arb['confidence'],
                                    'expected_return': arb['expected_profit'],
                                    'priority': 1
                                }
                            ])
                    else:
                        # 선물 지원 안되면 현물만
                        signals.append({
                            'strategy': 'arbitrage_spot_only',
                            'symbol': arb['symbol'],
                            'exchange_type': 'spot',
                            'action': 'buy' if arb['opportunity_type'] == 'long_spot_short_futures' else 'sell',
                            'size': spot_quantity,
                            'confidence': arb['confidence'],
                            'expected_return': arb['expected_profit'],
                            'priority': 1
                        })
            
            # 2. 트렌드 추종 신호
            trend_opportunities = opportunities.get('trend_following', [])
            logger.info(f"트렌드 기회 상세 분석:")
            for i, trend in enumerate(sorted(trend_opportunities, key=lambda x: x['confidence'], reverse=True)):
                logger.info(f"  트렌드 #{i+1}: {trend['symbol']} - 신뢰도: {trend['confidence']:.3f}, 방향: {trend.get('direction', 'N/A')}")
                
                if trend['confidence'] >= 0.25:  # 임계값을 25% 이상으로 수정 (경계값 포함)
                    # 현재 가격 가져오기
                    symbol_data = market_data.get(trend['symbol'], {}) if market_data else {}
                    spot_price = symbol_data.get('spot_ticker', {}).get('last', 0)
                    futures_price = symbol_data.get('futures_ticker', {}).get('last', 0)
                    
                    if spot_price <= 0 or futures_price <= 0:
                        logger.warning(f"가격 정보 부족으로 트렌드 신호 스킵: {trend['symbol']}")
                        continue
                    
                    # 사용 가능한 잔고의 3%만 사용 (더 보수적)
                    max_spot_amount = spot_free_balance * 0.03
                    max_futures_amount = futures_free_balance * 0.03
                    
                    # 최소 거래 금액 확인
                    min_trade_amount = 5.0
                    if max_spot_amount < min_trade_amount and max_futures_amount < min_trade_amount:
                        continue
                    
                    spot_size = self._calculate_safe_quantity(trend['symbol'], max_spot_amount, spot_price, 'spot')
                    futures_size = self._calculate_safe_quantity(trend['symbol'], max_futures_amount, futures_price, 'futures')
                    
                    if spot_size <= 0:
                        continue
                    
                    # 트렌드 방향에 따른 거래 결정 (잔고 고려)
                    action = 'buy' if trend['direction'] == 'bullish' else 'sell'
                    
                    # 매도 시도 시 해당 코인 보유량 확인 (현재는 USDT만 보유하므로 매도 불가)
                    if action == 'sell':
                        # TODO: 실제 보유량 확인 로직 추가 필요
                        # 현재는 USDT만 보유하므로 매도 신호 스킵
                        logger.debug(f"매도 신호 스킵: {trend['symbol']} - 해당 코인 미보유")
                        continue
                    
                    # 현물 신호는 항상 추가
                    signals.append({
                        'strategy': 'trend_following',
                        'symbol': trend['symbol'],
                        'exchange_type': 'spot',
                        'action': action,
                        'size': spot_size,
                        'confidence': trend['confidence'],
                        'priority': 2
                    })
                    
                    # 선물 지원 시에만 선물 신호 추가
                    if trend['symbol'] in self.futures_supported_symbols and futures_size > 0:
                        futures_symbol = self.futures_symbol_mapping.get(trend['symbol'], trend['symbol'])
                        signals.append({
                            'strategy': 'trend_following',
                            'symbol': futures_symbol,  # 올바른 선물 심볼 사용
                            'exchange_type': 'futures',
                            'action': action,
                            'size': futures_size,
                            'confidence': trend['confidence'],
                            'priority': 2
                        })
            
            # 3. 헤징 신호
            for hedge in opportunities['hedging']:
                if hedge['confidence'] > 0.4:
                    spot_position = hedge['spot_position']
                    hedge_size = spot_position.get('size', 0) * 0.8  # 80% 헤지
                    
                    hedge_action = 'sell' if hedge['hedge_type'] == 'protective_short' else 'buy'
                    
                    signals.append({
                        'strategy': 'hedging',
                        'symbol': hedge['symbol'],
                        'exchange_type': 'futures',
                        'action': hedge_action,
                        'size': hedge_size,
                        'confidence': hedge['confidence'],
                        'priority': 3
                    })
            
            # 4. 모멘텀 신호 (소규모)
            for momentum in sorted(opportunities['momentum'], key=lambda x: x['confidence'], reverse=True):
                if momentum['confidence'] > 0.5:
                    # 현재 가격 가져오기
                    symbol_data = market_data.get(momentum['symbol'], {}) if market_data else {}
                    current_price = symbol_data.get('spot_ticker', {}).get('last', 0)
                    
                    if current_price <= 0:
                        continue
                    
                    # 가용 잔고의 2%만 사용 (매우 보수적)
                    max_momentum_amount = min(spot_free_balance, futures_free_balance) * 0.02
                    
                    if max_momentum_amount < 10:  # 최소 $10
                        continue
                    
                    if momentum['type'] == 'oversold_bounce':
                        # 과매도 반등 기대 - 롱 포지션
                        spot_quantity = self._calculate_safe_quantity(momentum['symbol'], max_momentum_amount, current_price, 'spot')
                        futures_quantity = self._calculate_safe_quantity(momentum['symbol'], max_momentum_amount, current_price, 'futures')
                        
                        if spot_quantity > 0:
                            signals.append({
                                'strategy': 'momentum',
                                'symbol': momentum['symbol'],
                                'exchange_type': 'spot',
                                'action': 'buy',
                                'size': spot_quantity,
                                'confidence': momentum['confidence'],
                                'priority': 4
                            })
                        
                        if futures_quantity > 0 and momentum['symbol'] in self.futures_supported_symbols:
                            futures_symbol = self.futures_symbol_mapping.get(momentum['symbol'], momentum['symbol'])
                            signals.append({
                                'strategy': 'momentum',
                                'symbol': futures_symbol,  # 올바른 선물 심볼 사용
                                'exchange_type': 'futures',
                                'action': 'buy',
                                'size': futures_quantity,
                                'confidence': momentum['confidence'],
                                'priority': 4
                            })
                    else:
                        # 과매수 조정 기대 - 숏 포지션 (선물만)
                        if momentum['symbol'] in self.futures_supported_symbols:
                            futures_quantity = self._calculate_safe_quantity(momentum['symbol'], max_momentum_amount, current_price, 'futures')
                            if futures_quantity > 0:
                                futures_symbol = self.futures_symbol_mapping.get(momentum['symbol'], momentum['symbol'])
                                signals.append({
                                    'strategy': 'momentum',
                                    'symbol': futures_symbol,  # 올바른 선물 심볼 사용
                                    'exchange_type': 'futures',
                                    'action': 'sell',
                                    'size': futures_quantity,
                                    'confidence': momentum['confidence'],
                                    'priority': 4
                                })
            
            # 우선순위별 정렬
            signals.sort(key=lambda x: x['priority'])
            
            return signals[:10]  # 최대 10개 신호만
            
        except Exception as e:
            logger.error(f"포트폴리오 신호 생성 실패: {e}")
            return []
    
    def check_rebalancing_needed(self, portfolio_state: Dict[str, Any]) -> bool:
        """리밸런싱 필요 여부 확인 - USDT 전용 포트폴리오 최적화"""
        try:
            total_balance = portfolio_state.get('total_balance', 0)
            spot_usdt = portfolio_state.get('spot_balance', 0)
            futures_usdt = portfolio_state.get('futures_balance', 0)
            
            # 최소 잔고 확인
            if total_balance <= 100:
                logger.debug(f"잔고가 너무 적어 리밸런싱 불필요: ${total_balance:.2f}")
                return False
            
            # USDT만 보유한 경우의 비율 계산
            current_spot_ratio = spot_usdt / total_balance
            current_futures_ratio = futures_usdt / total_balance
            
            spot_deviation = abs(current_spot_ratio - self.spot_allocation)
            futures_deviation = abs(current_futures_ratio - self.futures_allocation)
            
            # 시간 기반 리밸런싱 조건 개선 (설정 기반)
            time_passed = datetime.now() - self.last_rebalance
            time_threshold = timedelta(minutes=self.rebalance_interval_minutes)  # 설정에서 가져온 간격
            
            # 자동 이체가 활성화된 경우 더 적극적으로 리밸런싱
            if self.auto_transfer_enabled:
                adjusted_threshold = self.rebalance_threshold  # 원래 임계값 사용
                min_balance_for_rebalancing = 20  # 최소 $20
            else:
                adjusted_threshold = self.rebalance_threshold * 2  # 더 관대한 임계값
                min_balance_for_rebalancing = 200  # 최소 $200
            
            needs_rebalancing = (
                (spot_deviation > adjusted_threshold or futures_deviation > adjusted_threshold) and
                total_balance >= min_balance_for_rebalancing
            ) or (
                time_passed > time_threshold and 
                (spot_deviation > self.rebalance_threshold * 0.5)  # 시간 기반은 더 민감하게
            )
            
            if needs_rebalancing:
                logger.info(f"리밸런싱 필요: 현물비율 {current_spot_ratio:.2%} (목표: {self.spot_allocation:.2%}), "
                          f"선물비율 {current_futures_ratio:.2%} (목표: {self.futures_allocation:.2%})")
            else:
                logger.debug(f"리밸런싱 불필요: 편차 현물={spot_deviation:.1%}, 선물={futures_deviation:.1%}, "
                           f"경과시간={time_passed.total_seconds()/3600:.1f}시간")
            
            return needs_rebalancing
            
        except Exception as e:
            logger.error(f"리밸런싱 확인 실패: {e}")
            return False
    
    def generate_rebalancing_orders(self, portfolio_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """리밸런싱 주문 생성 - USDT 전용 포트폴리오 최적화"""
        try:
            orders = []
            total_balance = portfolio_state.get('total_balance', 0)
            spot_usdt = portfolio_state.get('spot_balance', 0)
            futures_usdt = portfolio_state.get('futures_balance', 0)
            
            # 최소 잔고 확인 ($100 이하면 리밸런싱 스킵)
            if total_balance < 100:
                logger.info(f"잔고가 너무 적어 리밸런싱 스킵: ${total_balance:.2f}")
                return []
            
            # USDT만 보유한 경우: 초기 자산 구매 전략
            if spot_usdt > 0 or futures_usdt > 0:
                # 현재 비율 계산
                current_spot_ratio = spot_usdt / total_balance
                current_futures_ratio = futures_usdt / total_balance
                
                # 목표 비율과 비교
                spot_deviation = abs(current_spot_ratio - self.spot_allocation)
                futures_deviation = abs(current_futures_ratio - self.futures_allocation)
                
                # 리밸런싱 필요성 확인
                if spot_deviation > self.rebalance_threshold or futures_deviation > self.rebalance_threshold:
                    logger.info(f"USDT 리밸런싱 필요: 현물 {current_spot_ratio:.2%}→{self.spot_allocation:.2%}, "
                              f"선물 {current_futures_ratio:.2%}→{self.futures_allocation:.2%}")
                    
                    # 초기 자산 구매 주문 생성 (USDT → 암호화폐)
                    initial_orders = self._generate_initial_purchase_orders(portfolio_state)
                    orders.extend(initial_orders)
                else:
                    logger.debug("USDT 비율이 목표 범위 내에 있음")
            else:
                logger.warning(f"비정상적인 잔고 상태: 현물=${spot_usdt:.2f}, 선물=${futures_usdt:.2f}")
            
            if orders:
                self.last_rebalance = datetime.now()
                logger.info(f"리밸런싱 주문 생성: {len(orders)}개")
            else:
                logger.debug("리밸런싱 주문 생성 조건에 미달")
            
            return orders
            
        except Exception as e:
            logger.error(f"리밸런싱 주문 생성 실패: {e}")
            return []
    
    def calculate_portfolio_metrics(self, portfolio_state: Dict[str, Any]) -> Dict[str, Any]:
        """포트폴리오 메트릭 계산"""
        try:
            total_balance = portfolio_state.get('total_balance', 0)
            spot_balance = portfolio_state.get('spot_balance', 0)
            futures_balance = portfolio_state.get('futures_balance', 0)
            
            metrics = {
                'total_value': total_balance,
                'spot_value': spot_balance,
                'futures_value': futures_balance,
                'spot_ratio': spot_balance / total_balance if total_balance > 0 else 0,
                'futures_ratio': futures_balance / total_balance if total_balance > 0 else 0,
                'target_spot_ratio': self.spot_allocation,
                'target_futures_ratio': self.futures_allocation,
                'rebalancing_needed': self.check_rebalancing_needed(portfolio_state),
                'last_rebalance': self.last_rebalance.isoformat(),
                'total_positions': len(self.current_positions['spot']) + len(self.current_positions['futures']),
                'spot_positions': len(self.current_positions['spot']),
                'futures_positions': len(self.current_positions['futures'])
            }
            
            # 편차 계산
            metrics['spot_deviation'] = abs(metrics['spot_ratio'] - self.spot_allocation)
            metrics['futures_deviation'] = abs(metrics['futures_ratio'] - self.futures_allocation)
            
            # 리스크 메트릭
            metrics['leverage_ratio'] = futures_balance / spot_balance if spot_balance > 0 else 0
            metrics['risk_level'] = 'low' if metrics['leverage_ratio'] < 1 else 'medium' if metrics['leverage_ratio'] < 2 else 'high'
            
            return metrics
            
        except Exception as e:
            logger.error(f"포트폴리오 메트릭 계산 실패: {e}")
            return {}
    
    def update_positions(self, symbol: str, exchange_type: str, position_data: Dict[str, Any]):
        """포지션 업데이트"""
        try:
            if exchange_type in ['spot', 'futures']:
                self.current_positions[exchange_type][symbol] = position_data
                logger.debug(f"포지션 업데이트: {exchange_type} {symbol}")
        except Exception as e:
            logger.error(f"포지션 업데이트 실패: {e}")
    
    def remove_position(self, symbol: str, exchange_type: str):
        """포지션 제거"""
        try:
            if exchange_type in ['spot', 'futures'] and symbol in self.current_positions[exchange_type]:
                del self.current_positions[exchange_type][symbol]
                logger.debug(f"포지션 제거: {exchange_type} {symbol}")
        except Exception as e:
            logger.error(f"포지션 제거 실패: {e}")
    
    def _calculate_safe_quantity(self, symbol: str, max_amount: float, price: float, exchange_type: str) -> float:
        """안전한 거래 수량 계산 (최소 정밀도 및 거래 금액 준수)"""
        try:
            if price <= 0 or max_amount <= 0:
                return 0.0
            
            # 심볼별 최소 거래 수량 설정 (바이낸스 기준)
            min_quantities = {
                'BTC/USDT': 0.00001,   # 0.00001 BTC
                'ETH/USDT': 0.0001,    # 0.0001 ETH
                'BNB/USDT': 0.001,     # 0.001 BNB
                'XRP/USDT': 0.1,       # 0.1 XRP
                'SOL/USDT': 0.001,     # 0.001 SOL
                'ADA/USDT': 0.1,       # 0.1 ADA
                'AVAX/USDT': 0.01,     # 0.01 AVAX
                'LINK/USDT': 0.01,     # 0.01 LINK
                'DOT/USDT': 0.01,      # 0.01 DOT
                'MATIC/USDT': 0.1,     # 0.1 MATIC
                'TRX/USDT': 1.0        # 1.0 TRX
            }
            
            # 최소 거래 금액 (바이낸스 최소 $5)
            min_notional = 5.0
            
            # 기본 최소 수량
            min_quantity = min_quantities.get(symbol, 0.001)
            
            # 가격 기준 최대 구매 가능 수량
            max_quantity = max_amount / price
            
            # 최소 수량 확인
            if max_quantity < min_quantity:
                logger.debug(f"최소 수량 미달: {symbol} - 필요: {min_quantity}, 가능: {max_quantity:.6f}")
                return 0.0
            
            # 최소 거래 금액 확인
            calculated_notional = max_quantity * price
            if calculated_notional < min_notional:
                logger.debug(f"최소 거래 금액 미달: {symbol} - 필요: ${min_notional}, 가능: ${calculated_notional:.2f}")
                return 0.0
            
            # 안전한 수량 계산 (최소 수량의 정수배로 반올림)
            safe_quantity = max(min_quantity, max_quantity)
            
            # 정밀도 조정 (소수점 자릿수 제한)
            if symbol in ['BTC/USDT']:
                safe_quantity = round(safe_quantity, 5)
            elif symbol in ['ETH/USDT', 'BNB/USDT', 'SOL/USDT']:
                safe_quantity = round(safe_quantity, 4)
            elif symbol in ['AVAX/USDT', 'LINK/USDT', 'DOT/USDT']:
                safe_quantity = round(safe_quantity, 3)
            elif symbol in ['ADA/USDT', 'XRP/USDT', 'MATIC/USDT']:
                safe_quantity = round(safe_quantity, 2)
            else:
                safe_quantity = round(safe_quantity, 3)
            
            logger.debug(f"수량 계산 완료: {symbol} - 금액: ${max_amount:.2f}, 가격: ${price:.4f}, 수량: {safe_quantity:.6f}")
            
            return safe_quantity
            
        except Exception as e:
            logger.error(f"안전한 수량 계산 실패 ({symbol}): {e}")
            return 0.0

    def _generate_initial_purchase_orders(self, portfolio_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """초기 자산 구매 주문 생성 (USDT → 암호화폐)"""
        try:
            orders = []
            total_balance = portfolio_state.get('total_balance', 0)
            current_prices = portfolio_state.get('current_prices', {})
            
            # 기본 투자 심볼들 (유동성이 높고 안정적인 코인들)
            primary_symbols = ['BTC/USDT', 'ETH/USDT']
            
            # 현물 투자 (목표 비율에서 현재 비율을 뺀 만큼)
            spot_target_investment = total_balance * (self.spot_allocation * 0.8)  # 80%만 초기 투자
            
            # 심볼별 균등 분할
            per_symbol_amount = spot_target_investment / len(primary_symbols)
            
            for symbol in primary_symbols:
                current_price = current_prices.get(symbol, 0)
                
                if current_price <= 0:
                    logger.warning(f"가격 정보 없음, 스킵: {symbol}")
                    continue
                
                # 최소 투자 금액 확인 ($10 이상으로 완화)
                if per_symbol_amount < 10:
                    logger.info(f"투자 금액이 너무 적음: {symbol} - ${per_symbol_amount:.2f}")
                    continue
                
                # 안전한 수량 계산
                safe_quantity = self._calculate_safe_quantity(symbol, per_symbol_amount, current_price, 'spot')
                
                if safe_quantity > 0:
                    orders.append({
                        'strategy': 'initial_investment',
                        'symbol': symbol,
                        'exchange_type': 'spot',
                        'action': 'buy',
                        'size': safe_quantity,
                        'confidence': 0.8,
                        'priority': 1
                    })
                    logger.info(f"초기 투자 주문: {symbol} 매수 {safe_quantity:.6f} @ ${current_price:.2f} (${per_symbol_amount:.2f})")
            
            # 선물 투자는 더 보수적으로 접근 (BTC만)
            futures_target_investment = total_balance * (self.futures_allocation * 0.3)  # 30%만 초기 투자
            
            if futures_target_investment >= 50:  # 최소 $50으로 완화
                btc_price = current_prices.get('BTC/USDT', 0)
                
                if btc_price > 0:
                    # 선물은 BTC/USDT 형식으로 통일 (거래소 인터페이스에서 처리)
                    futures_symbol = 'BTC/USDT'
                    safe_quantity = self._calculate_safe_quantity(futures_symbol, futures_target_investment, btc_price, 'futures')
                    
                    if safe_quantity > 0:
                        orders.append({
                            'strategy': 'initial_investment',
                            'symbol': futures_symbol,
                            'exchange_type': 'futures',
                            'action': 'buy',
                            'size': safe_quantity,
                            'confidence': 0.7,
                            'priority': 2
                        })
                        logger.info(f"초기 선물 투자: {futures_symbol} 매수 {safe_quantity:.6f} @ ${btc_price:.2f} (${futures_target_investment:.2f})")
            
            return orders
            
        except Exception as e:
            logger.error(f"초기 구매 주문 생성 실패: {e}")
            return []

    def get_strategy_summary(self) -> Dict[str, Any]:
        """전략 요약 정보 반환"""
        return {
            'strategy_type': 'hybrid_spot_futures',
            'spot_allocation': self.spot_allocation,
            'futures_allocation': self.futures_allocation,
            'arbitrage_threshold': self.arbitrage_threshold,
            'max_leverage': self.max_leverage,
            'current_positions': self.current_positions,
            'last_rebalance': self.last_rebalance.isoformat()
        }