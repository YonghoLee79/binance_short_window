#!/usr/bin/env python3
"""
텔레그램 알림 모듈
"""

import os
import requests
from typing import Optional
from utils import logger


class TelegramBot:
    """텔레그램 봇 클래스"""
    
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.enabled = bool(self.bot_token and self.chat_id)
        
        if not self.enabled:
            logger.warning("텔레그램 봇 토큰 또는 채팅 ID가 설정되지 않았습니다")
    
    def send_message(self, message: str) -> bool:
        """텔레그램 메시지 전송"""
        if not self.enabled:
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, data=data, timeout=10)
            
            if response.status_code == 200:
                return True
            else:
                logger.error(f"텔레그램 메시지 전송 실패: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"텔레그램 메시지 전송 오류: {e}")
            return False


class TelegramNotifications:
    """텔레그램 알림 관리 클래스"""
    
    def __init__(self):
        self.telegram = TelegramBot()
        self.enabled = self.telegram.enabled
        
        if self.enabled:
            logger.info("텔레그램 알림 시스템 초기화 완료")
            self.send_startup_message()
        else:
            logger.warning("텔레그램 알림이 비활성화되어 있습니다")
    
    def send_startup_message(self):
        """봇 시작 알림"""
        try:
            message = """
🚀 <b>트레이딩 봇 시작</b>

📅 시작 시간: {}
💰 초기 상태: 시스템 점검 중
🔄 모드: 실시간 거래

<i>봇이 정상적으로 시작되었습니다.</i>
            """.format(
                __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ).strip()
            
            self.telegram.send_message(message)
            logger.info("봇 시작 알림 전송 완료")
        except Exception as e:
            logger.error(f"시작 알림 전송 실패: {e}")
    
    def send_trade_notification(self, trade_info: dict):
        """거래 알림"""
        if not self.enabled:
            return
        
        try:
            side_emoji = "📈" if trade_info.get('side') == 'buy' else "📉"
            
            message = f"""
{side_emoji} <b>거래 실행</b>

🏷️ 심볼: {trade_info.get('symbol', 'N/A')}
📊 방향: {trade_info.get('side', 'N/A').upper()}
🔢 수량: {trade_info.get('size', 0)}
💵 가격: ${trade_info.get('price', 0):,.2f}
💰 총액: ${(trade_info.get('size', 0) * trade_info.get('price', 0)):,.2f}
📍 거래소: {trade_info.get('exchange_type', 'spot').upper()}

<i>거래가 성공적으로 실행되었습니다.</i>
            """.strip()
            
            self.telegram.send_message(message)
            logger.info(f"거래 알림 전송: {trade_info.get('symbol')} {trade_info.get('side')}")
        except Exception as e:
            logger.error(f"거래 알림 전송 실패: {e}")
    
    def send_portfolio_update(self, portfolio_info: dict):
        """포트폴리오 업데이트 알림"""
        if not self.enabled:
            return
        
        try:
            pnl_emoji = "💚" if portfolio_info.get('total_pnl', 0) >= 0 else "❤️"
            
            message = f"""
💼 <b>포트폴리오 업데이트</b>

💰 현재 잔고: ${portfolio_info.get('current_balance', 0):,.2f}
{pnl_emoji} 총 손익: ${portfolio_info.get('total_pnl', 0):+,.2f} ({portfolio_info.get('total_pnl_pct', 0):+.2f}%)
📊 활성 포지션: {portfolio_info.get('positions_count', 0)}개
📈 총 거래: {portfolio_info.get('total_trades', 0)}회

<i>포트폴리오 상태가 업데이트되었습니다.</i>
            """.strip()
            
            self.telegram.send_message(message)
            logger.info("포트폴리오 업데이트 알림 전송 완료")
        except Exception as e:
            logger.error(f"포트폴리오 알림 전송 실패: {e}")
    
    def send_risk_alert(self, alert_info: dict):
        """리스크 알림"""
        if not self.enabled:
            return
        
        try:
            alert_type = alert_info.get('type', 'unknown')
            severity = alert_info.get('severity', 'medium')
            
            emoji_map = {
                'stop_loss': '🛑',
                'take_profit': '🎯',
                'timeout': '⏰',
                'emergency_stop': '🚨',
                'daily_loss': '📉',
                'max_drawdown': '📊'
            }
            
            severity_map = {
                'low': '🟡',
                'medium': '🟠', 
                'high': '🔴',
                'critical': '🚨'
            }
            
            alert_emoji = emoji_map.get(alert_type, '⚠️')
            severity_emoji = severity_map.get(severity, '🟠')
            
            message = f"""
{alert_emoji} <b>리스크 알림</b> {severity_emoji}

🏷️ 유형: {alert_type.replace('_', ' ').title()}
📍 심볼: {alert_info.get('symbol', 'N/A')}
⚠️ 경고도: {severity.upper()}
📝 메시지: {alert_info.get('message', '상세 정보 없음')}

<i>즉시 확인이 필요합니다.</i>
            """.strip()
            
            self.telegram.send_message(message)
            logger.warning(f"리스크 알림 전송: {alert_type} - {alert_info.get('symbol')}")
        except Exception as e:
            logger.error(f"리스크 알림 전송 실패: {e}")
    
    def send_system_status(self, status_info: dict):
        """시스템 상태 알림"""
        if not self.enabled:
            return
        
        try:
            status = status_info.get('status', 'unknown')
            status_emoji = "🟢" if status == 'running' else "🔴" if status == 'error' else "🟡"
            
            message = f"""
🖥️ <b>시스템 상태</b> {status_emoji}

📊 상태: {status.upper()}
💾 메모리: {status_info.get('memory_percent', 0):.1f}%
⚡ CPU: {status_info.get('cpu_percent', 0):.1f}%
🌐 네트워크: {status_info.get('network_status', 'unknown').upper()}
⏱️ 업타임: {status_info.get('uptime_hours', 0):.1f}시간

<i>시스템 상태 점검 완료</i>
            """.strip()
            
            self.telegram.send_message(message)
            logger.info("시스템 상태 알림 전송 완료")
        except Exception as e:
            logger.error(f"시스템 상태 알림 전송 실패: {e}")
    
    def send_daily_summary(self, summary_info: dict):
        """일일 요약 알림"""
        if not self.enabled:
            return
        
        try:
            message = f"""
📊 <b>일일 거래 요약</b>

📅 날짜: {summary_info.get('date', '오늘')}
💰 일일 손익: ${summary_info.get('daily_pnl', 0):+,.2f}
📈 거래 횟수: {summary_info.get('trades_count', 0)}회
🎯 승률: {summary_info.get('win_rate', 0):.1f}%
📊 최고 수익: ${summary_info.get('max_profit', 0):,.2f}
📉 최대 손실: ${summary_info.get('max_loss', 0):,.2f}

<i>오늘의 거래 결과입니다.</i>
            """.strip()
            
            self.telegram.send_message(message)
            logger.info("일일 요약 알림 전송 완료")
        except Exception as e:
            logger.error(f"일일 요약 알림 전송 실패: {e}")
    
    def send_trading_cycle_log(self, cycle_info: dict):
        """실시간 거래 사이클 로그 전송"""
        if not self.enabled:
            return
        
        try:
            cycle_num = cycle_info.get('cycle_number', 0)
            duration = cycle_info.get('duration', 0)
            opportunities = cycle_info.get('opportunities', {})
            trades_executed = cycle_info.get('trades_executed', 0)
            
            # 기회 발견 상황 요약
            opp_summary = []
            for strategy, count in opportunities.items():
                if count > 0:
                    emoji_map = {
                        'arbitrage': '🔀',
                        'trend_following': '📈', 
                        'hedging': '🛡️',
                        'momentum': '⚡'
                    }
                    opp_summary.append(f"{emoji_map.get(strategy, '📊')} {strategy}: {count}개")
            
            if not opp_summary:
                opp_text = "❌ 기회 없음"
            else:
                opp_text = "\n".join(opp_summary)
            
            # 거래 실행 상태
            trade_emoji = "💰" if trades_executed > 0 else "⏳"
            
            message = f"""
🔄 <b>거래 사이클 #{cycle_num}</b>

⏱️ 실행 시간: {duration:.1f}초
📊 거래 기회:
{opp_text}

{trade_emoji} 실행된 거래: {trades_executed}개
📅 시간: {__import__('datetime').datetime.now().strftime('%H:%M:%S')}

<i>사이클 완료</i>
            """.strip()
            
            self.telegram.send_message(message)
            
        except Exception as e:
            logger.error(f"거래 사이클 로그 전송 실패: {e}")
    
    def send_market_analysis_log(self, analysis_info: dict):
        """시장 분석 로그 전송"""
        if not self.enabled:
            return
        
        try:
            symbols_count = analysis_info.get('symbols_analyzed', 0)
            top_signals = analysis_info.get('top_signals', [])
            market_condition = analysis_info.get('market_condition', 'neutral')
            
            condition_emoji = {
                'bullish': '🐂',
                'bearish': '🐻', 
                'neutral': '📊',
                'volatile': '⚡'
            }.get(market_condition, '📊')
            
            message = f"""
📈 <b>시장 분석 리포트</b>

📊 분석 심볼: {symbols_count}개
{condition_emoji} 시장 상황: {market_condition.title()}

🎯 주요 신호:
"""
            
            if top_signals:
                for signal in top_signals[:3]:  # 상위 3개만
                    symbol = signal.get('symbol', 'N/A')
                    strategy = signal.get('strategy', 'N/A')
                    confidence = signal.get('confidence', 0) * 100
                    message += f"• {symbol}: {strategy} ({confidence:.0f}%)\n"
            else:
                message += "• 현재 유효한 신호 없음\n"
            
            message += f"\n📅 {__import__('datetime').datetime.now().strftime('%H:%M:%S')}"
            
            self.telegram.send_message(message)
            
        except Exception as e:
            logger.error(f"시장 분석 로그 전송 실패: {e}")
    
    def send_performance_log(self, performance_info: dict):
        """성과 로그 전송 (시간별)"""
        if not self.enabled:
            return
        
        try:
            current_balance = performance_info.get('current_balance', 0)
            hourly_pnl = performance_info.get('hourly_pnl', 0)
            hourly_pnl_pct = performance_info.get('hourly_pnl_pct', 0)
            total_trades = performance_info.get('total_trades', 0)
            win_rate = performance_info.get('win_rate', 0)
            
            pnl_emoji = "💚" if hourly_pnl >= 0 else "❤️"
            
            message = f"""
💎 <b>시간별 성과 리포트</b>

💰 현재 잔고: ${current_balance:,.2f}
{pnl_emoji} 시간 손익: ${hourly_pnl:+,.2f} ({hourly_pnl_pct:+.2f}%)
📊 총 거래: {total_trades}회
🎯 승률: {win_rate:.1f}%

📅 {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}

<i>성과 추적 중...</i>
            """.strip()
            
            self.telegram.send_message(message)
            
        except Exception as e:
            logger.error(f"성과 로그 전송 실패: {e}")
    
    def send_opportunity_alert(self, opportunity_info: dict):
        """거래 기회 발견 즉시 알림"""
        if not self.enabled:
            return
        
        try:
            strategy = opportunity_info.get('strategy', 'unknown')
            symbol = opportunity_info.get('symbol', 'N/A')
            confidence = opportunity_info.get('confidence', 0) * 100
            expected_return = opportunity_info.get('expected_return', 0) * 100
            
            strategy_emoji = {
                'arbitrage': '🔀',
                'trend_following': '📈',
                'hedging': '🛡️', 
                'momentum': '⚡'
            }.get(strategy, '📊')
            
            message = f"""
🚨 <b>거래 기회 발견!</b>

{strategy_emoji} 전략: {strategy.replace('_', ' ').title()}
💎 심볼: {symbol}
🎯 신뢰도: {confidence:.0f}%
💰 예상 수익: {expected_return:.2f}%

⏰ 발견 시간: {__import__('datetime').datetime.now().strftime('%H:%M:%S')}

<i>거래 검토 중...</i>
            """.strip()
            
            self.telegram.send_message(message)
            logger.info(f"거래 기회 알림 전송: {strategy} - {symbol}")
            
        except Exception as e:
            logger.error(f"거래 기회 알림 전송 실패: {e}")
    
    def send_error_log(self, error_info: dict):
        """오류 로그 전송"""
        if not self.enabled:
            return
        
        try:
            error_type = error_info.get('type', 'unknown')
            error_message = error_info.get('message', 'No details')
            severity = error_info.get('severity', 'medium')
            
            severity_emoji = {
                'low': '🟡',
                'medium': '🟠',
                'high': '🔴', 
                'critical': '🚨'
            }.get(severity, '🟠')
            
            message = f"""
{severity_emoji} <b>시스템 오류</b>

⚠️ 유형: {error_type.replace('_', ' ').title()}
📝 메시지: {error_message}
🔧 심각도: {severity.upper()}

📅 발생 시간: {__import__('datetime').datetime.now().strftime('%H:%M:%S')}

<i>오류 처리 중...</i>
            """.strip()
            
            self.telegram.send_message(message)
            
        except Exception as e:
            logger.error(f"오류 로그 전송 실패: {e}")
    
    def send_shutdown_message(self):
        """봇 종료 알림"""
        if not self.enabled:
            return
        
        try:
            message = f"""
🔴 <b>트레이딩 봇 종료</b>

📅 종료 시간: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
💡 상태: 정상 종료

<i>봇이 안전하게 종료되었습니다.</i>
            """.strip()
            
            self.telegram.send_message(message)
            logger.info("봇 종료 알림 전송 완료")
        except Exception as e:
            logger.error(f"종료 알림 전송 실패: {e}")