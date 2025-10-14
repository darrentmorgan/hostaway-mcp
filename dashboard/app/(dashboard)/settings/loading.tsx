export default function Loading() {
  return (
    <div className="space-y-6">
      {/* Page header skeleton */}
      <div className="animate-pulse">
        <div className="h-8 bg-gray-200 rounded w-1/4 mb-2"></div>
        <div className="h-4 bg-gray-200 rounded w-1/2"></div>
      </div>

      {/* Settings sections skeleton */}
      <div className="space-y-6">
        {[1, 2, 3].map((i) => (
          <div key={i} className="rounded-lg bg-white shadow p-6 animate-pulse">
            <div className="h-6 bg-gray-200 rounded w-48 mb-4"></div>
            <div className="space-y-4">
              <div>
                <div className="h-4 bg-gray-200 rounded w-32 mb-2"></div>
                <div className="h-10 bg-gray-200 rounded w-full"></div>
              </div>
              <div>
                <div className="h-4 bg-gray-200 rounded w-40 mb-2"></div>
                <div className="h-10 bg-gray-200 rounded w-full"></div>
              </div>
            </div>
            <div className="mt-6 h-10 bg-gray-200 rounded w-32"></div>
          </div>
        ))}
      </div>
    </div>
  )
}
