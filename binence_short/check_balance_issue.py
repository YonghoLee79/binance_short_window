#!/usr/bin/env python3
"""
잔고 부족 문제 분석 스크립트
"""

import ccxt
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

try:
    exchange = ccxt.binance({
        'apiKey': os.getenv('BINANCE_API_KEY'),
        'secret': os.getenv('BINANCE_SECRET_KEY'),
        'sandbox': False,
        'enableRateLimit': True,
    })

    # BTC 현재 가격 확인
    ticker = exchange.fetch_ticker('BTC/USDT')
    print(f'BTC/USDT 현재 가격: ${ticker["last"]:.2f}')

    # 시장 정보 확인
    markets = exchange.load_markets()
    market_info = markets['BTC/USDT']
    print(f'최소 주문량: {market_info["limits"]["amount"]["min"]} BTC')
    print(f'최소 주문 금액: ${market_info["limits"]["cost"]["min"]} USDT')

    # 현재 잔고 확인
    balance = exchange.fetch_balance()
    print(f'현물 USDT 잔고: ${balance["USDT"]["free"]:.2f}')
    print(f'현물 BTC 잔고: {balance["BTC"]["free"]:.6f} BTC')

    # 0.00117 BTC의 USDT 가치 계산
    btc_amount = 0.00117
    usdt_needed = btc_amount * ticker['last']
    print(f'주문하려는 0.00117 BTC = ${usdt_needed:.2f} USDT')
    
    # 수수료 고려한 실제 필요 금액
    fee_rate = 0.001  # 0.1%
    total_needed = usdt_needed * (1 + fee_rate)
    print(f'수수료 포함 필요 금액: ${total_needed:.2f} USDT')
    
    # 잔고 충분한지 확인
    available_usdt = balance["USDT"]["free"]
    if available_usdt >= total_needed:
        print("✅ 잔고 충분함")
    else:
        print(f"❌ 잔고 부족: 필요 ${total_needed:.2f}, 보유 ${available_usdt:.2f}")
        print(f"부족 금액: ${total_needed - available_usdt:.2f} USDT")

except Exception as e:
    print(f"오류: {e}")