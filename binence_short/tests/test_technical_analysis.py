#!/usr/bin/env python3
"""
기술적 분석 모듈 단위 테스트
"""

import unittest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.technical_analysis import TechnicalAnalyzer


class TestTechnicalAnalyzer(unittest.TestCase):
    """기술적 분석 모듈 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        self.config = {
            'rsi_period': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            'bb_period': 20,
            'bb_stddev': 2
        }
        self.analyzer = TechnicalAnalyzer(self.config)
        
        # 테스트용 데이터 생성
        np.random.seed(42)  # 재현 가능한 결과를 위해
        dates = pd.date_range('2024-01-01', periods=100, freq='h')
        base_price = 50000
        price_changes = np.random.randn(100) * 100
        prices = base_price + np.cumsum(price_changes)
        
        self.test_data = pd.DataFrame({
            'timestamp': dates,
            'open': prices * (1 + np.random.randn(100) * 0.001),
            'high': prices * (1 + np.abs(np.random.randn(100)) * 0.002),
            'low': prices * (1 - np.abs(np.random.randn(100)) * 0.002),
            'close': prices,
            'volume': np.random.randint(100, 1000, 100)
        })
    
    def test_calculate_rsi_normal_case(self):
        """RSI 정상 계산 테스트"""
        rsi = self.analyzer.calculate_rsi(self.test_data['close'])
        
        # RSI는 0-100 범위여야 함
        self.assertTrue(all(0 <= x <= 100 for x in rsi.dropna()))
        
        # 충분한 데이터가 있으면 NaN이 아닌 값이 있어야 함
        self.assertTrue(len(rsi.dropna()) > 0)
    
    def test_calculate_rsi_insufficient_data(self):
        """RSI 데이터 부족 시 테스트"""
        short_data = self.test_data['close'][:5]  # 5개 데이터만
        rsi = self.analyzer.calculate_rsi(short_data)
        
        # 기본값 50으로 채워져야 함
        self.assertTrue(all(x == 50 for x in rsi))
    
    def test_calculate_macd_normal_case(self):
        """MACD 정상 계산 테스트"""
        macd_data = self.analyzer.calculate_macd(self.test_data['close'])
        
        # MACD는 macd, signal, histogram 키를 가져야 함
        expected_keys = {'macd', 'signal', 'histogram'}
        self.assertEqual(set(macd_data.keys()), expected_keys)
        
        # 모든 값이 숫자여야 함
        for key, series in macd_data.items():
            self.assertTrue(all(isinstance(x, (int, float, np.number)) for x in series.dropna()))
    
    def test_calculate_bollinger_bands(self):
        """볼린저 밴드 계산 테스트"""
        bb_data = self.analyzer.calculate_bollinger_bands(self.test_data['close'])
        
        # 볼린저 밴드는 upper, middle, lower 키를 가져야 함
        expected_keys = {'upper', 'middle', 'lower'}
        self.assertEqual(set(bb_data.keys()), expected_keys)
        
        # upper >= middle >= lower 관계가 성립해야 함
        valid_data = ~(bb_data['upper'].isna() | bb_data['middle'].isna() | bb_data['lower'].isna())
        if valid_data.any():
            self.assertTrue(all(bb_data['upper'][valid_data] >= bb_data['middle'][valid_data]))
            self.assertTrue(all(bb_data['middle'][valid_data] >= bb_data['lower'][valid_data]))
    
    def test_calculate_atr(self):
        """ATR 계산 테스트"""
        atr = self.analyzer.calculate_atr(
            self.test_data['high'], 
            self.test_data['low'], 
            self.test_data['close']
        )
        
        # ATR은 양수여야 함
        if hasattr(atr, 'dropna'):
            self.assertTrue(all(x >= 0 for x in atr.dropna()))
        else:
            # numpy array인 경우
            atr_series = pd.Series(atr)
            self.assertTrue(all(x >= 0 for x in atr_series.dropna()))
    
    def test_get_all_indicators(self):
        """모든 지표 계산 통합 테스트"""
        indicators = self.analyzer.get_all_indicators(self.test_data)
        
        # 예상되는 지표들이 모두 있는지 확인
        expected_indicators = ['rsi', 'macd', 'bb', 'atr', 'stoch', 'williams_r', 'volume', 'ma']
        for indicator in expected_indicators:
            self.assertIn(indicator, indicators)
    
    def test_generate_signals(self):
        """거래 신호 생성 테스트"""
        indicators = self.analyzer.get_all_indicators(self.test_data)
        signals = self.analyzer.generate_signals(indicators)
        
        # combined_signal은 -1과 1 사이여야 함
        combined_signal = signals.get('combined_signal', 0)
        self.assertTrue(-1 <= combined_signal <= 1)
        
        # 각 신호들이 올바른 범위에 있는지 확인
        for signal_name, signal_value in signals.items():
            if signal_name != 'combined_signal':
                self.assertTrue(-1 <= signal_value <= 1)
    
    def test_get_market_strength(self):
        """시장 강도 분석 테스트"""
        indicators = self.analyzer.get_all_indicators(self.test_data)
        strength = self.analyzer.get_market_strength(indicators)
        
        # 예상되는 강도 지표들 확인
        expected_strengths = ['trend_strength', 'volatility_strength', 'momentum_strength']
        for strength_type in expected_strengths:
            if strength_type in strength:
                self.assertIsInstance(strength[strength_type], (int, float, np.number))
    
    @patch('modules.technical_analysis.ta.momentum.RSIIndicator')
    def test_calculate_rsi_exception_handling(self, mock_rsi_indicator):
        """RSI 계산 예외 처리 테스트"""
        # ta.momentum.RSIIndicator가 예외를 발생시키도록 설정
        mock_rsi_indicator.side_effect = Exception("Test exception")
        
        rsi = self.analyzer.calculate_rsi(self.test_data['close'])
        
        # 예외 발생 시 기본값으로 채워져야 함
        self.assertTrue(all(x == 50 for x in rsi))
    
    def test_config_parameters(self):
        """설정 파라미터 적용 테스트"""
        custom_config = {
            'rsi_period': 21,
            'rsi_oversold': 25,
            'rsi_overbought': 75,
            'macd_fast': 8,
            'macd_slow': 21,
            'macd_signal': 5
        }
        
        custom_analyzer = TechnicalAnalyzer(custom_config)
        
        # 설정이 올바르게 적용되었는지 확인
        self.assertEqual(custom_analyzer.rsi_period, 21)
        self.assertEqual(custom_analyzer.rsi_oversold, 25)
        self.assertEqual(custom_analyzer.rsi_overbought, 75)
        self.assertEqual(custom_analyzer.macd_fast, 8)
        self.assertEqual(custom_analyzer.macd_slow, 21)
        self.assertEqual(custom_analyzer.macd_signal, 5)
    
    def test_empty_data_handling(self):
        """빈 데이터 처리 테스트"""
        empty_data = pd.DataFrame()
        
        # 빈 데이터에 대해서도 예외가 발생하지 않아야 함
        try:
            indicators = self.analyzer.get_all_indicators(empty_data)
            self.assertIsInstance(indicators, dict)
        except Exception as e:
            self.fail(f"빈 데이터 처리 중 예외 발생: {e}")


class TestTechnicalAnalyzerPerformance(unittest.TestCase):
    """기술적 분석 성능 테스트"""
    
    def setUp(self):
        """성능 테스트 설정"""
        self.config = {
            'rsi_period': 14,
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            'bb_period': 20,
            'bb_stddev': 2
        }
        self.analyzer = TechnicalAnalyzer(self.config)
        
        # 대용량 테스트 데이터
        np.random.seed(42)
        dates = pd.date_range('2023-01-01', periods=10000, freq='1min')
        prices = 50000 + np.cumsum(np.random.randn(10000) * 10)
        
        self.large_data = pd.DataFrame({
            'timestamp': dates,
            'open': prices * (1 + np.random.randn(10000) * 0.0001),
            'high': prices * (1 + np.abs(np.random.randn(10000)) * 0.0002),
            'low': prices * (1 - np.abs(np.random.randn(10000)) * 0.0002),
            'close': prices,
            'volume': np.random.randint(100, 1000, 10000)
        })
    
    def test_large_dataset_performance(self):
        """대용량 데이터셋 성능 테스트"""
        import time
        
        start_time = time.time()
        indicators = self.analyzer.get_all_indicators(self.large_data)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # 10,000개 데이터 처리가 10초 이내에 완료되어야 함
        self.assertLess(execution_time, 10.0, f"성능 테스트 실패: {execution_time:.2f}초 소요")
        
        # 결과가 올바르게 생성되었는지 확인
        self.assertIsInstance(indicators, dict)
        self.assertGreater(len(indicators), 0)


if __name__ == '__main__':
    # 테스트 스위트 생성
    test_suite = unittest.TestSuite()
    
    # 기본 테스트 추가
    loader = unittest.TestLoader()
    test_suite.addTest(loader.loadTestsFromTestCase(TestTechnicalAnalyzer))
    
    # 성능 테스트 추가 (선택적)
    test_suite.addTest(loader.loadTestsFromTestCase(TestTechnicalAnalyzerPerformance))
    
    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 결과 출력
    if result.wasSuccessful():
        print("\n모든 기술적 분석 테스트가 성공했습니다!")
    else:
        print(f"\n{len(result.failures)} 테스트 실패, {len(result.errors)} 오류 발생")
        sys.exit(1)