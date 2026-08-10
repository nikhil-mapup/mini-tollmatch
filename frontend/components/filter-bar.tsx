"use client";

import { useRouter } from "next/navigation";
import type { Filters, TypeCount } from "@/types";
import { withFilters } from "@/lib/url";

// The only client component in this MVP. Every change here pushes a new
// URL, which Next.js re-fetches server-side — there is no client-held copy
// of mismatch data to accidentally go stale. This is what makes the date
// range filter "re-query correctly": a filter change IS a navigation, not
// a client-side re-filter of already-loaded data.
export function FilterBar({
  filters,
  units,
  types,
}: {
  filters: Filters;
  units: string[];
  types: TypeCount[];
}) {
  const router = useRouter();

  function update(overrides: Partial<Filters>) {
    // Any filter change resets to page 1 — staying on page 5 of a
    // now-different result set would silently show the wrong rows.
    router.push(withFilters(filters, { ...overrides, page: undefined }));
  }

  const inputStyle =
    "rounded border border-line bg-white px-2 py-1.5 text-sm text-ink focus:border-gantry-600 focus:outline-none focus:ring-1 focus:ring-gantry-600";
  const labelStyle = "font-display text-xs font-semibold uppercase tracking-wide text-ink/60";

  return (
    <div className="flex flex-wrap items-end gap-4 rounded border border-line bg-white p-4 shadow-sm">
      <label className="flex flex-col gap-1">
        <span className={labelStyle}>Unit</span>
        <select
          className={inputStyle}
          value={filters.unit ?? ""}
          onChange={(e) => update({ unit: e.target.value || undefined })}
        >
          <option value="">All units</option>
          {units.map((u) => (
            <option key={u} value={u}>
              {u}
            </option>
          ))}
        </select>
      </label>

      <label className="flex flex-col gap-1">
        <span className={labelStyle}>Type</span>
        <select
          className={inputStyle}
          value={filters.type ?? ""}
          onChange={(e) => update({ type: e.target.value || undefined })}
        >
          <option value="">All types</option>
          {types.map((t) => (
            <option key={t.type} value={t.type}>
              {t.type} ({t.count})
            </option>
          ))}
        </select>
      </label>

      <label className="flex flex-col gap-1">
        <span className={labelStyle}>From</span>
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
        <span className={labelStyle}>To</span>
        <input
          type="date"
          className={inputStyle}
          value={filters.end?.slice(0, 10) ?? ""}
          onChange={(e) =>
            update({ end: e.target.value ? `${e.target.value}T23:59:59Z` : undefined })
          }
        />
      </label>

      {(filters.unit || filters.type || filters.start || filters.end) && (
        <button
          onClick={() => router.push("/")}
          className="text-sm font-medium text-brick-500 underline hover:text-brick-600"
        >
          Clear filters
        </button>
      )}
    </div>
  );
}
