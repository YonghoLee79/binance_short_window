#!/usr/bin/env python3
"""
하이브리드 포트폴리오 전략 테스트
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_hybrid_strategy():
    """하이브리드 전략 테스트"""
    try:
        from config import config
        from modules.hybrid_portfolio_strategy import HybridPortfolioStrategy
        
        print("🔧 하이브리드 포트폴리오 전략 테스트")
        print("=" * 50)
        
        # 전략 초기화
        hybrid_config = {
            'spot_allocation': config.SPOT_ALLOCATION,
            'futures_allocation': config.FUTURES_ALLOCATION,
            'arbitrage_threshold': 0.003,
            'rebalance_threshold': config.REBALANCE_THRESHOLD,
            'max_leverage': 3,
            'max_position_size': 0.15,
            'correlation_limit': 0.75
        }
        strategy = HybridPortfolioStrategy(hybrid_config)
        print("✅ 전략 초기화 완료")
        
        # 테스트 시장 데이터 생성
        test_market_data = {
            'BTC/USDT': {
                'spot_ticker': {'last': 65000},
                'futures_ticker': {'last': 65200},  # 0.3% 프리미엄
                'spot_signals': {'combined_signal': 0.7},
                'futures_signals': {'combined_signal': 0.6},
                'spot_indicators': {'rsi': {'current': 25}},  # 과매도
                'futures_indicators': {'rsi': {'current': 28}}
            },
            'ETH/USDT': {
                'spot_ticker': {'last': 3500},
                'futures_ticker': {'last': 3485},  # -0.4% 디스카운트
                'spot_signals': {'combined_signal': -0.5},
                'futures_signals': {'combined_signal': -0.4},
                'spot_indicators': {'rsi': {'current': 75}},  # 과매수
                'futures_indicators': {'rsi': {'current': 78}}
            }
        }
        
        # 기회 분석
        print("\n📊 시장 기회 분석 중...")
        opportunities = strategy.analyze_market_opportunity(test_market_data)
        
        print(f"✅ 아비트라지 기회: {len(opportunities['arbitrage'])}개")
        for arb in opportunities['arbitrage']:
            print(f"  - {arb['symbol']}: {arb['premium']:.2%} 프리미엄, 신뢰도 {arb['confidence']:.1%}")
        
        print(f"✅ 트렌드 추종 기회: {len(opportunities['trend_following'])}개")
        for trend in opportunities['trend_following']:
            print(f"  - {trend['symbol']}: {trend['direction']} 트렌드, 신뢰도 {trend['confidence']:.1%}")
        
        print(f"✅ 모멘텀 기회: {len(opportunities['momentum'])}개")
        for momentum in opportunities['momentum']:
            print(f"  - {momentum['symbol']}: {momentum['type']}, 신뢰도 {momentum['confidence']:.1%}")
        
        # 포트폴리오 상태 테스트
        test_portfolio_state = {
            'total_balance': 10000,
            'spot_balance': 5500,   # 55% (목표: 60%)
            'futures_balance': 4500, # 45% (목표: 40%)
            'avg_price': {'BTC/USDT': 65000, 'ETH/USDT': 3500}
        }
        
        # 리밸런싱 필요 여부 확인
        print("\n⚖️ 리밸런싱 분석...")
        needs_rebalancing = strategy.check_rebalancing_needed(test_portfolio_state)
        print(f"리밸런싱 필요: {'예' if needs_rebalancing else '아니오'}")
        
        if needs_rebalancing:
            rebalancing_orders = strategy.generate_rebalancing_orders(test_portfolio_state)
            print(f"리밸런싱 주문: {len(rebalancing_orders)}개")
            for order in rebalancing_orders:
                print(f"  - {order['symbol']}: {order['action']} {order['size']:.6f}")
        
        # 포트폴리오 신호 생성
        print("\n📈 포트폴리오 신호 생성...")
        signals = strategy.generate_portfolio_signals(opportunities, test_portfolio_state)
        print(f"생성된 신호: {len(signals)}개")
        
        for i, signal in enumerate(signals[:5], 1):  # 최대 5개만
            print(f"  {i}. {signal['strategy']} - {signal['symbol']} {signal['action']} "
                  f"({signal['exchange_type']}) 신뢰도: {signal['confidence']:.1%}")
        
        # 포트폴리오 메트릭
        print("\n📊 포트폴리오 메트릭...")
        metrics = strategy.calculate_portfolio_metrics(test_portfolio_state)
        print(f"총 자산: ${metrics['total_value']:,.2f}")
        print(f"현물 비율: {metrics['spot_ratio']:.1%} (목표: {metrics['target_spot_ratio']:.1%})")
        print(f"선물 비율: {metrics['futures_ratio']:.1%} (목표: {metrics['target_futures_ratio']:.1%})")
        print(f"레버리지: {metrics['leverage_ratio']:.1f}x")
        print(f"리스크 레벨: {metrics['risk_level']}")
        
        # 전략 요약
        print("\n📋 전략 요약...")
        summary = strategy.get_strategy_summary()
        print(f"전략 타입: {summary['strategy_type']}")
        print(f"현물 할당: {summary['spot_allocation']:.0%}")
        print(f"선물 할당: {summary['futures_allocation']:.0%}")
        print(f"아비트라지 임계값: {summary['arbitrage_threshold']:.1%}")
        print(f"최대 레버리지: {summary['max_leverage']}배")
        
        print("\n✅ 하이브리드 전략 테스트 완료!")
        return True
        
    except Exception as e:
        print(f"❌ 하이브리드 전략 테스트 실패: {e}")
        return False


if __name__ == "__main__":
    success = test_hybrid_strategy()
    
    if success:
        print("\n🎉 하이브리드 포트폴리오 전략이 정상 작동합니다!")
        print("📱 이제 실제 봇에서 현물과 선물을 통합 운영할 수 있습니다.")
    else:
        print("\n❌ 하이브리드 전략에 문제가 있습니다.")