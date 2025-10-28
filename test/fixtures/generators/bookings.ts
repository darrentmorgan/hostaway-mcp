/**
 * Booking/reservation fixture generator
 *
 * Generates realistic Hostaway booking data for testing
 */

export interface Booking {
  id: number;
  listingId: number;
  guestName: string;
  guestEmail: string;
  checkIn: string;
  checkOut: string;
  nights: number;
  guests: number;
  totalPrice: number;
  currency: string;
  status: 'confirmed' | 'pending' | 'cancelled' | 'completed';
  channel: 'direct' | 'airbnb' | 'vrbo' | 'booking.com';
  createdAt: string;
  updatedAt: string;
}

const GUEST_NAMES = [
  'John Smith',
  'Maria Garcia',
  'Robert Johnson',
  'Emma Brown',
  'Michael Wilson',
];

const CHANNELS: Array<'direct' | 'airbnb' | 'vrbo' | 'booking.com'> = [
  'direct',
  'airbnb',
  'vrbo',
  'booking.com',
];

/**
 * Generate a single booking
 *
 * @param index - Booking index (for deterministic IDs and dates)
 * @returns Booking object
 */
export function generateBooking(index: number): Booking {
  const checkInDate = new Date(2024, 0, 1 + (index * 7)); // Start Jan 1, 2024, increment by weeks
  const nights = (index % 7) + 3; // 3-9 nights
  const checkOutDate = new Date(checkInDate);
  checkOutDate.setDate(checkOutDate.getDate() + nights);

  const guestName = GUEST_NAMES[index % GUEST_NAMES.length];
  const channel = CHANNELS[index % CHANNELS.length];

  return {
    id: 500000 + index,
    listingId: 400000 + (index % 100), // Reference properties from property generator
    guestName,
    guestEmail: guestName.toLowerCase().replace(' ', '.') + '@example.com',
    checkIn: checkInDate.toISOString().split('T')[0],
    checkOut: checkOutDate.toISOString().split('T')[0],
    nights,
    guests: (index % 6) + 1,
    totalPrice: (100 + (index * 50)) * nights,
    currency: 'EUR',
    status: index % 10 === 0 ? 'cancelled' : index % 5 === 0 ? 'completed' : 'confirmed',
    channel,
    createdAt: new Date(checkInDate.getTime() - 30 * 24 * 60 * 60 * 1000).toISOString(), // 30 days before check-in
    updatedAt: new Date(checkInDate.getTime() - 25 * 24 * 60 * 60 * 1000).toISOString(),
  };
}

/**
 * Generate multiple bookings
 *
 * @param count - Number of bookings to generate
 * @returns Array of booking objects
 */
export function generateBookings(count: number): Booking[] {
  return Array.from({ length: count }, (_, index) => generateBooking(index));
}
