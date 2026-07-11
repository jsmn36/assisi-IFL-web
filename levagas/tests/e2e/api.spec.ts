import { test, expect } from '@playwright/test';

test.describe('API Routes', () => {
  test('TC-API-001: POST /api/availability returns results', async ({ request }) => {
    const res = await request.post('http://localhost:3000/api/availability', {
      data: { checkin: '2026-06-01', checkout: '2026-06-03', guests: 2 },
    });
    expect(res.status()).toBe(200);
    const body = await res.json();
    expect(body.success).toBe(true);
    expect(Array.isArray(body.results)).toBeTruthy();
    expect(body.results.length).toBe(5);
    // Each result must have slug, name, price
    for (const r of body.results) {
      expect(r.slug).toBeTruthy();
      expect(r.name).toBeTruthy();
      expect(typeof r.price).toBe('number');
    }
  });

  test('TC-API-002: POST /api/create-payment returns payment data', async ({ request }) => {
    const res = await request.post('http://localhost:3000/api/create-payment', {
      data: {
        amount: 9500,
        currency: 'INR',
        cottageSlug: 'mist-valley',
        checkin: '2026-06-01',
        checkout: '2026-06-03',
        guestEmail: 'test@levagas.com',
      },
    });
    expect(res.status()).toBe(200);
    const body = await res.json();
    expect(body.success).toBe(true);
    expect(body.stripe).toBeTruthy();
    expect(body.razorpay).toBeTruthy();
    expect(body.stripe.clientSecret).toBeTruthy();
    expect(body.razorpay.orderId).toBeTruthy();
  });

  test('TC-API-003: POST /api/submit-booking returns booking ref', async ({ request }) => {
    const res = await request.post('http://localhost:3000/api/submit-booking', {
      data: {
        checkin: '2026-06-01',
        checkout: '2026-06-03',
        cottageSlug: 'mist-valley',
        guests: 2,
        guestInfo: {
          firstName: 'Test',
          lastName: 'Guest',
          email: 'test@levagas.com',
          phone: '+919876543210',
          specialRequests: '',
        },
        paymentIntentId: 'pi_mock_test123',
        paymentProvider: 'stripe',
        paymentStatus: 'authorized',
      },
    });
    expect(res.status()).toBe(202);
    const body = await res.json();
    expect(body.success).toBe(true);
    expect(body.booking_ref).toMatch(/^LV-2026-\d{4}$/);
  });

  test('TC-API-004: GET /api/booking-status/[ref] returns confirmed', async ({ request }) => {
    const res = await request.get('http://localhost:3000/api/booking-status/LV-2026-1234');
    expect(res.status()).toBe(200);
    const body = await res.json();
    expect(body.status).toBe('confirmed');
    expect(body.summary).toBeTruthy();
    expect(body.summary.cottage).toBeTruthy();
    expect(body.summary.checkin).toBeTruthy();
    expect(body.summary.checkout).toBeTruthy();
  });

  test('TC-API-005: /api/availability returns all 5 cottages by slug', async ({ request }) => {
    const res = await request.post('http://localhost:3000/api/availability', {
      data: { checkin: '2026-06-01', checkout: '2026-06-03', guests: 2 },
    });
    const body = await res.json();
    const slugs = body.results.map((r: { slug: string }) => r.slug);
    expect(slugs).toContain('mist-valley');
    expect(slugs).toContain('emerald-hills');
    expect(slugs).toContain('golden-peak');
    expect(slugs).toContain('cloud-breeze');
    expect(slugs).toContain('celeste-honeymoon-villa');
  });
});
