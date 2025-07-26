"""
거래소 인터페이스 모듈
"""
import ccxt
import pandas as pd
import time
from typing import Dict, Any, List, Optional, Tuple
from utils.logger import logger
from utils.decorators import retry_on_network_error, rate_limit, log_execution_time


class ExchangeInterface:
    """거래소 인터페이스 클래스"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.spot_exchange = None
        self.futures_exchange = None
        self.setup_exchanges()
    
    def setup_exchanges(self):
        """거래소 연결 설정"""
        try:
            use_testnet = self.config.get('use_testnet', False)
            
            # 테스트넷 사용시 테스트넷 API 키 사용
            if use_testnet:
                api_key = self.config.get('testnet_api_key', self.config['api_key'])
                secret_key = self.config.get('testnet_secret_key', self.config['secret_key'])
            else:
                api_key = self.config['api_key']
                secret_key = self.config['secret_key']
            
            # 현물 거래소 설정
            self.spot_exchange = ccxt.binance({
                'apiKey': api_key,
                'secret': secret_key,
                'sandbox': use_testnet,
                'defaultType': 'spot',
                'options': {
                    'adjustForTimeDifference': True,
                    'recvWindow': 60000,
                }
            })
            
            # 선물 거래소 설정
            self.futures_exchange = ccxt.binance({
                'apiKey': api_key,
                'secret': secret_key,
                'sandbox': use_testnet,
                'defaultType': 'future',
                'options': {
                    'adjustForTimeDifference': True,
                    'recvWindow': 60000,
                }
            })
            
            # 사용 가능한 심볼 목록 캐시
            self._available_symbols = {'spot': set(), 'future': set()}
            self._load_available_symbols()
            
            logger.info("거래소 연결 설정 완료")
        except Exception as e:
            logger.error(f"거래소 연결 설정 실패: {e}")
            raise
    
    def _load_available_symbols(self):
        """사용 가능한 심볼 목록 로드"""
        try:
            # 현물 심볼 로드
            if self.spot_exchange:
                spot_markets = self.spot_exchange.load_markets()
                self._available_symbols['spot'] = set(spot_markets.keys())
                logger.info(f"현물 심볼 {len(self._available_symbols['spot'])}개 로드됨")
            
            # 선물 심볼 로드
            if self.futures_exchange:
                futures_markets = self.futures_exchange.load_markets()
                self._available_symbols['future'] = set(futures_markets.keys())
                logger.info(f"선물 심볼 {len(self._available_symbols['future'])}개 로드됨")
                
        except Exception as e:
            logger.error(f"심볼 목록 로드 실패: {e}")
            # 실패 시 빈 set 유지
    
    def _is_symbol_available(self, symbol: str, exchange_type: str) -> bool:
        """심볼이 해당 거래소에서 사용 가능한지 확인"""
        try:
            if exchange_type not in self._available_symbols:
                return False
            return symbol in self._available_symbols[exchange_type]
        except Exception:
            # 확인할 수 없으면 True 반환 (기존 동작 유지)
            return True
    
    @retry_on_network_error(max_retries=3)
    @rate_limit(calls_per_second=0.5)
    def get_spot_balance(self) -> Dict[str, float]:
        """현물 잔고 조회"""
        try:
            if not self.spot_exchange:
                logger.error("현물 거래소 연결이 설정되지 않았습니다")
                return {'total': {}, 'free': {}, 'used': {}}
            
            balance = self.spot_exchange.fetch_balance()
            return {
                'total': balance['total'],
                'free': balance['free'],
                'used': balance['used']
            }
        except ccxt.AuthenticationError as e:
            logger.error(f"API 키 인증 오류: {e}")
            # API 키 문제일 때는 재시도하지 않고 빈 잔고 반환
            return {'total': {'USDT': 0}, 'free': {'USDT': 0}, 'used': {'USDT': 0}}
        except ccxt.PermissionDenied as e:
            logger.error(f"API 키 권한 오류: {e}")
            return {'total': {'USDT': 0}, 'free': {'USDT': 0}, 'used': {'USDT': 0}}
        except Exception as e:
            logger.error(f"현물 잔고 조회 실패: {e}")
            return {'total': {}, 'free': {}, 'used': {}}
    
    @retry_on_network_error(max_retries=3)
    @rate_limit(calls_per_second=0.5)
    def get_futures_balance(self) -> Dict[str, float]:
        """선물 잔고 조회"""
        try:
            if not self.futures_exchange:
                logger.error("선물 거래소 연결이 설정되지 않았습니다")
                return {'total': {}, 'free': {}, 'used': {}}
            
            balance = self.futures_exchange.fetch_balance()
            return {
                'total': balance['total'],
                'free': balance['free'],
                'used': balance['used']
            }
        except ccxt.AuthenticationError as e:
            logger.error(f"API 키 인증 오류: {e}")
            return {'total': {'USDT': 0}, 'free': {'USDT': 0}, 'used': {'USDT': 0}}
        except ccxt.PermissionDenied as e:
            logger.error(f"API 키 권한 오류: {e}")
            return {'total': {'USDT': 0}, 'free': {'USDT': 0}, 'used': {'USDT': 0}}
        except Exception as e:
            logger.error(f"선물 잔고 조회 실패: {e}")
            return {'total': {}, 'free': {}, 'used': {}}
    
    @retry_on_network_error(max_retries=3)
    @rate_limit(calls_per_second=1.0)
    def get_ticker(self, symbol: str, exchange_type: str = 'spot') -> Dict[str, Any]:
        """심볼 가격 정보 조회"""
        try:
            exchange = self.spot_exchange if exchange_type == 'spot' else self.futures_exchange
            
            # 심볼 유효성 검사
            if not self._is_symbol_available(symbol, exchange_type):
                logger.warning(f"심볼이 존재하지 않음: {symbol} ({exchange_type})")
                return {}
            
            ticker = exchange.fetch_ticker(symbol)
            return {
                'symbol': symbol,
                'last': ticker['last'],
                'bid': ticker['bid'],
                'ask': ticker['ask'],
                'volume': ticker['baseVolume'],
                'change': ticker['change'],
                'percentage': ticker['percentage'],
                'timestamp': ticker['timestamp']
            }
        except ccxt.BadSymbol as e:
            logger.warning(f"잘못된 심볼: {symbol} ({exchange_type}) - {e}")
            return {}
        except Exception as e:
            logger.error(f"가격 정보 조회 실패 ({symbol}): {e}")
            return {}
    
    @retry_on_network_error(max_retries=3)
    @rate_limit(calls_per_second=0.5)
    def get_orderbook(self, symbol: str, limit: int = 100, exchange_type: str = 'spot') -> Dict[str, Any]:
        """호가창 정보 조회"""
        try:
            exchange = self.spot_exchange if exchange_type == 'spot' else self.futures_exchange
            orderbook = exchange.fetch_order_book(symbol, limit)
            return {
                'symbol': symbol,
                'bids': orderbook['bids'],
                'asks': orderbook['asks'],
                'timestamp': orderbook['timestamp']
            }
        except Exception as e:
            logger.error(f"호가창 조회 실패 ({symbol}): {e}")
            return {}
    
    @retry_on_network_error(max_retries=3)
    @rate_limit(calls_per_second=0.2)
    def get_ohlcv(self, symbol: str, timeframe: str = '1h', limit: int = 500, exchange_type: str = 'spot') -> pd.DataFrame:
        """캔들 데이터 조회"""
        try:
            exchange = self.spot_exchange if exchange_type == 'spot' else self.futures_exchange
            
            # 심볼 유효성 검사
            if not self._is_symbol_available(symbol, exchange_type):
                logger.warning(f"심볼이 존재하지 않음: {symbol} ({exchange_type})")
                return pd.DataFrame()
            
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            if not ohlcv:
                logger.warning(f"OHLCV 데이터가 비어있음: {symbol}")
                return pd.DataFrame()
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            return df
        except ccxt.BadSymbol as e:
            logger.warning(f"잘못된 심볼: {symbol} ({exchange_type}) - {e}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"캔들 데이터 조회 실패 ({symbol}): {e}")
            return pd.DataFrame()
    
    @retry_on_network_error(max_retries=3)
    @rate_limit(calls_per_second=0.5)
    def place_order(self, symbol: str, side: str, amount: float, price: float = None, 
                   order_type: str = 'market', exchange_type: str = 'spot') -> Dict[str, Any]:
        """주문 생성"""
        try:
            exchange = self.spot_exchange if exchange_type == 'spot' else self.futures_exchange
            
            if order_type == 'market':
                order = exchange.create_market_order(symbol, side, amount)
            else:
                order = exchange.create_limit_order(symbol, side, amount, price)
            
            logger.info(f"주문 생성 완료: {symbol} {side} {amount} @ {price}")
            return {
                'id': order['id'],
                'symbol': order['symbol'],
                'side': order['side'],
                'amount': order['amount'],
                'price': order['price'],
                'type': order['type'],
                'status': order['status'],
                'timestamp': order['timestamp']
            }
        except Exception as e:
            logger.error(f"주문 생성 실패 ({symbol} {side} {amount}): {e}")
            return {}

    def execute_smart_order(self, symbol: str, side: str, amount: float, 
                           exchange_type: str = 'spot', strategy_type: str = 'default') -> Dict[str, Any]:
        """스마트 주문 실행 시스템"""
        try:
            # 1. 시장 상황 분석
            market_analysis = self._analyze_market_conditions(symbol, exchange_type)
            
            # 2. 최적 주문 타입 결정
            optimal_order_type = self._determine_optimal_order_type(
                market_analysis, amount, strategy_type
            )
            
            # 3. 주문 실행
            if optimal_order_type == 'twap':
                return self._execute_twap_order(symbol, side, amount, exchange_type)
            elif optimal_order_type == 'iceberg':
                return self._execute_iceberg_order(symbol, side, amount, exchange_type)
            elif optimal_order_type == 'smart_limit':
                return self._execute_smart_limit_order(symbol, side, amount, exchange_type)
            else:
                # 기본 지정가 주문
                current_price = self._get_current_price(symbol, exchange_type)
                spread = self._get_bid_ask_spread(symbol, exchange_type)
                
                # 스프레드의 30% 지점에 주문 (더 나은 가격 확보)
                if side == 'buy':
                    limit_price = current_price - (spread * 0.3)
                else:
                    limit_price = current_price + (spread * 0.3)
                
                return self.place_order(symbol, side, amount, limit_price, 'limit', exchange_type)
                
        except Exception as e:
            logger.error(f"스마트 주문 실행 실패: {e}")
            # 실패시 기본 시장가 주문으로 폴백
            return self.place_order(symbol, side, amount, None, 'market', exchange_type)

    def _analyze_market_conditions(self, symbol: str, exchange_type: str) -> Dict[str, Any]:
        """시장 상황 분석"""
        try:
            # 최근 캔들 데이터 가져오기
            df = self.get_ohlcv(symbol, '1m', 20, exchange_type)
            if df.empty:
                return {'volatility': 0.02, 'liquidity': 'normal', 'trend': 'neutral'}
            
            # 변동성 계산 (ATR 기반)
            high_low = df['high'] - df['low']
            high_close = abs(df['high'] - df['close'].shift(1))
            low_close = abs(df['low'] - df['close'].shift(1))
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = true_range.rolling(14).mean().iloc[-1]
            volatility = atr / df['close'].iloc[-1]
            
            # 거래량 분석
            avg_volume = df['volume'].rolling(10).mean().iloc[-1]
            current_volume = df['volume'].iloc[-1]
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
            
            # 유동성 평가
            if volume_ratio > 1.5:
                liquidity = 'high'
            elif volume_ratio < 0.5:
                liquidity = 'low'
            else:
                liquidity = 'normal'
            
            return {
                'volatility': volatility,
                'liquidity': liquidity,
                'volume_ratio': volume_ratio,
                'atr': atr
            }
        except Exception as e:
            logger.error(f"시장 상황 분석 실패: {e}")
            return {'volatility': 0.02, 'liquidity': 'normal', 'volume_ratio': 1.0}

    def _determine_optimal_order_type(self, market_analysis: Dict[str, Any], 
                                     amount: float, strategy_type: str) -> str:
        """최적 주문 타입 결정"""
        try:
            volatility = market_analysis.get('volatility', 0.02)
            liquidity = market_analysis.get('liquidity', 'normal')
            
            # 고변동성 시장 → TWAP (시간분산)
            if volatility > 0.03:
                return 'twap'
            
            # 유동성 부족 → 빙산주문
            if liquidity == 'low':
                return 'iceberg'
            
            # 아비트라지 전략 → 즉시 체결 우선
            if strategy_type == 'arbitrage':
                return 'smart_limit'
            
            # 기본적으로 스마트 지정가
            return 'smart_limit'
            
        except Exception as e:
            logger.error(f"주문 타입 결정 실패: {e}")
            return 'smart_limit'

    def _execute_twap_order(self, symbol: str, side: str, amount: float, 
                           exchange_type: str, duration_minutes: int = 5) -> Dict[str, Any]:
        """TWAP (시간가중평균가격) 주문 실행"""
        try:
            import asyncio
            import time
            
            # 주문을 5개로 분할
            num_splits = 5
            split_amount = amount / num_splits
            interval_seconds = (duration_minutes * 60) / num_splits
            
            executed_orders = []
            total_executed_amount = 0
            total_executed_value = 0
            
            for i in range(num_splits):
                try:
                    order = self.place_order(symbol, side, split_amount, None, 'market', exchange_type)
                    if order and order.get('id'):
                        executed_orders.append(order)
                        total_executed_amount += order.get('amount', 0)
                        total_executed_value += order.get('amount', 0) * order.get('price', 0)
                        
                        if i < num_splits - 1:  # 마지막 주문이 아니면 대기
                            time.sleep(interval_seconds)
                except Exception as e:
                    logger.error(f"TWAP 주문 {i+1}/{num_splits} 실패: {e}")
                    continue
            
            # 평균 실행 가격 계산
            avg_price = total_executed_value / total_executed_amount if total_executed_amount > 0 else 0
            
            return {
                'id': f"twap_{symbol}_{int(time.time())}",
                'symbol': symbol,
                'side': side,
                'amount': total_executed_amount,
                'price': avg_price,
                'type': 'twap',
                'status': 'filled' if total_executed_amount > 0 else 'failed',
                'timestamp': time.time() * 1000,
                'sub_orders': executed_orders
            }
            
        except Exception as e:
            logger.error(f"TWAP 주문 실행 실패: {e}")
            return self.place_order(symbol, side, amount, None, 'market', exchange_type)

    def _execute_iceberg_order(self, symbol: str, side: str, amount: float, 
                              exchange_type: str) -> Dict[str, Any]:
        """빙산 주문 실행 (대량 주문을 작은 단위로 분할)"""
        try:
            import time
            
            # 주문을 10%씩 분할하여 실행
            chunk_size = amount * 0.1
            remaining_amount = amount
            executed_orders = []
            
            while remaining_amount > chunk_size:
                current_chunk = min(chunk_size, remaining_amount)
                
                # 현재 가격 기준으로 지정가 주문
                current_price = self._get_current_price(symbol, exchange_type)
                spread = self._get_bid_ask_spread(symbol, exchange_type)
                
                if side == 'buy':
                    limit_price = current_price - (spread * 0.2)  # 매수는 현재가보다 약간 낮게
                else:
                    limit_price = current_price + (spread * 0.2)  # 매도는 현재가보다 약간 높게
                
                order = self.place_order(symbol, side, current_chunk, limit_price, 'limit', exchange_type)
                
                if order and order.get('id'):
                    executed_orders.append(order)
                    remaining_amount -= current_chunk
                    
                    # 주문 간 짧은 대기
                    time.sleep(2)
                else:
                    break
            
            # 남은 수량이 있으면 시장가로 처리
            if remaining_amount > 0:
                final_order = self.place_order(symbol, side, remaining_amount, None, 'market', exchange_type)
                if final_order:
                    executed_orders.append(final_order)
            
            # 결과 집계
            total_amount = sum(order.get('amount', 0) for order in executed_orders)
            total_value = sum(order.get('amount', 0) * order.get('price', 0) for order in executed_orders)
            avg_price = total_value / total_amount if total_amount > 0 else 0
            
            return {
                'id': f"iceberg_{symbol}_{int(time.time())}",
                'symbol': symbol,
                'side': side,
                'amount': total_amount,
                'price': avg_price,
                'type': 'iceberg',
                'status': 'filled' if total_amount > 0 else 'failed',
                'timestamp': time.time() * 1000,
                'sub_orders': executed_orders
            }
            
        except Exception as e:
            logger.error(f"빙산 주문 실행 실패: {e}")
            return self.place_order(symbol, side, amount, None, 'market', exchange_type)

    def _execute_smart_limit_order(self, symbol: str, side: str, amount: float, 
                                  exchange_type: str) -> Dict[str, Any]:
        """스마트 지정가 주문 (최적 가격 자동 계산)"""
        try:
            import time
            
            # 현재 시장 상황 분석
            current_price = self._get_current_price(symbol, exchange_type)
            spread = self._get_bid_ask_spread(symbol, exchange_type)
            
            # 최적 가격 계산 (스프레드 중간 지점)
            if side == 'buy':
                optimal_price = current_price - (spread * 0.4)  # 매수: 더 공격적
            else:
                optimal_price = current_price + (spread * 0.4)  # 매도: 더 공격적
            
            # 지정가 주문 실행
            order = self.place_order(symbol, side, amount, optimal_price, 'limit', exchange_type)
            
            # 5초 후에도 체결되지 않으면 가격 조정
            if order and order.get('id'):
                time.sleep(5)
                order_status = self.get_order_status(order['id'], symbol, exchange_type)
                
                if order_status.get('status') != 'closed':
                    # 주문 취소 후 더 공격적인 가격으로 재주문
                    self.cancel_order(order['id'], symbol, exchange_type)
                    
                    if side == 'buy':
                        new_price = current_price - (spread * 0.1)  # 더 높은 가격
                    else:
                        new_price = current_price + (spread * 0.1)  # 더 낮은 가격
                    
                    return self.place_order(symbol, side, amount, new_price, 'limit', exchange_type)
            
            return order
            
        except Exception as e:
            logger.error(f"스마트 지정가 주문 실행 실패: {e}")
            return self.place_order(symbol, side, amount, None, 'market', exchange_type)

    def _get_current_price(self, symbol: str, exchange_type: str) -> float:
        """현재 가격 조회"""
        try:
            ticker = self.get_ticker(symbol, exchange_type)
            return ticker.get('last', 0)
        except Exception as e:
            logger.error(f"현재 가격 조회 실패: {e}")
            return 0

    def _get_bid_ask_spread(self, symbol: str, exchange_type: str) -> float:
        """매수-매도 스프레드 계산"""
        try:
            ticker = self.get_ticker(symbol, exchange_type)
            bid = ticker.get('bid', 0)
            ask = ticker.get('ask', 0)
            if bid > 0 and ask > 0:
                return ask - bid
            return 0
        except Exception as e:
            logger.error(f"스프레드 계산 실패: {e}")
            return 0
    
    @retry_on_network_error(max_retries=3)
    @rate_limit(calls_per_second=0.5)
    def cancel_order(self, order_id: str, symbol: str, exchange_type: str = 'spot') -> bool:
        """주문 취소"""
        try:
            exchange = self.spot_exchange if exchange_type == 'spot' else self.futures_exchange
            exchange.cancel_order(order_id, symbol)
            logger.info(f"주문 취소 완료: {order_id}")
            return True
        except Exception as e:
            logger.error(f"주문 취소 실패 ({order_id}): {e}")
            return False
    
    @retry_on_network_error(max_retries=3)
    @rate_limit(calls_per_second=0.5)
    def get_order_status(self, order_id: str, symbol: str, exchange_type: str = 'spot') -> Dict[str, Any]:
        """주문 상태 조회"""
        try:
            exchange = self.spot_exchange if exchange_type == 'spot' else self.futures_exchange
            order = exchange.fetch_order(order_id, symbol)
            return {
                'id': order['id'],
                'symbol': order['symbol'],
                'side': order['side'],
                'amount': order['amount'],
                'filled': order['filled'],
                'remaining': order['remaining'],
                'price': order['price'],
                'status': order['status'],
                'timestamp': order['timestamp']
            }
        except Exception as e:
            logger.error(f"주문 상태 조회 실패 ({order_id}): {e}")
            return {}
    
    @retry_on_network_error(max_retries=3)
    @rate_limit(calls_per_second=0.5)
    def get_open_orders(self, symbol: str = None, exchange_type: str = 'spot') -> List[Dict[str, Any]]:
        """미체결 주문 조회"""
        try:
            exchange = self.spot_exchange if exchange_type == 'spot' else self.futures_exchange
            orders = exchange.fetch_open_orders(symbol)
            return [
                {
                    'id': order['id'],
                    'symbol': order['symbol'],
                    'side': order['side'],
                    'amount': order['amount'],
                    'price': order['price'],
                    'type': order['type'],
                    'status': order['status'],
                    'timestamp': order['timestamp']
                }
                for order in orders
            ]
        except Exception as e:
            logger.error(f"미체결 주문 조회 실패: {e}")
            return []
    
    @retry_on_network_error(max_retries=3)
    @rate_limit(calls_per_second=0.5)
    def get_trading_fees(self, symbol: str, exchange_type: str = 'spot') -> Dict[str, float]:
        """거래 수수료 조회"""
        try:
            exchange = self.spot_exchange if exchange_type == 'spot' else self.futures_exchange
            fees = exchange.fetch_trading_fees()
            
            if symbol in fees:
                return {
                    'maker': fees[symbol]['maker'],
                    'taker': fees[symbol]['taker']
                }
            else:
                # 기본 수수료 반환
                return {
                    'maker': 0.001 if exchange_type == 'spot' else 0.0002,
                    'taker': 0.001 if exchange_type == 'spot' else 0.0004
                }
        except Exception as e:
            logger.error(f"거래 수수료 조회 실패: {e}")
            return {
                'maker': 0.001 if exchange_type == 'spot' else 0.0002,
                'taker': 0.001 if exchange_type == 'spot' else 0.0004
            }
    
    @retry_on_network_error(max_retries=3)
    @rate_limit(calls_per_second=0.5)
    def get_positions(self, symbol: str = None) -> List[Dict[str, Any]]:
        """선물 포지션 조회"""
        try:
            if not self.futures_exchange:
                logger.warning("선물 거래소 연결이 설정되지 않았습니다")
                return []
            
            positions = self.futures_exchange.fetch_positions(symbol)
            return [
                {
                    'symbol': pos['symbol'],
                    'side': pos['side'],
                    'size': pos['size'],
                    'contracts': pos['contracts'],
                    'contractSize': pos['contractSize'],
                    'unrealizedPnl': pos['unrealizedPnl'],
                    'percentage': pos['percentage'],
                    'entryPrice': pos['entryPrice'],
                    'markPrice': pos['markPrice'],
                    'timestamp': pos['timestamp']
                }
                for pos in positions if pos['contracts'] > 0
            ]
        except ccxt.AuthenticationError as e:
            logger.error(f"API 키 인증 오류: {e}")
            return []
        except ccxt.PermissionDenied as e:
            logger.error(f"API 키 권한 오류: {e}")
            return []
        except Exception as e:
            logger.error(f"포지션 조회 실패: {e}")
            return []
    
    @retry_on_network_error(max_retries=3)
    @rate_limit(calls_per_second=0.5)
    def set_leverage(self, symbol: str, leverage: int) -> bool:
        """레버리지 설정"""
        try:
            if self.futures_exchange:
                self.futures_exchange.set_leverage(leverage, symbol)
                logger.info(f"레버리지 설정 완료: {symbol} {leverage}x")
                return True
            return False
        except Exception as e:
            logger.error(f"레버리지 설정 실패 ({symbol} {leverage}x): {e}")
            return False
    
    @retry_on_network_error(max_retries=3)
    @rate_limit(calls_per_second=0.5)
    def set_margin_mode(self, symbol: str, margin_mode: str = 'isolated') -> bool:
        """마진 모드 설정"""
        try:
            if self.futures_exchange:
                self.futures_exchange.set_margin_mode(margin_mode, symbol)
                logger.info(f"마진 모드 설정 완료: {symbol} {margin_mode}")
                return True
            return False
        except Exception as e:
            logger.error(f"마진 모드 설정 실패 ({symbol} {margin_mode}): {e}")
            return False
    
    @log_execution_time
    def get_market_info(self, symbol: str) -> Dict[str, Any]:
        """시장 정보 조회"""
        try:
            spot_ticker = self.get_ticker(symbol, 'spot')
            futures_ticker = self.get_ticker(symbol, 'future')
            
            # 프리미엄 계산
            premium = 0
            if spot_ticker.get('last') and futures_ticker.get('last'):
                premium = (futures_ticker['last'] - spot_ticker['last']) / spot_ticker['last']
            
            return {
                'symbol': symbol,
                'spot_price': spot_ticker.get('last', 0),
                'futures_price': futures_ticker.get('last', 0),
                'premium': premium,
                'spot_volume': spot_ticker.get('volume', 0),
                'futures_volume': futures_ticker.get('volume', 0),
                'timestamp': time.time()
            }
        except Exception as e:
            logger.error(f"시장 정보 조회 실패 ({symbol}): {e}")
            return {}
    
    @retry_on_network_error(max_retries=3)
    @rate_limit(calls_per_second=0.5)
    def get_deposit_address(self, currency: str, network: str = None) -> Dict[str, Any]:
        """입금 주소 조회"""
        try:
            if not self.spot_exchange:
                logger.error("현물 거래소 연결이 설정되지 않았습니다")
                return {}
            
            # Binance API를 통한 입금 주소 조회
            if network:
                address_info = self.spot_exchange.fetch_deposit_address(currency, network)
            else:
                address_info = self.spot_exchange.fetch_deposit_address(currency)
            
            return {
                'currency': currency,
                'address': address_info.get('address', ''),
                'tag': address_info.get('tag', ''),
                'network': address_info.get('network', network),
                'info': address_info.get('info', {})
            }
            
        except Exception as e:
            logger.error(f"입금 주소 조회 실패 ({currency}): {e}")
            return {}
    
    @retry_on_network_error(max_retries=3)
    @rate_limit(calls_per_second=0.5)
    def get_balance(self, currency: str = 'USDT', exchange_type: str = 'spot') -> Dict[str, float]:
        """잔고 조회"""
        try:
            exchange = self.spot_exchange if exchange_type == 'spot' else self.futures_exchange
            balance = exchange.fetch_balance()
            
            if currency in balance:
                return {
                    'free': float(balance[currency]['free']),
                    'used': float(balance[currency]['used']),
                    'total': float(balance[currency]['total'])
                }
            else:
                return {'free': 0.0, 'used': 0.0, 'total': 0.0}
                
        except Exception as e:
            logger.error(f"잔고 조회 실패 ({currency} {exchange_type}): {e}")
            return {'free': 0.0, 'used': 0.0, 'total': 0.0}
    
    def is_exchange_available(self, exchange_type: str = 'both') -> bool:
        """거래소 연결 상태 확인"""
        try:
            if exchange_type == 'spot' or exchange_type == 'both':
                if self.spot_exchange:
                    self.spot_exchange.fetch_balance()
            
            if exchange_type == 'futures' or exchange_type == 'both':
                if self.futures_exchange:
                    self.futures_exchange.fetch_balance()
            
            return True
        except Exception as e:
            logger.error(f"거래소 연결 상태 확인 실패: {e}")
            return False