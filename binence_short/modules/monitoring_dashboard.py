#!/usr/bin/env python3
"""
실시간 모니터링 대시보드
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import logger
from config import config


class MonitoringDashboard:
    """실시간 모니터링 대시보드 클래스"""
    
    def __init__(self, portfolio_manager=None, risk_manager=None, strategy_engine=None):
        self.portfolio_manager = portfolio_manager
        self.risk_manager = risk_manager
        self.strategy_engine = strategy_engine
        
        # 모니터링 데이터 저장
        self.metrics_history = []
        self.alerts_history = []
        self.trade_history = []
        
        # 대시보드 설정
        self.update_interval = 5  # 5초마다 업데이트
        self.max_history_length = 1000  # 최대 1000개 기록 보관
        
        # 웹 대시보드용 데이터
        self.dashboard_data = {
            'status': 'initializing',
            'last_update': datetime.now().isoformat(),
            'portfolio': {},
            'positions': [],
            'performance': {},
            'alerts': [],
            'system_health': {}
        }
        
        logger.info("모니터링 대시보드 초기화 완료")
    
    def collect_portfolio_metrics(self) -> Dict[str, Any]:
        """포트폴리오 메트릭 수집"""
        try:
            if not self.portfolio_manager:
                return {}
            
            portfolio_summary = self.portfolio_manager.get_portfolio_summary()
            position_details = self.portfolio_manager.get_position_details()
            
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'current_balance': portfolio_summary.get('current_balance', 0),
                'initial_balance': portfolio_summary.get('initial_balance', 0),
                'total_pnl': portfolio_summary.get('total_pnl', 0),
                'total_pnl_pct': portfolio_summary.get('total_pnl_pct', 0),
                'positions_count': len(position_details),
                'allocation': portfolio_summary.get('allocation', {}),
                'trades_count': portfolio_summary.get('trades', 0),
                'positions': position_details
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"포트폴리오 메트릭 수집 실패: {e}")
            return {}
    
    def collect_risk_metrics(self) -> Dict[str, Any]:
        """리스크 메트릭 수집"""
        try:
            if not self.risk_manager:
                return {}
            
            risk_summary = self.risk_manager.get_risk_summary()
            alerts = self.risk_manager.get_risk_alerts()
            
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'daily_pnl': risk_summary.get('daily_pnl', 0),
                'current_drawdown': risk_summary.get('current_drawdown', 0),
                'peak_balance': risk_summary.get('peak_balance', 0),
                'total_positions': risk_summary.get('total_positions', 0),
                'total_position_value': risk_summary.get('total_position_value', 0),
                'total_unrealized_pnl': risk_summary.get('total_unrealized_pnl', 0),
                'short_position_value': risk_summary.get('short_position_value', 0),
                'alerts_count': len(alerts),
                'alerts': alerts
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"리스크 메트릭 수집 실패: {e}")
            return {}
    
    def collect_strategy_metrics(self) -> Dict[str, Any]:
        """전략 메트릭 수집"""
        try:
            if not self.strategy_engine:
                return {}
            
            strategy_performance = self.strategy_engine.get_strategy_performance()
            
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'total_pnl': strategy_performance.get('total_pnl', 0),
                'total_trades': strategy_performance.get('total_trades', 0),
                'winning_trades': strategy_performance.get('winning_trades', 0),
                'losing_trades': strategy_performance.get('losing_trades', 0),
                'win_rate': strategy_performance.get('win_rate', 0),
                'active_positions': strategy_performance.get('active_positions', 0)
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"전략 메트릭 수집 실패: {e}")
            return {}
    
    def collect_system_health(self) -> Dict[str, Any]:
        """시스템 헬스 메트릭 수집"""
        try:
            import psutil
            import os
            
            # CPU 및 메모리 사용률
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # 프로세스 정보
            process = psutil.Process(os.getpid())
            process_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # 네트워크 연결 상태 (간단한 체크)
            network_status = self._check_network_connectivity()
            
            health_metrics = {
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_mb': memory.available / 1024 / 1024,
                'disk_percent': disk.percent,
                'disk_free_gb': disk.free / 1024 / 1024 / 1024,
                'process_memory_mb': process_memory,
                'network_status': network_status,
                'uptime_seconds': time.time() - psutil.boot_time()
            }
            
            return health_metrics
            
        except Exception as e:
            logger.error(f"시스템 헬스 수집 실패: {e}")
            return {}
    
    def _check_network_connectivity(self) -> str:
        """네트워크 연결 상태 확인"""
        try:
            import requests
            response = requests.get('https://api.binance.com/api/v3/ping', timeout=5)
            return 'connected' if response.status_code == 200 else 'disconnected'
        except:
            return 'disconnected'
    
    def update_dashboard_data(self):
        """대시보드 데이터 업데이트"""
        try:
            # 각 메트릭 수집
            portfolio_metrics = self.collect_portfolio_metrics()
            risk_metrics = self.collect_risk_metrics()
            strategy_metrics = self.collect_strategy_metrics()
            system_health = self.collect_system_health()
            
            # 대시보드 데이터 업데이트
            self.dashboard_data.update({
                'status': 'running',
                'last_update': datetime.now().isoformat(),
                'portfolio': {
                    'current_balance': portfolio_metrics.get('current_balance', 0),
                    'total_pnl': portfolio_metrics.get('total_pnl', 0),
                    'total_pnl_pct': portfolio_metrics.get('total_pnl_pct', 0),
                    'allocation': portfolio_metrics.get('allocation', {}),
                    'positions_count': portfolio_metrics.get('positions_count', 0)
                },
                'positions': portfolio_metrics.get('positions', []),
                'performance': {
                    'total_trades': strategy_metrics.get('total_trades', 0),
                    'win_rate': strategy_metrics.get('win_rate', 0),
                    'winning_trades': strategy_metrics.get('winning_trades', 0),
                    'losing_trades': strategy_metrics.get('losing_trades', 0),
                    'daily_pnl': risk_metrics.get('daily_pnl', 0),
                    'current_drawdown': risk_metrics.get('current_drawdown', 0)
                },
                'alerts': risk_metrics.get('alerts', [])[-10:],  # 최근 10개만
                'system_health': system_health
            })
            
            # 히스토리 저장
            current_metrics = {
                'timestamp': datetime.now().isoformat(),
                'portfolio': portfolio_metrics,
                'risk': risk_metrics,
                'strategy': strategy_metrics,
                'system': system_health
            }
            
            self.metrics_history.append(current_metrics)
            
            # 히스토리 크기 제한
            if len(self.metrics_history) > self.max_history_length:
                self.metrics_history = self.metrics_history[-self.max_history_length:]
            
            logger.debug("대시보드 데이터 업데이트 완료")
            
        except Exception as e:
            logger.error(f"대시보드 데이터 업데이트 실패: {e}")
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """대시보드 데이터 반환"""
        return self.dashboard_data.copy()
    
    def get_historical_data(self, hours: int = 24) -> List[Dict[str, Any]]:
        """과거 데이터 반환"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            filtered_history = [
                record for record in self.metrics_history
                if datetime.fromisoformat(record['timestamp']) > cutoff_time
            ]
            
            return filtered_history
            
        except Exception as e:
            logger.error(f"과거 데이터 조회 실패: {e}")
            return []
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """성과 리포트 생성"""
        try:
            if not self.metrics_history:
                return {}
            
            # 최근 24시간 데이터
            recent_data = self.get_historical_data(24)
            
            if not recent_data:
                return {}
            
            # 초기값과 현재값
            start_data = recent_data[0]
            end_data = recent_data[-1]
            
            start_balance = start_data.get('portfolio', {}).get('current_balance', 0)
            end_balance = end_data.get('portfolio', {}).get('current_balance', 0)
            
            # 성과 계산
            balance_change = end_balance - start_balance
            balance_change_pct = (balance_change / start_balance * 100) if start_balance > 0 else 0
            
            # 거래 통계
            start_trades = start_data.get('strategy', {}).get('total_trades', 0)
            end_trades = end_data.get('strategy', {}).get('total_trades', 0)
            trades_today = end_trades - start_trades
            
            # 최대/최소값
            balances = [d.get('portfolio', {}).get('current_balance', 0) for d in recent_data]
            max_balance = max(balances) if balances else 0
            min_balance = min(balances) if balances else 0
            
            report = {
                'period': '24h',
                'start_time': start_data['timestamp'],
                'end_time': end_data['timestamp'],
                'start_balance': start_balance,
                'end_balance': end_balance,
                'balance_change': balance_change,
                'balance_change_pct': balance_change_pct,
                'max_balance': max_balance,
                'min_balance': min_balance,
                'trades_count': trades_today,
                'current_win_rate': end_data.get('strategy', {}).get('win_rate', 0),
                'max_drawdown': max(
                    d.get('risk', {}).get('current_drawdown', 0) for d in recent_data
                ) if recent_data else 0
            }
            
            return report
            
        except Exception as e:
            logger.error(f"성과 리포트 생성 실패: {e}")
            return {}
    
    def save_dashboard_data(self, filepath: str = None):
        """대시보드 데이터를 파일로 저장"""
        try:
            if not filepath:
                filepath = f"dashboard_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            data_to_save = {
                'dashboard_data': self.dashboard_data,
                'metrics_history': self.metrics_history[-100:],  # 최근 100개만 저장
                'generated_at': datetime.now().isoformat()
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=2, ensure_ascii=False)
            
            logger.info(f"대시보드 데이터 저장 완료: {filepath}")
            
        except Exception as e:
            logger.error(f"대시보드 데이터 저장 실패: {e}")
    
    def print_console_dashboard(self):
        """콘솔용 대시보드 출력"""
        try:
            data = self.dashboard_data
            
            print("\n" + "=" * 80)
            print("🚀 실시간 트레이딩 봇 대시보드")
            print("=" * 80)
            
            # 상태 정보
            print(f"📊 상태: {data['status'].upper()}")
            print(f"⏰ 마지막 업데이트: {data['last_update']}")
            print()
            
            # 포트폴리오 정보
            portfolio = data.get('portfolio', {})
            print("💰 포트폴리오")
            print(f"  현재 잔고: ${portfolio.get('current_balance', 0):,.2f}")
            print(f"  총 손익: {portfolio.get('total_pnl', 0):+,.2f} USDT ({portfolio.get('total_pnl_pct', 0):+.2f}%)")
            print(f"  활성 포지션: {portfolio.get('positions_count', 0)}개")
            print()
            
            # 성과 정보
            performance = data.get('performance', {})
            print("📈 성과")
            print(f"  총 거래: {performance.get('total_trades', 0)}회")
            print(f"  승률: {performance.get('win_rate', 0):.1f}%")
            print(f"  일일 손익: {performance.get('daily_pnl', 0):+,.2f} USDT")
            print(f"  현재 드로우다운: {performance.get('current_drawdown', 0):.2%}")
            print()
            
            # 시스템 헬스
            health = data.get('system_health', {})
            print("🖥️ 시스템 헬스")
            print(f"  CPU 사용률: {health.get('cpu_percent', 0):.1f}%")
            print(f"  메모리 사용률: {health.get('memory_percent', 0):.1f}%")
            print(f"  네트워크: {health.get('network_status', 'unknown').upper()}")
            print()
            
            # 최근 알림
            alerts = data.get('alerts', [])
            if alerts:
                print("⚠️ 최근 알림")
                for alert in alerts[-3:]:  # 최근 3개만
                    print(f"  {alert.get('type', 'unknown').upper()}: {alert.get('message', '')}")
                print()
            
            print("=" * 80)
            
        except Exception as e:
            logger.error(f"콘솔 대시보드 출력 실패: {e}")
    
    async def start_monitoring(self):
        """모니터링 시작"""
        try:
            logger.info("실시간 모니터링 시작")
            
            while True:
                # 데이터 업데이트
                self.update_dashboard_data()
                
                # 콘솔 대시보드 출력 (선택적)
                self.print_console_dashboard()
                
                # 대기
                await asyncio.sleep(self.update_interval)
                
        except Exception as e:
            logger.error(f"모니터링 실행 실패: {e}")
    
    def stop_monitoring(self):
        """모니터링 중지"""
        logger.info("모니터링 중지")


# 웹 대시보드용 간단한 HTTP 서버
class WebDashboardServer:
    """웹 대시보드 서버"""
    
    def __init__(self, dashboard: MonitoringDashboard, port: int = 8080):
        self.dashboard = dashboard
        self.port = port
        self.app = None
    
    def create_html_dashboard(self) -> str:
        """HTML 대시보드 생성"""
        data = self.dashboard.get_dashboard_data()
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Trading Bot Dashboard</title>
            <meta charset="utf-8">
            <meta http-equiv="refresh" content="10">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .card {{ background: white; border-radius: 8px; padding: 20px; margin: 20px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; color: #333; }}
                .metric {{ display: inline-block; margin: 10px; padding: 15px; background: #f8f9fa; border-radius: 4px; }}
                .positive {{ color: #28a745; }}
                .negative {{ color: #dc3545; }}
                .status {{ padding: 5px 10px; border-radius: 4px; color: white; background: #28a745; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 트레이딩 봇 대시보드</h1>
                    <p>상태: <span class="status">{data['status'].upper()}</span></p>
                    <p>마지막 업데이트: {data['last_update']}</p>
                </div>
                
                <div class="card">
                    <h2>💰 포트폴리오</h2>
                    <div class="metric">
                        <strong>현재 잔고</strong><br>
                        ${data.get('portfolio', {}).get('current_balance', 0):,.2f}
                    </div>
                    <div class="metric">
                        <strong>총 손익</strong><br>
                        <span class="{'positive' if data.get('portfolio', {}).get('total_pnl', 0) >= 0 else 'negative'}">
                            {data.get('portfolio', {}).get('total_pnl', 0):+,.2f} USDT
                            ({data.get('portfolio', {}).get('total_pnl_pct', 0):+.2f}%)
                        </span>
                    </div>
                    <div class="metric">
                        <strong>활성 포지션</strong><br>
                        {data.get('portfolio', {}).get('positions_count', 0)}개
                    </div>
                </div>
                
                <div class="card">
                    <h2>📈 성과</h2>
                    <div class="metric">
                        <strong>총 거래</strong><br>
                        {data.get('performance', {}).get('total_trades', 0)}회
                    </div>
                    <div class="metric">
                        <strong>승률</strong><br>
                        {data.get('performance', {}).get('win_rate', 0):.1f}%
                    </div>
                    <div class="metric">
                        <strong>일일 손익</strong><br>
                        <span class="{'positive' if data.get('performance', {}).get('daily_pnl', 0) >= 0 else 'negative'}">
                            {data.get('performance', {}).get('daily_pnl', 0):+,.2f} USDT
                        </span>
                    </div>
                </div>
                
                <div class="card">
                    <h2>🖥️ 시스템 헬스</h2>
                    <div class="metric">
                        <strong>CPU 사용률</strong><br>
                        {data.get('system_health', {}).get('cpu_percent', 0):.1f}%
                    </div>
                    <div class="metric">
                        <strong>메모리 사용률</strong><br>
                        {data.get('system_health', {}).get('memory_percent', 0):.1f}%
                    </div>
                    <div class="metric">
                        <strong>네트워크</strong><br>
                        {data.get('system_health', {}).get('network_status', 'unknown').upper()}
                    </div>
                </div>
                
                <div class="card">
                    <h2>📋 활성 포지션</h2>
                    <table>
                        <tr>
                            <th>심볼</th>
                            <th>방향</th>
                            <th>크기</th>
                            <th>현재가</th>
                            <th>미실현 손익</th>
                        </tr>
        """
        
        for position in data.get('positions', []):
            html += f"""
                        <tr>
                            <td>{position.get('symbol', '')}</td>
                            <td>{position.get('side', '').upper()}</td>
                            <td>{position.get('size', 0):.6f}</td>
                            <td>${position.get('current_price', 0):,.2f}</td>
                            <td class="{'positive' if position.get('unrealized_pnl', 0) >= 0 else 'negative'}">
                                {position.get('unrealized_pnl', 0):+,.2f}
                            </td>
                        </tr>
            """
        
        html += """
                    </table>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    async def start_server(self):
        """웹 서버 시작"""
        try:
            from http.server import HTTPServer, BaseHTTPRequestHandler
            import threading
            
            class DashboardHandler(BaseHTTPRequestHandler):
                def do_GET(self):
                    if self.path == '/' or self.path == '/dashboard':
                        self.send_response(200)
                        self.send_header('Content-type', 'text/html; charset=utf-8')
                        self.end_headers()
                        html = server.create_html_dashboard()
                        self.wfile.write(html.encode('utf-8'))
                    elif self.path == '/api/data':
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        data = json.dumps(server.dashboard.get_dashboard_data())
                        self.wfile.write(data.encode('utf-8'))
                    else:
                        self.send_response(404)
                        self.end_headers()
                
                def log_message(self, format, *args):
                    pass  # 로그 출력 비활성화
            
            server = self
            httpd = HTTPServer(('localhost', self.port), DashboardHandler)
            
            def run_server():
                httpd.serve_forever()
            
            thread = threading.Thread(target=run_server, daemon=True)
            thread.start()
            
            logger.info(f"웹 대시보드 서버 시작: http://localhost:{self.port}")
            
        except Exception as e:
            logger.error(f"웹 서버 시작 실패: {e}")


if __name__ == "__main__":
    # 테스트용 실행
    dashboard = MonitoringDashboard()
    
    print("🖥️ 모니터링 대시보드 테스트")
    dashboard.update_dashboard_data()
    dashboard.print_console_dashboard()
    
    # 웹 서버 테스트
    web_server = WebDashboardServer(dashboard)
    asyncio.run(web_server.start_server())
    
    print("웹 대시보드가 http://localhost:8080 에서 실행 중입니다.")
    print("Ctrl+C로 종료하세요.")
    
    try:
        asyncio.run(dashboard.start_monitoring())
    except KeyboardInterrupt:
        print("\n모니터링 종료")