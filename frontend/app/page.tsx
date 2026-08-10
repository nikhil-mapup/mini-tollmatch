import type { Filters } from "@/types";
import { getMismatches, getMismatchTypes, getSummary, getUnits } from "@/lib/api";
import { SummaryCards } from "@/components/summary-cards";
import { FilterBar } from "@/components/filter-bar";
import { MismatchTable } from "@/components/mismatch-table";

// Filters live entirely in the URL. This page is a server component that
// reads searchParams, fetches fresh data on every render, and passes it
// down — there is no client-side data cache to fall out of sync. This is
// the core mechanism behind "date range filter must re-query correctly."
function parseFilters(searchParams: Record<string, string | string[] | undefined>): Filters {
  const get = (key: string) => {
    const v = searchParams[key];
    return Array.isArray(v) ? v[0] : v;
  };
  return {
    unit: get("unit"),
    type: get("type"),
    start: get("start"),
    end: get("end"),
    sort: get("sort"),
    order: get("order"),
    page: get("page"),
  };
}

export default async function DashboardPage({
  searchParams,
}: {
  searchParams: Record<string, string | string[] | undefined>;
}) {
  const filters = parseFilters(searchParams);

  // Summary, mismatches, units, and types are independent reads — fetch
  // them together rather than waterfalling one after another.
  const [summary, mismatches, unitsResult, typesResult] = await Promise.all([
    getSummary(filters),
    getMismatches(filters),
    getUnits(),
    getMismatchTypes(filters),
  ]);

  return (
    <div className="mx-auto max-w-6xl space-y-6 px-6 py-8">
      <FilterBar filters={filters} units={unitsResult.units} types={typesResult.types} />

      <SummaryCards summary={summary} />

      <MismatchTable data={mismatches} filters={filters} />
    </div>
  );
}
