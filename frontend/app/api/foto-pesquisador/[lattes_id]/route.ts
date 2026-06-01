import { NextRequest, NextResponse } from 'next/server';

export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ lattes_id: string }> }
) {
  const { lattes_id } = await params;

  const url = `https://servicosweb.cnpq.br/wspessoa/servletrecuperafoto?tipo=1&id=${lattes_id}`;

  try {
    const res = await fetch(url, {
      redirect: 'follow',
      headers: {
        'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Referer': 'http://lattes.cnpq.br/',
      },
      signal: AbortSignal.timeout(8000),
    });

    if (!res.ok) return new NextResponse(null, { status: 404 });

    const buffer = await res.arrayBuffer();
    const bytes = new Uint8Array(buffer);

    const isJpeg = bytes[0] === 0xFF && bytes[1] === 0xD8 && bytes[2] === 0xFF;
    const isPng  = bytes[0] === 0x89 && bytes[1] === 0x50 && bytes[2] === 0x4E && bytes[3] === 0x47;
    const isGif  = bytes[0] === 0x47 && bytes[1] === 0x49 && bytes[2] === 0x46;

    if (!isJpeg && !isPng && !isGif) {
      return new NextResponse(null, { status: 404 });
    }

    const mime = isJpeg ? 'image/jpeg' : isPng ? 'image/png' : 'image/gif';

    return new NextResponse(buffer, {
      status: 200,
      headers: {
        'Content-Type': mime,
        'Cache-Control': 'public, max-age=86400',
      },
    });
  } catch {
    return new NextResponse(null, { status: 404 });
  }
}
