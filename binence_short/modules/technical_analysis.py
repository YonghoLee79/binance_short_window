"""
기술적 분석 모듈
"""
import pandas as pd
import numpy as np
import ta
from typing import Dict, Any, List, Optional
from utils.logger import logger
from utils.decorators import cache_result, log_execution_time


class TechnicalAnalyzer:
    """기술적 분석 클래스"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.rsi_period = config.get('rsi_period', 14)
        self.rsi_oversold = config.get('rsi_oversold', 30)
        self.rsi_overbought = config.get('rsi_overbought', 70)
        self.macd_fast = config.get('macd_fast', 12)
        self.macd_slow = config.get('macd_slow', 26)
        self.macd_signal = config.get('macd_signal', 9)
        self.bb_period = config.get('bb_period', 20)
        self.bb_stddev = config.get('bb_stddev', 2)
    
    @log_execution_time
    def calculate_rsi(self, prices: pd.Series) -> pd.Series:
        """RSI 계산"""
        try:
            if len(prices) < self.rsi_period + 10:
                logger.warning(f"RSI 계산용 데이터 부족: {len(prices)} < {self.rsi_period + 10}")
                return pd.Series([50] * len(prices))
            
            # RSI 계산
            rsi_values = ta.momentum.RSIIndicator(close=prices, window=self.rsi_period).rsi()
            
            # NaN 값 처리
            rsi_series = rsi_values.fillna(50)
            
            return rsi_series
        except Exception as e:
            logger.error(f"RSI 계산 오류: {e}")
            return pd.Series([50] * len(prices))
    
    @log_execution_time 
    def calculate_macd(self, prices: pd.Series) -> Dict[str, pd.Series]:
        """MACD 계산"""
        try:
            min_length = max(self.macd_slow, self.macd_signal) + 20
            if len(prices) < min_length:
                logger.warning(f"MACD 계산용 데이터 부족: {len(prices)} < {min_length}")
                return {
                    'macd': pd.Series([0] * len(prices)),
                    'signal': pd.Series([0] * len(prices)),
                    'histogram': pd.Series([0] * len(prices))
                }
            
            # MACD 계산
            macd_indicator = ta.trend.MACD(
                close=prices,
                window_fast=self.macd_fast,
                window_slow=self.macd_slow,
                window_sign=self.macd_signal
            )
            
            # NaN 값 처리
            return {
                'macd': macd_indicator.macd().fillna(0),
                'signal': macd_indicator.macd_signal().fillna(0),
                'histogram': macd_indicator.macd_diff().fillna(0)
            }
        except Exception as e:
            logger.error(f"MACD 계산 오류: {e}")
            return {
                'macd': pd.Series([0] * len(prices)),
                'signal': pd.Series([0] * len(prices)),
                'histogram': pd.Series([0] * len(prices))
            }
    
    @log_execution_time
    def calculate_bollinger_bands(self, prices: pd.Series) -> Dict[str, pd.Series]:
        """볼린저 밴드 계산"""
        try:
            bb_indicator = ta.volatility.BollingerBands(
                close=prices,
                window=self.bb_period,
                window_dev=self.bb_stddev
            )
            return {
                'upper': bb_indicator.bollinger_hband(),
                'middle': bb_indicator.bollinger_mavg(),
                'lower': bb_indicator.bollinger_lband()
            }
        except Exception as e:
            logger.error(f"볼린저 밴드 계산 오류: {e}")
            return {
                'upper': pd.Series(prices),
                'middle': pd.Series(prices),
                'lower': pd.Series(prices)
            }
    
    @log_execution_time
    def calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """ATR (Average True Range) 계산"""
        try:
            atr_indicator = ta.volatility.AverageTrueRange(
                high=high, low=low, close=close, window=period
            )
            return atr_indicator.average_true_range()
        except Exception as e:
            logger.error(f"ATR 계산 오류: {e}")
            return pd.Series([0.01] * len(close))
    
    @log_execution_time
    def calculate_stochastic(self, high: pd.Series, low: pd.Series, close: pd.Series) -> Dict[str, pd.Series]:
        """스토캐스틱 계산"""
        try:
            stoch_indicator = ta.momentum.StochasticOscillator(
                high=high, low=low, close=close,
                window=14, smooth_window=3
            )
            return {
                'slowk': stoch_indicator.stoch(),
                'slowd': stoch_indicator.stoch_signal()
            }
        except Exception as e:
            logger.error(f"스토캐스틱 계산 오류: {e}")
            return {
                'slowk': pd.Series([50] * len(close)),
                'slowd': pd.Series([50] * len(close))
            }
    
    @log_execution_time
    def calculate_williams_r(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Williams %R 계산"""
        try:
            williams_r = ta.momentum.WilliamsRIndicator(
                high=high, low=low, close=close, lbp=period
            )
            return williams_r.williams_r()
        except Exception as e:
            logger.error(f"Williams %R 계산 오류: {e}")
            return pd.Series([-50] * len(close))
    
    @log_execution_time
    def calculate_volume_indicators(self, prices: pd.Series, volume: pd.Series) -> Dict[str, pd.Series]:
        """거래량 지표 계산"""
        try:
            # OBV (On-Balance Volume)
            obv_indicator = ta.volume.OnBalanceVolumeIndicator(
                close=prices, volume=volume
            )
            obv = obv_indicator.on_balance_volume()
            
            # VWAP (Volume Weighted Average Price)
            vwap = (prices * volume).cumsum() / volume.cumsum()
            
            return {
                'obv': obv,
                'vwap': vwap
            }
        except Exception as e:
            logger.error(f"거래량 지표 계산 오류: {e}")
            return {
                'obv': pd.Series([0] * len(prices)),
                'vwap': pd.Series(prices)
            }
    
    @log_execution_time
    def calculate_moving_averages(self, prices: pd.Series) -> Dict[str, pd.Series]:
        """이동평균 계산"""
        try:
            return {
                'sma_5': ta.trend.SMAIndicator(close=prices, window=5).sma_indicator(),
                'sma_10': ta.trend.SMAIndicator(close=prices, window=10).sma_indicator(),
                'sma_20': ta.trend.SMAIndicator(close=prices, window=20).sma_indicator(),
                'sma_50': ta.trend.SMAIndicator(close=prices, window=50).sma_indicator(),
                'ema_5': ta.trend.EMAIndicator(close=prices, window=5).ema_indicator(),
                'ema_10': ta.trend.EMAIndicator(close=prices, window=10).ema_indicator(),
                'ema_20': ta.trend.EMAIndicator(close=prices, window=20).ema_indicator(),
                'ema_50': ta.trend.EMAIndicator(close=prices, window=50).ema_indicator()
            }
        except Exception as e:
            logger.error(f"이동평균 계산 오류: {e}")
            return {}
    
    @cache_result(cache_time=300)
    def get_all_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """모든 지표 계산"""
        try:
            indicators = {}
            
            # 기본 지표
            indicators['rsi'] = self.calculate_rsi(df['close'])
            indicators['macd'] = self.calculate_macd(df['close'])
            indicators['bb'] = self.calculate_bollinger_bands(df['close'])
            indicators['atr'] = self.calculate_atr(df['high'], df['low'], df['close'])
            indicators['stoch'] = self.calculate_stochastic(df['high'], df['low'], df['close'])
            indicators['williams_r'] = self.calculate_williams_r(df['high'], df['low'], df['close'])
            
            # 거래량 지표
            if 'volume' in df.columns:
                indicators['volume'] = self.calculate_volume_indicators(df['close'], df['volume'])
            
            # 이동평균
            indicators['ma'] = self.calculate_moving_averages(df['close'])
            
            return indicators
        except Exception as e:
            logger.error(f"지표 계산 오류: {e}")
            return {}
    
    def validate_signal_strength(self, signals: Dict[str, float], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """다층 신호 검증 시스템"""
        try:
            validation_result = {
                'is_valid': False,
                'confidence': 0.0,
                'consistency_score': 0.0,
                'volume_confirmation': 0.0,
                'market_regime_score': 0.0,
                'final_strength': 0.0
            }
            
            # 1. 시간대별 일관성 검증
            consistency_score = self._check_timeframe_consistency(signals, market_data)
            
            # 2. 거래량 확인
            volume_confirmation = self._check_volume_support(market_data)
            
            # 3. 시장 구조 분석
            market_regime_score = self._identify_market_regime(market_data)
            
            # 4. 노이즈 필터링
            noise_filter_score = self._apply_noise_filter(signals, market_data)
            
            # 5. 최종 신호 강도 계산 (가중치 조정으로 더 균형잡힌 평가)
            final_strength = (
                consistency_score * 0.25 +      # 일관성 (25%)
                volume_confirmation * 0.30 +    # 거래량 확인 (30%)
                market_regime_score * 0.20 +    # 시장 체제 (20%)  
                noise_filter_score * 0.25       # 노이즈 필터링 (25%)
            )
            
            # 6. 검증 결과 (임계값을 더 낮춰서 더 많은 신호 허용)
            is_valid = final_strength > 0.25
            
            validation_result.update({
                'is_valid': is_valid,
                'confidence': final_strength,
                'consistency_score': consistency_score,
                'volume_confirmation': volume_confirmation,
                'market_regime_score': market_regime_score,
                'final_strength': final_strength
            })
            
            # 상세 로깅 (성공/실패 모두)
            logger.info(f"신호 검증 결과 - 유효:{is_valid}, 최종강도:{final_strength:.3f} (임계값:0.25)")
            if not is_valid:
                logger.info(f"신호 검증 세부점수 - 일관성:{consistency_score:.3f}, 거래량:{volume_confirmation:.3f}, "
                           f"시장체제:{market_regime_score:.3f}, 노이즈필터:{noise_filter_score:.3f}, "
                           f"최종:{final_strength:.3f}")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"신호 검증 실패: {e}")
            return {
                'is_valid': False,
                'confidence': 0.0,
                'consistency_score': 0.0,
                'volume_confirmation': 0.0,
                'market_regime_score': 0.0,
                'final_strength': 0.0
            }

    def _check_timeframe_consistency(self, signals: Dict[str, float], market_data: Dict[str, Any]) -> float:
        """여러 시간대 신호 일관성 검증"""
        try:
            # 현재 신호의 방향성
            combined_signal = signals.get('combined_signal', 0)
            if abs(combined_signal) < 0.1:
                return 0.0
            
            direction = 1 if combined_signal > 0 else -1
            consistency_count = 0
            total_checks = 0
            
            # 각 개별 신호들의 일관성 확인
            signal_keys = ['rsi_signal', 'macd_signal', 'bb_signal', 'stoch_signal']
            for key in signal_keys:
                if key in signals:
                    signal_value = signals[key]
                    if abs(signal_value) > 0.1:  # 중립이 아닌 신호만 검사
                        total_checks += 1
                        if (direction > 0 and signal_value > 0) or (direction < 0 and signal_value < 0):
                            consistency_count += 1
            
            if total_checks == 0:
                return 0.0
            
            return consistency_count / total_checks
            
        except Exception as e:
            logger.error(f"시간대별 일관성 검증 실패: {e}")
            return 0.0

    def _check_volume_support(self, market_data: Dict[str, Any]) -> float:
        """거래량 뒷받침 확인"""
        try:
            # 기본 데이터 구조에서 거래량 정보 추출
            if 'volume' not in market_data:
                return 0.5  # 거래량 정보가 없으면 중립
            
            current_volume = market_data.get('volume', 0)
            avg_volume = market_data.get('avg_volume', current_volume)
            
            if avg_volume <= 0:
                return 0.5
            
            volume_ratio = current_volume / avg_volume
            
            # 거래량 비율에 따른 점수 계산
            if volume_ratio > 1.5:  # 평균의 150% 이상
                return 0.9
            elif volume_ratio > 1.2:  # 평균의 120% 이상
                return 0.7
            elif volume_ratio > 0.8:  # 평균의 80% 이상
                return 0.5
            else:  # 평균의 80% 미만
                return 0.2
                
        except Exception as e:
            logger.error(f"거래량 확인 실패: {e}")
            return 0.5

    def _identify_market_regime(self, market_data: Dict[str, Any]) -> float:
        """시장 체제 식별"""
        try:
            # 기본값
            if 'price_data' not in market_data:
                return 0.5
            
            price_data = market_data['price_data']
            if len(price_data) < 20:
                return 0.5
            
            # 최근 20개 가격으로 트렌드 분석
            prices = pd.Series(price_data[-20:])
            
            # 1. 트렌드 강도 계산
            price_change = (prices.iloc[-1] - prices.iloc[0]) / prices.iloc[0]
            trend_strength = abs(price_change)
            
            # 2. 변동성 계산
            volatility = prices.pct_change().std()
            
            # 3. 체제 분류 및 점수 부여
            if trend_strength > 0.05 and volatility < 0.03:
                # 강한 트렌드, 낮은 변동성 → 트렌드 추종에 유리
                return 0.9
            elif trend_strength > 0.02 and volatility < 0.05:
                # 중간 트렌드, 적당한 변동성
                return 0.7
            elif volatility > 0.05:
                # 고변동성 → 신호 신뢰도 낮음
                return 0.3
            else:
                # 횡보 시장
                return 0.5
                
        except Exception as e:
            logger.error(f"시장 체제 식별 실패: {e}")
            return 0.5

    def _apply_noise_filter(self, signals: Dict[str, float], market_data: Dict[str, Any]) -> float:
        """노이즈 필터링"""
        try:
            combined_signal = signals.get('combined_signal', 0)
            
            # 신호가 너무 약하면 노이즈로 간주 (임계값 완화)
            if abs(combined_signal) < 0.08:
                return 0.1
            
            # 신호의 지속성 확인 (과거 신호와 비교)
            signal_history = market_data.get('signal_history', [])
            if len(signal_history) < 3:
                return 0.6  # 히스토리가 부족하면 중간 점수
            
            # 최근 3개 신호의 일관성 확인
            recent_signals = signal_history[-3:]
            current_direction = 1 if combined_signal > 0 else -1
            
            consistent_count = 0
            for historic_signal in recent_signals:
                if (current_direction > 0 and historic_signal > 0) or (current_direction < 0 and historic_signal < 0):
                    consistent_count += 1
            
            consistency_ratio = consistent_count / len(recent_signals)
            
            # 일관성이 높을수록 노이즈가 아닐 가능성 높음
            if consistency_ratio >= 0.67:  # 2/3 이상 일관성
                return 0.9
            elif consistency_ratio >= 0.33:  # 1/3 이상 일관성
                return 0.6
            else:
                return 0.3
                
        except Exception as e:
            logger.error(f"노이즈 필터링 실패: {e}")
            return 0.5

    def generate_signals(self, indicators: Dict[str, Any]) -> Dict[str, float]:
        """거래 신호 생성"""
        try:
            signals = {}
            
            # RSI 신호
            if 'rsi' in indicators and len(indicators['rsi']) > 0:
                rsi_current = indicators['rsi'].iloc[-1] if hasattr(indicators['rsi'], 'iloc') else indicators['rsi'][-1]
                
                # NaN 또는 무효한 값 처리
                if pd.isna(rsi_current) or not isinstance(rsi_current, (int, float)):
                    rsi_current = 50
                
                if rsi_current < self.rsi_oversold:
                    signals['rsi_signal'] = 1.0  # 매수
                elif rsi_current > self.rsi_overbought:
                    signals['rsi_signal'] = -1.0  # 매도
                else:
                    signals['rsi_signal'] = 0.0  # 중립
            else:
                signals['rsi_signal'] = 0.0
            
            # MACD 신호
            if 'macd' in indicators and 'histogram' in indicators['macd']:
                macd_hist = indicators['macd']['histogram']
                if len(macd_hist) >= 2:
                    hist_current = macd_hist.iloc[-1] if hasattr(macd_hist, 'iloc') else macd_hist[-1]
                    hist_prev = macd_hist.iloc[-2] if hasattr(macd_hist, 'iloc') else macd_hist[-2]
                    
                    # NaN 또는 무효한 값 처리
                    if pd.isna(hist_current) or pd.isna(hist_prev):
                        signals['macd_signal'] = 0.0
                    elif hist_current > 0 and hist_prev <= 0:
                        signals['macd_signal'] = 1.0  # 매수
                    elif hist_current < 0 and hist_prev >= 0:
                        signals['macd_signal'] = -1.0  # 매도
                    else:
                        signals['macd_signal'] = 0.0  # 중립
                else:
                    signals['macd_signal'] = 0.0
            else:
                signals['macd_signal'] = 0.0
            
            # 볼린저 밴드 신호
            if 'bb' in indicators:
                bb_data = indicators['bb']
                if (len(bb_data.get('lower', [])) > 0 and 
                    len(bb_data.get('upper', [])) > 0 and 
                    len(bb_data.get('middle', [])) > 0):
                    
                    current_price = bb_data['middle'].iloc[-1] if hasattr(bb_data['middle'], 'iloc') else bb_data['middle'][-1]
                    upper_band = bb_data['upper'].iloc[-1] if hasattr(bb_data['upper'], 'iloc') else bb_data['upper'][-1]
                    lower_band = bb_data['lower'].iloc[-1] if hasattr(bb_data['lower'], 'iloc') else bb_data['lower'][-1]
                    
                    # NaN 또는 무효한 값 처리
                    if pd.isna(current_price) or pd.isna(upper_band) or pd.isna(lower_band):
                        signals['bb_signal'] = 0.0
                    elif current_price <= lower_band:
                        signals['bb_signal'] = 1.0  # 매수
                    elif current_price >= upper_band:
                        signals['bb_signal'] = -1.0  # 매도
                    else:
                        signals['bb_signal'] = 0.0  # 중립
                else:
                    signals['bb_signal'] = 0.0
            else:
                signals['bb_signal'] = 0.0
            
            # 스토캐스틱 신호
            if 'stoch' in indicators and 'slowk' in indicators['stoch']:
                stoch_data = indicators['stoch']
                if len(stoch_data['slowk']) > 0:
                    slowk = stoch_data['slowk'].iloc[-1] if hasattr(stoch_data['slowk'], 'iloc') else stoch_data['slowk'][-1]
                    
                    # NaN 또는 무효한 값 처리
                    if pd.isna(slowk) or not isinstance(slowk, (int, float)):
                        signals['stoch_signal'] = 0.0
                    elif slowk < 20:
                        signals['stoch_signal'] = 1.0  # 매수
                    elif slowk > 80:
                        signals['stoch_signal'] = -1.0  # 매도
                    else:
                        signals['stoch_signal'] = 0.0  # 중립
                else:
                    signals['stoch_signal'] = 0.0
            else:
                signals['stoch_signal'] = 0.0
            
            # 종합 신호 계산 - 모든 신호 포함하여 평균 계산
            valid_signals = [v for k, v in signals.items() if k.endswith('_signal') and isinstance(v, (int, float)) and not pd.isna(v)]
            
            if valid_signals:
                signals['combined_signal'] = sum(valid_signals) / len(valid_signals)
            else:
                signals['combined_signal'] = 0.0
            
            # 안전 검증: 모든 신호가 유효한 숫자인지 확인
            for key, value in signals.items():
                if pd.isna(value) or not isinstance(value, (int, float)):
                    signals[key] = 0.0
            
            return signals
        except Exception as e:
            logger.error(f"신호 생성 오류: {e}")
            # 완전히 안전한 기본 신호 반환
            return {
                'rsi_signal': 0.0,
                'macd_signal': 0.0,
                'bb_signal': 0.0,
                'stoch_signal': 0.0,
                'combined_signal': 0.0
            }
    
    def get_market_strength(self, indicators: Dict[str, Any]) -> Dict[str, float]:
        """시장 강도 분석"""
        try:
            strength = {}
            
            # 트렌드 강도
            if 'ma' in indicators:
                ma_data = indicators['ma']
                if 'sma_20' in ma_data and 'sma_50' in ma_data:
                    sma_20 = ma_data['sma_20'][-1] if len(ma_data['sma_20']) > 0 else 0
                    sma_50 = ma_data['sma_50'][-1] if len(ma_data['sma_50']) > 0 else 0
                    
                    if sma_20 > sma_50:
                        strength['trend_strength'] = (sma_20 - sma_50) / sma_50
                    else:
                        strength['trend_strength'] = (sma_20 - sma_50) / sma_50
            
            # 변동성 강도
            if 'atr' in indicators:
                atr_current = indicators['atr'][-1] if len(indicators['atr']) > 0 else 0
                strength['volatility_strength'] = atr_current
            
            # 모멘텀 강도
            if 'rsi' in indicators:
                rsi_current = indicators['rsi'][-1] if len(indicators['rsi']) > 0 else 50
                strength['momentum_strength'] = abs(rsi_current - 50) / 50
            
            return strength
        except Exception as e:
            logger.error(f"시장 강도 분석 오류: {e}")
            return {}