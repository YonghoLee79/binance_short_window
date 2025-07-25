# 🚀 Advanced Hybrid Trading Bot v2

현물 + 선물 통합 전략을 사용하는 지능형 암호화폐 트레이딩 봇

## ✨ 주요 기능

### 🎯 **스마트 주문 실행 시스템**
- **TWAP 주문**: 고변동성 시장에서 시간분산 실행
- **빙산 주문**: 대량 거래시 시장 충격 최소화  
- **스마트 지정가**: 최적 가격 자동 계산 및 조정
- **시장 상황 분석**: 변동성, 유동성, 거래량 기반 주문 타입 자동 선택

### 🔍 **동적 신호 검증 시스템**
- **시간대별 일관성 검증**: 여러 지표간 신호 방향 일치도 확인
- **거래량 뒷받침 확인**: 신호 발생시 거래량 증가 여부 검증
- **시장 체제 식별**: 트렌딩/횡보/변동성 시장 구분
- **노이즈 필터링**: 과거 신호 일관성 기반 False Signal 제거

### ⚖️ **적응형 포지션 사이징**
- **실시간 승률 기반**: 최근 30일 거래 성과 반영
- **동적 Kelly Criterion**: 시장 조건별 수익/손실 비율 조정
- **변동성 적응**: 시장 변동성에 따른 포지션 크기 자동 조정
- **상관관계 리스크 관리**: 포트폴리오 다각화 수준 고려

### 🚨 **실시간 리스크 모니터링**
- **5단계 리스크 체크**: 포지션/상관관계/체제변화/유동성/레버리지
- **자동 대응 시스템**: 위험 수준별 자동 포지션 축소 및 스탑로스 강화
- **트레일링 스탑**: 수익 포지션 자동 손익확정선 상향 조정
- **위험도별 거래 제한**: High/Critical 위험시 신뢰도 임계값 상향

### 🔗 **하이브리드 전략**
- **현물 + 선물 통합**: 아비트라지, 헤징, 트렌드 추종
- **포트폴리오 리밸런싱**: 자동 자산 비중 조정
- **다중 거래소 지원**: Binance 현물/선물 동시 운영

## 🛠️ 설치 및 설정

### 1. 환경 요구사항
```bash
Python 3.11+
```

### 2. 의존성 설치
```bash
# Python 3.13 환경에서
pip install python-dotenv ccxt pandas ta numpy scipy scikit-learn
```

### 3. 환경 설정
```bash
# .env.template을 .env로 복사
cp binence_short/.env.template binence_short/.env

# .env 파일에 실제 API 키 입력
nano binence_short/.env
```

`.env` 파일 설정:
```env
# Binance API 설정
BINANCE_API_KEY=실제_API_키
BINANCE_SECRET_KEY=실제_시크릿_키

# 텔레그램 봇 설정 (선택사항)
TELEGRAM_BOT_TOKEN=실제_텔레그램_토큰
TELEGRAM_CHAT_ID=실제_채팅_ID

# 거래 설정
TRADING_MODE=testnet
MAX_POSITION_SIZE=100
RISK_PERCENTAGE=2.0
```

## 🚀 실행 방법

### 메인 트레이딩 봇 실행
```bash
python binence_short/run_trading_bot.py
```

실행 옵션:
1. **하이브리드 포트폴리오 봇 v2** (현물+선물) 🎯
2. **모니터링 대시보드만 실행**
3. **단위 테스트 실행**
4. **데이터베이스 테스트**

## 📊 지원 거래소 및 심볼

### 거래소
- **Binance**: 현물 + 선물 통합

### 지원 심볼
- BTC/USDT, ETH/USDT, BNB/USDT
- XRP/USDT, SOL/USDT, ADA/USDT
- AVAX/USDT, LINK/USDT, TRX/USDT

## 🎯 전략 종류

### 1. **아비트라지 전략**
- 현물-선물 가격차 활용
- 초민감 임계값 (0.05%)
- 즉시 체결 우선

### 2. **트렌드 추종 전략**
- 현물/선물 신호 일치시 실행
- 다중 시간대 검증
- 동적 신뢰도 조정

### 3. **헤징 전략**
- 포트폴리오 리스크 중화
- 상관관계 기반 포지션 조정
- 자동 리밸런싱

### 4. **모멘텀 전략**
- 기술적 지표 기반
- RSI, MACD, 볼린저밴드 활용
- 거래량 확인 필수

## 📈 성과 모니터링

### 실시간 모니터링
- **로그 파일**: `trading_bot.log`
- **거래 기록**: `trade_history.log`
- **데이터베이스**: `trading_bot.db`

### 텔레그램 알림
- 🚀 봇 시작/종료 알림
- 💰 거래 실행 알림
- 🚨 리스크 경고 알림
- 📊 성과 리포트 (20회차마다)

## ⚠️ 위험 관리

### 자동 리스크 제어
- **최대 포지션 크기**: 총 자금의 20%
- **일일 손실 한도**: 총 자금의 5%
- **최대 드로우다운**: 20%
- **포지션 타임아웃**: 24시간

### 긴급 대응
- **Critical 위험시**: 포지션 50% 자동 축소
- **High 위험시**: 스탑로스 3%로 강화
- **상관관계 초과시**: 연관 포지션 정리

## 🔧 고급 설정

### config.py 주요 설정
```python
# 포트폴리오 할당
SPOT_ALLOCATION = 0.4      # 현물 40%
FUTURES_ALLOCATION = 0.6   # 선물 60%

# 리스크 관리
MAX_POSITION_SIZE = 0.15   # 단일 포지션 최대 15%
RISK_PER_TRADE = 0.02      # 거래당 리스크 2%
MAX_LEVERAGE = 5           # 최대 레버리지 5배

# 전략 설정
ARBITRAGE_THRESHOLD = 0.0005  # 아비트라지 임계값 0.05%
REBALANCE_THRESHOLD = 0.05    # 리밸런싱 임계값 5%
```

## 📚 문서

- [`EXECUTION_GUIDE.md`](binence_short/EXECUTION_GUIDE.md): 상세 실행 가이드
- [`HYBRID_BOT_GUIDE.md`](binence_short/HYBRID_BOT_GUIDE.md): 하이브리드 전략 가이드
- [`FINAL_SUMMARY.md`](binence_short/FINAL_SUMMARY.md): 전체 시스템 요약

## 🧪 테스트

### 단위 테스트 실행
```bash
# 리스크 매니저 테스트
python -m pytest binence_short/tests/test_risk_manager.py -v

# 기술적 분석 테스트
python -m pytest binence_short/tests/test_technical_analysis.py -v
```

### 전략 테스트
```bash
python binence_short/test_hybrid_strategy.py
```

## 🚨 주의사항

### 보안
- **API 키 보안**: `.env` 파일을 절대 공유하지 마세요
- **권한 설정**: API 키는 거래 권한만 부여하세요
- **IP 제한**: 가능하면 IP 제한을 설정하세요

### 거래
- **테스트넷 사용**: 실제 거래 전 충분한 테스트 필수
- **소액 시작**: 처음에는 작은 금액으로 시작하세요
- **지속적 모니터링**: 봇 실행 중 정기적인 확인 필요

### 기술적
- **Python 버전**: 3.11+ 권장 (3.13에서 테스트됨)
- **네트워크 안정성**: 안정적인 인터넷 연결 필수
- **서버 운영**: 24/7 운영시 VPS 또는 클라우드 권장

## 📞 지원

### 문제 해결
1. **로그 확인**: `tail -f binence_short/trading_bot.log`
2. **API 연결 테스트**: API 키 및 권한 확인
3. **의존성 확인**: 모든 패키지 설치 여부 확인

### 버그 리포트
GitHub Issues를 통해 버그 리포트 및 기능 요청을 해주세요.

## 📄 라이선스

이 프로젝트는 교육 및 연구 목적으로 제공됩니다. 실제 거래 시 발생하는 손실에 대해서는 책임지지 않습니다.

---

**⚠️ 면책 조항**: 암호화폐 거래는 높은 위험을 수반합니다. 투자 전 충분한 연구와 리스크 관리가 필요하며, 손실을 감당할 수 있는 범위 내에서만 거래하세요.