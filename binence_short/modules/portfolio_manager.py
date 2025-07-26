"""
포트폴리오 관리 모듈
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from utils.logger import logger
from utils.decorators import log_execution_time, cache_result
from .exchange_interface import ExchangeInterface
from .risk_manager import RiskManager


class PortfolioManager:
    """포트폴리오 관리 클래스"""
    
    def __init__(self, config: Dict[str, Any], exchange: ExchangeInterface, risk_manager: RiskManager):
        self.config = config
        self.exchange = exchange
        self.risk_manager = risk_manager
        
        # 포트폴리오 설정
        self.initial_balance = config.get('initial_balance', 1000)
        self.spot_allocation = config.get('spot_allocation', 0.6)
        self.futures_allocation = config.get('futures_allocation', 0.4)
        self.rebalance_threshold = config.get('rebalance_threshold', 0.05)
        self.trading_symbols = config.get('trading_symbols', ['BTC/USDT', 'ETH/USDT'])
        
        # 포트폴리오 상태
        self.positions = {}
        self.balance_history = []
        self.trade_history = []
        self.performance_metrics = {}
        self.last_rebalance = None
        
        # 수수료 설정
        self.fees = config.get('fees', {
            'spot_maker': 0.001,
            'spot_taker': 0.001,
            'futures_maker': 0.0002,
            'futures_taker': 0.0004,
            'slippage': 0.0005
        })
        
        logger.info("포트폴리오 관리자 초기화 완료")
    
    @log_execution_time
    def update_portfolio_state(self):
        """포트폴리오 상태 업데이트"""
        try:
            # 잔고 조회
            spot_balance = self.exchange.get_spot_balance()
            futures_balance = self.exchange.get_futures_balance()
            
            # 포지션 조회
            futures_positions = self.exchange.get_positions()
            
            # 현재 포트폴리오 가치 계산
            portfolio_value = self._calculate_portfolio_value(spot_balance, futures_balance, futures_positions)
            
            # 포트폴리오 상태 업데이트
            self._update_positions(spot_balance, futures_positions)
            self._update_balance_history(portfolio_value)
            
            # 성과 메트릭 업데이트
            self._update_performance_metrics(portfolio_value)
            
            logger.debug(f"포트폴리오 상태 업데이트 완료: 총 가치 ${portfolio_value:.2f}")
            
        except Exception as e:
            logger.error(f"포트폴리오 상태 업데이트 실패: {e}")
    
    def _calculate_portfolio_value(self, spot_balance: Dict[str, Any], 
                                 futures_balance: Dict[str, Any], 
                                 futures_positions: List[Dict[str, Any]]) -> float:
        """포트폴리오 총 가치 계산"""
        try:
            total_value = 0.0
            
            # 현물 잔고 (설정된 거래 심볼들만 처리)
            for symbol, amount in spot_balance.get('total', {}).items():
                if symbol == 'USDT':
                    total_value += amount
                elif f"{symbol}/USDT" in self.trading_symbols:
                    # 설정된 거래 심볼만 처리
                    ticker = self.exchange.get_ticker(f"{symbol}/USDT", 'spot')
                    if ticker.get('last'):
                        total_value += amount * ticker['last']
            
            # 선물 잔고
            total_value += futures_balance.get('total', {}).get('USDT', 0)
            
            # 선물 포지션 미실현 손익
            for position in futures_positions:
                total_value += position.get('unrealizedPnl', 0)
            
            return total_value
            
        except Exception as e:
            logger.error(f"포트폴리오 가치 계산 실패: {e}")
            return 0.0
    
    def _update_positions(self, spot_balance: Dict[str, Any], futures_positions: List[Dict[str, Any]]):
        """포지션 정보 업데이트"""
        try:
            self.positions.clear()
            
            # 현물 포지션 (설정된 거래 심볼들만 처리)
            for symbol, amount in spot_balance.get('total', {}).items():
                if amount > 0 and symbol != 'USDT' and f"{symbol}/USDT" in self.trading_symbols:
                    # 설정된 거래 심볼만 처리
                    ticker = self.exchange.get_ticker(f"{symbol}/USDT", 'spot')
                    self.positions[f"{symbol}/USDT"] = {
                        'symbol': f"{symbol}/USDT",
                        'side': 'buy',
                        'size': amount,
                        'current_price': ticker.get('last', 0),
                        'exchange_type': 'spot',
                        'unrealized_pnl': 0,
                        'timestamp': datetime.now()
                    }
            
            # 선물 포지션
            for position in futures_positions:
                self.positions[position['symbol']] = {
                    'symbol': position['symbol'],
                    'side': position['side'],
                    'size': position['size'],
                    'current_price': position['markPrice'],
                    'exchange_type': 'futures',
                    'unrealized_pnl': position['unrealizedPnl'],
                    'timestamp': datetime.now()
                }
            
        except Exception as e:
            logger.error(f"포지션 업데이트 실패: {e}")
    
    def _update_balance_history(self, portfolio_value: float):
        """잔고 기록 업데이트"""
        try:
            self.balance_history.append({
                'timestamp': datetime.now(),
                'total_value': portfolio_value,
                'pnl': portfolio_value - self.initial_balance,
                'pnl_pct': (portfolio_value - self.initial_balance) / self.initial_balance * 100
            })
            
            # 기록 제한 (최근 1000개만 보관)
            if len(self.balance_history) > 1000:
                self.balance_history = self.balance_history[-1000:]
                
        except Exception as e:
            logger.error(f"잔고 기록 업데이트 실패: {e}")
    
    def _update_performance_metrics(self, portfolio_value: float):
        """성과 메트릭 업데이트"""
        try:
            if not self.balance_history:
                return
            
            # 기본 메트릭
            total_return = (portfolio_value - self.initial_balance) / self.initial_balance
            
            # 일일 수익률 계산
            daily_returns = []
            for i in range(1, len(self.balance_history)):
                prev_value = self.balance_history[i-1]['total_value']
                curr_value = self.balance_history[i]['total_value']
                if prev_value > 0:  # zero division 방지
                    daily_return = (curr_value - prev_value) / prev_value
                    daily_returns.append(daily_return)
            
            if daily_returns:
                avg_daily_return = np.mean(daily_returns)
                volatility = np.std(daily_returns)
                
                # 샤프 비율 (무위험 수익률 0으로 가정)
                sharpe_ratio = avg_daily_return / volatility if volatility > 0 else 0
                
                # 최대 드로우다운
                max_drawdown = self._calculate_max_drawdown()
                
                # 승률 계산
                win_rate = self._calculate_win_rate()
                
                self.performance_metrics = {
                    'total_return': total_return,
                    'total_return_pct': total_return * 100,
                    'avg_daily_return': avg_daily_return,
                    'volatility': volatility,
                    'sharpe_ratio': sharpe_ratio,
                    'max_drawdown': max_drawdown,
                    'win_rate': win_rate,
                    'total_trades': len(self.trade_history),
                    'current_positions': len(self.positions),
                    'last_updated': datetime.now()
                }
            
        except Exception as e:
            logger.error(f"성과 메트릭 업데이트 실패: {e}")
    
    def _calculate_max_drawdown(self) -> float:
        """최대 드로우다운 계산"""
        try:
            if len(self.balance_history) < 2:
                return 0.0
            
            values = [record['total_value'] for record in self.balance_history]
            peak = values[0]
            max_drawdown = 0.0
            
            for value in values[1:]:
                if value > peak:
                    peak = value
                else:
                    drawdown = (peak - value) / peak
                    max_drawdown = max(max_drawdown, drawdown)
            
            return max_drawdown
            
        except Exception as e:
            logger.error(f"최대 드로우다운 계산 실패: {e}")
            return 0.0
    
    def _calculate_win_rate(self) -> float:
        """승률 계산"""
        try:
            if not self.trade_history:
                return 0.0
            
            winning_trades = sum(1 for trade in self.trade_history if trade.get('pnl', 0) > 0)
            total_trades = len(self.trade_history)
            
            return winning_trades / total_trades * 100 if total_trades > 0 else 0.0
            
        except Exception as e:
            logger.error(f"승률 계산 실패: {e}")
            return 0.0
    
    @log_execution_time
    def execute_trade(self, symbol: str, side: str, size: float, price: float = None, 
                     exchange_type: str = 'spot', order_type: str = 'market') -> Dict[str, Any]:
        """거래 실행"""
        try:
            # 거래 전 검증
            current_balance = self.get_current_balance()
            validation_result = self.risk_manager.validate_trade(
                symbol, side, size, price or 0, current_balance, exchange_type
            )
            
            if not validation_result['is_valid']:
                logger.warning(f"거래 검증 실패: {validation_result['errors']}")
                return {
                    'success': False,
                    'error': validation_result['errors'],
                    'warnings': validation_result['warnings']
                }
            
            # 크기 조정
            adjusted_size = validation_result['adjusted_size']
            
            # 실제 거래 실행
            if price is None:
                ticker = self.exchange.get_ticker(symbol, exchange_type)
                price = ticker.get('last', 0)
            
            order_result = self.exchange.place_order(
                symbol, side, adjusted_size, price, order_type, exchange_type
            )
            
            if order_result:
                # 수수료 계산
                fees = self._calculate_fees(adjusted_size, price, exchange_type, order_type)
                
                # 거래 기록
                trade_record = {
                    'timestamp': datetime.now(),
                    'symbol': symbol,
                    'side': side,
                    'size': adjusted_size,
                    'price': price,
                    'exchange_type': exchange_type,
                    'order_type': order_type,
                    'fees': fees,
                    'order_id': order_result.get('id'),
                    'status': order_result.get('status')
                }
                
                self.trade_history.append(trade_record)
                
                # 포지션 업데이트
                self._update_position_from_trade(trade_record)
                
                logger.info(f"거래 실행 완료: {symbol} {side} {adjusted_size} @ {price}")
                
                return {
                    'success': True,
                    'trade_record': trade_record,
                    'order_result': order_result,
                    'warnings': validation_result['warnings']
                }
            else:
                return {
                    'success': False,
                    'error': "거래 실행 실패",
                    'warnings': validation_result['warnings']
                }
                
        except Exception as e:
            logger.error(f"거래 실행 실패: {e}")
            return {
                'success': False,
                'error': str(e),
                'warnings': []
            }
    
    def _calculate_fees(self, size: float, price: float, exchange_type: str, order_type: str) -> float:
        """수수료 계산"""
        try:
            position_value = size * price
            
            if exchange_type == 'spot':
                fee_rate = self.fees['spot_maker'] if order_type == 'limit' else self.fees['spot_taker']
            else:
                fee_rate = self.fees['futures_maker'] if order_type == 'limit' else self.fees['futures_taker']
            
            # 슬리피지 추가
            fee_rate += self.fees['slippage']
            
            return position_value * fee_rate
            
        except Exception as e:
            logger.error(f"수수료 계산 실패: {e}")
            return 0.0
    
    def _update_position_from_trade(self, trade_record: Dict[str, Any]):
        """거래로부터 포지션 업데이트"""
        try:
            symbol = trade_record['symbol']
            side = trade_record['side']
            size = trade_record['size']
            price = trade_record['price']
            exchange_type = trade_record['exchange_type']
            
            # 리스크 관리자에 포지션 추가
            if side == 'buy':
                # 스탑로스/테이크프로핏 계산
                stop_loss_price = self.risk_manager.calculate_stop_loss(symbol, side, price)
                take_profit_price = self.risk_manager.calculate_take_profit(symbol, side, price)
                
                self.risk_manager.add_position(
                    symbol, side, size, price, exchange_type, stop_loss_price, take_profit_price
                )
            
        except Exception as e:
            logger.error(f"포지션 업데이트 실패: {e}")
    
    @log_execution_time
    def rebalance_portfolio(self) -> Dict[str, Any]:
        """포트폴리오 리밸런싱"""
        try:
            # 현재 포트폴리오 상태 분석
            current_allocation = self._get_current_allocation()
            target_allocation = {
                'spot': self.spot_allocation,
                'futures': self.futures_allocation
            }
            
            rebalance_actions = []
            
            # 목표 비율과 현재 비율 비교
            for market_type, target_ratio in target_allocation.items():
                current_ratio = current_allocation.get(market_type, 0)
                difference = abs(current_ratio - target_ratio)
                
                if difference > self.rebalance_threshold:
                    # 리밸런싱 필요
                    total_value = self.get_current_balance()
                    
                    # 총 가치가 0이면 리밸런싱 건너뛰기
                    if total_value <= 0:
                        logger.warning(f"총 포트폴리오 가치가 0 이하입니다: {total_value}")
                        continue
                    
                    target_value = total_value * target_ratio
                    current_value = total_value * current_ratio
                    adjustment_needed = target_value - current_value
                    
                    rebalance_actions.append({
                        'market_type': market_type,
                        'current_ratio': current_ratio,
                        'target_ratio': target_ratio,
                        'adjustment_needed': adjustment_needed,
                        'adjustment_pct': adjustment_needed / total_value
                    })
            
            # 리밸런싱 실행
            executed_actions = []
            for action in rebalance_actions:
                if self._execute_rebalance_action(action):
                    executed_actions.append(action)
            
            if executed_actions:
                self.last_rebalance = datetime.now()
                logger.info(f"포트폴리오 리밸런싱 완료: {len(executed_actions)}개 조정")
            
            return {
                'success': True,
                'rebalance_needed': len(rebalance_actions) > 0,
                'actions_needed': rebalance_actions,
                'actions_executed': executed_actions,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"포트폴리오 리밸런싱 실패: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now()
            }
    
    def _get_current_allocation(self) -> Dict[str, float]:
        """현재 포트폴리오 배분 조회"""
        try:
            total_value = self.get_current_balance()
            
            if total_value == 0:
                return {'spot': 0, 'futures': 0}
            
            spot_value = 0
            futures_value = 0
            
            for position in self.positions.values():
                position_value = position['size'] * position['current_price']
                
                if position['exchange_type'] == 'spot':
                    spot_value += position_value
                else:
                    futures_value += position_value
            
            return {
                'spot': spot_value / total_value,
                'futures': futures_value / total_value
            }
            
        except Exception as e:
            logger.error(f"현재 배분 조회 실패: {e}")
            return {'spot': 0, 'futures': 0}
    
    def _get_current_prices(self) -> Dict[str, float]:
        """현재 가격 정보 조회"""
        try:
            prices = {}
            for symbol in self.trading_symbols:
                try:
                    ticker = self.exchange.get_ticker(symbol, 'spot')
                    if ticker and ticker.get('last'):
                        prices[symbol] = ticker['last']
                except Exception as e:
                    logger.warning(f"가격 조회 실패 ({symbol}): {e}")
                    prices[symbol] = 0
            return prices
        except Exception as e:
            logger.error(f"현재 가격 조회 실패: {e}")
            return {}
    
    def _execute_rebalance_action(self, action: Dict[str, Any]) -> bool:
        """리밸런싱 액션 실행"""
        try:
            # 리밸런싱 로직 구현
            # 여기서는 간단한 예시만 제공
            market_type = action['market_type']
            adjustment_needed = action['adjustment_needed']
            
            if adjustment_needed > 0:
                # 해당 시장에 투자 증가
                logger.info(f"{market_type} 시장 투자 증가: ${adjustment_needed:.2f}")
            else:
                # 해당 시장에서 자금 회수
                logger.info(f"{market_type} 시장 자금 회수: ${abs(adjustment_needed):.2f}")
            
            return True
            
        except Exception as e:
            logger.error(f"리밸런싱 액션 실행 실패: {e}")
            return False
    
    def get_current_balance(self) -> float:
        """현재 총 잔고 조회"""
        try:
            if self.balance_history:
                return self.balance_history[-1]['total_value']
            return self.initial_balance
        except Exception as e:
            logger.error(f"현재 잔고 조회 실패: {e}")
            return self.initial_balance
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """포트폴리오 요약 정보"""
        try:
            # 실제 거래소 잔고 조회
            spot_balance = self.exchange.get_spot_balance()
            futures_balance = self.exchange.get_futures_balance()
            
            # 현재 포트폴리오 가치 계산
            current_balance = self._calculate_portfolio_value(spot_balance, futures_balance, [])
            
            # 현물과 선물 잔고 분리
            spot_usdt = spot_balance.get('total', {}).get('USDT', 0)
            futures_usdt = futures_balance.get('total', {}).get('USDT', 0)
            total_balance = spot_usdt + futures_usdt
            
            allocation = self._get_current_allocation()
            
            return {
                'total_balance': total_balance,
                'current_balance': current_balance,
                'spot_balance': spot_usdt,
                'futures_balance': futures_usdt,
                'spot_free_balance': spot_balance.get('free', {}).get('USDT', 0),
                'futures_free_balance': futures_balance.get('free', {}).get('USDT', 0),
                'initial_balance': self.initial_balance,
                'total_pnl': current_balance - self.initial_balance,
                'total_pnl_pct': (current_balance - self.initial_balance) / self.initial_balance * 100 if self.initial_balance > 0 else 0,
                'allocation': allocation,
                'positions': len(self.positions),
                'trades': len(self.trade_history),
                'performance_metrics': self.performance_metrics,
                'last_updated': datetime.now(),
                'current_prices': self._get_current_prices()
            }
            
        except Exception as e:
            logger.error(f"포트폴리오 요약 정보 조회 실패: {e}")
            return {
                'total_balance': self.initial_balance,
                'current_balance': self.initial_balance,
                'spot_balance': self.initial_balance * self.spot_allocation,
                'futures_balance': self.initial_balance * self.futures_allocation,
                'spot_free_balance': self.initial_balance * self.spot_allocation,
                'futures_free_balance': self.initial_balance * self.futures_allocation,
                'initial_balance': self.initial_balance,
                'total_pnl': 0,
                'total_pnl_pct': 0,
                'allocation': {'spot': self.spot_allocation, 'futures': self.futures_allocation},
                'positions': 0,
                'trades': 0,
                'performance_metrics': {},
                'last_updated': datetime.now(),
                'current_prices': {}
            }
    
    def get_position_details(self) -> List[Dict[str, Any]]:
        """포지션 상세 정보"""
        try:
            position_details = []
            
            for symbol, position in self.positions.items():
                # 수익률 계산
                if position['side'] == 'buy':
                    pnl_pct = (position['current_price'] - position.get('entry_price', position['current_price'])) / position.get('entry_price', position['current_price']) * 100
                else:
                    pnl_pct = (position.get('entry_price', position['current_price']) - position['current_price']) / position.get('entry_price', position['current_price']) * 100
                
                position_details.append({
                    'symbol': symbol,
                    'side': position['side'],
                    'size': position['size'],
                    'current_price': position['current_price'],
                    'market_value': position['size'] * position['current_price'],
                    'unrealized_pnl': position.get('unrealized_pnl', 0),
                    'pnl_pct': pnl_pct,
                    'exchange_type': position['exchange_type'],
                    'timestamp': position['timestamp']
                })
            
            return position_details
            
        except Exception as e:
            logger.error(f"포지션 상세 정보 조회 실패: {e}")
            return []
    
    def get_trade_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """거래 내역 조회"""
        try:
            return self.trade_history[-limit:] if self.trade_history else []
        except Exception as e:
            logger.error(f"거래 내역 조회 실패: {e}")
            return []
    
    def cleanup_old_records(self, days_to_keep: int = 30):
        """오래된 기록 정리"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # 오래된 거래 내역 정리
            self.trade_history = [
                trade for trade in self.trade_history 
                if trade['timestamp'] > cutoff_date
            ]
            
            # 오래된 잔고 기록 정리
            self.balance_history = [
                record for record in self.balance_history 
                if record['timestamp'] > cutoff_date
            ]
            
            logger.info(f"오래된 기록 정리 완료: {days_to_keep}일 이전 데이터 삭제")
            
        except Exception as e:
            logger.error(f"오래된 기록 정리 실패: {e}")