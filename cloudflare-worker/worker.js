/**
 * Flow CS Hub · Claude API 프록시
 * Cloudflare Workers 전용
 *
 * 역할: 브라우저 → 이 Worker → Anthropic API
 * Claude API 키를 브라우저에 노출하지 않기 위한 중계자
 *
 * 환경변수 (Cloudflare 대시보드에서 설정):
 * - ANTHROPIC_API_KEY: sk-ant-api03-... (팀장님 Claude 콘솔에서 발급)
 * - ALLOWED_ORIGIN: https://coayay.github.io (CORS 허용 도메인)
 */

const ANTHROPIC_VERSION = '2023-06-01';
const DEFAULT_MODEL = 'claude-haiku-4-5';
const MAX_TOKENS = 1024;
const WORKSPACE_ID = 'wrkspc_011bMceL7W4DcLegyMuYMbVy';  // Default workspace (Flow CS Hub)

export default {
  async fetch(request, env, ctx) {
    const origin = request.headers.get('Origin') || '';
    const allowedOrigin = env.ALLOWED_ORIGIN || 'https://coayay.github.io';

    // CORS preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        status: 204,
        headers: corsHeaders(allowedOrigin),
      });
    }

    // POST만 허용
    if (request.method !== 'POST') {
      return jsonResponse({ error: 'Method not allowed' }, 405, allowedOrigin);
    }

    // Origin 검증 (CORS)
    if (origin && origin !== allowedOrigin) {
      return jsonResponse({ error: 'Forbidden origin: ' + origin }, 403, allowedOrigin);
    }

    try {
      const body = await request.json();
      const { messages, system, model, max_tokens, temperature } = body;

      if (!Array.isArray(messages) || messages.length === 0) {
        return jsonResponse({ error: 'messages array required' }, 400, allowedOrigin);
      }

      if (!env.ANTHROPIC_API_KEY) {
        return jsonResponse({ error: 'ANTHROPIC_API_KEY not set' }, 500, allowedOrigin);
      }

      // Anthropic API 호출
      // Workspace-scoped service account key는 workspace-id 헤더 불필요
      // Organization-scoped key(sk-ant-usr-)만 workspace-id 필요
      const needsWorkspaceId = env.ANTHROPIC_API_KEY.startsWith('sk-ant-usr-')
                             || env.ANTHROPIC_API_KEY.startsWith('sk-ant-adm-');
      const headers = {
        'Content-Type': 'application/json',
        'x-api-key': env.ANTHROPIC_API_KEY,
        'anthropic-version': ANTHROPIC_VERSION,
        'User-Agent': 'FlowCSHubProxy/1.0 (Cloudflare Worker)',
      };
      if (needsWorkspaceId) {
        headers['anthropic-workspace-id'] = WORKSPACE_ID;
      }

      const anthropicRes = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers,
        body: JSON.stringify({
          model: model || DEFAULT_MODEL,
          max_tokens: max_tokens || MAX_TOKENS,
          temperature: temperature ?? 0.3,
          system: system || '',
          messages: messages,
        }),
      });

      const data = await anthropicRes.json();

      if (!anthropicRes.ok) {
        return jsonResponse(
          { error: 'Anthropic API error', status: anthropicRes.status, detail: data },
          anthropicRes.status,
          allowedOrigin
        );
      }

      // 답변 텍스트 추출
      const text = data.content?.[0]?.text || '';
      const usage = data.usage || {};

      return jsonResponse(
        {
          text,
          usage,
          model: data.model,
        },
        200,
        allowedOrigin
      );
    } catch (err) {
      return jsonResponse({ error: 'Worker error: ' + err.message }, 500, allowedOrigin);
    }
  },
};

function corsHeaders(allowedOrigin) {
  return {
    'Access-Control-Allow-Origin': allowedOrigin,
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '86400',
  };
}

function jsonResponse(body, status, allowedOrigin) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      'Content-Type': 'application/json',
      ...corsHeaders(allowedOrigin),
    },
  });
}
