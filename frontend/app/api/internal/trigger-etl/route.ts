import { NextRequest, NextResponse } from 'next/server';

const BACKEND = process.env.NEXT_PUBLIC_API_URL ?? 'https://spark-production-1903.up.railway.app';
const API_KEY = process.env.INTERNAL_API_KEY ?? '';

export async function POST(req: NextRequest) {
  const formData = await req.formData();

  const res = await fetch(`${BACKEND}/internal/trigger-etl`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${API_KEY}` },
    body: formData,
  });

  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}
