#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
트레이딩 봇 실행 스크립트
"""

import sys
import asyncio
import os
from pathlib import Path

# UTF-8 인코딩 설정
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """메인 실행 함수"""
    try:
        print("🚀 암호화폐 트레이딩 봇")
        print("=" * 50)
    except UnicodeEncodeError:
        print("Trading Bot")
        print("=" * 50)
    
    try:
        print("\n실행 옵션을 선택하세요:")
        print("1. 하이브리드 포트폴리오 봇 v2 (현물+선물)")
        print("2. 모니터링 대시보드만 실행")
        print("3. 단위 테스트 실행")
        print("4. 데이터베이스 테스트")
    except UnicodeEncodeError:
        print("\nSelect execution option:")
        print("1. Hybrid Portfolio Bot v2 (Spot+Futures)")
        print("2. Run monitoring dashboard only")
        print("3. Run unit tests")
        print("4. Database test")
    
    choice = input("\n선택 (1-4): ").strip()
    
    if choice == "1":
        run_hybrid_bot_v2()
    elif choice == "2":
        run_dashboard()
    elif choice == "3":
        run_tests()
    elif choice == "4":
        run_database_test()
    else:
        print("❌ 잘못된 선택입니다. 1-4 사이의 숫자를 입력하세요.")

def run_hybrid_bot_v2():
    """하이브리드 포트폴리오 봇 v2 실행"""
    try:
        print("\n💎 하이브리드 포트폴리오 봇 v2 실행 중...")
        print("📊 현물 + 선물 통합 전략")
    except UnicodeEncodeError:
        print("\nHybrid Portfolio Bot v2 starting...")
        print("Spot + Futures integrated strategy")
    try:
        from hybrid_trading_bot_v2 import main as hybrid_main
        asyncio.run(hybrid_main())
    except Exception as e:
        try:
            print(f"❌ 하이브리드 봇 실행 실패: {e}")
        except UnicodeEncodeError:
            print(f"Hybrid bot execution failed: {e}")

def run_dashboard():
    """모니터링 대시보드 실행"""
    print("\n📊 모니터링 대시보드 실행 중...")
    print("웹 대시보드: http://localhost:8080")
    try:
        from modules.monitoring_dashboard import MonitoringDashboard, WebDashboardServer
        
        dashboard = MonitoringDashboard()
        web_server = WebDashboardServer(dashboard)
        
        async def start_dashboard():
            await web_server.start_server()
            await dashboard.start_monitoring()
        
        asyncio.run(start_dashboard())
    except KeyboardInterrupt:
        print("\n📊 대시보드 종료")
    except Exception as e:
        print(f"❌ 대시보드 실행 실패: {e}")

def run_tests():
    """단위 테스트 실행"""
    print("\n🧪 단위 테스트 실행 중...")
    try:
        import subprocess
        
        print("기술적 분석 테스트...")
        result1 = subprocess.run([sys.executable, "-m", "tests.test_technical_analysis"], 
                               capture_output=True, text=True)
        
        print("리스크 관리 테스트...")
        result2 = subprocess.run([sys.executable, "-m", "tests.test_risk_manager"], 
                               capture_output=True, text=True)
        
        if result1.returncode == 0 and result2.returncode == 0:
            print("✅ 모든 테스트 통과!")
        else:
            print("❌ 일부 테스트 실패")
            if result1.returncode != 0:
                print(f"기술적 분석 테스트 오류:\n{result1.stderr}")
            if result2.returncode != 0:
                print(f"리스크 관리 테스트 오류:\n{result2.stderr}")
                
    except Exception as e:
        print(f"❌ 테스트 실행 실패: {e}")

def run_database_test():
    """데이터베이스 테스트 실행"""
    print("\n🗄️ 데이터베이스 테스트 실행 중...")
    try:
        from modules.database_manager import DatabaseManager
        
        with DatabaseManager("test_trading_bot.db") as db:
            # 테스트 데이터 삽입
            trade_data = {
                'symbol': 'BTC/USDT',
                'side': 'buy',
                'size': 0.001,
                'price': 50000,
                'exchange_type': 'spot',
                'order_type': 'market',
                'fees': 0.5,
                'pnl': 10.0,
                'strategy': 'test_strategy',
                'status': 'filled'
            }
            
            trade_id = db.insert_trade(trade_data)
            print(f"✅ 거래 기록 삽입 성공: ID {trade_id}")
            
            trades = db.get_trades(limit=5)
            print(f"✅ 거래 기록 조회 성공: {len(trades)}개")
            
            stats = db.get_trading_statistics(days=1)
            print(f"✅ 거래 통계 조회 성공")
            
            print("✅ 데이터베이스 테스트 완료")
            
    except Exception as e:
        print(f"❌ 데이터베이스 테스트 실패: {e}")

if __name__ == "__main__":
    main()