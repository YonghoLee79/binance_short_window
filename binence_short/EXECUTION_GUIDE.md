# 🚀 하이브리드 트레이딩 봇 실행 가이드

현물거래와 선물거래 복합 전략 봇을 안전하게 실행하는 완전한 가이드

## 📋 목차
- [사전 준비](#-사전-준비)
- [올바른 실행 방법](#-올바른-실행-방법)
- [잘못된 실행 방법](#-잘못된-실행-방법)
- [텔레그램 알림 설정](#-텔레그램-알림-설정)
- [실행 중 모니터링](#-실행-중-모니터링)
- [문제 해결](#-문제-해결)

## 🔧 사전 준비

### 1. 환경 확인
```bash
# 현재 디렉토리 확인
pwd
# 출력: /Users/yongholee/binence_short

# 가상환경 폴더 확인
ls -la venv/
# venv 폴더가 있어야 함
```

### 2. 가상환경 활성화 확인
```bash
# 가상환경 활성화
source venv/bin/activate

# 활성화 확인 (프롬프트에 (venv) 표시)
# (venv) yongholee@YonghoLeeui-Macmini binence_short %
```

### 3. 필수 패키지 확인
```bash
# 필수 패키지 설치 확인
python -c "import pandas, ccxt, numpy; print('✅ 모든 패키지 설치됨')"

# 출력: ✅ 모든 패키지 설치됨
```

## ✅ 올바른 실행 방법

### 방법 1: 가상환경 스크립트 사용 (권장)
```bash
# 1. 가상환경 활성화
source venv/bin/activate

# 2. 봇 실행
python hybrid_trading_bot.py
```

### 방법 2: 실행 스크립트 사용
```bash
# 1. 실행 권한 확인
chmod +x start_hybrid_bot.sh

# 2. 스크립트 실행
./start_hybrid_bot.sh
```

### 방법 3: 빠른 시작 스크립트 사용
```bash
# 전체 테스트 및 실행
./quick_start.sh
```

## ❌ 잘못된 실행 방법

### 절대 하지 말아야 할 것들

#### 1. 잘못된 Python 경로 사용
```bash
# ❌ 잘못된 방법
/Users/yongholee/binence_short/.venv/bin/python /Users/yongholee/binence_short/hybrid_trading_bot.py
# 오류: ModuleNotFoundError: No module named 'pandas'
```

#### 2. 가상환경 없이 실행
```bash
# ❌ 잘못된 방법
python hybrid_trading_bot.py  # 가상환경 활성화 안함
# 오류: 패키지 없음 또는 버전 충돌
```

#### 3. 직접 Python 경로 사용
```bash
# ❌ 잘못된 방법
python3 hybrid_trading_bot.py
/opt/homebrew/bin/python3 hybrid_trading_bot.py
# 오류: 가상환경 패키지 인식 안됨
```

## 📱 텔레그램 알림 설정

### 1. 봇 토큰 생성
1. 텔레그램에서 `@BotFather` 검색
2. `/newbot` 명령어로 봇 생성
3. 봇 토큰 받기 (예: `123456789:ABC...`)

### 2. 채팅 ID 확인
1. 생성한 봇과 대화 시작
2. 메시지 전송 후 브라우저에서 확인:
   ```
   https://api.telegram.org/bot[봇토큰]/getUpdates
   ```

### 3. .env 파일 설정
```bash
# .env 파일 편집
nano .env

# 다음 내용 추가/수정
TELEGRAM_BOT_TOKEN=7645447915:AAHkFNh6yN0u9_KtHTLa4cL9p0WPIAZdPYQ
TELEGRAM_CHAT_ID=519926123
```

### 4. 텔레그램 봇 테스트
```bash
# 텔레그램 연결 테스트
python telegram_bot.py

# 예상 출력:
# ✅ 텔레그램 봇 연결 성공!
```

## 📊 실행 중 모니터링

### 1. 실시간 로그 확인
```bash
# 새 터미널에서 실시간 로그 확인
tail -f hybrid_trading_bot.log

# 에러 로그만 확인
tail -f hybrid_trading_bot.log | grep ERROR
```

### 2. 성능 모니터링
```bash
# 시스템 리소스 확인
top -p $(pgrep -f hybrid_trading_bot.py)

# 메모리 사용량 확인
ps aux | grep hybrid_trading_bot.py
```

### 3. 텔레그램 알림 확인
봇 실행 시 텔레그램으로 다음 알림들이 전송됩니다:
- 🚀 봇 시작 알림
- 💰 잔고 업데이트 (20회차마다)
- 🟢 거래 실행 알림
- 🚨 에러 알림 (문제 발생 시)

### 4. 실행 상태 확인
```bash
# 봇 프로세스 확인
ps aux | grep hybrid_trading_bot.py

# 포트 사용 확인
lsof -i :8080
```

## 📈 정상 실행 예시

### 성공적인 시작 로그
```
2025-07-19 00:40:15,123 - INFO - 하이브리드 트레이딩 봇 초기화 완료
2025-07-19 00:40:15,124 - INFO - 현물 잔고: 31.74 USDT
2025-07-19 00:40:15,124 - INFO - 선물 잔고: 0.00 USDT
2025-07-19 00:40:15,124 - INFO - 총 시작 자금: 31.74 USDT
2025-07-19 00:40:15,125 - INFO - 하이브리드 트레이딩 전략 시작
2025-07-19 00:40:15,125 - INFO - === 전략 실행 1회차 ===
```

### 정상 거래 로그
```
2025-07-19 00:40:20,456 - INFO - 페어 트레이딩 분석 - BTC/USDT: bullish (강도: 0.75)
2025-07-19 00:40:20,457 - INFO - 가격 스프레드: 0.0025 (117640.00 vs 117557.30)
2025-07-19 00:40:25,789 - INFO - 현물 거래 실행: buy 0.000150 BTC/USDT @ 117640.00
2025-07-19 00:40:30,123 - INFO - 5분 대기...
```

## 🚨 문제 해결

### 1. 패키지 없음 오류
```bash
# 문제: ModuleNotFoundError: No module named 'pandas'
# 해결:
source venv/bin/activate
pip install pandas ccxt numpy python-dotenv requests
```

### 2. API 키 오류
```bash
# 문제: Invalid API-key, IP, or permissions
# 해결:
python api_test.py  # API 키 권한 확인
```

### 3. 텔레그램 봇 연결 실패
```bash
# 문제: 텔레그램 봇 연결 실패: 401
# 해결:
1. 봇 토큰 재확인
2. 채팅 ID 재확인
3. 봇과 대화 시작 (Start 버튼 클릭)
```

### 4. 잔고 부족 오류
```bash
# 문제: Insufficient balance
# 해결:
python balance_test.py  # 잔고 확인
# 현물 계정에 최소 10 USDT 보유 필요
```

## 🔧 고급 실행 옵션

### 1. 백그라운드 실행
```bash
# 백그라운드에서 실행
nohup python hybrid_trading_bot.py > output.log 2>&1 &

# 프로세스 ID 확인
echo $!
```

### 2. 시스템 서비스 등록
```bash
# systemd 서비스 파일 생성
sudo nano /etc/systemd/system/hybrid-trading-bot.service

# 서비스 내용:
[Unit]
Description=Hybrid Trading Bot
After=network.target

[Service]
Type=simple
User=yongholee
WorkingDirectory=/Users/yongholee/binence_short
ExecStart=/Users/yongholee/binence_short/venv/bin/python hybrid_trading_bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### 3. 자동 재시작 설정
```bash
# 크론잡으로 자동 재시작
crontab -e

# 매일 자정 재시작
0 0 * * * /Users/yongholee/binence_short/restart_bot.sh
```

## 📞 지원 및 문의

### 즉시 도움이 필요한 경우
```bash
# 긴급 봇 종료
pkill -f hybrid_trading_bot.py

# 전체 시스템 테스트
python test_hybrid_bot.py

# 로그 확인
tail -50 hybrid_trading_bot.log
```

### 정기 점검 사항
- [ ] 매일: 로그 파일 확인
- [ ] 매주: 성능 리포트 검토
- [ ] 매월: API 키 권한 확인
- [ ] 분기별: 전략 파라미터 최적화

---

## 🎯 성공적인 실행을 위한 체크리스트

### 실행 전 체크리스트
- [ ] 가상환경 활성화 확인
- [ ] 필수 패키지 설치 확인
- [ ] API 키 설정 확인
- [ ] 텔레그램 봇 연결 확인
- [ ] 잔고 충분 여부 확인

### 실행 중 체크리스트
- [ ] 로그 파일 정상 생성
- [ ] 텔레그램 알림 수신 확인
- [ ] 거래 실행 정상 여부
- [ ] 에러 발생 시 즉시 대응

### 실행 후 체크리스트
- [ ] 성능 리포트 확인
- [ ] 수익률 분석
- [ ] 리스크 관리 상태 점검
- [ ] 다음 실행 계획 수립

---

**안전하고 수익성 있는 거래를 위해 이 가이드를 철저히 따라주세요! 🚀📈**