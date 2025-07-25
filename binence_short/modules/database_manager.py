#!/usr/bin/env python3
"""
데이터베이스 관리 모듈
"""

import sqlite3
import pandas as pd
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import logger


class DatabaseManager:
    """데이터베이스 관리 클래스"""
    
    def __init__(self, db_path: str = "trading_bot.db"):
        self.db_path = db_path
        self.connection = None
        self.init_database()
        logger.info(f"데이터베이스 관리자 초기화 완료: {db_path}")
    
    def init_database(self):
        """데이터베이스 초기화"""
        try:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row  # 딕셔너리 형태로 결과 반환
            
            self.create_tables()
            logger.info("데이터베이스 테이블 생성 완료")
            
        except Exception as e:
            logger.error(f"데이터베이스 초기화 실패: {e}")
            raise
    
    def create_tables(self):
        """테이블 생성"""
        try:
            cursor = self.connection.cursor()
            
            # 거래 기록 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    size REAL NOT NULL,
                    price REAL NOT NULL,
                    exchange_type TEXT NOT NULL,
                    order_type TEXT NOT NULL,
                    fees REAL DEFAULT 0,
                    pnl REAL DEFAULT 0,
                    strategy TEXT,
                    order_id TEXT,
                    status TEXT
                )
            """)
            
            # 포지션 기록 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    size REAL NOT NULL,
                    entry_price REAL NOT NULL,
                    current_price REAL,
                    exchange_type TEXT NOT NULL,
                    stop_loss_price REAL,
                    take_profit_price REAL,
                    unrealized_pnl REAL DEFAULT 0,
                    realized_pnl REAL DEFAULT 0,
                    entry_time DATETIME,
                    exit_time DATETIME,
                    status TEXT DEFAULT 'active'
                )
            """)
            
            # 성과 메트릭 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    total_balance REAL NOT NULL,
                    spot_balance REAL DEFAULT 0,
                    futures_balance REAL DEFAULT 0,
                    total_pnl REAL DEFAULT 0,
                    daily_pnl REAL DEFAULT 0,
                    total_trades INTEGER DEFAULT 0,
                    winning_trades INTEGER DEFAULT 0,
                    losing_trades INTEGER DEFAULT 0,
                    win_rate REAL DEFAULT 0,
                    max_drawdown REAL DEFAULT 0,
                    current_drawdown REAL DEFAULT 0,
                    active_positions INTEGER DEFAULT 0
                )
            """)
            
            # 리스크 알림 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS risk_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    alert_type TEXT NOT NULL,
                    symbol TEXT,
                    message TEXT NOT NULL,
                    severity TEXT DEFAULT 'medium',
                    resolved BOOLEAN DEFAULT FALSE,
                    metadata TEXT
                )
            """)
            
            # 시장 데이터 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    symbol TEXT NOT NULL,
                    exchange_type TEXT NOT NULL,
                    open_price REAL,
                    high_price REAL,
                    low_price REAL,
                    close_price REAL,
                    volume REAL,
                    timeframe TEXT DEFAULT '1h'
                )
            """)
            
            # 전략 성과 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS strategy_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    strategy_name TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    signal_strength REAL,
                    action TEXT,
                    confidence REAL,
                    result TEXT,
                    pnl REAL DEFAULT 0,
                    metadata TEXT
                )
            """)
            
            # 시스템 로그 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    level TEXT NOT NULL,
                    module TEXT,
                    message TEXT NOT NULL,
                    metadata TEXT
                )
            """)
            
            # 인덱스 생성
            self._create_indexes(cursor)
            
            self.connection.commit()
            
        except Exception as e:
            logger.error(f"테이블 생성 실패: {e}")
            raise
    
    def _create_indexes(self, cursor):
        """인덱스 생성"""
        try:
            # 자주 조회되는 컬럼들에 인덱스 생성
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)",
                "CREATE INDEX IF NOT EXISTS idx_positions_symbol ON positions(symbol)",
                "CREATE INDEX IF NOT EXISTS idx_positions_status ON positions(status)",
                "CREATE INDEX IF NOT EXISTS idx_performance_timestamp ON performance_metrics(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON risk_alerts(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_alerts_type ON risk_alerts(alert_type)",
                "CREATE INDEX IF NOT EXISTS idx_market_data_symbol_timestamp ON market_data(symbol, timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_strategy_timestamp ON strategy_performance(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON system_logs(timestamp)"
            ]
            
            for index_sql in indexes:
                cursor.execute(index_sql)
                
        except Exception as e:
            logger.error(f"인덱스 생성 실패: {e}")
    
    def insert_trade(self, trade_data: Dict[str, Any]) -> Optional[int]:
        """거래 기록 삽입"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
                INSERT INTO trades (
                    symbol, side, size, price, exchange_type, order_type,
                    fees, pnl, strategy, order_id, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trade_data.get('symbol'),
                trade_data.get('side'),
                trade_data.get('size'),
                trade_data.get('price'),
                trade_data.get('exchange_type'),
                trade_data.get('order_type'),
                trade_data.get('fees', 0),
                trade_data.get('pnl', 0),
                trade_data.get('strategy'),
                trade_data.get('order_id'),
                trade_data.get('status')
            ))
            
            self.connection.commit()
            trade_id = cursor.lastrowid
            
            logger.debug(f"거래 기록 삽입 완료: ID {trade_id}")
            return trade_id
            
        except Exception as e:
            logger.error(f"거래 기록 삽입 실패: {e}")
            return None
    
    def insert_position(self, position_data: Dict[str, Any]) -> Optional[int]:
        """포지션 기록 삽입"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
                INSERT INTO positions (
                    symbol, side, size, entry_price, current_price, exchange_type,
                    stop_loss_price, take_profit_price, unrealized_pnl, realized_pnl,
                    entry_time, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                position_data.get('symbol'),
                position_data.get('side'),
                position_data.get('size'),
                position_data.get('entry_price'),
                position_data.get('current_price'),
                position_data.get('exchange_type'),
                position_data.get('stop_loss_price'),
                position_data.get('take_profit_price'),
                position_data.get('unrealized_pnl', 0),
                position_data.get('realized_pnl', 0),
                position_data.get('entry_time', datetime.now()),
                position_data.get('status', 'active')
            ))
            
            self.connection.commit()
            position_id = cursor.lastrowid
            
            logger.debug(f"포지션 기록 삽입 완료: ID {position_id}")
            return position_id
            
        except Exception as e:
            logger.error(f"포지션 기록 삽입 실패: {e}")
            return None
    
    def update_position(self, position_id: int, update_data: Dict[str, Any]) -> bool:
        """포지션 업데이트"""
        try:
            cursor = self.connection.cursor()
            
            # 동적으로 UPDATE 쿼리 생성
            set_clauses = []
            values = []
            
            for key, value in update_data.items():
                if key in ['current_price', 'unrealized_pnl', 'realized_pnl', 'status', 'exit_time']:
                    set_clauses.append(f"{key} = ?")
                    values.append(value)
            
            if not set_clauses:
                return False
            
            values.append(position_id)
            
            query = f"UPDATE positions SET {', '.join(set_clauses)} WHERE id = ?"
            cursor.execute(query, values)
            
            self.connection.commit()
            
            logger.debug(f"포지션 업데이트 완료: ID {position_id}")
            return True
            
        except Exception as e:
            logger.error(f"포지션 업데이트 실패: {e}")
            return False
    
    def insert_performance_metrics(self, metrics: Dict[str, Any]) -> Optional[int]:
        """성과 메트릭 삽입"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
                INSERT INTO performance_metrics (
                    total_balance, spot_balance, futures_balance, total_pnl, daily_pnl,
                    total_trades, winning_trades, losing_trades, win_rate,
                    max_drawdown, current_drawdown, active_positions
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics.get('total_balance', 0),
                metrics.get('spot_balance', 0),
                metrics.get('futures_balance', 0),
                metrics.get('total_pnl', 0),
                metrics.get('daily_pnl', 0),
                metrics.get('total_trades', 0),
                metrics.get('winning_trades', 0),
                metrics.get('losing_trades', 0),
                metrics.get('win_rate', 0),
                metrics.get('max_drawdown', 0),
                metrics.get('current_drawdown', 0),
                metrics.get('active_positions', 0)
            ))
            
            self.connection.commit()
            metrics_id = cursor.lastrowid
            
            logger.debug(f"성과 메트릭 삽입 완료: ID {metrics_id}")
            return metrics_id
            
        except Exception as e:
            logger.error(f"성과 메트릭 삽입 실패: {e}")
            return None
    
    def insert_risk_alert(self, alert_data: Dict[str, Any]) -> Optional[int]:
        """리스크 알림 삽입"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
                INSERT INTO risk_alerts (
                    alert_type, symbol, message, severity, metadata
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                alert_data.get('type'),
                alert_data.get('symbol'),
                alert_data.get('message'),
                alert_data.get('severity', 'medium'),
                json.dumps(alert_data.get('metadata', {}))
            ))
            
            self.connection.commit()
            alert_id = cursor.lastrowid
            
            logger.debug(f"리스크 알림 삽입 완료: ID {alert_id}")
            return alert_id
            
        except Exception as e:
            logger.error(f"리스크 알림 삽입 실패: {e}")
            return None
    
    def get_trades(self, symbol: str = None, start_date: datetime = None, 
                   end_date: datetime = None, limit: int = 100) -> List[Dict[str, Any]]:
        """거래 기록 조회"""
        try:
            cursor = self.connection.cursor()
            
            query = "SELECT * FROM trades WHERE 1=1"
            params = []
            
            if symbol:
                query += " AND symbol = ?"
                params.append(symbol)
            
            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"거래 기록 조회 실패: {e}")
            return []
    
    def get_active_positions(self) -> List[Dict[str, Any]]:
        """활성 포지션 조회"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
                SELECT * FROM positions 
                WHERE status = 'active' 
                ORDER BY entry_time DESC
            """)
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"활성 포지션 조회 실패: {e}")
            return []
    
    def get_performance_metrics(self, hours: int = 24) -> List[Dict[str, Any]]:
        """성과 메트릭 조회"""
        try:
            cursor = self.connection.cursor()
            
            start_time = datetime.now() - timedelta(hours=hours)
            
            cursor.execute("""
                SELECT * FROM performance_metrics 
                WHERE timestamp >= ? 
                ORDER BY timestamp DESC
            """, (start_time,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"성과 메트릭 조회 실패: {e}")
            return []
    
    def get_risk_alerts(self, resolved: bool = False, hours: int = 24) -> List[Dict[str, Any]]:
        """리스크 알림 조회"""
        try:
            cursor = self.connection.cursor()
            
            start_time = datetime.now() - timedelta(hours=hours)
            
            cursor.execute("""
                SELECT * FROM risk_alerts 
                WHERE resolved = ? AND timestamp >= ?
                ORDER BY timestamp DESC
            """, (resolved, start_time))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"리스크 알림 조회 실패: {e}")
            return []
    
    def get_trading_statistics(self, days: int = 30) -> Dict[str, Any]:
        """거래 통계 조회"""
        try:
            cursor = self.connection.cursor()
            
            start_date = datetime.now() - timedelta(days=days)
            
            # 기본 통계
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                    SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losing_trades,
                    AVG(pnl) as avg_pnl,
                    SUM(pnl) as total_pnl,
                    MAX(pnl) as max_profit,
                    MIN(pnl) as max_loss,
                    SUM(fees) as total_fees
                FROM trades 
                WHERE timestamp >= ?
            """, (start_date,))
            
            stats = dict(cursor.fetchone())
            
            # 승률 계산
            if stats['total_trades'] > 0:
                stats['win_rate'] = (stats['winning_trades'] / stats['total_trades']) * 100
            else:
                stats['win_rate'] = 0
            
            # 심볼별 통계
            cursor.execute("""
                SELECT 
                    symbol,
                    COUNT(*) as trades_count,
                    SUM(pnl) as total_pnl,
                    AVG(pnl) as avg_pnl
                FROM trades 
                WHERE timestamp >= ?
                GROUP BY symbol
                ORDER BY total_pnl DESC
            """, (start_date,))
            
            symbol_stats = [dict(row) for row in cursor.fetchall()]
            stats['by_symbol'] = symbol_stats
            
            # 일별 통계
            cursor.execute("""
                SELECT 
                    DATE(timestamp) as date,
                    COUNT(*) as trades_count,
                    SUM(pnl) as daily_pnl,
                    SUM(fees) as daily_fees
                FROM trades 
                WHERE timestamp >= ?
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
            """, (start_date,))
            
            daily_stats = [dict(row) for row in cursor.fetchall()]
            stats['by_day'] = daily_stats
            
            return stats
            
        except Exception as e:
            logger.error(f"거래 통계 조회 실패: {e}")
            return {}
    
    def backup_database(self, backup_path: str = None) -> bool:
        """데이터베이스 백업"""
        try:
            if not backup_path:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_path = f"trading_bot_backup_{timestamp}.db"
            
            # 백업 연결 생성
            backup_conn = sqlite3.connect(backup_path)
            
            # 데이터베이스 복사
            self.connection.backup(backup_conn)
            backup_conn.close()
            
            logger.info(f"데이터베이스 백업 완료: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"데이터베이스 백업 실패: {e}")
            return False
    
    def export_to_csv(self, table_name: str, output_path: str = None) -> bool:
        """테이블을 CSV로 내보내기"""
        try:
            if not output_path:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_path = f"{table_name}_{timestamp}.csv"
            
            # pandas를 사용해서 CSV로 내보내기
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", self.connection)
            df.to_csv(output_path, index=False, encoding='utf-8-sig')
            
            logger.info(f"테이블 CSV 내보내기 완료: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"CSV 내보내기 실패: {e}")
            return False
    
    def cleanup_old_data(self, days_to_keep: int = 90) -> bool:
        """오래된 데이터 정리"""
        try:
            cursor = self.connection.cursor()
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # 각 테이블의 오래된 데이터 삭제
            tables_to_cleanup = [
                'system_logs',
                'market_data',
                'risk_alerts'
            ]
            
            total_deleted = 0
            
            for table in tables_to_cleanup:
                cursor.execute(f"""
                    DELETE FROM {table} 
                    WHERE timestamp < ?
                """, (cutoff_date,))
                
                deleted_count = cursor.rowcount
                total_deleted += deleted_count
                
                logger.debug(f"{table} 테이블에서 {deleted_count}개 레코드 삭제")
            
            self.connection.commit()
            
            # VACUUM으로 데이터베이스 압축
            cursor.execute("VACUUM")
            
            logger.info(f"데이터 정리 완료: 총 {total_deleted}개 레코드 삭제")
            return True
            
        except Exception as e:
            logger.error(f"데이터 정리 실패: {e}")
            return False
    
    def close(self):
        """데이터베이스 연결 종료"""
        try:
            if self.connection:
                self.connection.close()
                logger.info("데이터베이스 연결 종료")
        except Exception as e:
            logger.error(f"데이터베이스 연결 종료 실패: {e}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# 데이터베이스 매니저 싱글톤 인스턴스
_db_manager_instance = None

def get_database_manager() -> DatabaseManager:
    """데이터베이스 매니저 싱글톤 인스턴스 반환"""
    global _db_manager_instance
    
    if _db_manager_instance is None:
        _db_manager_instance = DatabaseManager()
    
    return _db_manager_instance


if __name__ == "__main__":
    # 테스트
    print("🗄️ 데이터베이스 관리자 테스트")
    
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
        print(f"거래 기록 삽입: ID {trade_id}")
        
        # 거래 조회
        trades = db.get_trades(limit=5)
        print(f"거래 기록 조회: {len(trades)}개")
        
        # 통계 조회
        stats = db.get_trading_statistics(days=1)
        print(f"거래 통계: {stats}")
        
        print("✅ 데이터베이스 테스트 완료")