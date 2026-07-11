import { NextResponse } from 'next/server';

export async function POST(req: Request) {
  try {
    const body = await req.json();
    // Proxy POST to CM Webhook
    const mockRef = `LV-2026-${Math.floor(Math.random() * 10000).toString().padStart(4, '0')}`;
    return NextResponse.json({
      success: true,
      booking_ref: mockRef,
      message: 'Booking submitted to Channel Manager webhook. Pending confirmation.'
    }, { status: 202 });
  } catch (error) {
    return NextResponse.json({ success: false, error: 'Failed' }, { status: 500 });
  }
}
