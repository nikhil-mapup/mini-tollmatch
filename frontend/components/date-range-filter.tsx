"use client";

import { useRouter } from "next/navigation";
import type { Filters } from "@/types";
import { withFilters } from "@/lib/url";

// Deliberately date-range only — none of the screenshots show a unit/type
// filter on the dashboard itself (that lives inside the Invoices table's
// search box instead). Same URL-is-the-state mechanism as before: a change
// here is a real navigation, not a client-side re-filter.
export function DateRangeFilter({
  filters,
  basePath = "/",
}: {
  filters: Filters;
  basePath?: string;
}) {
  const router = useRouter();

  function update(overrides: Partial<Filters>) {
    router.push(withFilters(filters, overrides, basePath));
  }

  const inputStyle =
    "rounded border border-line bg-white px-2 py-1.5 text-sm text-ink focus:border-gantry-600 focus:outline-none focus:ring-1 focus:ring-gantry-600";

  return (
    <div className="flex flex-wrap items-end gap-4 rounded border border-line bg-white p-4 shadow-sm">
      <label className="flex flex-col gap-1">
        <span className="font-display text-xs font-semibold uppercase tracking-wide text-ink/60">
          From
        </span>
        <input
          type="date"
          className={inputStyle}
          value={filters.start?.slice(0, 10) ?? ""}
          onChange={(e) =>
            update({ start: e.target.value ? `${e.target.value}T00:00:00Z` : undefined })
          }
        />
      </label>

      <label className="flex flex-col gap-1">
        <span className="font-display text-xs font-semibold uppercase tracking-wide text-ink/60">
          To
        </span>
        <input
          type="date"
          className={inputStyle}
          value={filters.end?.slice(0, 10) ?? ""}
          onChange={(e) =>
            update({ end: e.target.value ? `${e.target.value}T23:59:59Z` : undefined })
          }
        />
      </label>

      {(filters.start || filters.end) && (
        <button
          onClick={() => router.push(basePath)}
          className="text-sm font-medium text-brick-500 underline hover:text-brick-600"
        >
          Clear
        </button>
      )}
    </div>
  );
}
