#!/usr/bin/env python3
"""
현재 잔고 상태 확인 스크립트
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import config
from utils.logger import logger
from modules.exchange_interface import ExchangeInterface


def main():
    """잔고 확인"""
    logger.info("=== 현재 잔고 상태 확인 ===")
    
    # 거래소 인터페이스 초기화
    exchange_config = {
        'api_key': config.BINANCE_API_KEY,
        'secret_key': config.BINANCE_SECRET_KEY,
        'use_testnet': False
    }
    exchange = ExchangeInterface(exchange_config)
    
    try:
        # 1. 현물 잔고 (상세)
        print("\n=== 현물 잔고 ===")
        spot_balance = exchange.get_spot_balance()
        print(f"전체 현물 잔고: {spot_balance}")
        
        for asset, amount in spot_balance.items():
            if amount > 0:
                print(f"  {asset}: {amount}")
        
        # 2. 선물 잔고 (상세)
        print("\n=== 선물 잔고 ===")
        futures_balance = exchange.get_futures_balance()
        print(f"전체 선물 잔고: {futures_balance}")
        
        for asset, amount in futures_balance.items():
            if amount > 0:
                print(f"  {asset}: {amount}")
        
        # 3. 현재 가격으로 총 자산 계산
        print("\n=== 자산 가치 ===")
        total_value = 0
        
        # BTC 가치
        if spot_balance.get('BTC', 0) > 0:
            btc_ticker = exchange.get_ticker('BTC/USDT')
            btc_price = btc_ticker.get('last', 0) if btc_ticker else 0
            btc_value = spot_balance['BTC'] * btc_price
            total_value += btc_value
            print(f"  BTC: {spot_balance['BTC']:.8f} × ${btc_price:.2f} = ${btc_value:.2f}")
        
        # ETH 가치
        if spot_balance.get('ETH', 0) > 0.0001:  # 0.0001 이상만 표시
            eth_ticker = exchange.get_ticker('ETH/USDT')
            eth_price = eth_ticker.get('last', 0) if eth_ticker else 0
            eth_value = spot_balance['ETH'] * eth_price
            total_value += eth_value
            print(f"  ETH: {spot_balance['ETH']:.8f} × ${eth_price:.2f} = ${eth_value:.2f}")
        
        # USDT 현물
        spot_usdt = spot_balance.get('USDT', 0)
        total_value += spot_usdt
        print(f"  현물 USDT: ${spot_usdt:.2f}")
        
        # USDT 선물
        futures_usdt = futures_balance.get('USDT', 0)
        total_value += futures_usdt
        print(f"  선물 USDT: ${futures_usdt:.2f}")
        
        print(f"\n총 자산 가치: ${total_value:.2f}")
        
        # 4. 배분 비율
        if total_value > 0:
            spot_ratio = (total_value - futures_usdt) / total_value * 100
            futures_ratio = futures_usdt / total_value * 100
            print(f"\n현재 배분:")
            print(f"  현물: {spot_ratio:.1f}%")
            print(f"  선물: {futures_ratio:.1f}%")
            print(f"  목표: 현물 40%, 선물 60%")
        
        logger.info("=== 잔고 확인 완료 ===")
        
    except Exception as e:
        logger.error(f"잔고 확인 중 오류: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()