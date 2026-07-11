export interface Cottage {
  slug: string;
  name: string;
  description: string;
  priceFrom: number;
  priceMax: number;
  maxGuests: number;
  size: string;
  view: string;
  bed: string;
  features: string[];
  amenities: string[];
  images: {
    hero: string;
    gallery: string[];
  };
}
