export interface GuestInfo {
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  specialRequests?: string;
}

export interface BookingState {
  checkinDate: string | null;
  checkoutDate: string | null;
  guestCount: number;
  selectedCottage: {
    slug: string;
    name: string;
    price: number;
  } | null;
  guestInfo: GuestInfo | null;
  paymentIntentId: string | null;
  paymentProvider: 'razorpay' | 'stripe' | null;
  bookingRef: string | null;
}

export interface ReservationSummary {
  ref: string;
  checkin: string;
  checkout: string;
  cottageName: string;
  guestName: string;
  status: 'confirmed' | 'rejected' | 'pending';
  totalAmount: number;
}
