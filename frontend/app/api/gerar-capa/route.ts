import { NextRequest, NextResponse } from 'next/server';

const BASE = 'https://generativelanguage.googleapis.com/v1beta/models';
const TEXT_MODEL = 'gemini-2.5-flash';
const IMG_MODEL  = 'gemini-2.0-flash-preview-image-generation';

// Step 1: Gemini 2.5 Flash traduz o título em descrição visual concreta em inglês
async function toVisualDescription(titulo: string, resumo: string | undefined, apiKey: string): Promise<string> {
  const context = resumo ? `\nAbstract (excerpt): "${resumo.slice(0, 300)}"` : '';
  const res = await fetch(`${BASE}/${TEXT_MODEL}:generateContent?key=${apiKey}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      contents: [{
        parts: [{
          text:
            `You are helping create a scientific journal cover image.\n` +
            `Given this Brazilian academic paper, write in English a SPECIFIC visual description ` +
            `of what should appear in the cover image. Name concrete objects, organisms, landscapes, ` +
            `equipment, charts or phenomena that directly relate to the research subject.\n\n` +
            `Title: "${titulo}"${context}\n\n` +
            `Reply with ONE short paragraph in English. Focus only on WHAT to show, not colors or style.`,
        }],
      }],
      generationConfig: { maxOutputTokens: 150, temperature: 0.3 },
    }),
    signal: AbortSignal.timeout(15000),
  });

  if (!res.ok) throw new Error(`Text model error: ${res.status}`);
  const data = await res.json();
  const text = data.candidates?.[0]?.content?.parts?.[0]?.text?.trim();
  if (!text) throw new Error('No text from Gemini');
  return text;
}

// Step 2: gera a imagem a partir da descrição visual
async function generateImage(visualDesc: string, apiKey: string): Promise<string> {
  const prompt =
    `${visualDesc}\n\n` +
    `Style: dramatic cinematic lighting, dark background, high detail, magazine cover quality. ` +
    `Absolutely NO text, letters, words or numbers anywhere in the image.`;

  const res = await fetch(`${BASE}/${IMG_MODEL}:generateContent?key=${apiKey}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      contents: [{ parts: [{ text: prompt }] }],
      generationConfig: { responseModalities: ['TEXT', 'IMAGE'] },
    }),
    signal: AbortSignal.timeout(40000),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Image model error ${res.status}: ${err}`);
  }

  const data = await res.json();
  const parts: { inlineData?: { data: string; mimeType: string } }[] =
    data.candidates?.[0]?.content?.parts ?? [];
  const img = parts.find(p => p.inlineData);
  if (!img?.inlineData) throw new Error('No image in Gemini response');

  const { data: b64, mimeType } = img.inlineData;
  return `data:${mimeType};base64,${b64}`;
}

export async function POST(req: NextRequest) {
  const { titulo, resumo } = await req.json();

  if (!titulo) {
    return NextResponse.json({ error: 'titulo é obrigatório' }, { status: 400 });
  }

  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) {
    return NextResponse.json({ error: 'GEMINI_API_KEY não configurada' }, { status: 500 });
  }

  try {
    const visualDesc = await toVisualDescription(titulo, resumo, apiKey);
    const capa_url   = await generateImage(visualDesc, apiKey);
    return NextResponse.json({ capa_url });
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'Erro desconhecido';
    return NextResponse.json({ error: msg }, { status: 502 });
  }
}
