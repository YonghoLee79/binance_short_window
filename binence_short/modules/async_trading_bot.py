#!/usr/bin/env python3
"""
비동기 처리 최적화된 트레이딩 봇
"""

import asyncio
import aiohttp
import time
import concurrent.futures
from typing import Dict, Any, List, Optional
from datetime import datetime
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config
from utils import logger
from modules import (
    TechnicalAnalyzer,
    ExchangeInterface,
    StrategyEngine,
    RiskManager,
    PortfolioManager
)


class AsyncTradingBot:
    """비동기 처리 최적화된 트레이딩 봇"""
    
    def __init__(self):
        self.config = config
        self.logger = logger
        self.running = False
        
        # 컴포넌트 초기화
        self._initialize_components()
        
        # 비동기 처리용 세마포어 (동시 처리 제한)
        self.api_semaphore = asyncio.Semaphore(5)  # 최대 5개 동시 API 호출
        self.analysis_semaphore = asyncio.Semaphore(10)  # 최대 10개 동시 분석
        
        # 결과 캐시
        self.market_data_cache = {}
        self.cache_ttl = 60  # 캐시 유효 시간 (초)
        
        self.logger.info("비동기 트레이딩 봇 초기화 완료")
    
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
            
            self.logger.info("모든 컴포넌트 초기화 완료")
            
        except Exception as e:
            self.logger.error(f"컴포넌트 초기화 실패: {e}")
            raise
    
    async def fetch_market_data_async(self, symbol: str) -> Dict[str, Any]:
        """비동기 시장 데이터 수집"""
        try:
            # 캐시 확인
            cache_key = f"{symbol}_{int(time.time() // self.cache_ttl)}"
            if cache_key in self.market_data_cache:
                return self.market_data_cache[cache_key]
            
            async with self.api_semaphore:
                # 병렬로 현물/선물 데이터 수집
                tasks = [
                    self._fetch_ticker_async(symbol, 'spot'),
                    self._fetch_ticker_async(symbol, 'future'),
                    self._fetch_ohlcv_async(symbol, 'spot'),
                    self._fetch_ohlcv_async(symbol, 'future')
                ]
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                spot_ticker, futures_ticker, spot_ohlcv, futures_ohlcv = results
                
                # 오류 체크
                for result in results:
                    if isinstance(result, Exception):
                        self.logger.warning(f"시장 데이터 수집 중 오류: {result}")
                        return {}
                
                market_data = {
                    'symbol': symbol,
                    'spot_ticker': spot_ticker,
                    'futures_ticker': futures_ticker,
                    'spot_ohlcv': spot_ohlcv,
                    'futures_ohlcv': futures_ohlcv,
                    'timestamp': datetime.now()
                }
                
                # 캐시 저장
                self.market_data_cache[cache_key] = market_data
                
                return market_data
                
        except Exception as e:
            self.logger.error(f"비동기 시장 데이터 수집 실패 ({symbol}): {e}")
            return {}
    
    async def _fetch_ticker_async(self, symbol: str, exchange_type: str) -> Dict[str, Any]:
        """비동기 티커 데이터 수집"""
        return await asyncio.get_event_loop().run_in_executor(
            None, self.exchange.get_ticker, symbol, exchange_type
        )
    
    async def _fetch_ohlcv_async(self, symbol: str, exchange_type: str) -> Any:
        """비동기 OHLCV 데이터 수집"""
        return await asyncio.get_event_loop().run_in_executor(
            None, self.exchange.get_ohlcv, symbol, '1h', 100, exchange_type
        )
    
    async def analyze_market_async(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """비동기 시장 분석"""
        try:
            async with self.analysis_semaphore:
                # CPU 집약적 작업을 스레드 풀에서 실행
                analysis_task = asyncio.get_event_loop().run_in_executor(
                    None, self._analyze_market_sync, market_data
                )
                
                return await analysis_task
                
        except Exception as e:
            self.logger.error(f"비동기 시장 분석 실패: {e}")
            return {}
    
    def _analyze_market_sync(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """동기 시장 분석 (스레드 풀에서 실행)"""
        try:
            symbol = market_data['symbol']
            spot_ohlcv = market_data.get('spot_ohlcv')
            futures_ohlcv = market_data.get('futures_ohlcv')
            
            if spot_ohlcv is None or spot_ohlcv.empty or futures_ohlcv is None or futures_ohlcv.empty:
                return {}
            
            # 기술적 분석
            spot_indicators = self.technical_analyzer.get_all_indicators(spot_ohlcv)
            futures_indicators = self.technical_analyzer.get_all_indicators(futures_ohlcv)
            
            # 거래 신호 생성
            spot_signals = self.technical_analyzer.generate_signals(spot_indicators)
            futures_signals = self.technical_analyzer.generate_signals(futures_indicators)
            
            # 프리미엄 계산
            spot_price = market_data.get('spot_ticker', {}).get('last', 0)
            futures_price = market_data.get('futures_ticker', {}).get('last', 0)
            
            premium = 0
            if spot_price > 0 and futures_price > 0:
                premium = (futures_price - spot_price) / spot_price
            
            return {
                'symbol': symbol,
                'spot_price': spot_price,
                'futures_price': futures_price,
                'premium': premium,
                'spot_signals': spot_signals,
                'futures_signals': futures_signals,
                'spot_indicators': spot_indicators,
                'futures_indicators': futures_indicators,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"동기 시장 분석 실패: {e}")
            return {}
    
    async def process_symbols_async(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """여러 심볼을 비동기로 병렬 처리"""
        try:
            # 시장 데이터 수집 (병렬)
            market_data_tasks = [
                self.fetch_market_data_async(symbol) for symbol in symbols
            ]
            
            market_data_results = await asyncio.gather(
                *market_data_tasks, return_exceptions=True
            )
            
            # 분석 작업 (병렬)
            analysis_tasks = []
            for market_data in market_data_results:
                if isinstance(market_data, Exception):
                    self.logger.warning(f"시장 데이터 수집 실패: {market_data}")
                    continue
                
                if market_data:
                    analysis_tasks.append(self.analyze_market_async(market_data))
            
            analysis_results = await asyncio.gather(
                *analysis_tasks, return_exceptions=True
            )
            
            # 유효한 결과만 반환
            valid_results = []
            for result in analysis_results:
                if isinstance(result, Exception):
                    self.logger.warning(f"시장 분석 실패: {result}")
                    continue
                
                if result:
                    valid_results.append(result)
            
            return valid_results
            
        except Exception as e:
            self.logger.error(f"심볼 병렬 처리 실패: {e}")
            return []
    
    async def execute_trades_async(self, trade_decisions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """거래 결정들을 비동기로 실행"""
        try:
            trade_tasks = []
            
            for decision in trade_decisions:
                if decision.get('action') != 'hold':
                    task = self._execute_single_trade_async(decision)
                    trade_tasks.append(task)
            
            if not trade_tasks:
                return []
            
            # 거래 실행 (병렬)
            trade_results = await asyncio.gather(
                *trade_tasks, return_exceptions=True
            )
            
            # 결과 정리
            successful_trades = []
            for result in trade_results:
                if isinstance(result, Exception):
                    self.logger.error(f"거래 실행 실패: {result}")
                    continue
                
                if result and result.get('success'):
                    successful_trades.append(result)
            
            return successful_trades
            
        except Exception as e:
            self.logger.error(f"비동기 거래 실행 실패: {e}")
            return []
    
    async def _execute_single_trade_async(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """단일 거래를 비동기로 실행"""
        try:
            symbol = decision['symbol']
            side = decision['action']
            size = decision.get('size', 0)
            exchange_type = decision.get('exchange_type', 'spot')
            
            # 거래 실행을 스레드 풀에서 처리
            trade_result = await asyncio.get_event_loop().run_in_executor(
                None, 
                self.portfolio_manager.execute_trade,
                symbol, side, size, None, exchange_type, 'market'
            )
            
            return trade_result
            
        except Exception as e:
            self.logger.error(f"단일 거래 실행 실패: {e}")
            return {'success': False, 'error': str(e)}
    
    async def run_trading_cycle_async(self):
        """비동기 거래 사이클 실행"""
        try:
            cycle_start = time.time()
            
            # 1. 포트폴리오 상태 업데이트 (비동기)
            portfolio_task = asyncio.get_event_loop().run_in_executor(
                None, self.portfolio_manager.update_portfolio_state
            )
            
            # 2. 심볼 분석 (병렬)
            symbols_task = self.process_symbols_async(self.config.TRADING_SYMBOLS)
            
            # 3. 두 작업 동시 실행
            portfolio_result, analysis_results = await asyncio.gather(
                portfolio_task, symbols_task, return_exceptions=True
            )
            
            if isinstance(portfolio_result, Exception):
                self.logger.error(f"포트폴리오 업데이트 실패: {portfolio_result}")
            
            if isinstance(analysis_results, Exception):
                self.logger.error(f"심볼 분석 실패: {analysis_results}")
                return
            
            # 4. 거래 결정 생성
            trade_decisions = []
            for analysis_result in analysis_results:
                decision = await asyncio.get_event_loop().run_in_executor(
                    None, self.strategy_engine.generate_trade_decision, analysis_result
                )
                
                if decision and decision.get('final_decision', {}).get('strategy') != 'hold':
                    trade_decisions.append({
                        'symbol': analysis_result['symbol'],
                        'action': 'buy',  # 예시
                        'size': 0.001,    # 예시
                        'exchange_type': 'spot'
                    })
            
            # 5. 거래 실행 (병렬)
            if trade_decisions:
                trade_results = await self.execute_trades_async(trade_decisions)
                self.logger.info(f"거래 실행 완료: {len(trade_results)}개 성공")
            
            # 6. 리스크 알림 확인
            alerts = self.risk_manager.get_risk_alerts()
            if alerts:
                self.logger.warning(f"리스크 알림: {len(alerts)}개")
            
            cycle_duration = time.time() - cycle_start
            self.logger.info(f"비동기 거래 사이클 완료: {cycle_duration:.2f}초")
            
        except Exception as e:
            self.logger.error(f"비동기 거래 사이클 실패: {e}")
    
    async def start_async(self):
        """비동기 봇 시작"""
        try:
            self.running = True
            self.logger.info("비동기 트레이딩 봇 시작")
            
            cycle_count = 0
            
            while self.running:
                cycle_count += 1
                self.logger.info(f"비동기 거래 사이클 #{cycle_count} 시작")
                
                # 거래 사이클 실행
                await self.run_trading_cycle_async()
                
                # 대기 (60초)
                await asyncio.sleep(60)
                
                # 캐시 정리 (주기적)
                if cycle_count % 10 == 0:
                    await self._cleanup_cache()
                
        except Exception as e:
            self.logger.error(f"비동기 봇 실행 실패: {e}")
        finally:
            self.running = False
            self.logger.info("비동기 트레이딩 봇 종료")
    
    async def _cleanup_cache(self):
        """캐시 정리"""
        try:
            current_time = time.time()
            expired_keys = [
                key for key in self.market_data_cache.keys()
                if current_time - int(key.split('_')[-1]) * self.cache_ttl > self.cache_ttl
            ]
            
            for key in expired_keys:
                del self.market_data_cache[key]
            
            if expired_keys:
                self.logger.debug(f"캐시 정리 완료: {len(expired_keys)}개 항목 제거")
                
        except Exception as e:
            self.logger.error(f"캐시 정리 실패: {e}")
    
    def stop(self):
        """봇 중지"""
        self.running = False
        self.logger.info("비동기 봇 중지 요청됨")


async def main():
    """메인 함수"""
    try:
        bot = AsyncTradingBot()
        await bot.start_async()
        
    except KeyboardInterrupt:
        logger.info("사용자에 의한 중단")
    except Exception as e:
        logger.error(f"비동기 봇 실행 실패: {e}")


if __name__ == "__main__":
    print("🚀 비동기 처리 최적화된 트레이딩 봇")
    print("=" * 50)
    
    # 비동기 실행
    asyncio.run(main())