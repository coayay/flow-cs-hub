# Anthropic 지원 문의 템플릿

**받는 사람**: support@anthropic.com
**발신**: f004a@flowedu.ai.kr (팀장님 계정)
**제목**: Service Account key returning 403 "Request not allowed" on /v1/messages

---

Hi Anthropic Support team,

We're integrating Claude Haiku 4.5 into our internal CS chatbot via a Cloudflare Workers proxy, but our newly-created Service Account API key is consistently returning 403 "Request not allowed" when calling `/v1/messages`.

**Account**:
- Email: f004a@flowedu.ai.kr
- Organization: flowedu
- Workspace: Default (ID: `wrkspc_011bMceL7W4DcLegyMuYMbVy`)

**Service Account**:
- Name: `flow-cs-hub-cloudflare`
- Service Account ID: `svac_01THhx4TfUipEg4Rq3aiS1Ni`
- Organization role: Developer
- Workspace role: Workspace User (Default workspace)

**API Key**:
- Name: `cloudflare-key-v1`
- Key prefix: `sk-ant-svc-1zF`
- Scope: Default workspace
- Expiration: None

**Error details**:
```
Request:
POST https://api.anthropic.com/v1/messages
Headers:
  x-api-key: sk-ant-svc-1zF... (106 chars, starts with sk-ant-svc-)
  anthropic-version: 2023-06-01
  Content-Type: application/json
Body:
  {"model":"claude-haiku-4-5-20251001","max_tokens":30,"messages":[{"role":"user","content":"hi"}]}

Response (consistent):
Status: 403
Body: {"type":"error","error":{"type":"forbidden","message":"Request not allowed"}}

Sample request_id: req_011Cg1tja1pMiriFGfBX4Y4f
```

**What I've tried**:
1. Different model IDs: `claude-haiku-4-5-20251001`, `claude-haiku-5-5`, `claude-sonnet-5`, etc. — all 403
2. Added/removed `anthropic-workspace-id` header — no effect
3. Added `User-Agent` header — no effect
4. Tested from the same Cloudflare Worker that received 200 OK on the very first call
5. The organization has an existing Standard API key (`sk-ant-api03-`) that works fine in Dify, so the organization account itself is active

**Observed pattern**:
- The very first API call succeeded (returned valid completion from Claude Haiku 4.5)
- All subsequent calls return 403, regardless of query content or model
- This happened within ~10 minutes of key creation

**Request**:
Please investigate why this Service Account key is being rejected. If it was auto-flagged by abuse detection due to debugging activity, please clear the block. If there's a specific role or configuration we're missing, please advise.

Thank you,
송재풍 (Song Jaepung)
Flow Education Co., Ltd.
