import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  const { titulo, resumo } = await req.json();

  if (!titulo) {
    return NextResponse.json({ error: 'titulo é obrigatório' }, { status: 400 });
  }

  const prompt = buildPrompt(titulo, resumo);
  const encoded = encodeURIComponent(prompt);
  // Retorna a URL diretamente — o browser carrega a imagem sem passar pelo servidor,
  // evitando o bloqueio de requests server-side da Pollinations (402).
  const capa_url = `https://image.pollinations.ai/prompt/${encoded}?width=1280&height=720&nologo=true&seed=${Date.now()}`;

  return NextResponse.json({ capa_url });
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
