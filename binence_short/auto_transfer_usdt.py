#!/usr/bin/env python3
"""
자동 USDT 이체 스크립트 - 다양한 방법 시도
"""

import sys
import requests
import hmac
import hashlib
import time
from pathlib import Path
from urllib.parse import urlencode

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import config
from utils.logger import logger
from modules.exchange_interface import ExchangeInterface


class AutoUSDTTransfer:
    """자동 USDT 이체 클래스"""
    
    def __init__(self):
        self.api_key = config.BINANCE_API_KEY
        self.secret_key = config.BINANCE_SECRET_KEY
        self.base_url = 'https://api.binance.com'
        
        # 거래소 인터페이스도 준비
        exchange_config = {
            'api_key': self.api_key,
            'secret_key': self.secret_key,
            'use_testnet': False
        }
        self.exchange = ExchangeInterface(exchange_config)
    
    def _generate_signature(self, query_string):
        """바이낸스 API 서명 생성"""
        return hmac.new(
            self.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _make_request(self, endpoint, params=None, method='GET'):
        """바이낸스 API 요청"""
        if params is None:
            params = {}
        
        # 타임스탬프 추가
        params['timestamp'] = int(time.time() * 1000)
        
        # 쿼리 스트링 생성
        query_string = urlencode(params)
        
        # 서명 생성
        signature = self._generate_signature(query_string)
        params['signature'] = signature
        
        # 헤더 설정
        headers = {
            'X-MBX-APIKEY': self.api_key,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        # 요청 실행
        url = f"{self.base_url}{endpoint}"
        
        if method == 'POST':
            response = requests.post(url, data=params, headers=headers)
        else:
            response = requests.get(url, params=params, headers=headers)
        
        return response
    
    def check_account_permissions(self):
        """계정 권한 확인"""
        try:
            logger.info("계정 권한 확인 중...")
            
            # 계정 정보 조회
            response = self._make_request('/api/v3/account')
            
            if response.status_code == 200:
                account_info = response.json()
                permissions = account_info.get('permissions', [])
                logger.info(f"계정 권한: {permissions}")
                
                if 'SPOT' in permissions:
                    logger.info("현물 거래 권한 있음")
                if 'FUTURES' in permissions:
                    logger.info("선물 거래 권한 있음")
                if 'MARGIN' in permissions:
                    logger.info("마진 거래 권한 있음")
                
                return True
            else:
                logger.error(f"계정 정보 조회 실패: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"권한 확인 중 오류: {e}")
            return False
    
    def method1_sapi_transfer(self, amount):
        """방법 1: SAPI 내부 이체 (Universal Transfer)"""
        try:
            logger.info(f"방법 1 시도: SAPI Universal Transfer - ${amount}")
            
            params = {
                'type': 'MAIN_UMFUTURE',  # 현물 -> USDⓈ-M 선물
                'asset': 'USDT',
                'amount': amount
            }
            
            response = self._make_request('/sapi/v1/asset/transfer', params, 'POST')
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"방법 1 성공: {result}")
                return True
            else:
                logger.error(f"방법 1 실패: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"방법 1 오류: {e}")
            return False
    
    def method2_futures_transfer(self, amount):
        """방법 2: 선물 API 직접 이체"""
        try:
            logger.info(f"방법 2 시도: 선물 API 직접 이체 - ${amount}")
            
            params = {
                'asset': 'USDT',
                'amount': amount,
                'type': 1  # 1: 현물 -> 선물, 2: 선물 -> 현물
            }
            
            response = self._make_request('/fapi/v1/transfer', params, 'POST')
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"방법 2 성공: {result}")
                return True
            else:
                logger.error(f"방법 2 실패: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"방법 2 오류: {e}")
            return False
    
    def method3_ccxt_transfer(self, amount):
        """방법 3: CCXT 라이브러리 사용"""
        try:
            logger.info(f"방법 3 시도: CCXT 라이브러리 - ${amount}")
            
            result = self.exchange.spot_exchange.transfer('USDT', amount, 'spot', 'future')
            
            if result:
                logger.info(f"성공: 방법 3 성공: {result}")
                return True
            else:
                logger.error(f"실패: 방법 3 실패: {result}")
                return False
                
        except Exception as e:
            logger.error(f"방법 3 오류: {e}")
            return False
    
    def method4_margin_transfer(self, amount):
        """방법 4: 마진 계정을 경유한 이체"""
        try:
            logger.info(f"방법 4 시도: 마진 계정 경유 - ${amount}")
            
            # 1단계: 현물 -> 마진
            params1 = {
                'asset': 'USDT',
                'amount': amount,
                'type': 1  # 1: 메인 -> 마진
            }
            
            response1 = self._make_request('/sapi/v1/margin/transfer', params1, 'POST')
            
            if response1.status_code == 200:
                logger.info("1단계: 현물 -> 마진 성공")
                
                # 잠시 대기
                time.sleep(2)
                
                # 2단계: 마진 -> 선물 (시도)
                params2 = {
                    'type': 'MARGIN_UMFUTURE',
                    'asset': 'USDT',
                    'amount': amount
                }
                
                response2 = self._make_request('/sapi/v1/asset/transfer', params2, 'POST')
                
                if response2.status_code == 200:
                    result = response2.json()
                    logger.info(f"성공: 방법 4 성공: {result}")
                    return True
                else:
                    logger.error(f"2단계 실패: {response2.status_code} - {response2.text}")
                    # 롤백: 마진 -> 현물
                    rollback_params = {
                        'asset': 'USDT',
                        'amount': amount,
                        'type': 2  # 2: 마진 -> 메인
                    }
                    self._make_request('/sapi/v1/margin/transfer', rollback_params, 'POST')
                    return False
            else:
                logger.error(f"1단계 실패: {response1.status_code} - {response1.text}")
                return False
                
        except Exception as e:
            logger.error(f"방법 4 오류: {e}")
            return False
    
    def auto_transfer(self, amount=370.0):
        """자동 이체 실행 - 여러 방법 순차 시도"""
        try:
            logger.info("=== 자동 USDT 이체 시작 ===")
            logger.info(f"이체 금액: ${amount}")
            
            # 계정 권한 확인
            if not self.check_account_permissions():
                logger.error("계정 권한 확인 실패")
                return False
            
            # 현물 잔고 확인
            spot_balance = self.exchange.get_spot_balance()
            logger.info(f"현물 잔고 전체: {spot_balance}")
            
            # 여러 방법으로 USDT 잔고 확인
            spot_usdt = 0
            if isinstance(spot_balance, dict):
                if 'USDT' in spot_balance:
                    spot_usdt = spot_balance['USDT']
                elif 'total' in spot_balance and 'USDT' in spot_balance['total']:
                    spot_usdt = spot_balance['total']['USDT']
                elif 'free' in spot_balance and 'USDT' in spot_balance['free']:
                    spot_usdt = spot_balance['free']['USDT']
            
            logger.info(f"현물 USDT 잔고: ${spot_usdt}")
            
            if spot_usdt < amount:
                logger.error(f"잔고 부족: 필요 ${amount}, 보유 ${spot_usdt}")
                # 강제로 계속 진행 (디버깅용)
                logger.warning("잔고 부족하지만 강제로 계속 진행...")
                # return False
            
            # 방법들을 순차적으로 시도
            methods = [
                self.method1_sapi_transfer,
                self.method2_futures_transfer,
                self.method3_ccxt_transfer,
                self.method4_margin_transfer
            ]
            
            for i, method in enumerate(methods, 1):
                logger.info(f"\n--- 방법 {i} 시도 ---")
                
                if method(amount):
                    logger.info(f"이체 성공! (방법 {i})")
                    
                    # 결과 확인
                    time.sleep(5)
                    self.verify_transfer_result(amount)
                    return True
                
                logger.info(f"방법 {i} 실패, 다음 방법 시도...")
                time.sleep(2)
            
            logger.error("모든 이체 방법 실패")
            return False
            
        except Exception as e:
            logger.error(f"자동 이체 중 오류: {e}")
            return False
    
    def verify_transfer_result(self, expected_amount):
        """이체 결과 확인"""
        try:
            logger.info("이체 결과 확인 중...")
            
            # 현물 잔고 확인
            spot_balance = self.exchange.get_spot_balance()
            spot_usdt = spot_balance.get('USDT', 0)
            
            # 선물 잔고 확인
            futures_balance = self.exchange.get_futures_balance()
            futures_usdt = futures_balance.get('USDT', 0)
            
            logger.info(f"이체 후 잔고:")
            logger.info(f"  현물 USDT: ${spot_usdt}")
            logger.info(f"  선물 USDT: ${futures_usdt}")
            
            total_usdt = spot_usdt + futures_usdt
            spot_ratio = (spot_usdt / total_usdt * 100) if total_usdt > 0 else 0
            futures_ratio = (futures_usdt / total_usdt * 100) if total_usdt > 0 else 0
            
            logger.info(f"새로운 배분:")
            logger.info(f"  현물: {spot_ratio:.1f}%")
            logger.info(f"  선물: {futures_ratio:.1f}%")
            
        except Exception as e:
            logger.error(f"결과 확인 중 오류: {e}")


def main():
    """메인 실행 함수"""
    transfer = AutoUSDTTransfer()
    
    print("자동 USDT 이체를 시작하시겠습니까?")
    print("현물 -> 선물 계정으로 $370 이체")
    confirm = input("실행하려면 'yes'를 입력하세요: ")
    
    if confirm.lower() == 'yes':
        success = transfer.auto_transfer(370.0)
        if success:
            print("이체 완료!")
        else:
            print("이체 실패!")
    else:
        print("취소되었습니다.")


if __name__ == "__main__":
    main()