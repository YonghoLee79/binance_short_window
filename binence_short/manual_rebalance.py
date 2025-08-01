#!/usr/bin/env python3
"""
수동 리밸런싱 스크립트 (간단 버전)
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
    """수동 리밸런싱 실행"""
    logger.info("=== 수동 리밸런싱 시작 ===")
    
    # 거래소 인터페이스 초기화
    exchange_config = {
        'api_key': config.BINANCE_API_KEY,
        'secret_key': config.BINANCE_SECRET_KEY,
        'use_testnet': False
    }
    exchange = ExchangeInterface(exchange_config)
    
    try:
        # 1. ETH 전량 매도
        logger.info("ETH 전량 매도 시작...")
        eth_balance = 0.0971258  # 로그에서 확인된 ETH 잔고
        
        if eth_balance > 0:
            result = exchange.execute_smart_order(
                symbol='ETH/USDT',
                side='sell',
                amount=eth_balance,
                exchange_type='spot'
            )
            
            if result.get('success'):
                logger.info(f"ETH 매도 성공: {eth_balance} ETH")
            else:
                logger.error(f"ETH 매도 실패: {result.get('error', result)}")
                return
        
        # 2. BTC 일부 매도 (약 $50 정도)
        logger.info("BTC 일부 매도 시작...")
        btc_price = 118000  # 대략적인 BTC 가격
        btc_sell_amount = 50 / btc_price  # $50 상당
        btc_sell_amount = round(btc_sell_amount, 8)  # 8자리로 반올림
        
        if btc_sell_amount > 0:
            result = exchange.execute_smart_order(
                symbol='BTC/USDT',
                side='sell',
                amount=btc_sell_amount,
                exchange_type='spot'
            )
            
            if result.get('success'):
                logger.info(f"BTC 매도 성공: {btc_sell_amount} BTC")
            else:
                logger.error(f"BTC 매도 실패: {result.get('error', result)}")
                return
        
        # 3. 잠시 대기
        import time
        time.sleep(10)
        
        # 4. 현물 USDT 잔고 확인
        spot_balance = exchange.get_spot_balance()
        spot_usdt = spot_balance.get('USDT', 0)
        logger.info(f"현물 USDT 잔고: ${spot_usdt:.2f}")
        
        # 5. 선물로 이체 (최소 $10 이상)
        if spot_usdt >= 10:
            logger.info(f"선물 계정으로 이체 시작: ${spot_usdt:.2f}")
            
            result = exchange.transfer_between_accounts(
                asset='USDT',
                amount=spot_usdt,
                from_account='SPOT',
                to_account='USDM'
            )
            
            if result.get('success'):
                logger.info(f"이체 성공: ${spot_usdt:.2f} USDT")
            else:
                logger.error(f"이체 실패: {result.get('error')}")
        else:
            logger.warning(f"이체 금액 부족: ${spot_usdt:.2f} (최소 $10 필요)")
        
        logger.info("=== 수동 리밸런싱 완료 ===")
        
    except Exception as e:
        logger.error(f"리밸런싱 중 오류: {e}")


if __name__ == "__main__":
    confirm = input("실제 매도와 이체를 실행하시겠습니까? (yes/no): ")
    if confirm.lower() == 'yes':
        main()
    else:
        print("취소되었습니다.")