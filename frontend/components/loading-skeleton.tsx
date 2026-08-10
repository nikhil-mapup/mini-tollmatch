// Rendered automatically by Next.js (via app/loading.tsx) while the
// dashboard's server-side fetches are in flight — never a blank screen
// during load, matching the same "no blank screens" requirement that
// EmptyState covers for legitimately-empty results.
export function LoadingSkeleton() {
  return (
    <div className="mx-auto max-w-6xl space-y-6 px-6 py-8">
      <div className="h-16 animate-pulse rounded border border-line bg-white" />
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="h-20 animate-pulse rounded border border-line bg-white" />
        ))}
      </div>
      <div className="h-64 animate-pulse rounded border border-line bg-white" />
    </div>
  );
}
