import { NextRequest, NextResponse } from 'next/server';

export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ lattes_id: string }> }
) {
  const { lattes_id } = await params;

  const url = `https://servicosweb.cnpq.br/wspessoa/servletrecuperafoto?tipo=1&id=${lattes_id}`;

  try {
    const res = await fetch(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'http://lattes.cnpq.br/',
      },
      signal: AbortSignal.timeout(5000),
    });

    if (!res.ok || !res.headers.get('content-type')?.startsWith('image/')) {
      return new NextResponse(null, { status: 404 });
    }

    const buffer = await res.arrayBuffer();
    return new NextResponse(buffer, {
      status: 200,
      headers: {
        'Content-Type': res.headers.get('content-type') ?? 'image/jpeg',
        'Cache-Control': 'public, max-age=86400',
      },
    });
  } catch {
    return new NextResponse(null, { status: 404 });
  }
}
