#!/usr/bin/env python3
"""
Upbit API 인터페이스
한국 규제 환경에서 USDT 구매 및 전송 관리
"""

import hashlib
import hmac
import time
import uuid
# JWT 모듈 import
JWT_AVAILABLE = False
_jwt_module = None

# 먼저 표준 jwt 모듈 시도
try:
    import jwt
    if hasattr(jwt, 'encode') and hasattr(jwt, 'decode'):
        JWT_AVAILABLE = True
        _jwt_module = jwt
        print(f"JWT module successfully loaded for Upbit API (version: {getattr(jwt, '__version__', 'unknown')})")
    else:
        print("Warning: Invalid JWT module. Upbit functionality will be limited.")
except ImportError as e:
    print(f"Warning: JWT module not available ({e}). Upbit functionality will be limited.")
import requests
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode
# PyUpbit 모듈 조건부 import
PYUPBIT_AVAILABLE = False
_pyupbit_module = None
try:
    import pyupbit
    PYUPBIT_AVAILABLE = True
    _pyupbit_module = pyupbit
    print("PyUpbit module successfully loaded")
except ImportError as e:
    print(f"Warning: pyupbit module not available ({e}). Some Upbit functionality will be limited.")

import logging

logger = logging.getLogger(__name__)


class UpbitInterface:
    """Upbit 거래소 API 인터페이스"""
    
    def __init__(self, config: Dict[str, Any]):
        self.access_key = config.get('upbit_access_key', '')
        self.secret_key = config.get('upbit_secret_key', '')
        self.base_url = "https://api.upbit.com"
        self.session = requests.Session()
        
        # PyUpbit 인터페이스 (읽기 전용 작업용)
        if PYUPBIT_AVAILABLE and _pyupbit_module:
            try:
                self.upbit = _pyupbit_module.Upbit(self.access_key, self.secret_key) if self.access_key else None
            except Exception as e:
                logger.warning(f"PyUpbit 인터페이스 초기화 실패: {e}")
                self.upbit = None
        else:
            self.upbit = None
        
        # 거래 제한 관리
        self.last_trade_time = {}
        self.min_trade_interval = 3  # 3초 간격
        
        # API 사용 가능 여부 확인
        self.api_available = JWT_AVAILABLE and bool(self.access_key and self.secret_key)
        
        
        if not self.api_available:
            missing = []
            if not JWT_AVAILABLE:
                missing.append("JWT 모듈")
            if not self.access_key:
                missing.append("Access Key")
            if not self.secret_key:
                missing.append("Secret Key")
            logger.warning(f"Upbit API 사용 불가: {', '.join(missing)} 누락")
        else:
            logger.info("Upbit 인터페이스 초기화 완료 - API 사용 가능")
    
    def _generate_jwt_token(self, query_params: Optional[Dict] = None) -> str:
        """JWT 토큰 생성"""
        if not JWT_AVAILABLE or not _jwt_module:
            logger.error("JWT 모듈이 없어 Upbit API 인증을 할 수 없습니다")
            return ""
            
        payload = {
            'access_key': self.access_key,
            'nonce': str(uuid.uuid4()),
        }
        
        if query_params:
            query_string = urlencode(query_params, doseq=True, safe='')
            m = hashlib.sha512()
            m.update(query_string.encode())
            query_hash = m.hexdigest()
            
            payload['query_hash'] = query_hash
            payload['query_hash_alg'] = 'SHA512'
        
        return _jwt_module.encode(payload, self.secret_key, algorithm='HS256')
    
    def _make_authenticated_request(self, method: str, endpoint: str, 
                                  params: Optional[Dict] = None, 
                                  data: Optional[Dict] = None) -> Dict[str, Any]:
        """인증된 API 요청"""
        try:
            url = f"{self.base_url}{endpoint}"
            
            if method.upper() == 'GET' and params:
                token = self._generate_jwt_token(params)
            elif method.upper() == 'POST' and data:
                token = self._generate_jwt_token(data)
            else:
                token = self._generate_jwt_token()
            
            headers = {'Authorization': f'Bearer {token}'}
            
            if method.upper() == 'GET':
                response = self.session.get(url, headers=headers, params=params)
            elif method.upper() == 'POST':
                headers['Content-Type'] = 'application/json'
                response = self.session.post(url, headers=headers, json=data)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, headers=headers, params=params)
            else:
                raise ValueError(f"지원하지 않는 HTTP 메소드: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Upbit API 요청 실패: {e}")
            return {'error': str(e)}
        except Exception as e:
            logger.error(f"API 요청 처리 중 오류: {e}")
            return {'error': str(e)}
    
    def get_balance(self, currency: str = 'KRW') -> float:
        """잔고 조회"""
        if not self.api_available:
            logger.warning("Upbit API를 사용할 수 없어 잔고 조회를 건너뜁니다")
            return 0.0
            
        try:
            accounts = self._make_authenticated_request('GET', '/v1/accounts')
            
            if 'error' in accounts:
                logger.error(f"잔고 조회 실패: {accounts['error']}")
                return 0.0
            
            for account in accounts:
                if account['currency'] == currency:
                    return float(account['balance'])
            
            return 0.0
            
        except Exception as e:
            logger.error(f"잔고 조회 중 오류: {e}")
            return 0.0
    
    def get_usdt_balance(self) -> float:
        """USDT 잔고 조회"""
        return self.get_balance('USDT')
    
    def get_krw_balance(self) -> float:
        """KRW 잔고 조회"""
        return self.get_balance('KRW')
    
    def get_all_balances(self) -> Dict[str, float]:
        """모든 보유 자산 잔고 조회"""
        if not self.api_available:
            logger.warning("Upbit API를 사용할 수 없어 잔고 조회를 건너뜁니다")
            return {}
            
        try:
            accounts = self._make_authenticated_request('GET', '/v1/accounts')
            
            if 'error' in accounts:
                logger.error(f"잔고 조회 실패: {accounts['error']}")
                return {}
            
            balances = {}
            for account in accounts:
                currency = account['currency']
                balance = float(account['balance'])
                locked = float(account['locked'])
                
                # 잔고가 있는 통화만 포함
                if balance > 0 or locked > 0:
                    balances[currency] = {
                        'balance': balance,
                        'locked': locked,
                        'total': balance + locked
                    }
            
            return balances
            
        except Exception as e:
            logger.error(f"전체 잔고 조회 중 오류: {e}")
            return {}
    
    def format_balance_display(self, use_emoji: bool = True) -> str:
        """잔고 정보를 보기 좋게 포맷"""
        balances = self.get_all_balances()
        
        if not balances:
            return "🚫 업비트 잔고 조회 불가" if use_emoji else "업비트 잔고 조회 불가"
        
        header = "💰 업비트 잔고 현황:" if use_emoji else "업비트 잔고 현황:"
        display_lines = [header]
        
        # KRW 먼저 표시
        if 'KRW' in balances:
            krw = balances['KRW']
            prefix = "  🇰🇷" if use_emoji else "  "
            display_lines.append(f"{prefix} KRW: {krw['balance']:,.0f}원 (사용가능: {krw['balance']:,.0f}, 거래중: {krw['locked']:,.0f})")
        
        # 다른 통화들 표시
        for currency, info in balances.items():
            if currency == 'KRW':
                continue
                
            balance = info['balance']
            locked = info['locked']
            
            if currency == 'USDT':
                prefix = "  💵" if use_emoji else "  "
                display_lines.append(f"{prefix} {currency}: {balance:.2f} (사용가능: {balance:.2f}, 거래중: {locked:.2f})")
            elif currency == 'BTC':
                prefix = "  ₿" if use_emoji else "  "
                display_lines.append(f"{prefix} {currency}: {balance:.8f} (사용가능: {balance:.8f}, 거래중: {locked:.8f})")
            else:
                prefix = "  🪙" if use_emoji else "  "
                display_lines.append(f"{prefix} {currency}: {balance:.4f} (사용가능: {balance:.4f}, 거래중: {locked:.4f})")
        
        return "\n".join(display_lines)
    
    def get_ticker(self, market: str = 'KRW-USDT') -> Dict[str, Any]:
        """티커 정보 조회"""
        try:
            url = f"{self.base_url}/v1/ticker"
            params = {'markets': market}
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            ticker_data = response.json()
            if ticker_data:
                return ticker_data[0]
            
            return {}
            
        except Exception as e:
            logger.error(f"티커 조회 실패: {e}")
            return {}
    
    def buy_usdt_with_krw(self, krw_amount: float) -> Dict[str, Any]:
        """KRW로 USDT 구매"""
        try:
            # 거래 간격 체크
            market = 'KRW-USDT'
            current_time = time.time()
            
            if market in self.last_trade_time:
                time_diff = current_time - self.last_trade_time[market]
                if time_diff < self.min_trade_interval:
                    wait_time = self.min_trade_interval - time_diff
                    logger.info(f"거래 간격 대기: {wait_time:.1f}초")
                    time.sleep(wait_time)
            
            # 현재 USDT 가격 조회
            ticker = self.get_ticker(market)
            if not ticker:
                return {'success': False, 'error': 'USDT 가격 조회 실패'}
            
            current_price = float(ticker['trade_price'])
            
            # 수수료 고려 (0.05%)
            fee_rate = 0.0005
            effective_amount = krw_amount * (1 - fee_rate)
            usdt_volume = effective_amount / current_price
            
            # 최소 주문 금액 확인 (5,000 KRW)
            if krw_amount < 5000:
                return {
                    'success': False, 
                    'error': f'최소 주문 금액 미달: {krw_amount} < 5,000 KRW'
                }
            
            # 지정가 주문 실행 (시장가보다 안전)
            # 업비트 API는 limit order에 대해 price와 volume을 정확히 지정해야 함
            order_data = {
                'market': market,
                'side': 'bid',  # 매수
                'ord_type': 'limit',  # 지정가
                'price': f"{current_price:.0f}",  # 현재 시장가격으로 주문
                'volume': f"{usdt_volume:.8f}",  # USDT 수량
                'identifier': f"upbit_buy_{int(time.time() * 1000)}"  # 고유 주문 식별자
            }
            
            result = self._make_authenticated_request('POST', '/v1/orders', data=order_data)
            
            if 'error' in result:
                logger.error(f"USDT 구매 주문 실패: {result['error']}")
                return {'success': False, 'error': result['error']}
            
            # 거래 시간 업데이트
            self.last_trade_time[market] = time.time()
            
            logger.info(f"USDT 구매 주문 성공: {usdt_volume:.6f} USDT @ {current_price:,.0f} KRW")
            
            return {
                'success': True,
                'order_id': result.get('uuid'),
                'market': market,
                'side': 'buy',
                'volume': usdt_volume,
                'price': current_price,
                'krw_amount': krw_amount,
                'order_type': 'limit'
            }
            
        except Exception as e:
            logger.error(f"USDT 구매 실패: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """주문 상태 조회"""
        try:
            params = {'uuid': order_id}
            result = self._make_authenticated_request('GET', '/v1/order', params=params)
            
            if 'error' in result:
                return {'success': False, 'error': result['error']}
            
            return {
                'success': True,
                'order_id': result.get('uuid'),
                'state': result.get('state'),  # wait, done, cancel
                'side': result.get('side'),
                'volume': float(result.get('volume', 0)),
                'remaining_volume': float(result.get('remaining_volume', 0)),
                'executed_volume': float(result.get('executed_volume', 0)),
                'trades_count': result.get('trades_count', 0),
                'price': float(result.get('price', 0))
            }
            
        except Exception as e:
            logger.error(f"주문 상태 조회 실패: {e}")
            return {'success': False, 'error': str(e)}
    
    def wait_for_order_completion(self, order_id: str, timeout: int = 300) -> Dict[str, Any]:
        """주문 완료 대기 (최대 5분)"""
        try:
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                status = self.get_order_status(order_id)
                
                if not status['success']:
                    return status
                
                if status['state'] == 'done':
                    logger.info(f"주문 완료: {order_id}")
                    return status
                elif status['state'] == 'cancel':
                    logger.warning(f"주문 취소됨: {order_id}")
                    return {'success': False, 'error': '주문이 취소되었습니다'}
                
                # 5초마다 확인
                time.sleep(5)
            
            # 타임아웃
            logger.warning(f"주문 완료 대기 타임아웃: {order_id}")
            return {'success': False, 'error': '주문 완료 대기 시간 초과'}
            
        except Exception as e:
            logger.error(f"주문 완료 대기 중 오류: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_usdt_withdraw_info(self) -> Dict[str, Any]:
        """USDT 출금 정보 조회 (기본값 반환)"""
        try:
            # 업비트 API 호출 시 문제가 있어 기본값 반환
            logger.warning("출금 정보 API 호출 대신 기본값 사용")
            
            return {
                'success': True,
                'currency': 'USDT',
                'net_type': 'TRC20',  # TRC20 (저렴한 수수료)
                'withdraw_fee': 1.0,  # 일반적인 TRC20 USDT 출금 수수료
                'is_withdraw_suspended': False,
                'min_withdraw_amount': 10.0  # 일반적인 최소 출금 금액
            }
            
        except Exception as e:
            logger.error(f"USDT 출금 정보 조회 실패: {e}")
            return {'success': False, 'error': str(e)}
    
    def withdraw_usdt_to_binance(self, amount: float, binance_address: str, 
                                network: str = 'TRC20') -> Dict[str, Any]:
        """Binance로 USDT 출금"""
        try:
            # 출금 정보 확인
            withdraw_info = self.get_usdt_withdraw_info()
            if not withdraw_info['success']:
                return withdraw_info
            
            # 최소 출금 금액 확인
            min_amount = withdraw_info.get('min_withdraw_amount', 10)
            if amount < min_amount:
                return {
                    'success': False,
                    'error': f'최소 출금 금액 미달: {amount} < {min_amount} USDT'
                }
            
            # 출금 수수료 고려
            withdraw_fee = withdraw_info.get('withdraw_fee', 1)
            net_amount = amount - withdraw_fee
            
            if net_amount <= 0:
                return {
                    'success': False,
                    'error': f'출금 수수료가 출금 금액보다 큽니다: 수수료 {withdraw_fee} USDT'
                }
            
            # 출금 실행 (업비트 API 필수 파라미터 포함)
            withdraw_data = {
                'currency': 'USDT',
                'amount': f"{amount:.2f}",  # 소수점 2자리로 포맷
                'address': binance_address,
                'net_type': network,  # TRC20 (저렴한 수수료)
                'transaction_type': 'default',  # 기본 출금 타입
                # KYC 관련 정보 (업비트 API 요구사항)
                'beneficiary_name': 'Binance Transfer',
                'beneficiary_residential_country_code': 'KR',
                'beneficiary_residential_address': 'Cryptocurrency Exchange'
            }
            
            result = self._make_authenticated_request('POST', '/v1/withdraws/coin', data=withdraw_data)
            
            if 'error' in result:
                logger.error(f"USDT 출금 실패: {result['error']}")
                return {'success': False, 'error': result['error']}
            
            logger.info(f"USDT 출금 요청 성공: {amount} USDT -> {binance_address[:10]}...")
            
            return {
                'success': True,
                'withdraw_id': result.get('uuid'),
                'currency': 'USDT',
                'amount': amount,
                'net_amount': net_amount,
                'fee': withdraw_fee,
                'address': binance_address,
                'network': network,
                'state': result.get('state', 'pending')
            }
            
        except Exception as e:
            logger.error(f"USDT 출금 실패: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_withdraw_status(self, withdraw_id: str) -> Dict[str, Any]:
        """출금 상태 조회"""
        try:
            params = {'uuid': withdraw_id}
            result = self._make_authenticated_request('GET', '/v1/withdraw', params=params)
            
            if 'error' in result:
                return {'success': False, 'error': result['error']}
            
            return {
                'success': True,
                'withdraw_id': result.get('uuid'),
                'state': result.get('state'),  # submitting, submitted, almost_accepted, rejected, accepted, processing, done, canceled
                'currency': result.get('currency'),
                'amount': float(result.get('amount', 0)),
                'fee': float(result.get('fee', 0)),
                'txid': result.get('txid', ''),
                'created_at': result.get('created_at', ''),
                'done_at': result.get('done_at', '')
            }
            
        except Exception as e:
            logger.error(f"출금 상태 조회 실패: {e}")
            return {'success': False, 'error': str(e)}
    
    def calculate_optimal_usdt_amount(self, target_usdt: float) -> Dict[str, Any]:
        """필요한 KRW 금액 계산"""
        try:
            ticker = self.get_ticker('KRW-USDT')
            if not ticker:
                return {'success': False, 'error': '가격 정보 조회 실패'}
            
            current_price = float(ticker['trade_price'])
            
            # 수수료 고려 (구매 0.05% + 출금 수수료)
            purchase_fee_rate = 0.0005
            withdraw_fee = 1.0  # 일반적인 USDT 출금 수수료
            
            # 실제 필요한 USDT (출금 수수료 포함)
            total_usdt_needed = target_usdt + withdraw_fee
            
            # 구매 수수료 고려한 KRW 금액
            krw_amount = total_usdt_needed * current_price / (1 - purchase_fee_rate)
            
            return {
                'success': True,
                'target_usdt': target_usdt,
                'total_usdt_needed': total_usdt_needed,
                'krw_amount': krw_amount,
                'current_price': current_price,
                'purchase_fee_rate': purchase_fee_rate,
                'withdraw_fee': withdraw_fee
            }
            
        except Exception as e:
            logger.error(f"필요 금액 계산 실패: {e}")
            return {'success': False, 'error': str(e)}
    
    async def auto_purchase_and_transfer(self, target_usdt: float, 
                                       binance_address: str,
                                       network: str = 'TRC20') -> Dict[str, Any]:
        """자동 USDT 구매 및 Binance 전송"""
        try:
            logger.info(f"자동 USDT 구매 및 전송 시작: {target_usdt} USDT -> Binance")
            
            # 1. 필요한 KRW 금액 계산
            calculation = self.calculate_optimal_usdt_amount(target_usdt)
            if not calculation['success']:
                return calculation
            
            required_krw = calculation['krw_amount']
            
            # 2. KRW 잔고 확인
            krw_balance = self.get_krw_balance()
            if krw_balance < required_krw:
                return {
                    'success': False,
                    'error': f'KRW 잔고 부족: {krw_balance:,.0f} < {required_krw:,.0f}'
                }
            
            # 3. USDT 구매
            logger.info(f"USDT 구매 시작: {required_krw:,.0f} KRW")
            purchase_result = self.buy_usdt_with_krw(required_krw)
            
            if not purchase_result['success']:
                return purchase_result
            
            order_id = purchase_result['order_id']
            
            # 4. 주문 완료 대기
            logger.info(f"주문 완료 대기: {order_id}")
            completion_result = self.wait_for_order_completion(order_id)
            
            if not completion_result['success']:
                return completion_result
            
            # 5. 잠시 대기 (잔고 반영 시간)
            await asyncio.sleep(10)
            
            # 6. USDT 잔고 확인
            usdt_balance = self.get_usdt_balance()
            if usdt_balance < target_usdt:
                return {
                    'success': False,
                    'error': f'구매된 USDT 부족: {usdt_balance} < {target_usdt}'
                }
            
            # 7. Binance로 출금
            logger.info(f"Binance로 USDT 출금 시작: {usdt_balance} USDT")
            withdraw_result = self.withdraw_usdt_to_binance(
                amount=usdt_balance,
                binance_address=binance_address,
                network=network
            )
            
            if not withdraw_result['success']:
                return withdraw_result
            
            logger.info(f"자동 USDT 구매 및 전송 완료: {target_usdt} USDT")
            
            return {
                'success': True,
                'target_usdt': target_usdt,
                'purchased_usdt': completion_result['executed_volume'],
                'transferred_usdt': withdraw_result['amount'],
                'total_krw_used': required_krw,
                'purchase_order_id': order_id,
                'withdraw_id': withdraw_result['withdraw_id'],
                'binance_address': binance_address,
                'network': network
            }
            
        except Exception as e:
            logger.error(f"자동 USDT 구매 및 전송 실패: {e}")
            return {'success': False, 'error': str(e)}