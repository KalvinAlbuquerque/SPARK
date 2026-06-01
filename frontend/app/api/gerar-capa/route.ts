import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  const { titulo, resumo } = await req.json();

  if (!titulo) {
    return NextResponse.json({ error: 'titulo é obrigatório' }, { status: 400 });
  }

  const prompt = buildPrompt(titulo, resumo);
  const encoded = encodeURIComponent(prompt);
  const imageUrl = `https://image.pollinations.ai/prompt/${encoded}?width=1280&height=720&nologo=true&seed=${Date.now()}`;

  const res = await fetch(imageUrl);

  if (!res.ok) {
    return NextResponse.json({ error: `Pollinations API: ${res.status}` }, { status: res.status });
  }

  const buffer = await res.arrayBuffer();
  const b64 = Buffer.from(buffer).toString('base64');
  const mime = res.headers.get('content-type') ?? 'image/jpeg';

  return NextResponse.json({ capa_url: `data:${mime};base64,${b64}` });
}

function buildPrompt(titulo: string, resumo?: string): string {
  const snippet = resumo ? resumo.slice(0, 200) : '';
  return [
    `Scientific journal cover art for academic research paper: "${titulo}".`,
    snippet ? `Topic: ${snippet}.` : '',
    'Dramatic photorealistic scientific visualization,',
    'vibrant bold colors, deep blues, electric purples, golden accents,',
    'abstract data patterns, cinematic lighting, 4K quality, editorial design.',
    'No text, no letters, no words in the image.',
  ].filter(Boolean).join(' ');
}
