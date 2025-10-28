/**
 * Financial report fixture generator
 *
 * Generates realistic (and oversized) financial report data for testing
 */

export interface FinancialReport {
  startDate: string;
  endDate: string;
  revenue: {
    total: number;
    byChannel: Record<string, number>;
    byMonth: Array<{ month: string; amount: number }>;
  };
  expenses: {
    total: number;
    byCategory: Record<string, number>;
    byMonth: Array<{ month: string; amount: number }>;
  };
  netIncome: number;
  occupancyRate: number;
  averageDailyRate: number;
  totalBookings: number;
  totalNights: number;
  detailedTransactions?: Array<{
    date: string;
    description: string;
    amount: number;
    category: string;
  }>;
}

/**
 * Generate a realistic financial report
 *
 * @param options - Configuration options
 * @returns Financial report object
 */
export function generateFinancialReport(options: {
  startDate?: string;
  endDate?: string;
  includeTransactions?: boolean;
  transactionCount?: number;
} = {}): FinancialReport {
  const {
    startDate = '2024-01-01',
    endDate = '2024-12-31',
    includeTransactions = false,
    transactionCount = 100,
  } = options;

  const revenue = {
    total: 125000,
    byChannel: {
      direct: 35000,
      airbnb: 45000,
      vrbo: 30000,
      'booking.com': 15000,
    },
    byMonth: Array.from({ length: 12 }, (_, i) => ({
      month: `2024-${String(i + 1).padStart(2, '0')}`,
      amount: 8000 + Math.random() * 4000,
    })),
  };

  const expenses = {
    total: 45000,
    byCategory: {
      cleaning: 15000,
      maintenance: 10000,
      utilities: 8000,
      commissions: 12000,
    },
    byMonth: Array.from({ length: 12 }, (_, i) => ({
      month: `2024-${String(i + 1).padStart(2, '0')}`,
      amount: 3000 + Math.random() * 2000,
    })),
  };

  const report: FinancialReport = {
    startDate,
    endDate,
    revenue,
    expenses,
    netIncome: revenue.total - expenses.total,
    occupancyRate: 0.75,
    averageDailyRate: 150,
    totalBookings: 250,
    totalNights: 833,
  };

  if (includeTransactions) {
    report.detailedTransactions = Array.from({ length: transactionCount }, (_, i) => ({
      date: `2024-${String(Math.floor(i / 30) + 1).padStart(2, '0')}-${String((i % 30) + 1).padStart(2, '0')}`,
      description: i % 3 === 0 ? 'Booking revenue' : i % 3 === 1 ? 'Cleaning expense' : 'Maintenance expense',
      amount: i % 3 === 0 ? 500 + Math.random() * 500 : -(100 + Math.random() * 200),
      category: i % 3 === 0 ? 'revenue' : i % 3 === 1 ? 'cleaning' : 'maintenance',
    }));
  }

  return report;
}

/**
 * Generate an oversized financial report to trigger preview mode
 *
 * This report should be large enough to exceed the token threshold
 * and trigger preview/summarization in the MCP server.
 *
 * @returns Large financial report (>50K tokens)
 */
export function generateLargeFinancialReport(): FinancialReport {
  return generateFinancialReport({
    startDate: '2020-01-01',
    endDate: '2024-12-31',
    includeTransactions: true,
    transactionCount: 10000, // 10,000 transactions should create ~50K+ token response
  });
}
