#!/usr/bin/env python3
"""
간단한 USDT 이체 스크립트
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
    """간단한 이체 실행"""
    logger.info("=== 간단한 USDT 이체 ===")
    
    # 거래소 인터페이스 초기화
    exchange_config = {
        'api_key': config.BINANCE_API_KEY,
        'secret_key': config.BINANCE_SECRET_KEY,
        'use_testnet': False
    }
    exchange = ExchangeInterface(exchange_config)
    
    try:
        # 현물에서 선물로 $370 이체 (약간의 버퍼 남겨둠)
        amount = 370.0
        
        logger.info(f"선물 계정으로 ${amount} 이체 시작")
        
        # CCXT를 직접 사용한 이체
        result = exchange.spot_exchange.transfer('USDT', amount, 'spot', 'future')
        
        if result:
            logger.info(f"이체 성공: ${amount} USDT")
            logger.info(f"이체 결과: {result}")
        else:
            logger.error(f"이체 실패: {result}")
        
        logger.info("=== 이체 완료 ===")
        
    except Exception as e:
        logger.error(f"이체 중 오류: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()