// Server-side Gemini call. Runs only on Vercel's Node.js serverless runtime,
// so GEMINI_API_KEY (read from the environment) never reaches the browser.
//
// Model + REST shape confirmed against the official Gemini API docs
// (ai.google.dev/gemini-api/docs/models, ai.google.dev/api/generate-content):
// generateContent remains fully supported and is used here for a single-turn
// text response. Model: gemini-3.8-flash (current stable Flash model, GA 2026-09-02).

const GEMINI_MODEL = 'gemini-3.8-flash';
const GEMINI_ENDPOINT = `https://generativelanguage.googleapis.com/v1beta/models/${GEMINI_MODEL}:generateContent`;
const MAX_CANDIDATES = 5;
const REQUEST_TIMEOUT_MS = 15000;

function buildPrompt(conditions, candidates) {
  const conditionLines = Object.entries(conditions || {})
    .filter(([, value]) => value !== null && value !== undefined && value !== '')
    .map(([key, value]) => `- ${key}: ${value}`)
    .join('\n') || '- (지정된 조건 없음)';

  const candidateLines = candidates
    .map((c, i) => `${i + 1}. name: ${c.name} / price: ${c.price} / rating: ${c.rating}`)
    .join('\n');

  const systemInstruction = [
    '너는 요가 공간 추천 도우미다.',
    '아래 "후보 목록"에 있는 시설 중에서 정확히 한 곳만 선택해라.',
    '후보 목록에 없는 시설을 언급하거나 만들어내지 마라.',
    '후보 목록에 주어지지 않은 정보(분위기, 위치, 프로그램, 강사, 후기 등)는 절대 추측하거나 지어내지 마라.',
    '추천 이유는 반드시 후보 목록에 있는 price와 rating 숫자만 근거로 삼아 정확히 두 줄로 써라.',
    '다른 설명 없이 아래 형식을 그대로 지켜서 답하라:',
    'NAME: <후보 목록에 있는 name을 그대로>',
    'REASON: <첫 번째 줄>',
    '<두 번째 줄>',
  ].join('\n');

  const userInput = [
    '사용자 조건:',
    conditionLines,
    '',
    '후보 목록 (price 낮은 순):',
    candidateLines,
  ].join('\n');

  return { systemInstruction, userInput };
}

function parseGeminiText(text) {
  const nameMatch = text.match(/NAME:\s*(.+)/);
  const reasonMatch = text.match(/REASON:\s*([\s\S]+)/);
  if (!nameMatch || !reasonMatch) return null;

  const name = nameMatch[1].trim();
  const reason = reasonMatch[1].trim();
  if (!name || !reason) return null;

  return { name, reason };
}

module.exports = async (req, res) => {
  if (req.method !== 'POST') {
    res.status(405).json({ ok: false, reason: 'method_not_allowed' });
    return;
  }

  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) {
    res.status(500).json({ ok: false, reason: 'server_misconfigured' });
    return;
  }

  const { conditions, candidates } = req.body || {};

  if (!Array.isArray(candidates) || candidates.length === 0) {
    res.status(400).json({ ok: false, reason: 'no_candidates' });
    return;
  }

  const trimmedCandidates = candidates.slice(0, MAX_CANDIDATES).map((c) => ({
    name: String(c.name ?? ''),
    price: Number(c.price),
    rating: Number(c.rating),
  }));

  const { systemInstruction, userInput } = buildPrompt(conditions, trimmedCandidates);

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const geminiRes = await fetch(GEMINI_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-goog-api-key': apiKey,
      },
      body: JSON.stringify({
        systemInstruction: { parts: [{ text: systemInstruction }] },
        contents: [{ parts: [{ text: userInput }] }],
        // gemini-3.8-flash spends part of its output budget on internal
        // "thinking" tokens before the visible answer, so this needs real
        // headroom or the reply gets cut off before NAME:/REASON: appears.
        generationConfig: { maxOutputTokens: 1024 },
      }),
      signal: controller.signal,
    });

    if (!geminiRes.ok) {
      res.status(200).json({ ok: false, reason: 'ai_error' });
      return;
    }

    const data = await geminiRes.json();
    const text = data?.candidates?.[0]?.content?.parts?.[0]?.text;

    if (!text) {
      res.status(200).json({ ok: false, reason: 'ai_error' });
      return;
    }

    const parsed = parseGeminiText(text);
    if (!parsed) {
      res.status(200).json({ ok: false, reason: 'parse_error' });
      return;
    }

    const isValidCandidate = trimmedCandidates.some((c) => c.name === parsed.name);
    if (!isValidCandidate) {
      res.status(200).json({ ok: false, reason: 'invalid_name' });
      return;
    }

    res.status(200).json({ ok: true, name: parsed.name, reason: parsed.reason });
  } catch (err) {
    res.status(200).json({ ok: false, reason: 'ai_error' });
  } finally {
    clearTimeout(timeout);
  }
};
