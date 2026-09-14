/**
 * Utility Functions
 */

import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merge Tailwind classes safely
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(...inputs));
}

// Module-level currency state, driven by ThemeContext at startup
let _currency = "INR";
let _locale = "en-IN";

const LOCALE_MAP: Record<string, string> = {
  INR: "en-IN",
  USD: "en-US",
  EUR: "de-DE",
  GBP: "en-GB",
};

export function setCurrencyPreference(currency: string) {
  _currency = currency;
  _locale = LOCALE_MAP[currency] ?? "en-US";
}

/**
 * Format currency — reads the active currency from ThemeContext via setCurrencyPreference.
 */
export function formatCurrency(amount: number): string {
  const safe = isNaN(amount) ? 0 : amount;
  return new Intl.NumberFormat(_locale, {
    style: "currency",
    currency: _currency,
  }).format(safe);
}

/**
 * Format date (safe)
 */
export function formatDate(dateString: string): string {
  const date = new Date(dateString);
  if (isNaN(date.getTime())) return "Invalid date";

  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(date);
}

/**
 * Format date and time
 */
export function formatDateTime(dateString: string): string {
  const date = new Date(dateString);
  if (isNaN(date.getTime())) return "Invalid date";

  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

/**
 * Calculate nights between dates
 * Uses UTC to prevent timezone shift issues
 */
export function calculateNights(
  checkIn: string,
  checkOut: string
): number {
  const start = new Date(checkIn);
  const end = new Date(checkOut);

  if (isNaN(start.getTime()) || isNaN(end.getTime())) return 0;

  // Normalize to midnight UTC to avoid timezone bugs
  const utcStart = Date.UTC(
    start.getFullYear(),
    start.getMonth(),
    start.getDate()
  );

  const utcEnd = Date.UTC(
    end.getFullYear(),
    end.getMonth(),
    end.getDate()
  );

  const diffTime = utcEnd - utcStart;
  return Math.max(diffTime / (1000 * 60 * 60 * 24), 0);
}

/**
 * Get status badge color
 */
export function getStatusColor(status: string): string {
  const normalized = status.toLowerCase();

  const colors: Record<string, string> = {
    pending: "bg-yellow-100 text-yellow-800",
    confirmed: "bg-blue-100 text-blue-800",
    checked_in: "bg-green-100 text-green-800",
    checked_out: "bg-gray-100 text-gray-800",
    cancelled: "bg-red-100 text-red-800",
    no_show: "bg-red-100 text-red-800",
  };

  return colors[normalized] ?? "bg-gray-100 text-gray-800";
}
