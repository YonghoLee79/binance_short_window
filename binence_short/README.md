# 🚀 Advanced Binance Trading Bot v2

고급 암호화폐 자동매매 봇 시스템 - 현물거래와 선물거래를 복합으로 운영하는 하이브리드 전략

## 📋 목차
- [특징](#-특징)
- [설치 및 설정](#-설치-및-설정)
- [사용 방법](#-사용-방법)
- [하이브리드 전략](#-하이브리드-전략)
- [수익률 최적화](#-수익률-최적화)
- [리스크 관리](#-리스크-관리)
- [모니터링](#-모니터링)
- [파일 구조](#-파일-구조)
- [주의사항](#-주의사항)

## 🎯 특징

### 🔥 핵심 기능 (v2 업데이트)
- **🎯 하이브리드 포트폴리오 봇 v2**: 시장상황에 따른 현물 0~100% + 선물 0~100% 최적화된 비율 분석 및 설정
- **⚡ 고급 기술적 분석**: RSI, MACD, 볼린저밴드, Stochastic 등 12개 지표
- **🤖 4가지 전략 알고리즘**: 아비트라지, 트렌드 추종, 헤징, 모멘텀
- **📊 실시간 포트폴리오 관리**: 자동 리밸런싱 및 위험 분산
- **💬 텔레그램 알림**: 실시간 거래 알림 및 상태 모니터링
- **🔧 모듈화 설계**: 유지보수 및 확장성 향상

### 💡 고급 기능
- **🎲 Kelly Criterion**: 최적 포지션 크기 자동 계산
- **🔄 동적 리밸런싱**: 5% 편차 시 자동 포트폴리오 조정
- **⚡ 레버리지 최적화**: 최대 5배 레버리지 활용
- **📈 실시간 대시보드**: 웹 기반 모니터링 시스템
- **🧪 백테스팅**: 전략 성과 검증 및 최적화
- **🛡️ 고급 리스크 관리**: 다층 보호 시스템

## 🛠 설치 및 설정

### 1. 필수 요구사항
```bash
# Python 3.8 이상
python --version

# 시스템 의존성 설치 (macOS)
brew install ta-lib

# 시스템 의존성 설치 (Ubuntu)
sudo apt-get install libta-lib-dev
```

### 2. 프로젝트 클론 및 설정
```bash
# 프로젝트 클론
git clone https://github.com/yourusername/binance-trading-bot.git
cd binance-trading-bot

# 가상환경 생성 및 활성화
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate  # Windows

# 의존성 설치
pip install -r requirements.txt
```

### 3. API 키 설정
```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집
BINANCE_API_KEY=your_api_key_here
BINANCE_SECRET_KEY=your_secret_key_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
```

### 4. 바이낸스 API 키 생성
1. [바이낸스 계정](https://www.binance.com) 로그인
2. 계정 → API 관리 → API 키 생성
3. 권한 설정:
   - ✅ 현물 및 마진 거래
   - ✅ 선물 거래
   - ✅ 읽기 전용 (필수)
   - ❌ 출금 (보안상 비활성화 권장)

## 🚀 사용 방법

### 하이브리드 포트폴리오 봇 v2 실행 (권장)
```bash
# 가상환경 활성화
source .venv/bin/activate

# 봇 실행
python run_trading_bot.py

# 옵션 선택:
# 1. 하이브리드 포트폴리오 봇 v2 (현물+선물) 🎯 ← 추천
# 2. 모니터링 대시보드만 실행
# 3. 단위 테스트 실행
# 4. 데이터베이스 테스트
```

### 잔고 테스트
```bash
# 계정 연결 및 잔고 확인
python test_connection.py
```

## 📊 하이브리드 전략

### 🎯 최적화된 포트폴리오 비율 (v2)
- **현물 40%**: 안정적인 기반 포트폴리오
- **선물 60%**: 레버리지를 활용한 수익률 확대
- **자동 리밸런싱**: 5% 편차 시 자동 조정

### 🔄 4가지 전략 알고리즘

#### 1. 🔀 아비트라지 전략
- **임계값**: 0.1% 프리미엄 (기존 0.2%에서 향상)
- **원리**: 현물-선물 간 가격 차이 활용
- **수익**: 안정적인 무위험 수익 추구

#### 2. 📈 트렌드 추종 전략
- **신호 감도**: 0.2 (기존 0.3에서 향상)
- **원리**: 현물과 선물이 같은 방향으로 움직일 때
- **수익**: 강한 트렌드에서 높은 수익률

#### 3. 🛡️ 헤징 전략
- **보호 수준**: 80% 헤지
- **원리**: 현물 포지션을 선물로 보호
- **수익**: 리스크 최소화 및 안정성 확보

#### 4. ⚡ 모멘텀 전략
- **RSI 임계값**: 35/65 (기존 30/70에서 향상)
- **원리**: 과매수/과매도 구간에서 반전 포착
- **수익**: 빠른 가격 변동 활용

### 📊 거래 대상 심볼 (12개 메이저 코인)
```python
TRADING_SYMBOLS = [
    'BTC/USDT',   # 비트코인
    'ETH/USDT',   # 이더리움
    'BNB/USDT',   # 바이낸스 코인
    'XRP/USDT',   # 리플
    'SOL/USDT',   # 솔라나
    'ADA/USDT',   # 카르다노
    'AVAX/USDT',  # 아발란체
    'LINK/USDT',  # 체인링크
    'DOT/USDT',   # 폴카닷
    'MATIC/USDT', # 폴리곤
    'LTC/USDT',   # 라이트코인
    'TRX/USDT'    # 트론
]
```

## 💰 수익률 최적화

### 🎯 최적화된 설정 (v2)

| 구분 | 기존 설정 | 최적화 설정 | 수익률 효과 |
|------|----------|------------|------------|
| **현물 비율** | 60% | 40% | +25% 공격성 |
| **선물 비율** | 40% | 60% | +50% 레버리지 |
| **아비트라지 임계값** | 0.2% | 0.1% | +100% 기회 포착 |
| **리밸런싱 임계값** | 8% | 5% | +60% 반응성 |
| **트렌드 신호** | 0.3 | 0.2 | +50% 민감도 |
| **RSI 임계값** | 30/70 | 35/65 | +17% 조기 진입 |
| **최대 레버리지** | 3배 | 5배 | +67% 수익 잠재력 |

### 📈 시장 상황별 권장 비율

#### 🐂 강세장 (Bull Market)
```python
SPOT_ALLOCATION = 0.3     # 현물 30%
FUTURES_ALLOCATION = 0.7  # 선물 70%
MAX_LEVERAGE = 5          # 레버리지 최대 활용
```

#### 🐻 약세장 (Bear Market)
```python
SPOT_ALLOCATION = 0.2     # 현물 20%
FUTURES_ALLOCATION = 0.8  # 선물 80% (숏 포지션)
MAX_LEVERAGE = 3          # 안전한 레버리지
```

#### 📊 횡보장 (Sideways)
```python
SPOT_ALLOCATION = 0.5     # 현물 50%
FUTURES_ALLOCATION = 0.5  # 선물 50%
MAX_LEVERAGE = 2          # 보수적 레버리지
```

## 🛡 리스크 관리

### 🔒 다층 보호 시스템
- **포지션 크기 제한**: 단일 거래 최대 15%
- **일일 손실 한도**: 5% 초과 시 거래 중단
- **최대 드로우다운**: 20% 제한
- **스탑로스**: 5% 손절매
- **테이크프로핏**: 10% 이익실현

### 💡 Kelly Criterion 활용
```python
# 최적 포지션 크기 자동 계산
optimal_position = kelly_criterion(
    win_rate=0.6,          # 승률 60%
    avg_win=0.08,          # 평균 수익 8%
    avg_loss=0.04,         # 평균 손실 4%
    account_balance=10000   # 계좌 잔고
)
```

### 🔄 동적 리밸런싱
- **임계값**: 5% 편차 시 자동 리밸런싱
- **주기**: 12시간마다 체크
- **방식**: 점진적 조정으로 슬리피지 최소화

## 📱 모니터링

### 💬 텔레그램 알림
```
🚀 하이브리드 트레이딩 봇 v2 시작
💰 현물 할당: 40%
⚡ 선물 할당: 60%
📊 거래 심볼: 12개
🔧 레버리지: 최대 5배

📈 거래 신호 발생!
🎯 전략: 아비트라지
💎 심볼: BTC/USDT
💰 수익률: +0.15%
```

### 📊 실시간 대시보드
- **포트폴리오 현황**: 실시간 자산 분배
- **거래 내역**: 최근 거래 및 수익률
- **성과 지표**: 샤프 비율, 승률, MDD
- **위험 지표**: VaR, 포지션 익스포저

### 📈 핵심 지표 추적
```python
성과_지표 = {
    '총_수익률': '+12.5%',
    '샤프_비율': 1.8,
    '최대_손실': '-3.2%',
    '승률': '68%',
    '총_거래수': 247,
    '평균_수익': '+2.1%',
    '월간_수익률': '+8.3%'
}
```

## 📁 파일 구조

```
binance-trading-bot/
├── 🚀 run_trading_bot.py         # 통합 실행 런처
├── 💎 hybrid_trading_bot_v2.py   # 하이브리드 봇 v2 (메인)
├── ⚙️ config.py                 # 설정 파일
├── 📊 modules/                   # 모듈 패키지
│   ├── technical_analysis.py    # 기술적 분석
│   ├── exchange_interface.py    # 거래소 인터페이스
│   ├── risk_manager.py          # 리스크 관리
│   ├── portfolio_manager.py     # 포트폴리오 관리
│   ├── strategy_engine.py       # 전략 엔진
│   ├── hybrid_portfolio_strategy.py # 하이브리드 전략
│   ├── telegram_notifications.py # 텔레그램 알림
│   ├── database_manager.py      # 데이터베이스
│   └── async_trading_bot.py     # 비동기 봇
├── 🧪 tests/                    # 테스트 파일
├── 🛠️ utils/                     # 유틸리티
├── 📈 monitoring_dashboard.py    # 모니터링 대시보드
├── 🔧 requirements.txt          # Python 의존성
├── 📝 .env.example             # 환경 변수 예시
├── 📊 trading_bot.db           # SQLite 데이터베이스
├── 📋 trading_bot.log          # 거래 로그
└── 📖 README.md               # 프로젝트 설명서
```

## ⚠️ 주의사항

### 🔒 보안
- **API 키 보안**: .env 파일을 절대 공개하지 마세요
- **권한 최소화**: 출금 권한은 비활성화하세요
- **IP 제한**: 가능한 경우 IP 화이트리스트 설정
- **2FA 활성화**: 바이낸스 계정에 2단계 인증 설정

### 💰 투자 위험
- **투자 원금 손실 가능**: 암호화폐 투자는 고위험 투자입니다
- **소액 테스트**: 처음에는 소액으로 시작하세요
- **백테스팅**: 실제 거래 전 충분한 테스트 필요
- **시장 변동성**: 급격한 가격 변동에 주의하세요
- **레버리지 위험**: 선물 거래는 손실이 확대될 수 있습니다

### 🔧 기술적 고려사항
- **네트워크 안정성**: 안정적인 인터넷 연결 필요
- **서버 다운타임**: 24/7 운영을 위한 서버 관리
- **API 제한**: 바이낸스 API 호출 제한 준수
- **로그 모니터링**: 정기적인 로그 파일 확인

## 🎯 성능 최적화

### 시스템 요구사항
- **CPU**: 최소 2코어 (4코어 권장)
- **메모리**: 최소 4GB RAM (8GB 권장)
- **네트워크**: 안정적인 인터넷 연결 (< 100ms 지연)
- **디스크**: 최소 2GB 여유공간

### 최적화 기법
```python
# 1. 비동기 처리
async def collect_market_data():
    tasks = [get_ticker(symbol) for symbol in symbols]
    results = await asyncio.gather(*tasks)
    return results

# 2. 캐싱 활용
@lru_cache(maxsize=128)
def get_technical_indicators(symbol, timeframe):
    return calculate_indicators(symbol, timeframe)

# 3. 메모리 최적화
import gc
gc.collect()  # 주기적 가비지 컬렉션
```

## 🔧 고급 설정

### 커스텀 전략 추가
```python
# custom_strategy.py
from modules.hybrid_portfolio_strategy import HybridPortfolioStrategy

class CustomStrategy(HybridPortfolioStrategy):
    def analyze_custom_opportunity(self, market_data):
        # 커스텀 전략 로직
        return opportunities
```

### 개발자 설정
```python
# config.py 수정
class Config:
    # 공격적 설정 (고수익 추구)
    SPOT_ALLOCATION = 0.2
    FUTURES_ALLOCATION = 0.8
    MAX_LEVERAGE = 10
    
    # 보수적 설정 (안정성 우선)
    SPOT_ALLOCATION = 0.7
    FUTURES_ALLOCATION = 0.3
    MAX_LEVERAGE = 2
```

## ⚡ 빠른 시작

```bash
# 1. 프로젝트 설정
git clone https://github.com/yourusername/binance-trading-bot.git
cd binance-trading-bot
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. API 키 설정
echo "BINANCE_API_KEY=your_key" > .env
echo "BINANCE_SECRET_KEY=your_secret" >> .env
echo "TELEGRAM_BOT_TOKEN=your_token" >> .env
echo "TELEGRAM_CHAT_ID=your_chat_id" >> .env

# 3. 연결 테스트
python test_connection.py

# 4. 하이브리드 봇 v2 실행
python run_trading_bot.py
# 1번 선택: 하이브리드 포트폴리오 봇 v2 🎯
```

## 📞 지원 및 문의

### 문제 해결
1. **로그 확인**: `trading_bot.log` 파일 확인
2. **API 연결**: `test_connection.py` 실행
3. **의존성 설치**: `pip install -r requirements.txt`
4. **가상환경**: `source .venv/bin/activate`

### 🆕 v2 업데이트 내용
- ✅ 현물 40% + 선물 60% 최적화된 비율
- ✅ 4가지 고급 전략 알고리즘
- ✅ 개선된 신호 감도 (더 많은 거래 기회)
- ✅ 실시간 텔레그램 알림
- ✅ 완전 모듈화된 아키텍처
- ✅ SQLite 데이터베이스 통합
- ✅ 고급 리스크 관리 시스템

---

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

---

⚠️ **면책 조항**: 이 소프트웨어는 교육 목적으로 제공됩니다. 실제 거래 시 발생하는 모든 손실에 대해 개발자는 책임을 지지 않습니다. 투자는 본인의 판단과 책임하에 이루어져야 합니다.

🚀 **Happy Trading with v2!**