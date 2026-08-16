import Link from "next/link";
import { getSummary, getTrips } from "@/lib/api";
import { EmptyState } from "@/components/empty-state";

// "Unit view" step 2 — for the selected vehicle, list its trips and show
// which ones had mismatches. mismatchCount/mismatchTypes per row come from
// the Go backend's $lookup join against `mismatches` — no extra
// client-side computation, same principle as everywhere else: read what
// the backend already computed, don't recompute it here.
//
// The page-level total (added here) deliberately does NOT sum the
// per-trip mismatchCount values — most mismatches (unmatched, unassigned)
// never get attributed to a trip_id at all, so summing trip-level counts
// would silently undercount the unit's real total. getSummary({ unit })
// queries `mismatches` directly by unit, which is reliable regardless of
// whether a trip match was ever found.
export default async function UnitDetailPage({ params }: { params: { unit: string } }) {
  const unit = decodeURIComponent(params.unit);

  const [{ trips }, summary] = await Promise.all([
    getTrips(unit),
    getSummary({ unit }),
  ]);

  return (
    <div className="mx-auto max-w-6xl space-y-6 px-6 py-8">
      <div className="flex items-center justify-between">
        <h1 className="font-display text-xl font-semibold uppercase tracking-wide text-ink">
          Trips — <span className="font-mono">{unit}</span>
        </h1>
        <Link href="/units" className="text-sm font-medium text-gantry-700 hover:underline">
          ← All vehicles
        </Link>
      </div>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div className="rounded border border-line bg-white p-4 shadow-sm">
          <p className="font-display text-xs font-semibold uppercase tracking-wide text-ink/60">
            Total Mismatches
          </p>
          <p className="mt-1 font-mono text-2xl font-semibold text-brick-600">
            {summary.mismatchCount.toLocaleString()}
          </p>
        </div>
        <div className="rounded border border-line bg-white p-4 shadow-sm">
          <p className="font-display text-xs font-semibold uppercase tracking-wide text-ink/60">
            Mismatch $
          </p>
          <p className="mt-1 font-mono text-2xl font-semibold text-brick-600">
            {new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(
              summary.mismatchAmount
            )}
          </p>
        </div>
        <div className="rounded border border-line bg-white p-4 shadow-sm">
          <p className="font-display text-xs font-semibold uppercase tracking-wide text-ink/60">
            Total Toll Spend
          </p>
          <p className="mt-1 font-mono text-2xl font-semibold text-ink">
            {new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(
              summary.totalTollSpend
            )}
          </p>
        </div>
        <div className="rounded border border-line bg-white p-4 shadow-sm">
          <p className="font-display text-xs font-semibold uppercase tracking-wide text-ink/60">
            Top Mismatch Type
          </p>
          <p className="mt-1 font-mono text-2xl font-semibold text-ink">
            {summary.topType || "—"}
          </p>
        </div>
      </div>

      {trips.length === 0 ? (
        <EmptyState message="No trips found for this vehicle." />
      ) : (
        <div className="overflow-hidden rounded border border-line bg-white shadow-sm">
          <table className="min-w-full divide-y divide-line text-sm">
            <thead className="bg-gantry-50">
              <tr>
                <th className="px-4 py-2.5 text-left font-display text-xs font-semibold uppercase tracking-wide text-gantry-700">
                  Start
                </th>
                <th className="px-4 py-2.5 text-left font-display text-xs font-semibold uppercase tracking-wide text-gantry-700">
                  End
                </th>
                <th className="px-4 py-2.5 text-left font-display text-xs font-semibold uppercase tracking-wide text-gantry-700">
                  GPS Points
                </th>
                <th className="px-4 py-2.5 text-left font-display text-xs font-semibold uppercase tracking-wide text-gantry-700">
                  Mismatches (this trip)
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {trips.map((trip, i) => (
                <tr key={trip.tripId} className={i % 2 === 1 ? "bg-paper/60" : undefined}>
                  <td className="whitespace-nowrap px-4 py-2.5 text-ink/80">
                    {new Date(trip.startTime).toLocaleString()}
                  </td>
                  <td className="whitespace-nowrap px-4 py-2.5 text-ink/80">
                    {new Date(trip.endTime).toLocaleString()}
                  </td>
                  <td className="whitespace-nowrap px-4 py-2.5 font-mono text-ink/80">
                    {trip.gpsPointCount.toLocaleString()}
                  </td>
                  <td className="whitespace-nowrap px-4 py-2.5">
                    {trip.mismatchCount === 0 ? (
                      <span className="rounded-full bg-moss-100 px-2.5 py-0.5 text-xs font-medium text-moss-600">
                        Clean
                      </span>
                    ) : (
                      <span className="rounded-full bg-brick-100 px-2.5 py-0.5 text-xs font-medium text-brick-600">
                        {trip.mismatchCount} mismatch{trip.mismatchCount > 1 ? "es" : ""} —{" "}
                        {trip.mismatchTypes.join(", ")}
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {trips.length > 0 && summary.mismatchCount > trips.reduce((sum, t) => sum + t.mismatchCount, 0) && (
        <p className="text-sm text-ink/50">
          Note: the total above ({summary.mismatchCount}) is higher than the sum of per-trip counts
          shown in this table. That's expected — mismatches classified as &quot;unmatched&quot; or
          &quot;unassigned&quot; couldn&apos;t be attributed to a specific trip, so they count toward
          this unit&apos;s total but won&apos;t appear on any individual row above.
        </p>
      )}
    </div>
  );
}