import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  const { titulo, variant = 0 } = await req.json();

  if (!titulo) {
    return NextResponse.json({ error: 'titulo é obrigatório' }, { status: 400 });
  }

  // Seed determinístico: mesma produção + variant → imagem diferente a cada "Regenerar"
  let seed = variant * 999983;
  for (let i = 0; i < titulo.length; i++) {
    seed = Math.imul(seed * 31 + titulo.charCodeAt(i), 1) >>> 0;
  }

  // picsum.photos: seed-based, 1280×720, gratuito e sem autenticação
  const capa_url = `https://picsum.photos/seed/${seed}/1280/720`;

  return NextResponse.json({ capa_url });
}
