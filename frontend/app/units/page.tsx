import Link from "next/link";
import { getUnits } from "@/lib/api";
import { EmptyState } from "@/components/empty-state";

// "Unit view" step 1 — select a vehicle. Deliberately its own page rather
// than a dropdown-only interaction, so a unit has a real, linkable URL.
export default async function UnitsPage() {
  const { units } = await getUnits();

  return (
    <div className="mx-auto max-w-6xl space-y-6 px-6 py-8">
      <h1 className="font-display text-xl font-semibold uppercase tracking-wide text-ink">
        Select a vehicle
      </h1>

      {units.length === 0 ? (
        <EmptyState message="No units found in the data yet." />
      ) : (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {units.map((unit) => (
            <Link
              key={unit}
              href={`/units/${encodeURIComponent(unit)}`}
              className="rounded border border-line bg-white px-4 py-3 text-center font-mono text-sm text-ink shadow-sm hover:border-gantry-600 hover:text-gantry-700"
            >
              {unit}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
