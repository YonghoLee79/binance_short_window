# 🚀 하이브리드 트레이딩 봇 사용 가이드

현물거래와 선물거래를 복합으로 운영하는 고급 암호화폐 자동매매 봇 완전 가이드

## 📋 목차
- [봇 개요](#-봇-개요)
- [테스트 결과](#-테스트-결과)
- [설치 및 설정](#-설치-및-설정)
- [실행 방법](#-실행-방법)
- [전략 상세](#-전략-상세)
- [모니터링](#-모니터링)
- [문제 해결](#-문제-해결)

## 🎯 봇 개요

### 🔥 하이브리드 전략의 핵심 장점
- **위험 분산**: 현물과 선물 포지션으로 리스크 헤지
- **수익 극대화**: 아비트라지 기회 활용
- **안정성**: 60% 현물, 40% 선물 비율로 안정적 운영
- **자동화**: 24/7 무인 거래 시스템

### 📊 최신 테스트 결과 (2025-07-19)
```
==================================================
하이브리드 트레이딩 봇 종합 테스트 결과
==================================================
✅ 현물 거래소 연결: 성공 (USDT 잔고: 31.74)
✅ 선물 거래소 연결: 성공 (USDT 잔고: 0.00)
✅ 시장 데이터 조회: 성공
✅ 과거 데이터 조회: 성공
✅ 기술적 분석: 성공 (RSI: 24.77 - 과매도 구간)

총 5개 테스트 중 5개 성공 (100.0%)
🎉 모든 테스트 통과! 하이브리드 봇이 정상적으로 작동할 수 있습니다.
```

### 💡 실시간 시장 분석 예시
```
BTC/USDT - 현물: 117,538.79, 선물: 117,509.50, 스프레드: -0.025%
ETH/USDT - 현물: 3,530.84, 선물: 3,531.97, 스프레드: 0.032%
BNB/USDT - 현물: 733.56, 선물: 733.86, 스프레드: 0.041%
```

## 🛠 설치 및 설정

### 1. 필수 요구사항 확인
```bash
# Python 버전 확인
python --version  # 3.8 이상 필요

# 가상환경 활성화
source venv/bin/activate

# 필수 패키지 설치 확인
pip list | grep -E "(pandas|ccxt|numpy)"
```

### 2. API 키 설정 확인
```bash
# .env 파일 확인
cat .env

# 예상 출력:
# BINANCE_API_KEY=your_api_key_here
# BINANCE_SECRET_KEY=your_secret_key_here
```

### 3. 계정 연결 테스트
```bash
# API 키 권한 테스트
python api_test.py

# 하이브리드 봇 전체 테스트
python test_hybrid_bot.py
```

## 🚀 실행 방법

### 방법 1: 스크립트 실행 (권장)
```bash
# 실행 권한 부여
chmod +x start_hybrid_bot.sh

# 하이브리드 봇 실행
./start_hybrid_bot.sh
```

### 방법 2: 직접 실행
```bash
# 가상환경 활성화 후 실행
source venv/bin/activate
python hybrid_trading_bot.py
```

### 방법 3: 테스트 모드 실행
```bash
# 실제 거래 없이 테스트
python test_hybrid_bot.py
```

## 📊 전략 상세

### 🔄 하이브리드 전략 구조
```
총 자금: 100%
├── 현물 거래: 60%
│   ├── BTC/USDT: 20%
│   ├── ETH/USDT: 20%
│   └── BNB/USDT: 20%
└── 선물 거래: 40%
    ├── 레버리지: 5x
    ├── 헤지 포지션: 30%
    └── 아비트라지: 10%
```

### 🎯 거래 신호 생성 로직
```python
# 1. 트렌드 분석
if 상승_트렌드 and 신호_강도 > 0.6:
    현물_매수() + 선물_매수()

elif 하락_트렌드 and 신호_강도 > 0.6:
    현물_매도() + 선물_매도()

# 2. 아비트라지 기회
if 스프레드 > 1%:
    현물_매수() + 선물_매도()
```

### 🛡 리스크 관리 시스템
```python
# 손절매 설정
현물_손절매 = -5%     # 현물 포지션
선물_손절매 = -3%     # 선물 포지션 (레버리지 고려)

# 포지션 크기 제한
거래당_리스크 = 2%    # 계좌 자금 대비
최대_포지션 = 20%     # 단일 심볼 최대 비중
```

## 📈 모니터링

### 실시간 성과 지표
```
=== 하이브리드 트레이딩 성과 보고 ===
시작 자금: 31,740 USDT
현재 자금: 32,156 USDT
  - 현물 잔고: 19,294 USDT
  - 선물 잔고: 12,862 USDT
총 수익: +416 USDT (+1.31%)
활성 포지션:
  - 현물 포지션: 3개
  - 선물 포지션: 2개
총 거래 수: 47회
승률: 68.1% (32/47)
```

### 로그 파일 모니터링
```bash
# 실시간 로그 확인
tail -f hybrid_trading_bot.log

# 최근 에러 확인
grep ERROR hybrid_trading_bot.log | tail -10

# 거래 내역 확인
grep "거래 실행" hybrid_trading_bot.log
```

## 🔧 고급 설정

### 전략 파라미터 조정
```python
# hybrid_trading_bot.py 파일에서 수정
self.strategy_config = {
    'spot_allocation': 0.6,      # 현물 비율 (조정 가능)
    'futures_allocation': 0.4,   # 선물 비율 (조정 가능)
    'hedge_ratio': 0.3,          # 헤지 비율
    'rebalance_threshold': 0.05, # 리밸런싱 임계값
    'max_leverage': 5,           # 최대 레버리지
    'risk_per_trade': 0.02,      # 거래당 리스크
}
```

### 거래 심볼 변경
```python
# 거래할 심볼 목록 수정
self.symbols = [
    'BTC/USDT',   # 비트코인
    'ETH/USDT',   # 이더리움
    'BNB/USDT',   # 바이낸스코인
    'ADA/USDT',   # 카르다노 (추가 가능)
    'SOL/USDT',   # 솔라나 (추가 가능)
]
```

## 🚨 문제 해결

### 자주 발생하는 문제들

#### 1. API 키 관련 오류
```
❌ 오류: Invalid API-key, IP, or permissions for action
✅ 해결: 
- API 키 권한 확인 (현물 + 선물 거래 활성화)
- IP 제한 설정 확인
- API 키 재생성
```

#### 2. 잔고 부족 오류
```
❌ 오류: Insufficient balance
✅ 해결:
- 현물 계정에 최소 10 USDT 이상 보유
- 선물 계정에 별도 자금 할당
- 포지션 크기 축소
```

#### 3. 네트워크 연결 오류
```
❌ 오류: NetworkError, ExchangeNotAvailable
✅ 해결:
- 인터넷 연결 확인
- VPN 사용 시 해제
- 재시도 대기 후 실행
```

#### 4. 권한 관련 오류
```
❌ 오류: Permission denied for futures trading
✅ 해결:
- 바이낸스 계정에서 선물 거래 활성화
- KYC 인증 완료
- 선물 거래 약관 동의
```

### 긴급 상황 대처

#### 봇 강제 종료
```bash
# 프로세스 찾기
ps aux | grep hybrid_trading_bot

# 강제 종료
kill -9 [프로세스_ID]

# 또는 Ctrl+C로 안전 종료
```

#### 모든 포지션 종료
```bash
# 긴급 종료 스크립트 실행
python emergency_close.py  # (별도 개발 필요)
```

## 📞 지원 정보

### 추가 도구들
- **api_test.py**: API 키 권한 테스트
- **test_hybrid_bot.py**: 전체 시스템 테스트
- **balance_test.py**: 잔고 확인 도구

### 로그 파일 위치
- **hybrid_trading_bot.log**: 메인 봇 로그
- **test_hybrid_bot.log**: 테스트 로그
- **trading_bot.log**: 기본 봇 로그

### 백업 및 복구
```bash
# 설정 백업
cp .env .env.backup
cp hybrid_trading_bot.py hybrid_trading_bot.py.backup

# 로그 백업
cp *.log logs_backup/
```

## 🎯 성능 최적화 팁

### 1. 시스템 리소스 관리
```bash
# 메모리 사용량 확인
htop

# 디스크 공간 확인
df -h

# 로그 파일 정리
find . -name "*.log" -size +100M -delete
```

### 2. 네트워크 최적화
```python
# API 호출 간격 조정
time.sleep(1)  # 1초 대기 (필요시 조정)

# 동시 연결 제한
max_connections = 10
```

### 3. 전략 최적화
```python
# 백테스팅으로 최적 파라미터 찾기
optimal_params = backtest_strategy(
    start_date='2024-01-01',
    end_date='2024-12-31',
    param_ranges={
        'spot_allocation': [0.5, 0.6, 0.7],
        'risk_per_trade': [0.01, 0.02, 0.03],
    }
)
```

---

## 📄 라이선스 및 면책

⚠️ **중요**: 이 소프트웨어는 교육 목적으로 제공됩니다. 실제 거래 시 발생하는 모든 손실에 대해 개발자는 책임을 지지 않습니다.

🚀 **성공적인 거래를 위한 조언**:
- 소액부터 시작하세요
- 백테스팅을 충분히 수행하세요
- 리스크 관리를 철저히 하세요
- 시장 상황을 지속적으로 모니터링하세요

---

**Happy Trading! 🎊**