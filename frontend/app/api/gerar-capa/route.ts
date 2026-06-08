import { NextRequest, NextResponse } from 'next/server';

const PT_STOPWORDS = new Set([
  'de','da','do','das','dos','e','em','na','no','nas','nos',
  'a','o','as','os','um','uma','com','por','para','que','se',
  'ao','à','sobre','entre','após','ante','até','desde','sem',
  'sob','sua','seu','suas','seus','este','esta','um','uma',
  'análise','estudo','avaliação','investigação','pesquisa',
]);

function extractTerms(titulo: string): string {
  return titulo
    .split(/\s+/)
    .map(w => w.replace(/[^a-záéíóúâêîôûãõàèìòùç\w]/gi, ''))
    .filter(w => w.length > 3 && !PT_STOPWORDS.has(w.toLowerCase()))
    .slice(0, 5)
    .join(' ');
}

// Seed determinístico para fallback picsum
function titleSeed(titulo: string, variant: number): number {
  let seed = variant * 999983;
  for (let i = 0; i < titulo.length; i++) {
    seed = Math.imul(seed * 31 + titulo.charCodeAt(i), 1) >>> 0;
  }
  return seed;
}

export async function POST(req: NextRequest) {
  const { titulo, variant = 0 } = await req.json();

  if (!titulo) {
    return NextResponse.json({ error: 'titulo é obrigatório' }, { status: 400 });
  }

  const terms = extractTerms(titulo) || titulo.split(' ').slice(0, 3).join(' ');

  try {
    const res = await fetch(
      `https://lexica.art/api/v1/search?q=${encodeURIComponent(terms)}`,
      { headers: { 'User-Agent': 'SPARK/1.0' }, signal: AbortSignal.timeout(8000) }
    );

    if (res.ok) {
      const data = await res.json();
      const images: { src: string }[] = data.images ?? [];
      if (images.length > 0) {
        const idx = variant % images.length;
        return NextResponse.json({ capa_url: images[idx].src });
      }
    }
  } catch {
    // Lexica indisponível → fallback
  }

  // Fallback: picsum com seed do título
  const seed = titleSeed(titulo, variant);
  return NextResponse.json({ capa_url: `https://picsum.photos/seed/${seed}/1280/720` });
}
