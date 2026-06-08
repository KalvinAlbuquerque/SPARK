import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  const { titulo, resumo, variant = 0 } = await req.json();

  if (!titulo) {
    return NextResponse.json({ error: 'titulo é obrigatório' }, { status: 400 });
  }

  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) {
    return NextResponse.json({ error: 'GEMINI_API_KEY não configurada' }, { status: 500 });
  }

  const prompt = buildPrompt(titulo, resumo);

  try {
    const res = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-preview-image-generation:generateContent?key=${apiKey}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contents: [{ parts: [{ text: prompt }] }],
          generationConfig: { responseModalities: ['TEXT', 'IMAGE'] },
        }),
        signal: AbortSignal.timeout(30000),
      }
    );

    if (!res.ok) {
      const errText = await res.text();
      throw new Error(`Gemini ${res.status}: ${errText}`);
    }

    const data = await res.json();
    const parts: { inlineData?: { data: string; mimeType: string } }[] =
      data.candidates?.[0]?.content?.parts ?? [];
    const imagePart = parts.find(p => p.inlineData);

    if (imagePart?.inlineData) {
      const { data: b64, mimeType } = imagePart.inlineData;
      return NextResponse.json({ capa_url: `data:${mimeType};base64,${b64}` });
    }

    throw new Error('Gemini não retornou imagem');
  } catch {
    // Fallback: picsum com seed do título
    let seed = (variant * 999983) >>> 0;
    for (let i = 0; i < titulo.length; i++) {
      seed = Math.imul(seed * 31 + titulo.charCodeAt(i), 1) >>> 0;
    }
    return NextResponse.json({ capa_url: `https://picsum.photos/seed/${seed}/1280/720` });
  }
}

function buildPrompt(titulo: string, resumo?: string): string {
  const context = resumo ? resumo.slice(0, 300) : '';
  return `Create a photorealistic scientific illustration for a research paper.

Title: "${titulo}"${context ? `\nAbstract excerpt: "${context}"` : ''}

Instructions:
- The image must visually represent the SPECIFIC topic of this research (not generic science)
- Show concrete objects, phenomena or scenarios directly related to the subject
- Style: dramatic lighting, high detail, dark background, magazine cover quality
- Absolutely NO text, letters, words or numbers anywhere in the image`;
}
