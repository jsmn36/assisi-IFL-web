"use client";

import React, { createContext, useContext, useState, useEffect } from 'react';
import { BookingState, GuestInfo } from '@/types/booking';

interface BookingContextType {
  state: BookingState;
  setDates: (checkin: string, checkout: string) => void;
  setGuests: (count: number) => void;
  selectCottage: (cottage: { slug: string; name: string; price: number }) => void;
  setGuestInfo: (info: GuestInfo) => void;
  setPaymentStatus: (provider: 'razorpay' | 'stripe', id: string) => void;
  setBookingRef: (ref: string) => void;
  resetBooking: () => void;
}

const initialState: BookingState = {
  checkinDate: null,
  checkoutDate: null,
  guestCount: 2,
  selectedCottage: null,
  guestInfo: null,
  paymentIntentId: null,
  paymentProvider: null,
  bookingRef: null,
};

const BookingContext = createContext<BookingContextType | undefined>(undefined);

export const BookingProvider = ({ children }: { children: React.ReactNode }) => {
  const [state, setState] = useState<BookingState>(initialState);

  // Sync with URL params on initial load if present
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const checkin = params.get('checkin');
    const checkout = params.get('checkout');
    const guests = params.get('guests');

    if (checkin || checkout || guests) {
      setState(prev => ({
        ...prev,
        checkinDate: checkin || prev.checkinDate,
        checkoutDate: checkout || prev.checkoutDate,
        guestCount: guests ? parseInt(guests) : prev.guestCount
      }));
    }
  }, []);

  const setDates = (checkin: string, checkout: string) => 
    setState(prev => ({ ...prev, checkinDate: checkin, checkoutDate: checkout }));

  const setGuests = (count: number) => 
    setState(prev => ({ ...prev, guestCount: count }));

  const selectCottage = (cottage: { slug: string; name: string; price: number }) => 
    setState(prev => ({ ...prev, selectedCottage: cottage }));

  const setGuestInfo = (info: GuestInfo) => 
    setState(prev => ({ ...prev, guestInfo: info }));

  const setPaymentStatus = (provider: 'razorpay' | 'stripe', id: string) => 
    setState(prev => ({ ...prev, paymentProvider: provider, paymentIntentId: id }));

  const setBookingRef = (ref: string) => 
    setState(prev => ({ ...prev, bookingRef: ref }));

  const resetBooking = () => setState(initialState);

  return (
    <BookingContext.Provider value={{ 
      state, setDates, setGuests, selectCottage, setGuestInfo, setPaymentStatus, setBookingRef, resetBooking 
    }}>
      {children}
    </BookingContext.Provider>
  );
};

export const useBooking = () => {
  const context = useContext(BookingContext);
  if (!context) throw new Error('useBooking must be used within a BookingProvider');
  return context;
};
