#!/usr/bin/env python3
"""
업비트 잔액 조회 테스트 스크립트
"""

from config import config
from modules.upbit_interface import UpbitInterface

def test_upbit_balance():
    """업비트 잔액 조회 테스트"""
    
    # UpbitInterface 초기화
    upbit_config = {
        'upbit_access_key': config.UPBIT_ACCESS_KEY,
        'upbit_secret_key': config.UPBIT_SECRET_KEY
    }
    
    upbit = UpbitInterface(upbit_config)
    
    print("업비트 잔액 조회 테스트 시작")
    print("=" * 50)
    
    # API 사용 가능 여부 확인
    if not upbit.api_available:
        print("업비트 API를 사용할 수 없습니다.")
        print("   - API 키와 시크릿 키를 확인해주세요.")
        return
    
    print("업비트 API 연결 성공")
    print()
    
    # 전체 잔액 조회
    print("전체 잔액 조회:")
    balance_display = upbit.format_balance_display(use_emoji=False)
    print(balance_display)
    print()
    
    # 개별 잔액 조회
    print("개별 잔액 조회:")
    krw_balance = upbit.get_krw_balance()
    usdt_balance = upbit.get_usdt_balance()
    
    print(f"  KRW 잔고: {krw_balance:,.0f}원")
    print(f"  USDT 잔고: {usdt_balance:.2f} USDT")
    print()
    
    # 모든 보유 자산 조회
    print("모든 보유 자산:")
    all_balances = upbit.get_all_balances()
    
    if all_balances:
        for currency, info in all_balances.items():
            total = info['total']
            if total > 0:
                if currency == 'KRW':
                    print(f"  {currency}: {total:,.0f}원")
                elif currency in ['USDT', 'USD']:
                    print(f"  {currency}: {total:.2f}")
                elif currency == 'BTC':
                    print(f"  {currency}: {total:.8f}")
                else:
                    print(f"  {currency}: {total:.4f}")
    else:
        print("  보유 자산이 없습니다.")

if __name__ == "__main__":
    test_upbit_balance()