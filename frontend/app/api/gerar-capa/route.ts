import { NextRequest, NextResponse } from 'next/server';

const BASE = 'https://generativelanguage.googleapis.com/v1beta/models';

async function toVisualDescription(titulo: string, resumo: string | undefined, apiKey: string): Promise<string> {
  const context = resumo ? `\nAbstract: "${resumo.slice(0, 300)}"` : '';
  const res = await fetch(`${BASE}/gemini-2.0-flash:generateContent?key=${apiKey}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      contents: [{ parts: [{ text:
        `You are helping create a scientific journal cover image.\n` +
        `Given this Brazilian academic paper, write in English a SPECIFIC visual description ` +
        `of what should appear in the cover image. Name concrete objects, organisms, landscapes, ` +
        `equipment, charts or phenomena that directly relate to the research subject.\n\n` +
        `Title: "${titulo}"${context}\n\n` +
        `Reply with ONE short paragraph in English. Focus only on WHAT to show, not colors or style.`
      }] }],
      generationConfig: { maxOutputTokens: 150, temperature: 0.3 },
    }),
    signal: AbortSignal.timeout(15000),
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`[Step 1 - text] ${res.status}: ${body.slice(0, 200)}`);
  }
  const data = await res.json();
  const text = data.candidates?.[0]?.content?.parts?.[0]?.text?.trim();
  if (!text) throw new Error('[Step 1 - text] Gemini não retornou texto');
  return text;
}

async function generateImage(visualDesc: string, apiKey: string): Promise<string> {
  const prompt =
    `${visualDesc}\n\nStyle: dramatic lighting, dark background, high detail, magazine cover quality. ` +
    `Absolutely NO text, letters, words or numbers in the image.`;

  // Tenta gemini-2.0-flash-preview-image-generation, depois gemini-2.0-flash-exp
  const models = [
    'gemini-2.0-flash-preview-image-generation',
    'gemini-2.0-flash-exp',
  ];

  let lastError = '';
  for (const model of models) {
    const res = await fetch(`${BASE}/${model}:generateContent?key=${apiKey}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contents: [{ parts: [{ text: prompt }] }],
        generationConfig: { responseModalities: ['TEXT', 'IMAGE'] },
      }),
      signal: AbortSignal.timeout(40000),
    });

    if (!res.ok) {
      const body = await res.text();
      lastError = `[Step 2 - image/${model}] ${res.status}: ${body.slice(0, 200)}`;
      continue;
    }

    const data = await res.json();
    const parts: { inlineData?: { data: string; mimeType: string } }[] =
      data.candidates?.[0]?.content?.parts ?? [];
    const img = parts.find(p => p.inlineData);

    if (img?.inlineData) {
      const { data: b64, mimeType } = img.inlineData;
      return `data:${mimeType};base64,${b64}`;
    }
    lastError = `[Step 2 - image/${model}] sem imagem na resposta`;
  }

  throw new Error(lastError);
}

export async function POST(req: NextRequest) {
  const { titulo, resumo } = await req.json();

  if (!titulo) return NextResponse.json({ error: 'titulo obrigatório' }, { status: 400 });

  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) return NextResponse.json({ error: 'GEMINI_API_KEY não configurada no servidor' }, { status: 500 });

  try {
    const visualDesc = await toVisualDescription(titulo, resumo, apiKey);
    const capa_url   = await generateImage(visualDesc, apiKey);
    return NextResponse.json({ capa_url });
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    console.error('[gerar-capa]', msg);
    return NextResponse.json({ error: msg }, { status: 502 });
  }
}
