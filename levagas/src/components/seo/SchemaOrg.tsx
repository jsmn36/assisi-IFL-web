import React from 'react';
import { PROPERTY_INFO } from '@/lib/constants';
import { cottages } from '@/data/cottages';

export default function SchemaOrg() {
  const hotelSchema = {
    "@context": "https://schema.org",
    "@type": "Hotel",
    "name": PROPERTY_INFO.name,
    "description": PROPERTY_INFO.tagline,
    "url": "https://levagas.com",
    "telephone": PROPERTY_INFO.phone,
    "address": {
      "@type": "PostalAddress",
      "streetAddress": PROPERTY_INFO.address.street,
      "addressLocality": PROPERTY_INFO.address.city,
      "addressRegion": PROPERTY_INFO.address.state,
      "postalCode": PROPERTY_INFO.address.pincode,
      "addressCountry": "IN"
    },
    "geo": {
      "@type": "GeoCoordinates",
      "latitude": "9.6806",
      "longitude": "76.9037"
    },
    "starRating": {
      "@type": "Rating",
      "ratingValue": "5"
    },
    "amenityFeature": [
      { "@type": "LocationFeatureSpecification", "name": "Free WiFi", "value": "true" },
      { "@type": "LocationFeatureSpecification", "name": "Private Balcony", "value": "true" },
      { "@type": "LocationFeatureSpecification", "name": "Restaurant", "value": "true" }
    ],
    "containsPlace": cottages.map(c => ({
      "@type": "HotelRoom",
      "name": c.name,
      "description": c.description,
      "occupancy": {
        "@type": "QuantitativeValue",
        "maxValue": c.maxGuests
      }
    }))
  };

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(hotelSchema) }}
    />
  );
}
