"""
로깅 시스템 모듈
"""
import logging
import logging.handlers
import os
from datetime import datetime
from typing import Optional

class TradingLogger:
    """거래 봇 전용 로거 클래스"""
    
    def __init__(self, 
                 name: str = 'trading_bot',
                 log_file: str = 'trading_bot.log',
                 log_level: str = 'INFO',
                 max_size: str = '10MB',
                 backup_count: int = 5):
        
        self.name = name
        self.log_file = log_file
        self.log_level = getattr(logging, log_level.upper())
        self.max_size = self._parse_size(max_size)
        self.backup_count = backup_count
        
        self.logger = self._setup_logger()
    
    def _parse_size(self, size_str: str) -> int:
        """크기 문자열을 바이트로 변환"""
        if size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        else:
            return int(size_str)
    
    def _setup_logger(self) -> logging.Logger:
        """로거 설정"""
        logger = logging.getLogger(self.name)
        logger.setLevel(self.log_level)
        
        # 기존 핸들러 제거
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # 포맷터 설정
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 파일 핸들러 (로테이팅)
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_file,
            maxBytes=self.max_size,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # 콘솔 핸들러
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        return logger
    
    def info(self, message: str, **kwargs):
        """정보 로그"""
        self.logger.info(message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """디버그 로그"""
        self.logger.debug(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """경고 로그"""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """에러 로그"""
        self.logger.error(message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """크리티컬 로그"""
        self.logger.critical(message, **kwargs)
    
    def trade_log(self, symbol: str, side: str, amount: float, price: float, 
                  trade_type: str = 'spot', pnl: float = 0):
        """거래 전용 로그"""
        message = f"거래 실행 - {trade_type.upper()} | {symbol} | {side.upper()} | {amount:.6f} @ ${price:.2f}"
        if pnl != 0:
            message += f" | PnL: {pnl:+.2f} USDT"
        self.info(message)
    
    def balance_log(self, current_balance: float, initial_balance: float, 
                   spot_balance: float = 0, futures_balance: float = 0):
        """잔고 전용 로그"""
        pnl = current_balance - initial_balance
        pnl_pct = (pnl / initial_balance * 100) if initial_balance > 0 else 0
        
        message = f"잔고 업데이트 - 총: ${current_balance:.2f} | 손익: {pnl:+.2f} ({pnl_pct:+.2f}%)"
        if spot_balance > 0 or futures_balance > 0:
            message += f" | 현물: ${spot_balance:.2f} | 선물: ${futures_balance:.2f}"
        self.info(message)
    
    def system_log(self, status: str, positions: int = 0, trades: int = 0, win_rate: float = 0):
        """시스템 상태 로그"""
        message = f"시스템 상태 - {status.upper()} | 포지션: {positions}개 | 거래: {trades}회"
        if win_rate > 0:
            message += f" | 승률: {win_rate:.1f}%"
        self.info(message)
    
    def performance_log(self, metrics: dict):
        """성과 지표 로그"""
        message = "성과 지표 - "
        for key, value in metrics.items():
            if isinstance(value, float):
                message += f"{key}: {value:.2f} | "
            else:
                message += f"{key}: {value} | "
        self.info(message.rstrip(" | "))

class TradeFileLogger:
    """거래 기록 전용 파일 로거"""
    
    def __init__(self, log_file: str = 'trade_history.log'):
        self.log_file = log_file
        self.ensure_log_file()
    
    def ensure_log_file(self):
        """로그 파일 존재 확인"""
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w', encoding='utf-8') as f:
                f.write("timestamp,symbol,side,amount,price,type,pnl,fees\n")
    
    def log_trade(self, symbol: str, side: str, amount: float, price: float,
                  trade_type: str = 'spot', pnl: float = 0, fees: float = 0):
        """거래 기록 CSV 로그"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"{timestamp},{symbol},{side},{amount:.6f},{price:.2f},{trade_type},{pnl:.2f},{fees:.2f}\n")

# 전역 로거 인스턴스
logger = TradingLogger()
trade_logger = TradeFileLogger()