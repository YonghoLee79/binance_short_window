#!/usr/bin/env python3
"""
자동 리밸런싱 스크립트
현물 자산을 매도하여 USDT로 전환 후 선물 계정으로 이체
"""

import asyncio
import sys
import time
from pathlib import Path
from decimal import Decimal, ROUND_DOWN

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import config
from utils.logger import logger
from modules.exchange_interface import ExchangeInterface


class AutoRebalancer:
    """자동 리밸런싱 클래스"""
    
    def __init__(self):
        self.config = config
        self.logger = logger
        
        # 거래소 인터페이스 초기화
        exchange_config = {
            'api_key': self.config.BINANCE_API_KEY,
            'secret_key': self.config.BINANCE_SECRET_KEY,
            'use_testnet': False
        }
        self.exchange = ExchangeInterface(exchange_config)
        
        # 목표 배분
        self.spot_target = 0.4  # 40%
        self.futures_target = 0.6  # 60%
        
    async def get_current_balances(self):
        """현재 잔고 조회"""
        try:
            # 현물 잔고
            spot_balance = self.exchange.get_spot_balance()
            
            # 선물 잔고
            futures_balance = self.exchange.get_futures_balance()
            
            return spot_balance, futures_balance
        except Exception as e:
            self.logger.error(f"잔고 조회 실패: {e}")
            return None, None
    
    def calculate_asset_values(self, spot_balance, futures_balance, current_prices):
        """자산 가치 계산"""
        spot_values = {}
        total_spot_value = 0
        
        # 현물 자산 가치 계산
        for symbol in ['BTC', 'ETH', 'BNB', 'XRP', 'TRX']:
            if symbol in spot_balance and spot_balance[symbol] > 0:
                price_key = f"{symbol}/USDT"
                if price_key in current_prices:
                    value = spot_balance[symbol] * current_prices[price_key]
                    spot_values[symbol] = {
                        'amount': spot_balance[symbol],
                        'price': current_prices[price_key],
                        'value': value
                    }
                    total_spot_value += value
        
        # 선물 USDT 잔고
        futures_usdt = futures_balance.get('USDT', 0)
        
        total_value = total_spot_value + futures_usdt
        
        return {
            'spot_values': spot_values,
            'total_spot_value': total_spot_value,
            'futures_usdt': futures_usdt,
            'total_value': total_value
        }
    
    def calculate_rebalance_plan(self, asset_info):
        """리밸런싱 계획 수립"""
        total_value = asset_info['total_value']
        current_spot_value = asset_info['total_spot_value']
        current_futures_value = asset_info['futures_usdt']
        
        # 목표 금액
        target_spot_value = total_value * self.spot_target
        target_futures_value = total_value * self.futures_target
        
        # 현재 비율
        current_spot_ratio = current_spot_value / total_value if total_value > 0 else 0
        current_futures_ratio = current_futures_value / total_value if total_value > 0 else 0
        
        # 필요한 조정
        spot_adjustment = current_spot_value - target_spot_value
        futures_adjustment = target_futures_value - current_futures_value
        
        self.logger.info(f"현재 배분 - 현물: {current_spot_ratio:.2%}, 선물: {current_futures_ratio:.2%}")
        self.logger.info(f"목표 배분 - 현물: {self.spot_target:.2%}, 선물: {self.futures_target:.2%}")
        self.logger.info(f"조정 필요 - 현물 매도: ${spot_adjustment:.2f}, 선물 증가: ${futures_adjustment:.2f}")
        
        return {
            'total_value': total_value,
            'current_spot_ratio': current_spot_ratio,
            'current_futures_ratio': current_futures_ratio,
            'spot_adjustment': spot_adjustment,
            'futures_adjustment': futures_adjustment,
            'target_spot_value': target_spot_value,
            'target_futures_value': target_futures_value
        }
    
    def create_sell_orders(self, asset_info, rebalance_plan):
        """매도 주문 계획 생성"""
        spot_values = asset_info['spot_values']
        sell_amount_needed = rebalance_plan['spot_adjustment']
        
        if sell_amount_needed <= 0:
            self.logger.info("매도 불필요 - 이미 목표 배분 달성")
            return []
        
        sell_orders = []
        remaining_to_sell = sell_amount_needed
        
        # 우선순위: ETH > BTC > 기타 (큰 금액부터)
        priority_order = ['ETH', 'BTC', 'BNB', 'XRP', 'TRX']
        
        for symbol in priority_order:
            if symbol in spot_values and remaining_to_sell > 0:
                asset = spot_values[symbol]
                asset_value = asset['value']
                
                if asset_value > 10:  # 최소 거래 금액 $10 이상만
                    sell_value = min(asset_value, remaining_to_sell)
                    sell_amount = sell_value / asset['price']
                    
                    # 수량 정밀도 조정 (8자리)
                    sell_amount = float(Decimal(str(sell_amount)).quantize(
                        Decimal('0.00000001'), rounding=ROUND_DOWN
                    ))
                    
                    if sell_amount > 0:
                        sell_orders.append({
                            'symbol': f"{symbol}/USDT",
                            'amount': sell_amount,
                            'price': asset['price'],
                            'value': sell_value
                        })
                        remaining_to_sell -= sell_value
                        
                        self.logger.info(f"매도 계획: {symbol} {sell_amount:.8f} @ ${asset['price']:.2f} = ${sell_value:.2f}")
        
        return sell_orders
    
    async def execute_sell_order(self, order):
        """매도 주문 실행"""
        try:
            self.logger.info(f"매도 실행 중: {order['symbol']} {order['amount']:.8f}")
            
            # 시장가 매도 주문
            result = self.exchange.place_spot_order(
                symbol=order['symbol'],
                side='sell',
                order_type='market',
                amount=order['amount']
            )
            
            if result.get('success'):
                self.logger.info(f"매도 성공: {order['symbol']} - 주문ID: {result.get('order_id')}")
                return True
            else:
                self.logger.error(f"매도 실패: {order['symbol']} - {result.get('error')}")
                return False
                
        except Exception as e:
            self.logger.error(f"매도 주문 실행 중 오류: {order['symbol']} - {e}")
            return False
    
    async def transfer_to_futures(self, amount):
        """현물에서 선물로 USDT 이체"""
        try:
            self.logger.info(f"선물 계정 이체 시작: ${amount:.2f}")
            
            result = self.exchange.transfer_between_accounts(
                asset='USDT',
                amount=amount,
                from_account='SPOT',
                to_account='USDM'
            )
            
            if result.get('success'):
                self.logger.info(f"이체 성공: ${amount:.2f} USDT")
                return True
            else:
                self.logger.error(f"이체 실패: {result.get('error')}")
                return False
                
        except Exception as e:
            self.logger.error(f"이체 중 오류: {e}")
            return False
    
    async def run_rebalancing(self, dry_run=True):
        """리밸런싱 실행"""
        try:
            self.logger.info("=== 자동 리밸런싱 시작 ===")
            
            # 1. 현재 잔고 조회
            spot_balance, futures_balance = await self.get_current_balances()
            if not spot_balance or not futures_balance:
                return False
            
            # 2. 현재 가격 조회
            current_prices = {}
            for symbol in ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'XRP/USDT', 'TRX/USDT']:
                ticker = self.exchange.get_ticker(symbol)
                if ticker and 'last' in ticker:
                    current_prices[symbol] = ticker['last']
            
            # 3. 자산 가치 계산
            asset_info = self.calculate_asset_values(spot_balance, futures_balance, current_prices)
            
            # 4. 리밸런싱 계획 수립
            rebalance_plan = self.calculate_rebalance_plan(asset_info)
            
            # 5. 매도 주문 계획 생성
            sell_orders = self.create_sell_orders(asset_info, rebalance_plan)
            
            if not sell_orders:
                self.logger.info("리밸런싱 불필요")
                return True
            
            if dry_run:
                self.logger.info("=== DRY RUN 모드 - 실제 주문 없음 ===")
                for order in sell_orders:
                    self.logger.info(f"[DRY RUN] 매도: {order['symbol']} {order['amount']:.8f} = ${order['value']:.2f}")
                return True
            
            # 6. 매도 주문 실행
            total_sold_value = 0
            for order in sell_orders:
                success = await self.execute_sell_order(order)
                if success:
                    total_sold_value += order['value']
                    await asyncio.sleep(1)  # API 호출 간격
                else:
                    self.logger.error(f"매도 실패로 리밸런싱 중단: {order['symbol']}")
                    break
            
            # 7. 잠시 대기 (주문 체결 대기)
            await asyncio.sleep(5)
            
            # 8. 현물 USDT 잔고 확인
            spot_balance_after = self.exchange.get_spot_balance()
            spot_usdt = spot_balance_after.get('USDT', 0)
            
            # 9. 선물 계정으로 이체
            if spot_usdt > 10:  # 최소 $10 이상만 이체
                transfer_success = await self.transfer_to_futures(spot_usdt)
                if transfer_success:
                    self.logger.info("리밸런싱 완료!")
                else:
                    self.logger.error("이체 실패 - 수동으로 이체 필요")
            
            self.logger.info("=== 자동 리밸런싱 완료 ===")
            return True
            
        except Exception as e:
            self.logger.error(f"리밸런싱 중 오류: {e}")
            return False


async def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='자동 리밸런싱 스크립트')
    parser.add_argument('--dry-run', action='store_true', help='실제 거래 없이 시뮬레이션만 실행')
    parser.add_argument('--execute', action='store_true', help='실제 거래 실행')
    
    args = parser.parse_args()
    
    if not args.dry_run and not args.execute:
        print("사용법:")
        print("  python auto_rebalance.py --dry-run    # 시뮬레이션")
        print("  python auto_rebalance.py --execute    # 실제 실행")
        return
    
    rebalancer = AutoRebalancer()
    
    if args.execute:
        confirm = input("실제 매도 주문을 실행하시겠습니까? (yes/no): ")
        if confirm.lower() != 'yes':
            print("취소되었습니다.")
            return
    
    success = await rebalancer.run_rebalancing(dry_run=args.dry_run)
    
    if success:
        print("리밸런싱 완료!")
    else:
        print("리밸런싱 실패!")


if __name__ == "__main__":
    asyncio.run(main())