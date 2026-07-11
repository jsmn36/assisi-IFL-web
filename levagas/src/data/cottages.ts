import { Cottage } from "@/types/cottage";

export const cottages: Cottage[] = [
  {
    slug: 'mist-valley',
    name: 'Mist Valley Cottage',
    description: 'Wake up to the magical morning mist rolling across the valley. This cottage offers the most dramatic misty views, especially during early mornings from October to February.',
    priceFrom: 9500,
    priceMax: 11000,
    maxGuests: 2,
    size: '400 sq ft',
    view: 'Valley view with mist',
    bed: 'King bed',
    features: ['🛏️ King Bed', '👥 2 Guests', '🌄 Valley View', '🛁 Private Balcony'],
    amenities: [
      'High-speed WiFi',
      'Smart TV with Netflix',
      'Mini refrigerator',
      'Electric kettle & coffee maker',
      'Premium toiletries',
      'Room heater (winter months)',
      'Daily housekeeping',
      'Complimentary breakfast'
    ],
    images: {
      hero: 'https://images.unsplash.com/photo-1542401886-65d6c60db275?q=80&w=1200',
      gallery: [
        'https://images.unsplash.com/photo-1512918728675-ed5a9ecdebfd?q=80&w=1200',
        'https://images.unsplash.com/photo-1584132967334-10e028bd69f7?q=80&w=1200',
        'https://images.unsplash.com/photo-1590490360182-c33d57733427?q=80&w=1200',
        'https://images.unsplash.com/photo-1618221195710-dd6b41faaea6?q=80&w=1200'
      ]
    }
  },
  {
    slug: 'emerald-hills',
    name: 'Emerald Hills Cottage',
    description: 'Overlooking lush green hills and tea plantations. Emerald Hills offers a refreshing stay surrounded by nature.',
    priceFrom: 8500,
    priceMax: 10000,
    maxGuests: 2,
    size: '380 sq ft',
    view: 'Tea garden view',
    bed: 'King bed',
    features: ['🛏️ King Bed', '👥 2 Guests', '🍃 Tea Garden View', '🛁 Private Balcony'],
    amenities: [
      'High-speed WiFi',
      'Smart TV',
      'Mini refrigerator',
      'Electric kettle',
      'Premium toiletries',
      'Daily housekeeping',
      'Complimentary breakfast'
    ],
    images: {
      hero: 'https://images.unsplash.com/photo-1470770841072-f978cf4d019e?q=80&w=1200',
      gallery: [
        'https://images.unsplash.com/photo-1445013511191-837965883391?q=80&w=1200',
        'https://images.unsplash.com/photo-1566073771259-6a8506099945?q=80&w=1200',
        'https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?q=80&w=1200'
      ]
    }
  },
  {
    slug: 'golden-peak',
    name: 'Golden Peak Cottage',
    description: 'Perfect for sunset lovers. Golden Peak offers stunning views of the western hills during the golden hour.',
    priceFrom: 9000,
    priceMax: 10500,
    maxGuests: 2,
    size: '400 sq ft',
    view: 'Western hills for golden hour',
    bed: 'King bed',
    features: ['🛏️ King Bed', '👥 2 Guests', '🌅 Sunset View', '🛁 Private Balcony'],
    amenities: [
      'High-speed WiFi',
      'Smart TV',
      'Mini refrigerator',
      'Electric kettle',
      'Premium toiletries',
      'Daily housekeeping',
      'Complimentary breakfast'
    ],
    images: {
      hero: 'https://images.unsplash.com/photo-1493809842364-78817add7ffb?q=80&w=1200',
      gallery: [
        'https://images.unsplash.com/photo-1564013799919-ab600027ffc6?q=80&w=1200',
        'https://images.unsplash.com/photo-1522771731478-44eb9321f4ae?q=80&w=1200'
      ]
    }
  },
  {
    slug: 'cloud-breeze',
    name: 'Cloud Breeze Cottage',
    description: 'Located at a corner to catch the refreshing mountain breeze. Open valley views ensure a cool and pleasant stay.',
    priceFrom: 8500,
    priceMax: 10000,
    maxGuests: 2,
    size: '380 sq ft',
    view: 'Open valley',
    bed: 'King bed',
    features: ['🛏️ King Bed', '👥 2 Guests', '☁️ Cloud View', '🛁 Private Balcony'],
    amenities: [
      'High-speed WiFi',
      'Smart TV',
      'Mini refrigerator',
      'Electric kettle',
      'Premium toiletries',
      'Daily housekeeping',
      'Complimentary breakfast'
    ],
    images: {
      hero: 'https://images.unsplash.com/photo-1440186347098-386b7459ad6b?q=80&w=1200',
      gallery: [
        'https://images.unsplash.com/photo-1582719508461-905c673771fd?q=80&w=1200',
        'https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?q=80&w=1200'
      ]
    }
  },
  {
    slug: 'celeste-honeymoon-villa',
    name: 'Celeste Honeymoon Villa',
    description: 'The ultimate romantic experience. A panoramic villa with 270° views, designed specially for couples seeking privacy and luxury.',
    priceFrom: 15000,
    priceMax: 18000,
    maxGuests: 2,
    size: '650 sq ft',
    view: 'Panoramic 270° views',
    bed: 'King bed + Jacuzzi tub',
    features: ['🛏️ King Bed + Jacuzzi', '👥 2 Guests', '🌅 Panoramic View', '🤍 Honeymoon Special'],
    amenities: [
      'Private jacuzzi with valley view',
      'Rose petal turndown service',
      'Complimentary champagne on arrival',
      'Romantic candlelight dinner setup (on request)',
      'Separate living area',
      'High-speed WiFi',
      'Smart TV with streaming',
      'Daily housekeeping',
      'Complimentary breakfast'
    ],
    images: {
      hero: 'https://images.unsplash.com/photo-1566073771259-6a8506099945?q=80&w=1200',
      gallery: [
        'https://images.unsplash.com/photo-1578683010236-d716f9a3f461?q=80&w=1200',
        'https://images.unsplash.com/photo-1507039228507-356b212196d5?q=80&w=1200',
        'https://images.unsplash.com/photo-1510798831971-661eb04b3739?q=80&w=1200'
      ]
    }
  }
];
