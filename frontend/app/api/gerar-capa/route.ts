import { NextRequest, NextResponse } from 'next/server';

const GEMINI_KEY = process.env.GEMINI_API_KEY ?? '';
const MODEL = 'gemini-2.0-flash-preview-image-generation';

export async function POST(req: NextRequest) {
  const { titulo, resumo } = await req.json();

  if (!titulo) {
    return NextResponse.json({ error: 'titulo é obrigatório' }, { status: 400 });
  }

  if (!GEMINI_KEY) {
    return NextResponse.json({ error: 'GEMINI_API_KEY não configurada no servidor' }, { status: 500 });
  }

  const prompt = buildPrompt(titulo, resumo);

  const res = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models/${MODEL}:generateContent?key=${GEMINI_KEY}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contents: [{ role: 'user', parts: [{ text: prompt }] }],
        generationConfig: { responseModalities: ['IMAGE'] },
      }),
    }
  );

  if (!res.ok) {
    const err = await res.text();
    console.error('[gerar-capa] Gemini API error:', res.status, err);
    return NextResponse.json({ error: `Gemini API: ${res.status}`, detail: err }, { status: res.status });
  }

  const data = await res.json();
  const parts: { inlineData?: { mimeType: string; data: string } }[] =
    data.candidates?.[0]?.content?.parts ?? [];

  const imagePart = parts.find(p => p.inlineData?.mimeType?.startsWith('image/'));

  if (!imagePart?.inlineData) {
    console.error('[gerar-capa] Sem imagem na resposta:', JSON.stringify(data).slice(0, 400));
    return NextResponse.json({ error: 'Modelo não retornou imagem' }, { status: 502 });
  }

  const { mimeType, data: b64 } = imagePart.inlineData;
  return NextResponse.json({ capa_url: `data:${mimeType};base64,${b64}` });
}

function buildPrompt(titulo: string, resumo?: string): string {
  const snippet = resumo ? resumo.slice(0, 250) : '';
  return [
    `Scientific journal cover art for a Brazilian academic research paper titled: "${titulo}".`,
    snippet ? `Research context: ${snippet}.` : '',
    'Visual style: dramatic photorealistic scientific visualization,',
    'vibrant bold colors (deep blues, electric purples, golden accents),',
    'abstract data patterns, microscopic or satellite imagery elements,',
    'modern editorial design, cinematic lighting, highly detailed, 4K quality.',
    'Absolutely no text, no letters, no numbers visible in the image.',
  ].filter(Boolean).join(' ');
}
