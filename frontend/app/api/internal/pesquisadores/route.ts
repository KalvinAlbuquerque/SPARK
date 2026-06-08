import { NextRequest, NextResponse } from 'next/server';

const BACKEND = process.env.NEXT_PUBLIC_API_URL ?? 'https://spark-production-1903.up.railway.app';
const API_KEY = process.env.INTERNAL_API_KEY ?? '';

export async function GET(req: NextRequest) {
  const q = req.nextUrl.searchParams.get('q');
  const url = `${BACKEND}/internal/pesquisadores${q ? `?q=${encodeURIComponent(q)}` : ''}`;

  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${API_KEY}` },
    cache: 'no-store',
  });

  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}

export async function POST(req: NextRequest) {
  const body = await req.json();
  const res = await fetch(`${BACKEND}/internal/pesquisadores`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });

  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}
