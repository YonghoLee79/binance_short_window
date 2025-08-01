"""
자동 이체 모듈 (Stub Implementation)
"""

from utils.logger import logger


class AutoTransfer:
    """자동 이체 관리 클래스 - 기본 구현"""
    
    def __init__(self, config):
        self.config = config
        logger.info("AutoTransfer 모듈 초기화 (기본 구현)")
    
    def ensure_sufficient_balance(self, market_type: str, required_amount: float) -> bool:
        """
        충분한 잔고 확보 (기본 구현 - 항상 False 반환)
        
        Args:
            market_type: 'spot' 또는 'futures'
            required_amount: 필요한 USDT 금액
            
        Returns:
            bool: 항상 False (기본 구현에서는 이체 불가)
        """
        logger.debug(f"잔고 확보 요청: {market_type}에 ${required_amount:.2f} USDT 필요")
        logger.debug("기본 구현: 자동 이체 기능 비활성화됨")
        return False
    
    def auto_balance_transfer(self, target_spot: float, target_futures: float) -> bool:
        """
        자동 리밸런싱 이체 (기본 구현 - 항상 False 반환)
        
        Args:
            target_spot: 목표 현물 금액
            target_futures: 목표 선물 금액
            
        Returns:
            bool: 항상 False (기본 구현에서는 이체 불가)
        """
        logger.debug(f"리밸런싱 요청: 현물 ${target_spot:.2f}, 선물 ${target_futures:.2f}")
        logger.debug("기본 구현: 자동 리밸런싱 기능 비활성화됨")
        return False
    
    def get_transfer_status(self) -> dict:
        """
        이체 상태 조회
        
        Returns:
            dict: 이체 상태 정보
        """
        return {
            'enabled': False,
            'last_transfer': None,
            'status': 'disabled',
            'message': '기본 구현: 자동 이체 기능 비활성화됨'
        }