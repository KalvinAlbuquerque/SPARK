import { NextRequest, NextResponse } from 'next/server';

const GEMINI_KEY = process.env.GEMINI_API_KEY ?? '';

export async function POST(req: NextRequest) {
  const { titulo, resumo } = await req.json();

  if (!titulo) {
    return NextResponse.json({ error: 'titulo é obrigatório' }, { status: 400 });
  }

  if (!GEMINI_KEY) {
    return NextResponse.json({ error: 'GEMINI_API_KEY não configurada' }, { status: 500 });
  }

  const prompt = buildPrompt(titulo, resumo);

  const res = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict?key=${GEMINI_KEY}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        instances: [{ prompt }],
        parameters: { sampleCount: 1, aspectRatio: '16:9' },
      }),
    }
  );

  if (!res.ok) {
    const err = await res.text();
    return NextResponse.json({ error: err }, { status: res.status });
  }

  const data = await res.json();
  const prediction = data.predictions?.[0];
  if (!prediction?.bytesBase64Encoded) {
    return NextResponse.json({ error: 'Resposta inesperada da API Imagen' }, { status: 502 });
  }

  const mime = prediction.mimeType ?? 'image/png';
  const capa_url = `data:${mime};base64,${prediction.bytesBase64Encoded}`;

  return NextResponse.json({ capa_url });
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
