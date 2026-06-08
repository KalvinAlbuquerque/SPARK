import { NextRequest, NextResponse } from 'next/server';

const GEMINI_TEXT_URL =
  'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent';
const GEMINI_IMG_URL =
  'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-preview-image-generation:generateContent';

// Passo 1: pede ao Gemini texto uma descrição visual em inglês
async function toVisualDescription(
  titulo: string,
  resumo: string | undefined,
  apiKey: string,
): Promise<string> {
  const context = resumo ? `\nAbstract (excerpt): "${resumo.slice(0, 300)}"` : '';
  const res = await fetch(`${GEMINI_TEXT_URL}?key=${apiKey}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      contents: [{
        parts: [{
          text:
            `You are creating a scientific journal cover image.\n` +
            `Given this Brazilian academic paper, describe in English the SPECIFIC scientific imagery ` +
            `that would visually represent this research. Be concrete: name organisms, equipment, ` +
            `phenomena, data charts, or environments directly related to the subject.\n\n` +
            `Title: "${titulo}"${context}\n\n` +
            `Reply with ONE short paragraph in English describing what to show visually. No style, no colors.`,
        }],
      }],
      generationConfig: { maxOutputTokens: 120, temperature: 0.4 },
    }),
    signal: AbortSignal.timeout(12000),
  });

  if (!res.ok) return titulo;
  const data = await res.json();
  return data.candidates?.[0]?.content?.parts?.[0]?.text?.trim() ?? titulo;
}

// Passo 2: gera a imagem com a descrição visual
async function generateImage(
  visualDesc: string,
  apiKey: string,
): Promise<string | null> {
  const prompt =
    `${visualDesc}\n\n` +
    `Style: dramatic lighting, dark background, high detail, magazine cover quality. ` +
    `Absolutely NO text, letters, words or numbers anywhere in the image.`;

  const res = await fetch(`${GEMINI_IMG_URL}?key=${apiKey}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      contents: [{ parts: [{ text: prompt }] }],
      generationConfig: { responseModalities: ['TEXT', 'IMAGE'] },
    }),
    signal: AbortSignal.timeout(30000),
  });

  if (!res.ok) return null;

  const data = await res.json();
  const parts: { inlineData?: { data: string; mimeType: string } }[] =
    data.candidates?.[0]?.content?.parts ?? [];
  const img = parts.find(p => p.inlineData);
  if (!img?.inlineData) return null;

  const { data: b64, mimeType } = img.inlineData;
  return `data:${mimeType};base64,${b64}`;
}

// Fallback: picsum com seed determinístico
function picsumUrl(titulo: string, variant: number): string {
  let seed = (variant * 999983) >>> 0;
  for (let i = 0; i < titulo.length; i++) {
    seed = Math.imul(seed * 31 + titulo.charCodeAt(i), 1) >>> 0;
  }
  return `https://picsum.photos/seed/${seed}/1280/720`;
}

export async function POST(req: NextRequest) {
  const { titulo, resumo, variant = 0 } = await req.json();

  if (!titulo) {
    return NextResponse.json({ error: 'titulo é obrigatório' }, { status: 400 });
  }

  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) {
    return NextResponse.json({ capa_url: picsumUrl(titulo, variant) });
  }

  try {
    // Passo 1: traduz o título em descrição visual em inglês
    const visualDesc = await toVisualDescription(titulo, resumo, apiKey);

    // Passo 2: gera a imagem
    const capa_url = await generateImage(visualDesc, apiKey);

    if (capa_url) {
      return NextResponse.json({ capa_url });
    }
  } catch {
    // fallthrough
  }

  return NextResponse.json({ capa_url: picsumUrl(titulo, variant) });
}
