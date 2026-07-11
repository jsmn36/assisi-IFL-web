import { NextResponse } from 'next/server';

export async function POST(req: Request) {
  try {
    const body = await req.json();
    // Delegate authorize-only creation to payment provider
    return NextResponse.json({
      success: true,
      stripe: { clientSecret: 'pi_mock_123_secret' },
      razorpay: { orderId: 'order_mock_123' }
    });
  } catch (error) {
    return NextResponse.json({ success: false, error: 'Failed to create payment' }, { status: 500 });
  }
}
