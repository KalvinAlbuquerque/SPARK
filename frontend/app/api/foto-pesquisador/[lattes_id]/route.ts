import { NextRequest, NextResponse } from 'next/server';

export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ lattes_id: string }> }
) {
  const { lattes_id } = await params;

  const url = `https://servicosweb.cnpq.br/wspessoa/servletrecuperafoto?tipo=1&id=${lattes_id}`;

  try {
    const res = await fetch(url, {
      redirect: 'manual',
      headers: {
        'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Referer': 'http://lattes.cnpq.br/',
      },
      signal: AbortSignal.timeout(8000),
    });

    // CNPq redireciona para login quando bloqueia ou não há foto
    if (res.status >= 300) {
      return new NextResponse(null, { status: 404 });
    }

    const contentType = res.headers.get('content-type') ?? '';
    if (!contentType.includes('image')) {
      return new NextResponse(null, { status: 404 });
    }

    const buffer = await res.arrayBuffer();
    // Imagem real tem pelo menos 1KB; placeholder do CNPq costuma ser menor
    if (buffer.byteLength < 1024) {
      return new NextResponse(null, { status: 404 });
    }

    return new NextResponse(buffer, {
      status: 200,
      headers: {
        'Content-Type': contentType,
        'Cache-Control': 'public, max-age=86400',
      },
    });
  } catch {
    return new NextResponse(null, { status: 404 });
  }
}
