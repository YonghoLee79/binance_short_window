#!/usr/bin/env python3
"""
현물 + 선물 하이브리드 트레이딩 봇 v2
고급 포트폴리오 전략 적용
"""

import asyncio
import time
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import config
from utils import logger
from modules import (
    TechnicalAnalyzer,
    ExchangeInterface,
    StrategyEngine,
    RiskManager,
    PortfolioManager,
    TelegramNotifications
)
from modules.hybrid_portfolio_strategy import HybridPortfolioStrategy
from modules.database_manager import get_database_manager


class HybridTradingBotV2:
    """현물 + 선물 하이브리드 트레이딩 봇 v2"""
    
    def __init__(self):
        self.config = config
        self.logger = logger
        self.running = False
        self.cycle_count = 0
        self.start_time = datetime.now()
        
        # 컴포넌트 초기화
        self._initialize_components()
        
        # 하이브리드 전략 초기화 (매우 적극적 설정)
        hybrid_config = {
            'spot_allocation': self.config.SPOT_ALLOCATION,
            'futures_allocation': self.config.FUTURES_ALLOCATION,
            'arbitrage_threshold': 0.0005,  # 0.05% 프리미엄 (매우 민감하게)
            'rebalance_threshold': 0.03,    # 3% 편차시 리밸런싱
            'max_leverage': 5,              # 레버리지 증가
            'max_position_size': 0.2,       # 단일 포지션 최대 20%
            'correlation_limit': 0.75
        }
        self.hybrid_strategy = HybridPortfolioStrategy(hybrid_config)
        
        # 상태 추적
        self.last_portfolio_update = datetime.now()
        self.last_telegram_summary = datetime.now()
        self.performance_metrics = {
            'total_trades': 0,
            'successful_trades': 0,
            'total_pnl': 0.0,
            'daily_pnl': 0.0,
            'max_drawdown': 0.0,
            'win_rate': 0.0
        }
        
        self.logger.info("하이브리드 트레이딩 봇 v2 초기화 완료")
        
        # 시작 알림 전송
        self._send_startup_notification()
    
    def _initialize_components(self):
        """컴포넌트 초기화"""
        try:
            # 거래소 인터페이스
            exchange_config = {
                'api_key': self.config.BINANCE_API_KEY,
                'secret_key': self.config.BINANCE_SECRET_KEY,
                'use_testnet': self.config.USE_TESTNET
            }
            self.exchange = ExchangeInterface(exchange_config)
            
            # 리스크 관리자
            risk_config = self.config.get_risk_config()
            self.risk_manager = RiskManager(risk_config)
            
            # 기술적 분석기
            technical_config = self.config.get_technical_config()
            self.technical_analyzer = TechnicalAnalyzer(technical_config)
            
            # 전략 엔진
            strategy_config = self.config.get_strategy_config()
            strategy_config.update(technical_config)
            self.strategy_engine = StrategyEngine(strategy_config, self.exchange)
            
            # 포트폴리오 관리자
            portfolio_config = {
                'initial_balance': self.config.INITIAL_BALANCE,
                'spot_allocation': self.config.SPOT_ALLOCATION,
                'futures_allocation': self.config.FUTURES_ALLOCATION,
                'rebalance_threshold': self.config.REBALANCE_THRESHOLD,
                'trading_symbols': self.config.TRADING_SYMBOLS,
                'fees': self.config.FEES
            }
            portfolio_config.update(risk_config)
            self.portfolio_manager = PortfolioManager(
                portfolio_config, self.exchange, self.risk_manager
            )
            
            # 텔레그램 알림
            self.telegram = TelegramNotifications()
            
            # 데이터베이스
            self.db = get_database_manager()
            
            self.logger.info("모든 컴포넌트 초기화 완료")
            
        except Exception as e:
            self.logger.error(f"컴포넌트 초기화 실패: {e}")
            raise
    
    def _send_startup_notification(self):
        """시작 알림 전송"""
        try:
            startup_info = {
                'start_time': self.start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'strategy': 'Hybrid Spot + Futures',
                'spot_allocation': f"{self.config.SPOT_ALLOCATION:.0%}",
                'futures_allocation': f"{self.config.FUTURES_ALLOCATION:.0%}",
                'trading_symbols': ', '.join(self.config.TRADING_SYMBOLS[:3]) + f" (+{len(self.config.TRADING_SYMBOLS)-3} more)",
                'mode': 'TESTNET' if self.config.USE_TESTNET else 'LIVE TRADING'
            }
            
            message = f"""
🚀 <b>하이브리드 트레이딩 봇 v2 시작</b>

📅 시작 시간: {startup_info['start_time']}
🎯 전략: {startup_info['strategy']}
💰 현물 할당: {startup_info['spot_allocation']}
⚡ 선물 할당: {startup_info['futures_allocation']}
📊 거래 심볼: {startup_info['trading_symbols']}
🔧 모드: <b>{startup_info['mode']}</b>

🔄 <b>전략 특징:</b>
• 아비트라지 기회 포착
• 트렌드 추종 + 헤징
• 자동 리밸런싱
• 다층 리스크 관리

<i>하이브리드 포트폴리오 전략으로 시작합니다!</i>
            """.strip()
            
            self.telegram.telegram.send_message(message)
            
        except Exception as e:
            self.logger.error(f"시작 알림 전송 실패: {e}")
    
    async def collect_market_data(self) -> Dict[str, Any]:
        """시장 데이터 수집"""
        try:
            market_data = {}
            
            # 병렬로 모든 심볼의 데이터 수집
            tasks = []
            for symbol in self.config.TRADING_SYMBOLS:
                tasks.append(self._fetch_symbol_data(symbol))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.logger.warning(f"데이터 수집 실패 ({self.config.TRADING_SYMBOLS[i]}): {result}")
                    continue
                
                if result:
                    symbol = self.config.TRADING_SYMBOLS[i]
                    market_data[symbol] = result
            
            self.logger.info(f"시장 데이터 수집 완료: {len(market_data)}개 심볼")
            return market_data
            
        except Exception as e:
            self.logger.error(f"시장 데이터 수집 실패: {e}")
            return {}
    
    async def _fetch_symbol_data(self, symbol: str) -> Dict[str, Any]:
        """개별 심볼 데이터 수집"""
        try:
            # 현물 및 선물 티커
            spot_ticker = self.exchange.get_ticker(symbol, 'spot')
            futures_ticker = self.exchange.get_ticker(symbol, 'future')
            
            # OHLCV 데이터
            spot_ohlcv = self.exchange.get_ohlcv(symbol, '1h', 100, 'spot')
            futures_ohlcv = self.exchange.get_ohlcv(symbol, '1h', 100, 'future')
            
            if spot_ohlcv is None or futures_ohlcv is None or spot_ohlcv.empty or futures_ohlcv.empty:
                return None
            
            # 기술적 분석
            spot_indicators = self.technical_analyzer.get_all_indicators(spot_ohlcv)
            futures_indicators = self.technical_analyzer.get_all_indicators(futures_ohlcv)
            
            # 신호 생성
            spot_signals = self.technical_analyzer.generate_signals(spot_indicators)
            futures_signals = self.technical_analyzer.generate_signals(futures_indicators)
            
            return {
                'symbol': symbol,
                'spot_ticker': spot_ticker,
                'futures_ticker': futures_ticker,
                'spot_ohlcv': spot_ohlcv,
                'futures_ohlcv': futures_ohlcv,
                'spot_indicators': spot_indicators,
                'futures_indicators': futures_indicators,
                'spot_signals': spot_signals,
                'futures_signals': futures_signals,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"심볼 데이터 수집 실패 ({symbol}): {e}")
            return None
    
    def analyze_and_execute_strategy(self, market_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """전략 분석 및 실행"""
        try:
            # 포트폴리오 상태 업데이트
            portfolio_state = self.portfolio_manager.get_portfolio_summary()
            
            # 하이브리드 전략 기회 분석
            opportunities = self.hybrid_strategy.analyze_market_opportunity(market_data)
            
            self.logger.info(f"전략 기회 발견: "
                           f"아비트라지 {len(opportunities['arbitrage'])}개, "
                           f"트렌드 {len(opportunities['trend_following'])}개, "
                           f"헤징 {len(opportunities['hedging'])}개, "
                           f"모멘텀 {len(opportunities['momentum'])}개")
            
            # 리밸런싱 확인
            executed_trades = []
            if self.hybrid_strategy.check_rebalancing_needed(portfolio_state):
                rebalancing_orders = self.hybrid_strategy.generate_rebalancing_orders(portfolio_state)
                for order in rebalancing_orders:
                    trade_result = self._execute_trade(order)
                    if trade_result and trade_result.get('success'):
                        executed_trades.append(trade_result)
                        self._send_trade_notification(trade_result, order)
            
            # 전략 신호 생성
            signals = self.hybrid_strategy.generate_portfolio_signals(opportunities, portfolio_state, market_data)
            
            # 실시간 리스크 모니터링
            risk_monitoring_result = self.risk_manager.real_time_risk_monitoring()
            if risk_monitoring_result['risk_level'] in ['high', 'critical']:
                self.logger.warning(f"⚠️ 높은 리스크 감지: {risk_monitoring_result['risk_level']}")
                for recommendation in risk_monitoring_result.get('recommendations', []):
                    self.logger.warning(f"권장사항: {recommendation}")
                
                # 위험 수준이 critical이면 텔레그램 알림
                if risk_monitoring_result['risk_level'] == 'critical':
                    risk_message = f"""
🚨 <b>위험 경고 - CRITICAL</b>
레벨: {risk_monitoring_result['risk_level'].upper()}
조치사항: {', '.join(risk_monitoring_result.get('actions_taken', []))}
권장사항: {', '.join(risk_monitoring_result.get('recommendations', []))[:100]}...
"""
                    self.telegram.send_message(risk_message)

            # 위험 수준에 따른 거래 신뢰도 임계값 조정
            base_confidence_threshold = 0.3  # 기본 30%
            if risk_monitoring_result['risk_level'] == 'high':
                confidence_threshold = 0.6  # 60%로 상향
            elif risk_monitoring_result['risk_level'] == 'critical':
                confidence_threshold = 0.8  # 80%로 대폭 상향
                signals = signals[:2]  # 신호 개수도 제한
            else:
                confidence_threshold = base_confidence_threshold
            
            # 신호 실행
            self.logger.info(f"생성된 신호 수: {len(signals)}개 (리스크 레벨: {risk_monitoring_result['risk_level']})")
            valid_signal_count = 0
            
            for i, signal in enumerate(signals[:5]):  # 최대 5개까지만
                # 신뢰도 사전 체크
                signal_confidence = signal.get('confidence', 0)
                if signal_confidence < confidence_threshold:
                    self.logger.info(f"신호 #{i+1} 신뢰도 부족으로 스킵: {signal['symbol']} - "
                                   f"신뢰도 {signal_confidence:.2f} < {confidence_threshold:.2f}")
                    continue
                
                valid_signal_count += 1
                self.logger.info(f"신호 #{valid_signal_count}: {signal['symbol']} {signal['action']} "
                               f"({signal['exchange_type']}) - 신뢰도: {signal_confidence:.2f}")
                
                # 리스크 검증
                current_price = market_data.get(signal['symbol'], {}).get(f"{signal['exchange_type']}_ticker", {}).get('last', 0)
                risk_check = self.risk_manager.validate_trade(
                    symbol=signal['symbol'],
                    side=signal['action'],
                    size=signal['size'],
                    price=current_price,
                    current_balance=portfolio_state['current_balance'],
                    exchange_type=signal['exchange_type']
                )
                
                if risk_check['is_valid']:
                    self.logger.info(f"리스크 검증 통과: {signal['symbol']} - 거래 실행 중...")
                    # 거래 실행
                    trade_result = self._execute_trade(signal)
                    if trade_result and trade_result.get('success'):
                        executed_trades.append(trade_result)
                        self._send_trade_notification(trade_result, signal)
                        self.logger.info(f"거래 성공: {signal['symbol']} {signal['action']} "
                                       f"{signal['size']} @ ${current_price}")
                        
                        # 포지션 업데이트
                        self.hybrid_strategy.update_positions(
                            signal['symbol'], 
                            signal['exchange_type'], 
                            trade_result
                        )
                    else:
                        self.logger.warning(f"거래 실행 실패: {signal['symbol']} - {trade_result}")
                else:
                    self.logger.warning(f"리스크 검증 실패: {signal['symbol']} - {risk_check['errors']}")
            
            return executed_trades
            
        except Exception as e:
            self.logger.error(f"전략 분석 및 실행 실패: {e}")
            return []
    
    def _execute_trade(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """거래 실행 (스마트 주문 시스템 적용)"""
        try:
            # 1. 신호 검증 (동적 신호 검증 시스템)
            validation_result = self.technical_analyzer.validate_signal_strength(
                {'combined_signal': signal.get('confidence', 0)},
                {
                    'volume': signal.get('volume', 0),
                    'avg_volume': signal.get('avg_volume', 0),
                    'price_data': signal.get('price_history', []),
                    'signal_history': getattr(self, '_signal_history', [])
                }
            )
            
            if not validation_result['is_valid']:
                self.logger.info(f"신호 검증 실패: {signal['symbol']} - 신뢰도 {validation_result['confidence']:.2f}")
                return {'success': False, 'error': 'Signal validation failed'}
            
            # 2. 시장 조건 분석 및 적응형 포지션 사이징
            market_conditions = {
                'volatility': signal.get('volatility', 0.02),
                'regime': signal.get('market_regime', 'neutral'),
                'liquidity': signal.get('liquidity', 'normal')
            }
            
            # 기존 크기 대신 적응형 사이징 적용
            current_balance = self.portfolio_manager.get_total_balance()
            current_price = signal.get('current_price', 0)
            
            adaptive_size = self.risk_manager.adaptive_position_sizing(
                symbol=signal['symbol'],
                signal_strength=validation_result['confidence'],
                current_balance=current_balance,
                current_price=current_price,
                market_conditions=market_conditions
            )
            
            # 3. 스마트 주문 실행
            result = self.exchange.execute_smart_order(
                symbol=signal['symbol'],
                side=signal['action'],
                amount=adaptive_size,
                exchange_type=signal['exchange_type'],
                strategy_type=signal['strategy']
            )
            
            if result and result.get('success'):
                # 데이터베이스에 기록
                trade_data = {
                    'symbol': signal['symbol'],
                    'side': signal['action'],
                    'size': signal['size'],
                    'price': result.get('price', 0),
                    'exchange_type': signal['exchange_type'],
                    'order_type': 'market',
                    'fees': result.get('fees', 0),
                    'strategy': signal['strategy']
                }
                self.db.insert_trade(trade_data)
                
                # 성과 업데이트
                self.performance_metrics['total_trades'] += 1
                if result.get('pnl', 0) > 0:
                    self.performance_metrics['successful_trades'] += 1
                
                # 0 나누기 방지
                if self.performance_metrics['total_trades'] > 0:
                    self.performance_metrics['win_rate'] = (
                        self.performance_metrics['successful_trades'] / 
                        self.performance_metrics['total_trades'] * 100
                    )
                else:
                    self.performance_metrics['win_rate'] = 0.0
                
                self.logger.info(f"거래 실행 성공: {signal['strategy']} - {signal['symbol']} {signal['action']}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"거래 실행 실패: {e}")
            return {'success': False, 'error': str(e)}
    
    def _send_trade_notification(self, trade_result: Dict[str, Any], signal: Dict[str, Any]):
        """거래 알림 전송"""
        try:
            trade_info = {
                'symbol': signal['symbol'],
                'side': signal['action'],
                'size': signal['size'],
                'price': trade_result.get('price', 0),
                'exchange_type': signal['exchange_type'],
                'strategy': signal['strategy'],
                'confidence': signal.get('confidence', 0)
            }
            
            # 전략별 이모지
            strategy_emoji = {
                'arbitrage': '⚖️',
                'trend_following': '📈',
                'hedging': '🛡️',
                'momentum': '🚀',
                'rebalancing': '⚖️'
            }
            
            emoji = strategy_emoji.get(signal['strategy'], '📊')
            side_emoji = "📈" if signal['action'] == 'buy' else "📉"
            
            message = f"""
{emoji} <b>{signal['strategy'].title()} 거래 실행</b> {side_emoji}

🏷️ 심볼: {signal['symbol']}
📊 방향: {signal['action'].upper()}
🔢 수량: {signal['size']:.6f}
💵 가격: ${trade_result.get('price', 0):,.2f}
💰 총액: ${signal['size'] * trade_result.get('price', 0):,.2f}
📍 거래소: {signal['exchange_type'].upper()}
🎯 신뢰도: {signal.get('confidence', 0):.1%}

<i>{signal['strategy']} 전략으로 거래 완료</i>
            """.strip()
            
            self.telegram.telegram.send_message(message)
            
        except Exception as e:
            self.logger.error(f"거래 알림 전송 실패: {e}")
    
    def _send_portfolio_update(self):
        """포트폴리오 업데이트 알림"""
        try:
            portfolio_state = self.portfolio_manager.get_portfolio_summary()
            metrics = self.hybrid_strategy.calculate_portfolio_metrics(portfolio_state)
            
            message = f"""
💼 <b>하이브리드 포트폴리오 현황</b>

💰 총 자산: ${metrics.get('total_value', 0):,.2f}
💎 현물: ${metrics.get('spot_value', 0):,.2f} ({metrics.get('spot_ratio', 0):.1%})
⚡ 선물: ${metrics.get('futures_value', 0):,.2f} ({metrics.get('futures_ratio', 0):.1%})

🎯 <b>목표 비율:</b>
• 현물: {metrics.get('target_spot_ratio', 0):.0%} (편차: {metrics.get('spot_deviation', 0):.1%})
• 선물: {metrics.get('target_futures_ratio', 0):.0%} (편차: {metrics.get('futures_deviation', 0):.1%})

📊 포지션: {metrics.get('total_positions', 0)}개 (현물 {metrics.get('spot_positions', 0)}, 선물 {metrics.get('futures_positions', 0)})
📈 총 거래: {self.performance_metrics['total_trades']}회
🎯 승률: {self.performance_metrics['win_rate']:.1f}%
⚖️ 레버리지: {metrics.get('leverage_ratio', 0):.1f}x

{'🟢 균형 상태' if not metrics.get('rebalancing_needed') else '🟡 리밸런싱 필요'}
            """.strip()
            
            self.telegram.telegram.send_message(message)
            self.last_portfolio_update = datetime.now()
            
        except Exception as e:
            self.logger.error(f"포트폴리오 업데이트 알림 실패: {e}")
    
    def _send_daily_summary(self):
        """일일 요약 전송"""
        try:
            stats = self.db.get_trading_statistics(days=1)
            
            summary_info = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'daily_pnl': stats.get('total_pnl', 0),
                'trades_count': stats.get('total_trades', 0),
                'win_rate': stats.get('win_rate', 0),
                'max_profit': stats.get('max_profit', 0),
                'max_loss': stats.get('max_loss', 0)
            }
            
            self.telegram.send_daily_summary(summary_info)
            self.last_telegram_summary = datetime.now()
            
        except Exception as e:
            self.logger.error(f"일일 요약 전송 실패: {e}")
    
    def _send_cycle_log(self, market_data: Dict[str, Any], executed_trades: List[Dict], cycle_duration: float):
        """실시간 거래 사이클 로그 전송"""
        try:
            # 기회 발견 현황 분석
            opportunities = self.hybrid_strategy.analyze_market_opportunity(market_data)
            opp_counts = {
                'arbitrage': len(opportunities.get('arbitrage', [])),
                'trend_following': len(opportunities.get('trend_following', [])),
                'hedging': len(opportunities.get('hedging', [])),
                'momentum': len(opportunities.get('momentum', []))
            }
            
            cycle_info = {
                'cycle_number': self.cycle_count,
                'duration': cycle_duration,
                'opportunities': opp_counts,
                'trades_executed': len(executed_trades)
            }
            
            self.telegram.send_trading_cycle_log(cycle_info)
            
            # 거래 기회가 발견되었을 때 즉시 알림
            for strategy, opportunities_list in opportunities.items():
                for opp in opportunities_list[:2]:  # 최대 2개까지만
                    if opp.get('confidence', 0) > 0.7:  # 신뢰도 70% 이상
                        opp_info = {
                            'strategy': strategy,
                            'symbol': opp.get('symbol', 'N/A'),
                            'confidence': opp.get('confidence', 0),
                            'expected_return': opp.get('expected_profit', opp.get('expected_return', 0))
                        }
                        self.telegram.send_opportunity_alert(opp_info)
            
        except Exception as e:
            self.logger.error(f"사이클 로그 전송 실패: {e}")
    
    def _send_performance_log(self):
        """성과 로그 전송"""
        try:
            portfolio_state = self.portfolio_manager.get_portfolio_summary()
            
            # 시간별 성과 계산
            current_time = datetime.now()
            hour_ago = current_time - timedelta(hours=1)
            
            hourly_stats = self.db.get_trading_statistics_period(hour_ago, current_time)
            
            performance_info = {
                'current_balance': portfolio_state.get('total_balance', 0),
                'hourly_pnl': hourly_stats.get('total_pnl', 0),
                'hourly_pnl_pct': hourly_stats.get('pnl_percentage', 0),
                'total_trades': self.performance_metrics['total_trades'],
                'win_rate': self.performance_metrics['win_rate']
            }
            
            self.telegram.send_performance_log(performance_info)
            
        except Exception as e:
            self.logger.error(f"성과 로그 전송 실패: {e}")
    
    def _send_market_analysis_log(self, market_data: Dict[str, Any]):
        """시장 분석 로그 전송"""
        try:
            # 시장 상황 분석
            bullish_signals = 0
            bearish_signals = 0
            total_signals = 0
            top_signals = []
            
            for symbol, data in market_data.items():
                spot_signals = data.get('spot_signals', {})
                futures_signals = data.get('futures_signals', {})
                
                if spot_signals and futures_signals:
                    spot_strength = spot_signals.get('combined_signal', 0)
                    futures_strength = futures_signals.get('combined_signal', 0)
                    
                    if spot_strength and futures_strength:
                        avg_strength = (spot_strength + futures_strength) / 2
                        
                        if avg_strength > 0.3:
                            bullish_signals += 1
                        elif avg_strength < -0.3:
                            bearish_signals += 1
                        
                        total_signals += 1
                        
                        if abs(avg_strength) > 0.5:
                            top_signals.append({
                                'symbol': symbol,
                                'strategy': 'trend_following',
                                'confidence': abs(avg_strength)
                            })
            
            # 시장 상황 판단
            if total_signals > 0:
                bullish_ratio = bullish_signals / total_signals
                bearish_ratio = bearish_signals / total_signals
                
                if bullish_ratio > 0.6:
                    market_condition = 'bullish'
                elif bearish_ratio > 0.6:
                    market_condition = 'bearish'
                elif abs(bullish_ratio - bearish_ratio) < 0.2:
                    market_condition = 'neutral'
                else:
                    market_condition = 'volatile'
            else:
                market_condition = 'neutral'
            
            # 상위 신호 정렬
            top_signals.sort(key=lambda x: x['confidence'], reverse=True)
            
            analysis_info = {
                'symbols_analyzed': len(market_data),
                'top_signals': top_signals[:3],
                'market_condition': market_condition
            }
            
            self.telegram.send_market_analysis_log(analysis_info)
            
        except Exception as e:
            self.logger.error(f"시장 분석 로그 전송 실패: {e}")
    
    async def run_trading_cycle(self):
        """거래 사이클 실행"""
        try:
            cycle_start = time.time()
            self.cycle_count += 1
            
            self.logger.info(f"=== 하이브리드 거래 사이클 #{self.cycle_count} 시작 ===")
            
            # 1. 시장 데이터 수집
            market_data = await self.collect_market_data()
            
            if not market_data:
                self.logger.warning("시장 데이터가 없어 사이클을 건너뜁니다")
                return
            
            # 2. 전략 분석 및 실행
            executed_trades = self.analyze_and_execute_strategy(market_data)
            
            # 3. 포트폴리오 상태 업데이트
            self.portfolio_manager.update_portfolio_state()
            
            # 4. 리스크 모니터링
            alerts = self.risk_manager.get_risk_alerts()
            for alert in alerts:
                self.telegram.send_risk_alert(alert)
            
            # 5. 주기적 알림
            time_since_portfolio_update = datetime.now() - self.last_portfolio_update
            if time_since_portfolio_update > timedelta(hours=2):  # 2시간마다
                self._send_portfolio_update()
            
            time_since_daily_summary = datetime.now() - self.last_telegram_summary
            if time_since_daily_summary > timedelta(hours=24):  # 24시간마다
                self._send_daily_summary()
            
            cycle_duration = time.time() - cycle_start
            self.logger.info(f"사이클 #{self.cycle_count} 완료: {cycle_duration:.2f}초, "
                           f"거래 {len(executed_trades)}개 실행")
            
            # 6. 실시간 거래 사이클 로그 전송 (매 사이클마다)
            self._send_cycle_log(market_data, executed_trades, cycle_duration)
            
            # 7. 시장 분석 로그 전송 (10사이클마다, 약 10분마다)
            if self.cycle_count % 10 == 0:
                self._send_market_analysis_log(market_data)
            
            # 8. 성과 로그 전송 (30분마다, 사이클 30개마다)  
            if self.cycle_count % 30 == 0:
                self._send_performance_log()
            
        except Exception as e:
            self.logger.error(f"거래 사이클 실행 실패: {e}")
            
            # 오류 로그 전송
            error_info = {
                'type': 'trading_cycle_error',
                'message': str(e)[:200],
                'severity': 'high'
            }
            self.telegram.send_error_log(error_info)
            
            # 기존 리스크 알림도 유지
            error_alert = {
                'type': 'system_error',
                'symbol': 'SYSTEM',
                'severity': 'high',
                'message': f'거래 사이클 오류: {str(e)[:100]}'
            }
            self.telegram.send_risk_alert(error_alert)
    
    async def start(self):
        """봇 시작"""
        try:
            self.running = True
            self.logger.info("🚀 하이브리드 트레이딩 봇 v2 시작")
            
            while self.running:
                await self.run_trading_cycle()
                
                # 1분 대기
                await asyncio.sleep(60)
                
        except KeyboardInterrupt:
            self.logger.info("사용자에 의한 중단")
        except Exception as e:
            self.logger.error(f"봇 실행 실패: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """봇 중지"""
        self.running = False
        self.telegram.send_shutdown_message()
        self.logger.info("하이브리드 트레이딩 봇 v2 종료")


async def main():
    """메인 함수"""
    bot = HybridTradingBotV2()
    await bot.start()


if __name__ == "__main__":
    print("🚀 하이브리드 트레이딩 봇 v2 (현물 + 선물)")
    print("=" * 50)
    
    # 비동기 실행
    asyncio.run(main())