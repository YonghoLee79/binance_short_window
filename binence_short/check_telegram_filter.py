#!/usr/bin/env python3
"""
텔레그램 필터링 테스트 스크립트
"""

import sys
import os
from datetime import datetime

# 프로젝트 루트 경로를 sys.path에 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from modules.telegram_notifications import TelegramNotifications

def test_telegram_filtering():
    """텔레그램 필터링 테스트"""
    
    print("텔레그램 필터링 테스트 시작")
    print("=" * 50)
    
    telegram = TelegramNotifications()
    
    # 거래가 없는 사이클 정보
    cycle_info_no_trades = {
        'cycle_number': 999,
        'duration': 120.5,
        'opportunities': {'trend_following': 5},
        'trades_executed': 0  # 거래 없음
    }
    
    print("테스트 1: 거래가 없는 사이클 (알림 전송되지 않아야 함)")
    telegram.send_trading_cycle_log(cycle_info_no_trades)
    print("-> 위에 알림이 없다면 필터링 정상 작동")
    
    print("\n" + "=" * 50)
    
    # 거래가 있는 사이클 정보  
    cycle_info_with_trades = {
        'cycle_number': 1000,
        'duration': 145.2,
        'opportunities': {'trend_following': 3},
        'trades_executed': 2  # 거래 있음
    }
    
    print("테스트 2: 거래가 있는 사이클 (알림 전송되어야 함)")
    telegram.send_trading_cycle_log(cycle_info_with_trades)
    print("-> 위에 알림이 있다면 정상 작동")
    
    print("\n테스트 완료")

if __name__ == "__main__":
    test_telegram_filtering()