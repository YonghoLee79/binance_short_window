#!/usr/bin/env python3
"""
한국 규제 준수 관리자
Upbit-Binance 자금 흐름 자동화 및 규제 준수 모니터링
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging

from .upbit_interface import UpbitInterface
from .exchange_interface import ExchangeInterface

logger = logging.getLogger(__name__)


class KoreaComplianceManager:
    """한국 규제 준수 관리자"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Upbit 인터페이스 초기화
        upbit_config = {
            'upbit_access_key': config.get('UPBIT_ACCESS_KEY', ''),
            'upbit_secret_key': config.get('UPBIT_SECRET_KEY', '')
        }
        self.upbit = UpbitInterface(upbit_config)
        
        # Binance 인터페이스 (이미 존재하는 것 사용)
        self.binance = None  # 외부에서 주입받음
        
        # 자동 전송 설정
        self.auto_transfer_enabled = config.get('AUTO_USDT_TRANSFER', True)
        self.min_transfer_amount = config.get('MIN_USDT_TRANSFER', 50)  # 최소 50 USDT
        self.max_transfer_amount = config.get('MAX_USDT_TRANSFER', 5000)  # 최대 5000 USDT
        self.transfer_buffer = config.get('USDT_TRANSFER_BUFFER', 1.1)  # 10% 버퍼
        
        # Binance 입금 주소 (설정에서 가져오거나 자동 조회)
        self.binance_usdt_address = config.get('BINANCE_USDT_ADDRESS', '')
        self.preferred_network = config.get('USDT_NETWORK', 'TRC20')  # TRC20이 수수료가 저렴
        
        # 자금 흐름 추적
        self.pending_transfers = {}
        self.transfer_history = []
        self.last_balance_check = datetime.now()
        
        # 자동 모니터링 설정
        self.monitoring_enabled = True
        self.check_interval = config.get('BALANCE_CHECK_INTERVAL', 300)  # 5분마다 확인
        
        logger.info("한국 규제 준수 관리자 초기화 완료")
    
    def set_binance_interface(self, binance_interface: ExchangeInterface):
        """Binance 인터페이스 설정"""
        self.binance = binance_interface
        
        # Binance USDT 입금 주소 자동 조회
        if not self.binance_usdt_address:
            self._fetch_binance_deposit_address()
    
    def _fetch_binance_deposit_address(self):
        """Binance USDT 입금 주소 조회"""
        try:
            # Binance API를 통해 USDT 입금 주소 조회
            if self.binance:
                deposit_info = self.binance.get_deposit_address('USDT', self.preferred_network)
                if deposit_info and 'address' in deposit_info:
                    self.binance_usdt_address = deposit_info['address']
                    logger.info(f"Binance USDT 입금 주소 자동 설정: {self.binance_usdt_address[:10]}...")
                else:
                    logger.warning("Binance USDT 입금 주소 조회 실패")
            
        except Exception as e:
            logger.error(f"Binance 입금 주소 조회 실패: {e}")
    
    def get_usdt_balance_status(self) -> Dict[str, Any]:
        """USDT 잔고 현황 조회"""
        try:
            # Upbit USDT 잔고
            upbit_usdt = self.upbit.get_usdt_balance()
            upbit_krw = self.upbit.get_krw_balance()
            
            # Binance USDT 잔고
            binance_usdt = 0.0
            if self.binance:
                binance_balance = self.binance.get_balance('USDT', 'spot')
                binance_usdt = binance_balance.get('free', 0.0)
            
            # USDT 가격 (KRW)
            ticker = self.upbit.get_ticker('KRW-USDT')
            usdt_price_krw = float(ticker.get('trade_price', 0)) if ticker else 0
            
            return {
                'upbit': {
                    'usdt': upbit_usdt,
                    'krw': upbit_krw,
                    'usdt_value_krw': upbit_usdt * usdt_price_krw
                },
                'binance': {
                    'usdt': binance_usdt,
                    'usdt_value_krw': binance_usdt * usdt_price_krw
                },
                'total_usdt': upbit_usdt + binance_usdt,
                'usdt_price_krw': usdt_price_krw,
                'last_updated': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"USDT 잔고 현황 조회 실패: {e}")
            return {}
    
    def calculate_required_usdt(self, trading_signals: List[Dict[str, Any]]) -> float:
        """거래 신호 기반 필요 USDT 계산"""
        try:
            total_usdt_needed = 0.0
            
            for signal in trading_signals:
                if signal.get('exchange_type') == 'spot' and signal.get('action') == 'buy':
                    # 현물 매수 신호인 경우 USDT 필요
                    symbol = signal.get('symbol', '')
                    size = signal.get('size', 0)
                    
                    # 대략적인 가격 계산 (실시간 가격 조회 필요시 개선 가능)
                    estimated_price = signal.get('current_price', 0)
                    if estimated_price > 0:
                        usdt_needed = size * estimated_price
                        total_usdt_needed += usdt_needed
            
            # 버퍼 적용 (10% 여유분)
            total_usdt_needed *= self.transfer_buffer
            
            return total_usdt_needed
            
        except Exception as e:
            logger.error(f"필요 USDT 계산 실패: {e}")
            return 0.0
    
    async def ensure_usdt_availability(self, required_usdt: float) -> Dict[str, Any]:
        """USDT 가용성 보장 (필요시 자동 구매 및 전송)"""
        try:
            logger.info(f"USDT 가용성 확인: {required_usdt} USDT 필요")
            
            # Upbit API가 사용 가능한지 확인
            if not hasattr(self.upbit, 'api_available') or not self.upbit.api_available:
                logger.warning("Upbit API를 사용할 수 없어 수동 USDT 관리가 필요합니다")
                return {
                    'success': False,
                    'error': 'Upbit API 사용 불가',
                    'manual_action_required': True
                }
            
            if required_usdt < self.min_transfer_amount:
                logger.info(f"필요 USDT가 최소 전송량 미만: {required_usdt} < {self.min_transfer_amount}")
                return {'success': True, 'action': 'no_action_needed'}
            
            # 현재 잔고 확인
            balance_status = self.get_usdt_balance_status()
            binance_usdt = balance_status.get('binance', {}).get('usdt', 0)
            
            if binance_usdt >= required_usdt:
                logger.info(f"Binance USDT 잔고 충분: {binance_usdt} >= {required_usdt}")
                return {'success': True, 'action': 'sufficient_balance'}
            
            # 부족한 USDT 계산
            shortage = required_usdt - binance_usdt
            transfer_amount = min(shortage * self.transfer_buffer, self.max_transfer_amount)
            
            logger.info(f"USDT 부족으로 자동 전송 필요: {shortage} USDT 부족, {transfer_amount} USDT 전송 예정")
            
            if not self.auto_transfer_enabled:
                return {
                    'success': False,
                    'error': '자동 전송이 비활성화됨',
                    'shortage': shortage,
                    'manual_action_required': True
                }
            
            # Binance 입금 주소 확인
            if not self.binance_usdt_address:
                self._fetch_binance_deposit_address()
                
                if not self.binance_usdt_address:
                    return {
                        'success': False,
                        'error': 'Binance 입금 주소를 찾을 수 없음',
                        'manual_action_required': True
                    }
            
            # 자동 구매 및 전송 실행
            transfer_result = await self.upbit.auto_purchase_and_transfer(
                target_usdt=transfer_amount,
                binance_address=self.binance_usdt_address,
                network=self.preferred_network
            )
            
            if transfer_result['success']:
                # 전송 기록 추가
                transfer_record = {
                    'timestamp': datetime.now(),
                    'amount': transfer_amount,
                    'purpose': 'trading_requirement',
                    'status': 'pending',
                    'withdraw_id': transfer_result.get('withdraw_id'),
                    'required_usdt': required_usdt,
                    'shortage': shortage
                }
                
                self.pending_transfers[transfer_result['withdraw_id']] = transfer_record
                self.transfer_history.append(transfer_record)
                
                logger.info(f"USDT 자동 전송 시작: {transfer_amount} USDT -> Binance")
                
                return {
                    'success': True,
                    'action': 'auto_transfer_initiated',
                    'transfer_amount': transfer_amount,
                    'withdraw_id': transfer_result['withdraw_id'],
                    'estimated_arrival': '10-30분 예상'
                }
            else:
                logger.error(f"USDT 자동 전송 실패: {transfer_result.get('error')}")
                return {
                    'success': False,
                    'error': transfer_result.get('error'),
                    'manual_action_required': True
                }
                
        except Exception as e:
            logger.error(f"USDT 가용성 보장 실패: {e}")
            return {'success': False, 'error': str(e)}
    
    async def monitor_pending_transfers(self):
        """대기 중인 전송 모니터링"""
        try:
            completed_transfers = []
            
            for withdraw_id, transfer_record in self.pending_transfers.items():
                if transfer_record['status'] != 'pending':
                    continue
                
                # 출금 상태 확인
                status = self.upbit.get_withdraw_status(withdraw_id)
                
                if status['success']:
                    state = status['state']
                    
                    if state == 'done':
                        transfer_record['status'] = 'completed'
                        transfer_record['completed_at'] = datetime.now()
                        completed_transfers.append(withdraw_id)
                        
                        logger.info(f"USDT 전송 완료: {withdraw_id}")
                        
                    elif state in ['rejected', 'canceled']:
                        transfer_record['status'] = 'failed'
                        transfer_record['failed_at'] = datetime.now()
                        transfer_record['failure_reason'] = state
                        completed_transfers.append(withdraw_id)
                        
                        logger.error(f"USDT 전송 실패: {withdraw_id} - {state}")
                
                # 24시간 이상 대기 중인 전송은 타임아웃 처리
                elapsed = datetime.now() - transfer_record['timestamp']
                if elapsed > timedelta(hours=24):
                    transfer_record['status'] = 'timeout'
                    transfer_record['timeout_at'] = datetime.now()
                    completed_transfers.append(withdraw_id)
                    
                    logger.warning(f"USDT 전송 타임아웃: {withdraw_id}")
            
            # 완료된 전송 제거
            for withdraw_id in completed_transfers:
                self.pending_transfers.pop(withdraw_id, None)
                
        except Exception as e:
            logger.error(f"대기 중인 전송 모니터링 실패: {e}")
    
    async def proactive_balance_management(self):
        """선제적 잔고 관리"""
        try:
            # 현재 시간이 거래 활성 시간대인지 확인
            current_hour = datetime.now().hour
            
            # 한국 시간 기준 거래 활성 시간대 (9시-22시)
            is_active_trading_hours = 9 <= current_hour <= 22
            
            if not is_active_trading_hours:
                return
            
            balance_status = self.get_usdt_balance_status()
            binance_usdt = balance_status.get('binance', {}).get('usdt', 0)
            upbit_krw = balance_status.get('upbit', {}).get('krw', 0)
            
            # Binance USDT가 임계값 이하이고 Upbit에 충분한 KRW가 있는 경우
            low_balance_threshold = self.min_transfer_amount * 2  # 100 USDT
            sufficient_krw_threshold = 150000  # 15만원
            
            if (binance_usdt < low_balance_threshold and 
                upbit_krw > sufficient_krw_threshold and 
                len(self.pending_transfers) == 0):  # 대기 중인 전송이 없는 경우
                
                # 선제적 USDT 전송
                proactive_amount = self.min_transfer_amount * 2
                
                logger.info(f"선제적 USDT 전송 시작: Binance 잔고 {binance_usdt} < {low_balance_threshold}")
                
                transfer_result = await self.ensure_usdt_availability(proactive_amount)
                
                if transfer_result['success']:
                    logger.info(f"선제적 USDT 전송 완료: {proactive_amount} USDT")
                else:
                    logger.warning(f"선제적 USDT 전송 실패: {transfer_result.get('error')}")
                    
        except Exception as e:
            logger.error(f"선제적 잔고 관리 실패: {e}")
    
    def get_transfer_statistics(self, days: int = 7) -> Dict[str, Any]:
        """전송 통계 조회"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            recent_transfers = [
                t for t in self.transfer_history 
                if t['timestamp'] > cutoff_date
            ]
            
            if not recent_transfers:
                return {
                    'period_days': days,
                    'total_transfers': 0,
                    'total_amount': 0,
                    'successful_transfers': 0,
                    'failed_transfers': 0,
                    'success_rate': 0
                }
            
            total_amount = sum(t['amount'] for t in recent_transfers)
            successful = len([t for t in recent_transfers if t['status'] == 'completed'])
            failed = len([t for t in recent_transfers if t['status'] == 'failed'])
            
            return {
                'period_days': days,
                'total_transfers': len(recent_transfers),
                'total_amount': total_amount,
                'successful_transfers': successful,
                'failed_transfers': failed,
                'success_rate': (successful / len(recent_transfers)) * 100 if recent_transfers else 0,
                'average_amount': total_amount / len(recent_transfers),
                'pending_transfers': len(self.pending_transfers)
            }
            
        except Exception as e:
            logger.error(f"전송 통계 조회 실패: {e}")
            return {}
    
    async def start_monitoring(self):
        """모니터링 시작"""
        logger.info("한국 규제 준수 모니터링 시작")
        
        while self.monitoring_enabled:
            try:
                # 대기 중인 전송 모니터링
                await self.monitor_pending_transfers()
                
                # 선제적 잔고 관리
                await self.proactive_balance_management()
                
                # 잔고 상태 업데이트
                self.last_balance_check = datetime.now()
                
                # 설정된 간격만큼 대기
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"모니터링 중 오류: {e}")
                await asyncio.sleep(60)  # 1분 후 재시도
    
    def stop_monitoring(self):
        """모니터링 중지"""
        self.monitoring_enabled = False
        logger.info("한국 규제 준수 모니터링 중지")
    
    def get_compliance_status(self) -> Dict[str, Any]:
        """규제 준수 현황"""
        try:
            balance_status = self.get_usdt_balance_status()
            transfer_stats = self.get_transfer_statistics()
            
            return {
                'balance_status': balance_status,
                'transfer_statistics': transfer_stats,
                'pending_transfers_count': len(self.pending_transfers),
                'auto_transfer_enabled': self.auto_transfer_enabled,
                'monitoring_enabled': self.monitoring_enabled,
                'binance_deposit_address': self.binance_usdt_address[:10] + '...' if self.binance_usdt_address else 'Not Set',
                'preferred_network': self.preferred_network,
                'last_balance_check': self.last_balance_check,
                'configuration': {
                    'min_transfer_amount': self.min_transfer_amount,
                    'max_transfer_amount': self.max_transfer_amount,
                    'transfer_buffer': self.transfer_buffer,
                    'check_interval': self.check_interval
                }
            }
            
        except Exception as e:
            logger.error(f"규제 준수 현황 조회 실패: {e}")
            return {'error': str(e)}