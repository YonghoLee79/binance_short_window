#!/usr/bin/env python3
"""
Upbit 출금 정보 조회 테스트
"""

import sys
import os
from dotenv import load_dotenv

# 프로젝트 루트 경로를 sys.path에 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from modules.upbit_interface import UpbitInterface

def test_withdraw_info():
    """출금 정보 조회 테스트"""
    
    # 환경 변수 로드
    load_dotenv()
    
    config = {
        'upbit_access_key': os.getenv('UPBIT_ACCESS_KEY', ''),
        'upbit_secret_key': os.getenv('UPBIT_SECRET_KEY', '')
    }
    
    if not config['upbit_access_key'] or not config['upbit_secret_key']:
        print("WARNING Upbit API 키가 설정되지 않았습니다")
        return
    
    print("업비트 출금 정보 조회 테스트 시작")
    print("=" * 50)
    
    upbit = UpbitInterface(config)
    print("업비트 API 사용 가능:", upbit.api_available)
    
    if not upbit.api_available:
        print("ERROR Upbit API를 사용할 수 없습니다")
        return
    
    # USDT 출금 정보 조회
    print("\nUSDT 출금 정보 조회:")
    withdraw_info = upbit.get_usdt_withdraw_info()
    
    if withdraw_info['success']:
        print("OK USDT 출금 정보 조회 성공:")
        print(f"  통화: {withdraw_info.get('currency')}")
        print(f"  네트워크: {withdraw_info.get('net_type')}")
        print(f"  출금 수수료: {withdraw_info.get('withdraw_fee')} USDT")
        print(f"  최소 출금 금액: {withdraw_info.get('min_withdraw_amount')} USDT")
        print(f"  출금 중단 여부: {withdraw_info.get('is_withdraw_suspended')}")
    else:
        print(f"ERROR USDT 출금 정보 조회 실패: {withdraw_info.get('error')}")

if __name__ == "__main__":
    test_withdraw_info()