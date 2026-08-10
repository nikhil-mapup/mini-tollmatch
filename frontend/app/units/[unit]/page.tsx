import Link from "next/link";
import { getTrips } from "@/lib/api";
import { EmptyState } from "@/components/empty-state";

// "Unit view" step 2 — for the selected vehicle, list its trips and show
// which ones had mismatches. mismatchCount/mismatchTypes come from the
// Go backend's $lookup join against `mismatches` — no extra client-side
// computation, same principle as everywhere else: read what the backend
// already computed, don't recompute it here.
export default async function UnitDetailPage({ params }: { params: { unit: string } }) {
  const unit = decodeURIComponent(params.unit);
  const { trips } = await getTrips(unit);

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
                  Mismatches
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
    </div>
  );
}
