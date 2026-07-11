import { NextResponse } from 'next/server';
import { cottages } from '@/data/cottages';

export async function POST(req: Request) {
  try {
    const { checkin, checkout, guests } = await req.json();
    // Proxy to Channel Manager in production
    // CM API unknown → use mock
    return NextResponse.json({
      success: true,
      results: cottages.map(c => ({
        slug: c.slug,
        name: c.name,
        price: c.priceFrom
      }))
    });
  } catch (error) {
    return NextResponse.json({ success: false, error: 'Failed to fetch availability' }, { status: 500 });
  }
}
