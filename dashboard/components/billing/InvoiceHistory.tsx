'use client'

interface Invoice {
  id: string
  date: number
  amount: number
  currency: string
  status: string | null
  invoice_pdf: string | null
  hosted_invoice_url: string | null
  period_start: number | null
  period_end: number | null
  listing_count: number
}

interface InvoiceHistoryProps {
  invoices: Invoice[]
}

export default function InvoiceHistory({ invoices }: InvoiceHistoryProps) {
  if (invoices.length === 0) {
    return (
      <div className="rounded-lg bg-white shadow p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Invoice History</h2>
        <div className="text-center py-12">
          <p className="text-gray-500">No invoices yet.</p>
          <p className="text-sm text-gray-400 mt-2">
            Your billing history will appear here once you subscribe.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="rounded-lg bg-white shadow overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-200">
        <h2 className="text-lg font-medium text-gray-900">Invoice History</h2>
        <p className="mt-1 text-sm text-gray-500">
          View and download your past invoices.
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Date
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Period
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Listings
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Amount
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {invoices.map((invoice) => {
              const invoiceDate = new Date(invoice.date * 1000)
              const periodStart = invoice.period_start ? new Date(invoice.period_start * 1000) : null
              const periodEnd = invoice.period_end ? new Date(invoice.period_end * 1000) : null

              return (
                <tr key={invoice.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {invoiceDate.toLocaleDateString('en-US', {
                      month: 'short',
                      day: 'numeric',
                      year: 'numeric',
                    })}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {periodStart && periodEnd ? (
                      <>
                        {periodStart.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                        {' - '}
                        {periodEnd.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                      </>
                    ) : (
                      'N/A'
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {invoice.listing_count} listings
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-medium">
                    ${(invoice.amount / 100).toFixed(2)} {invoice.currency.toUpperCase()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        invoice.status === 'paid'
                          ? 'bg-green-100 text-green-800'
                          : invoice.status === 'open'
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {invoice.status || 'Unknown'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    {invoice.invoice_pdf && (
                      <a
                        href={invoice.invoice_pdf}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-900 mr-4"
                      >
                        PDF
                      </a>
                    )}
                    {invoice.hosted_invoice_url && (
                      <a
                        href={invoice.hosted_invoice_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-900"
                      >
                        View
                      </a>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
        <p className="text-xs text-gray-500">
          Invoices are generated monthly based on your listing count. Download PDFs for your records.
        </p>
      </div>
    </div>
  )
}
