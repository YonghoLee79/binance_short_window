# 🇰🇷 한국 규제 준수 가이드

한국의 암호화폐 규제 환경에 대응하여 Upbit-Binance 자동 연동 시스템을 구축했습니다.

## 🚀 주요 기능

### 1. **자동 USDT 구매 및 전송**
- **KRW → USDT 자동 구매**: Upbit에서 필요한 만큼 USDT 자동 구매
- **Binance 자동 전송**: TRC20 네트워크를 통한 저렴한 수수료로 자동 전송
- **실시간 모니터링**: 전송 상태 실시간 추적 및 알림

### 2. **선제적 잔고 관리**
- **자동 임계값 모니터링**: Binance USDT 잔고가 부족해지기 전 선제적 충전
- **거래 시간대 고려**: 한국 시간 기준 활성 거래 시간대에만 자동 전송
- **버퍼 관리**: 10% 여유분을 고려한 스마트 전송량 계산

### 3. **규제 준수 모니터링**
- **24/7 모니터링**: 대기 중인 전송 상태 실시간 추적
- **실패 처리**: 전송 실패시 자동 재시도 및 알림
- **통계 제공**: 전송 성공률 및 패턴 분석

## 📋 설정 방법

### 1. 환경 변수 설정

`.env` 파일에 다음 설정을 추가하세요:

```env
# Upbit API 설정 (한국 규제 대응용)
UPBIT_ACCESS_KEY=your_upbit_access_key_here
UPBIT_SECRET_KEY=your_upbit_secret_key_here

# 한국 규제 준수 설정
AUTO_USDT_TRANSFER=true
MIN_USDT_TRANSFER=50
MAX_USDT_TRANSFER=5000
USDT_TRANSFER_BUFFER=1.1
USDT_NETWORK=TRC20
BINANCE_USDT_ADDRESS=your_binance_usdt_deposit_address_here
BALANCE_CHECK_INTERVAL=300
```

### 2. Upbit API 키 생성

1. **Upbit Pro 로그인**: https://upbit.com/mypage/open_api_management
2. **API 키 생성**: 
   - 자산 조회 권한 ✅
   - 주문 조회 권한 ✅
   - 주문하기 권한 ✅
   - 출금하기 권한 ✅
3. **IP 제한 설정** (권장): 봇 실행 서버 IP만 허용

### 3. Binance USDT 입금 주소 확인

1. **Binance 로그인** → **지갑** → **입금**
2. **USDT 선택** → **TRC20 네트워크**
3. **입금 주소 복사** → `.env` 파일에 설정

## 🔄 작동 원리

### 자동 워크플로우

```
1. 거래 신호 발생
    ↓
2. 필요 USDT 계산
    ↓
3. Binance 잔고 확인
    ↓
4. 부족시 자동 구매/전송
    ↓ 
5. 거래 실행
```

### 상세 프로세스

#### **Phase 1: 필요량 계산**
```python
required_usdt = calculate_required_usdt(buy_signals)
# 버퍼 적용: required_usdt * 1.1 (10% 여유분)
```

#### **Phase 2: 잔고 확인**
```python
binance_usdt = get_binance_balance('USDT')
if binance_usdt < required_usdt:
    initiate_auto_transfer()
```

#### **Phase 3: 자동 구매**
```python
# 1. KRW → USDT 지정가 주문
order = upbit.buy_usdt_with_krw(krw_amount)

# 2. 주문 완료 대기 (최대 5분)
wait_for_completion(order_id)
```

#### **Phase 4: 자동 전송**
```python
# 3. Binance로 TRC20 출금
withdraw = upbit.withdraw_usdt_to_binance(
    amount=usdt_amount,
    address=binance_address,
    network='TRC20'
)
```

#### **Phase 5: 모니터링**
```python
# 4. 전송 상태 추적 (10-30분)
monitor_transfer_status(withdraw_id)
```

## 📊 모니터링 및 알림

### 텔레그램 알림

#### **1. USDT 부족 경고**
```
🚨 USDT 부족 경고
필요 USDT: 150.00
상태: Binance 잔고 부족
조치: 자동 전송 시작됨 (예상 10-30분)
```

#### **2. 자동 전송 시작**
```
🔄 자동 USDT 전송 시작
구매량: 165.00 USDT
전송량: 164.00 USDT (수수료 1 USDT)
예상 도착: 10-30분
상태: 진행 중...
```

#### **3. 전송 완료**
```
✅ USDT 전송 완료
전송 ID: abc123...
최종 금액: 164.00 USDT
소요 시간: 15분
상태: 거래 재개 가능
```

### 실시간 통계

```python
# 전송 통계 조회
stats = korea_compliance.get_transfer_statistics(days=7)

{
    'total_transfers': 5,
    'total_amount': 850.0,
    'successful_transfers': 5,
    'success_rate': 100.0,
    'average_amount': 170.0,
    'pending_transfers': 0
}
```

## ⚠️ 주의사항

### 보안

1. **API 키 보안**
   - Upbit API 키 절대 공유 금지
   - IP 제한 설정 필수
   - 권한 최소화 (필요한 권한만)

2. **자금 안전**
   - 테스트넷에서 충분한 테스트 후 라이브 전환
   - 소액부터 시작하여 점진적 확대
   - 일일 전송 한도 설정

### 규제 준수

1. **KYC/AML**
   - Upbit 실명 인증 완료 필수
   - 거래 목적 명확히 기재
   - 의심스러운 활동 시 즉시 신고

2. **세무**
   - 모든 거래 기록 보관
   - 암호화폐 거래 소득 신고
   - 전문가 상담 권장

### 기술적 제약

1. **네트워크 지연**
   - TRC20 전송: 일반적으로 10-30분
   - 네트워크 혼잡시 더 오래 소요 가능
   - 긴급시 ERC20 대안 고려

2. **API 제한**
   - Upbit: 초당 8회 요청 제한
   - 대량 거래시 순차 처리
   - 실패시 자동 재시도 (3회)

## 🛠️ 트러블슈팅

### 일반적인 문제

#### **1. USDT 구매 실패**
```
오류: 최소 주문 금액 미달
해결: 5,000원 이상 주문 필요
```

#### **2. 출금 실패**
```
오류: 출금 한도 초과
해결: 일일 출금 한도 확인 및 조정
```

#### **3. 전송 지연**
```
상황: 30분 이상 미완료
조치: 네트워크 상태 확인, 필요시 고객센터 문의
```

### 로그 확인

```bash
# 한국 규제 준수 로그 확인
tail -f korea_compliance.log

# 전체 시스템 로그
tail -f trading_bot.log | grep "korea"
```

## 📈 성능 최적화

### 권장 설정

```env
# 최적 설정 예시
MIN_USDT_TRANSFER=100      # 최소 전송량 (수수료 효율성)
MAX_USDT_TRANSFER=2000     # 최대 전송량 (리스크 관리)
USDT_TRANSFER_BUFFER=1.15  # 15% 버퍼 (여유분)
BALANCE_CHECK_INTERVAL=300 # 5분마다 확인
USDT_NETWORK=TRC20         # 저렴한 수수료
```

### 비용 최적화

1. **전송 수수료**
   - TRC20: ~1 USDT (권장)
   - ERC20: ~10-50 USDT (높음)
   - BEP20: ~0.5 USDT (최저)

2. **거래 수수료**
   - Upbit 구매: 0.05%
   - 전체 비용: 구매액의 약 0.1-0.2%

## 🎯 고급 기능

### 선제적 잔고 관리

시스템이 자동으로 다음 상황을 모니터링합니다:

- **거래 활성 시간대**: 오전 9시 - 오후 10시
- **잔고 임계값**: 최소 전송량의 2배 미만
- **KRW 충분도**: 15만원 이상 보유
- **대기 전송**: 진행 중인 전송 없음

모든 조건 만족시 자동으로 선제적 USDT 전송을 실행합니다.

### 통계 및 분석

```python
# 규제 준수 현황 조회
status = korea_compliance.get_compliance_status()

{
    'balance_status': {
        'upbit': {'usdt': 50.0, 'krw': 500000},
        'binance': {'usdt': 200.0},
        'total_usdt': 250.0
    },
    'transfer_statistics': {...},
    'auto_transfer_enabled': True,
    'monitoring_enabled': True
}
```

## 📞 지원 및 문의

### 문제 해결 순서

1. **로그 확인**: 오류 메시지 및 상세 정보 확인
2. **설정 검토**: API 키, 주소, 권한 등 재확인
3. **네트워크 상태**: Upbit/Binance 서비스 상태 확인
4. **수동 테스트**: 소액으로 수동 거래 테스트

### 긴급 상황 대응

1. **자동 시스템 중지**
   ```python
   korea_compliance.stop_monitoring()
   korea_compliance.auto_transfer_enabled = False
   ```

2. **수동 USDT 확보**
   - Upbit에서 직접 USDT 구매
   - 수동으로 Binance 전송
   - 봇 재시작 후 거래 재개

---

**⚠️ 면책 조항**: 이 시스템은 한국의암호화폐 규제 환경에 대응하기 위해 개발되었습니다. 모든 거래는 사용자 책임하에 이루어지며, 규제 변경에 따른 대응은 사용자가 직접 해야 합니다.