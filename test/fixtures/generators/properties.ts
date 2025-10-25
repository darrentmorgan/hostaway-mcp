/**
 * Property/listing fixture generator
 *
 * Generates realistic Hostaway property data for testing
 */

export interface Property {
  id: number;
  name: string;
  address: {
    street: string;
    city: string;
    state: string;
    country: string;
    zipCode: string;
  };
  bedrooms: number;
  bathrooms: number;
  maxGuests: number;
  basePrice: number;
  currency: string;
  status: 'active' | 'inactive' | 'archived';
  amenities: string[];
  images: string[];
  description: string;
}

const CITIES = ['Rome', 'Florence', 'Venice', 'Milan', 'Naples'];
const AMENITIES = ['WiFi', 'Air Conditioning', 'Kitchen', 'Parking', 'Pool', 'Hot Tub', 'Washer', 'Dryer'];
const PROPERTY_TYPES = ['Villa', 'Apartment', 'House', 'Condo', 'Studio'];

/**
 * Generate a single property
 *
 * @param index - Property index (for deterministic IDs and names)
 * @returns Property object
 */
export function generateProperty(index: number): Property {
  const propertyType = PROPERTY_TYPES[index % PROPERTY_TYPES.length];
  const city = CITIES[index % CITIES.length];

  return {
    id: 400000 + index,
    name: `${propertyType} ${city} ${index}`,
    address: {
      street: `${index + 1} Via Roma`,
      city,
      state: 'Lazio',
      country: 'Italy',
      zipCode: `00${100 + index}`,
    },
    bedrooms: (index % 4) + 1,
    bathrooms: (index % 3) + 1,
    maxGuests: (index % 8) + 2,
    basePrice: 100 + (index * 50),
    currency: 'EUR',
    status: index % 10 === 0 ? 'inactive' : 'active',
    amenities: AMENITIES.slice(0, (index % AMENITIES.length) + 2),
    images: [
      `https://example.com/images/${index}/1.jpg`,
      `https://example.com/images/${index}/2.jpg`,
    ],
    description: `Beautiful ${propertyType.toLowerCase()} in the heart of ${city}. Perfect for ${(index % 8) + 2} guests with ${(index % 4) + 1} bedrooms and ${(index % 3) + 1} bathrooms.`,
  };
}

/**
 * Generate multiple properties
 *
 * @param count - Number of properties to generate
 * @returns Array of property objects
 */
export function generateProperties(count: number): Property[] {
  return Array.from({ length: count }, (_, index) => generateProperty(index));
}
