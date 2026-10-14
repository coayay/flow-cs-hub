# Cloudflare Workers · Claude API 프록시 설정 가이드

## 왜 필요한가
브라우저에서 Claude API를 직접 호출하면 API 키가 노출되어 악용될 수 있습니다.
이 Worker는 중간에서 프록시 역할을 하며, API 키는 Cloudflare 서버에만 저장됩니다.

## 설정 순서 (10분)

### 1. Cloudflare 계정 생성
- https://dash.cloudflare.com/sign-up 에서 무료 계정 생성
- 신용카드 등록 불필요 (무료 티어 월 10만 요청)

### 2. Worker 생성
1. 왼쪽 메뉴 **Workers & Pages** 클릭
2. **Create application** → **Create Worker**
3. 이름: `flow-cs-hub-claude-proxy`
4. **Deploy** (기본 코드 그대로 일단 배포)

### 3. Worker 코드 교체
1. 생성된 Worker 상세 화면 → **Edit code**
2. `worker.js` 파일 전체 내용을 복사해서 붙여넣기
3. **Save and Deploy**

### 4. 환경변수 설정
1. Worker 상세 화면 → **Settings** → **Variables and Secrets**
2. **Add** 클릭
3. 변수 추가:

   | Variable name | Type | Value |
   |---|---|---|
   | `ANTHROPIC_API_KEY` | Secret | 팀장님 Claude API 키 (sk-ant-api03-...) |
   | `ALLOWED_ORIGIN` | Text | `https://coayay.github.io` |

4. **Save** 클릭

### 5. Worker URL 확인
- Worker 상세 화면 상단에 URL 표시됨
- 예: `https://flow-cs-hub-claude-proxy.koyaya.workers.dev`
- 이 URL을 저에게 알려주세요 → 웹앱에 연결 처리

## 비용
- **무료 티어**: 월 10만 요청 (하루 3,300회)
- CS 실장 15명이 하루 평균 20회 상담 챗봇 사용 가정 시: 300회/일 = 월 9,000회 → 무료 티어 충분

## 테스트 (설정 완료 후)

```bash
curl -X POST https://flow-cs-hub-claude-proxy.{YOUR-SUBDOMAIN}.workers.dev \
  -H "Content-Type: application/json" \
  -H "Origin: https://coayay.github.io" \
  -d '{"messages":[{"role":"user","content":"안녕"}]}'
```

정상 응답: `{"text":"안녕하세요!...","usage":{...}}`
