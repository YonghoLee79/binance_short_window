#!/usr/bin/env python3
"""
USDT를 현물에서 선물로 이체하는 스크립트
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
    """USDT 이체 실행"""
    logger.info("=== USDT 선물 계정 이체 시작 ===")
    
    # 거래소 인터페이스 초기화
    exchange_config = {
        'api_key': config.BINANCE_API_KEY,
        'secret_key': config.BINANCE_SECRET_KEY,
        'use_testnet': False
    }
    exchange = ExchangeInterface(exchange_config)
    
    try:
        # 1. 현물 USDT 잔고 확인
        spot_balance = exchange.get_spot_balance()
        spot_usdt = spot_balance.get('USDT', 0)
        logger.info(f"현물 USDT 잔고: ${spot_usdt:.2f}")
        
        if spot_usdt < 10:
            logger.warning(f"이체할 USDT 부족: ${spot_usdt:.2f} (최소 $10 필요)")
            return
        
        # 2. 선물로 이체
        logger.info(f"선물 계정으로 이체 시작: ${spot_usdt:.2f}")
        
        result = exchange.transfer_between_accounts(
            asset='USDT',
            amount=spot_usdt,
            from_account='SPOT',
            to_account='USDM'
        )
        
        if result.get('success'):
            logger.info(f"이체 성공: ${spot_usdt:.2f} USDT")
            
            # 3. 이체 후 잔고 확인
            import time
            time.sleep(3)
            
            futures_balance = exchange.get_futures_balance()
            futures_usdt = futures_balance.get('USDT', 0)
            logger.info(f"선물 USDT 잔고 (이체 후): ${futures_usdt:.2f}")
            
        else:
            logger.error(f"이체 실패: {result.get('error', result)}")
        
        logger.info("=== USDT 이체 완료 ===")
        
    except Exception as e:
        logger.error(f"이체 중 오류: {e}")


if __name__ == "__main__":
    confirm = input("USDT를 선물 계정으로 이체하시겠습니까? (yes/no): ")
    if confirm.lower() == 'yes':
        main()
    else:
        print("취소되었습니다.")