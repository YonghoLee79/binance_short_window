#!/usr/bin/env python3
"""
리스크 관리 모듈 단위 테스트
"""

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.risk_manager import RiskManager


class TestRiskManager(unittest.TestCase):
    """리스크 관리 모듈 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        self.config = {
            'max_position_size': 0.2,
            'max_daily_loss': 0.05,
            'max_drawdown': 0.20,
            'stop_loss_pct': 0.05,
            'take_profit_pct': 0.10,
            'position_timeout_hours': 24,
            'max_leverage': 5,
            'risk_per_trade': 0.02,
            'short_position_limit': 0.3,
            'short_squeeze_threshold': 0.10,
            'funding_rate_threshold': 0.01
        }
        self.risk_manager = RiskManager(self.config)
    
    def test_validate_trade_normal_case(self):
        """정상적인 거래 검증 테스트"""
        result = self.risk_manager.validate_trade(
            symbol='BTC/USDT',
            side='buy',
            size=0.001,
            price=50000,
            current_balance=1000,
            exchange_type='spot'
        )
        
        self.assertTrue(result['is_valid'])
        self.assertEqual(result['adjusted_size'], 0.001)
        self.assertIsInstance(result['warnings'], list)
        self.assertIsInstance(result['errors'], list)
    
    def test_validate_trade_oversized_position(self):
        """포지션 크기 초과 시 테스트"""
        result = self.risk_manager.validate_trade(
            symbol='BTC/USDT',
            side='buy',
            size=10,  # 매우 큰 크기
            price=50000,
            current_balance=1000,
            exchange_type='spot'
        )
        
        # 포지션 크기가 조정되어야 함
        self.assertLess(result['adjusted_size'], 10)
        self.assertGreater(len(result['warnings']), 0)
    
    def test_validate_trade_daily_loss_limit(self):
        """일일 손실 한도 초과 시 테스트"""
        # 일일 손실을 한도 이상으로 설정
        self.risk_manager.daily_pnl = -100  # 1000의 10% 손실
        
        result = self.risk_manager.validate_trade(
            symbol='BTC/USDT',
            side='buy',
            size=0.001,
            price=50000,
            current_balance=1000,
            exchange_type='spot'
        )
        
        self.assertFalse(result['is_valid'])
        self.assertGreater(len(result['errors']), 0)
    
    def test_validate_trade_max_drawdown(self):
        """최대 드로우다운 초과 시 테스트"""
        # 드로우다운을 한도 이상으로 설정
        self.risk_manager.current_drawdown = 0.25  # 25% 드로우다운
        
        result = self.risk_manager.validate_trade(
            symbol='BTC/USDT',
            side='buy',
            size=0.001,
            price=50000,
            current_balance=1000,
            exchange_type='spot'
        )
        
        self.assertFalse(result['is_valid'])
        self.assertGreater(len(result['errors']), 0)
    
    def test_calculate_position_size_kelly_criterion(self):
        """Kelly Criterion 기반 포지션 크기 계산 테스트"""
        position_size = self.risk_manager.calculate_position_size(
            symbol='BTC/USDT',
            signal_strength=0.8,
            current_balance=1000,
            current_price=50000,
            volatility=0.02
        )
        
        # 포지션 크기가 양수여야 함
        self.assertGreater(position_size, 0)
        
        # 최대 리스크 한도 내에 있어야 함
        max_position_value = 1000 * self.config['risk_per_trade']
        actual_position_value = position_size * 50000
        self.assertLessEqual(actual_position_value, max_position_value)
    
    def test_calculate_position_size_zero_signal(self):
        """신호 강도가 0일 때 포지션 크기 테스트"""
        position_size = self.risk_manager.calculate_position_size(
            symbol='BTC/USDT',
            signal_strength=0.0,
            current_balance=1000,
            current_price=50000,
            volatility=0.02
        )
        
        # 신호가 없으면 포지션 크기가 0이거나 매우 작아야 함
        self.assertLessEqual(position_size, 0.001)
    
    def test_calculate_stop_loss(self):
        """스탑로스 가격 계산 테스트"""
        entry_price = 50000
        
        # 매수 포지션 스탑로스
        buy_stop_loss = self.risk_manager.calculate_stop_loss(
            symbol='BTC/USDT',
            side='buy',
            entry_price=entry_price,
            volatility=0.02
        )
        
        # 매수 시 스탑로스는 진입가보다 낮아야 함
        self.assertLess(buy_stop_loss, entry_price)
        
        # 매도 포지션 스탑로스
        sell_stop_loss = self.risk_manager.calculate_stop_loss(
            symbol='BTC/USDT',
            side='sell',
            entry_price=entry_price,
            volatility=0.02
        )
        
        # 매도 시 스탑로스는 진입가보다 높아야 함
        self.assertGreater(sell_stop_loss, entry_price)
    
    def test_calculate_take_profit(self):
        """테이크프로핏 가격 계산 테스트"""
        entry_price = 50000
        
        # 매수 포지션 테이크프로핏
        buy_take_profit = self.risk_manager.calculate_take_profit(
            symbol='BTC/USDT',
            side='buy',
            entry_price=entry_price,
            signal_strength=0.7
        )
        
        # 매수 시 테이크프로핏은 진입가보다 높아야 함
        self.assertGreater(buy_take_profit, entry_price)
        
        # 매도 포지션 테이크프로핏
        sell_take_profit = self.risk_manager.calculate_take_profit(
            symbol='BTC/USDT',
            side='sell',
            entry_price=entry_price,
            signal_strength=0.7
        )
        
        # 매도 시 테이크프로핏은 진입가보다 낮아야 함
        self.assertLess(sell_take_profit, entry_price)
    
    def test_add_and_remove_position(self):
        """포지션 추가 및 제거 테스트"""
        symbol = 'BTC/USDT'
        
        # 포지션 추가
        self.risk_manager.add_position(
            symbol=symbol,
            side='buy',
            size=0.001,
            price=50000,
            exchange_type='spot',
            stop_loss_price=47500,
            take_profit_price=55000
        )
        
        # 포지션이 추가되었는지 확인
        self.assertIn(symbol, self.risk_manager.positions)
        position = self.risk_manager.positions[symbol]
        self.assertEqual(position['side'], 'buy')
        self.assertEqual(position['size'], 0.001)
        self.assertEqual(position['price'], 50000)
        
        # 포지션 제거
        self.risk_manager.remove_position(symbol)
        
        # 포지션이 제거되었는지 확인
        self.assertNotIn(symbol, self.risk_manager.positions)
    
    def test_update_position_risk(self):
        """포지션 리스크 업데이트 테스트"""
        symbol = 'BTC/USDT'
        
        # 포지션 추가
        self.risk_manager.add_position(
            symbol=symbol,
            side='buy',
            size=0.001,
            price=50000,
            exchange_type='spot',
            stop_loss_price=47500,
            take_profit_price=55000
        )
        
        # 포지션 리스크 업데이트
        self.risk_manager.update_position_risk(
            symbol=symbol,
            current_price=52000,
            unrealized_pnl=2.0
        )
        
        # 업데이트된 정보 확인
        position = self.risk_manager.positions[symbol]
        self.assertEqual(position['current_price'], 52000)
        self.assertEqual(position['unrealized_pnl'], 2.0)
    
    def test_stop_loss_trigger(self):
        """스탑로스 발동 테스트"""
        symbol = 'BTC/USDT'
        
        # 매수 포지션 추가
        self.risk_manager.add_position(
            symbol=symbol,
            side='buy',
            size=0.001,
            price=50000,
            exchange_type='spot',
            stop_loss_price=47500,
            take_profit_price=55000
        )
        
        # 스탑로스 가격 이하로 하락
        self.risk_manager.update_position_risk(
            symbol=symbol,
            current_price=47000,  # 스탑로스 발동
            unrealized_pnl=-3.0
        )
        
        # 리스크 알림 확인
        alerts = self.risk_manager.get_risk_alerts()
        stop_loss_alerts = [alert for alert in alerts if alert['type'] == 'stop_loss']
        self.assertGreater(len(stop_loss_alerts), 0)
    
    def test_take_profit_trigger(self):
        """테이크프로핏 발동 테스트"""
        symbol = 'BTC/USDT'
        
        # 매수 포지션 추가
        self.risk_manager.add_position(
            symbol=symbol,
            side='buy',
            size=0.001,
            price=50000,
            exchange_type='spot',
            stop_loss_price=47500,
            take_profit_price=55000
        )
        
        # 테이크프로핏 가격 이상으로 상승
        self.risk_manager.update_position_risk(
            symbol=symbol,
            current_price=56000,  # 테이크프로핏 발동
            unrealized_pnl=6.0
        )
        
        # 리스크 알림 확인
        alerts = self.risk_manager.get_risk_alerts()
        take_profit_alerts = [alert for alert in alerts if alert['type'] == 'take_profit']
        self.assertGreater(len(take_profit_alerts), 0)
    
    def test_position_timeout(self):
        """포지션 타임아웃 테스트"""
        symbol = 'BTC/USDT'
        
        # 오래된 포지션 추가
        self.risk_manager.add_position(
            symbol=symbol,
            side='buy',
            size=0.001,
            price=50000,
            exchange_type='spot'
        )
        
        # 진입 시간을 과거로 설정
        position = self.risk_manager.positions[symbol]
        position['entry_time'] = datetime.now() - timedelta(hours=25)  # 25시간 전
        
        # 포지션 리스크 업데이트
        self.risk_manager.update_position_risk(
            symbol=symbol,
            current_price=51000,
            unrealized_pnl=1.0
        )
        
        # 타임아웃 알림 확인
        alerts = self.risk_manager.get_risk_alerts()
        timeout_alerts = [alert for alert in alerts if alert['type'] == 'timeout']
        self.assertGreater(len(timeout_alerts), 0)
    
    def test_daily_pnl_update(self):
        """일일 손익 업데이트 테스트"""
        initial_pnl = self.risk_manager.daily_pnl
        
        # 손익 업데이트
        self.risk_manager.update_daily_pnl(10.5)
        self.assertEqual(self.risk_manager.daily_pnl, initial_pnl + 10.5)
        
        # 추가 손익 업데이트
        self.risk_manager.update_daily_pnl(-5.2)
        self.assertEqual(self.risk_manager.daily_pnl, initial_pnl + 10.5 - 5.2)
    
    def test_drawdown_update(self):
        """드로우다운 업데이트 테스트"""
        # 초기 피크 설정
        self.risk_manager.update_drawdown(1000)
        self.assertEqual(self.risk_manager.peak_balance, 1000)
        self.assertEqual(self.risk_manager.current_drawdown, 0.0)
        
        # 잔고 감소 시 드로우다운 계산
        self.risk_manager.update_drawdown(800)
        expected_drawdown = (1000 - 800) / 1000
        self.assertEqual(self.risk_manager.current_drawdown, expected_drawdown)
        
        # 새로운 피크 달성
        self.risk_manager.update_drawdown(1200)
        self.assertEqual(self.risk_manager.peak_balance, 1200)
        self.assertEqual(self.risk_manager.current_drawdown, 0.0)
    
    def test_get_risk_summary(self):
        """리스크 요약 정보 테스트"""
        # 몇 개 포지션 추가
        self.risk_manager.add_position('BTC/USDT', 'buy', 0.001, 50000)
        self.risk_manager.add_position('ETH/USDT', 'sell', 0.1, 3000, 'futures')
        
        summary = self.risk_manager.get_risk_summary()
        
        # 예상되는 키들이 있는지 확인
        expected_keys = [
            'daily_pnl', 'current_drawdown', 'peak_balance',
            'total_positions', 'total_position_value',
            'total_unrealized_pnl', 'short_position_value'
        ]
        
        for key in expected_keys:
            self.assertIn(key, summary)
        
        # 포지션 개수 확인
        self.assertEqual(summary['total_positions'], 2)
    
    def test_emergency_stop(self):
        """비상 정지 테스트"""
        reason = "Test emergency stop"
        
        self.risk_manager.emergency_stop(reason)
        
        # 비상 정지 알림 확인
        alerts = self.risk_manager.get_risk_alerts()
        emergency_alerts = [alert for alert in alerts if alert['type'] == 'emergency_stop']
        self.assertGreater(len(emergency_alerts), 0)
        self.assertEqual(emergency_alerts[0]['message'], f"비상 정지: {reason}")
    
    def test_reset_daily_metrics(self):
        """일일 메트릭 초기화 테스트"""
        # 일일 손익 설정
        self.risk_manager.daily_pnl = 50.0
        
        # 초기화
        self.risk_manager.reset_daily_metrics()
        
        # 초기화 확인
        self.assertEqual(self.risk_manager.daily_pnl, 0.0)


class TestRiskManagerShortSelling(unittest.TestCase):
    """공매도 특화 리스크 관리 테스트"""
    
    def setUp(self):
        """공매도 테스트 설정"""
        self.config = {
            'max_position_size': 0.2,
            'short_position_limit': 0.3,
            'short_squeeze_threshold': 0.10,
            'funding_rate_threshold': 0.01,
            'risk_per_trade': 0.02
        }
        self.risk_manager = RiskManager(self.config)
    
    def test_short_position_limit(self):
        """공매도 포지션 한도 테스트"""
        # 기존 공매도 포지션들 추가
        self.risk_manager.add_position('BTC/USDT', 'sell', 0.002, 50000, 'futures')
        self.risk_manager.add_position('ETH/USDT', 'sell', 0.05, 3000, 'futures')
        
        # 새로운 공매도 거래 검증 (한도 초과)
        result = self.risk_manager.validate_trade(
            symbol='ADA/USDT',
            side='sell',
            size=100,  # 매우 큰 크기로 변경
            price=1,
            current_balance=1000,
            exchange_type='futures'
        )
        
        # 공매도 한도 초과로 거래가 거부되어야 함
        self.assertFalse(result['is_valid'])
        error_messages = [error for error in result['errors'] if '공매도 포지션 한도' in error]
        self.assertGreater(len(error_messages), 0)


if __name__ == '__main__':
    # 테스트 스위트 생성
    test_suite = unittest.TestSuite()
    
    # 기본 리스크 관리 테스트
    test_suite.addTest(unittest.makeSuite(TestRiskManager))
    
    # 공매도 특화 테스트
    test_suite.addTest(unittest.makeSuite(TestRiskManagerShortSelling))
    
    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 결과 출력
    if result.wasSuccessful():
        print("\n🎉 모든 리스크 관리 테스트가 성공했습니다!")
    else:
        print(f"\n❌ {len(result.failures)} 테스트 실패, {len(result.errors)} 오류 발생")
        sys.exit(1)