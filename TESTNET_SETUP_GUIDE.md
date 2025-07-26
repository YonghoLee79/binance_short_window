# 🧪 Binance 테스트넷 설정 가이드

실제 자금 손실 없이 안전하게 트레이딩 봇을 테스트하는 방법입니다.

## 📋 1단계: Binance 테스트넷 계정 생성

### Binance Spot 테스트넷
1. **https://testnet.binance.vision/** 접속
2. **GitHub 계정으로 로그인**
3. **API 키 생성**:
   - "Generate HMAC_SHA256 Key" 클릭
   - API Key와 Secret Key 복사

### Binance Futures 테스트넷  
1. **https://testnet.binancefuture.com/** 접속
2. **GitHub 계정으로 로그인**
3. **API 키 생성**:
   - 우상단 프로필 → API Management
   - Create API 클릭
   - API Key와 Secret Key 복사

## 📋 2단계: 테스트 자금 받기

### Spot 테스트넷 자금
- 테스트넷 로그인 후 자동으로 테스트 USDT 지급
- 추가 필요시 "Get Test Funds" 버튼 클릭

### Futures 테스트넷 자금
- Futures 테스트넷에서 테스트 USDT 지급
- 레버리지 거래 테스트 가능

## 📋 3단계: .env 파일 설정

`.env` 파일을 다음과 같이 수정하세요:

```env
# 메인넷 API (실제 거래용 - 나중에 사용)
BINANCE_API_KEY=실제_메인넷_API_키
BINANCE_SECRET_KEY=실제_메인넷_시크릿_키

# 테스트넷 API (안전한 테스트용)
BINANCE_TESTNET_API_KEY=테스트넷_API_키_여기에_입력
BINANCE_TESTNET_SECRET_KEY=테스트넷_시크릿_키_여기에_입력

# 테스트 모드 설정
TRADING_MODE=testnet
USE_TESTNET=true
```

## 📋 4단계: 테스트넷 검증

봇 실행 전 테스트넷 연결을 확인하세요:

```bash
cd binence_short
python -c "
import ccxt
exchange = ccxt.binance({
    'apiKey': '테스트넷_API_키',
    'secret': '테스트넷_시크릿_키',
    'sandbox': True
})
balance = exchange.fetch_balance()
print('테스트넷 잔고:', balance['USDT'])
"
```

## 📋 5단계: 안전한 테스트 실행

### 권장 테스트 순서
1. **테스트넷에서 충분한 테스트** (최소 1주일)
2. **모든 기능 검증 완료**
3. **메인넷으로 전환** (소액부터 시작)

### 테스트 체크리스트
- [ ] 테스트넷 API 연결 성공
- [ ] 시장 데이터 수집 정상
- [ ] 거래 신호 생성 확인
- [ ] 주문 실행 테스트
- [ ] 리스크 관리 작동
- [ ] 텔레그램 알림 수신
- [ ] 한국 규제 준수 시스템 테스트 (Upbit 연동)

## 🚨 중요 안전 수칙

### ❌ 절대 하지 말 것
- 테스트 없이 바로 메인넷 사용
- 큰 금액으로 첫 거래 시작
- API 키 권한에 출금(Withdraw) 포함

### ✅ 반드시 할 것
- 테스트넷에서 충분한 검증
- API 키 IP 제한 설정
- 소액부터 점진적 확대
- 24시간 모니터링 체계 구축

## 📞 테스트넷 관련 FAQ

### Q: 테스트넷 자금이 부족해요
A: 각 테스트넷 사이트에서 "Get Test Funds" 기능 사용

### Q: 테스트넷 API가 느려요
A: 정상입니다. 테스트넷은 메인넷보다 느릴 수 있습니다

### Q: 테스트넷에서 실제 수익이 나나요?
A: 아니요. 테스트넷의 모든 거래는 가상이며 실제 수익/손실은 없습니다

### Q: 언제 메인넷으로 전환하나요?
A: 최소 1주일 이상 테스트하고 모든 기능이 안정적으로 작동할 때

---

**⚠️ 안전 경고**: 테스트넷에서 충분한 검증 없이 메인넷 사용시 자금 손실 위험이 있습니다. 반드시 단계적으로 진행하세요.