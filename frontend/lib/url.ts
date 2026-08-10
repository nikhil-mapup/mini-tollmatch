import type { Filters } from "@/types";

// Takes the current filter state and a set of overrides, returns a query
// string with everything else preserved. Used by both the table's sort
// links (server-rendered <a> tags) and the filter bar's client-side
// navigation — one implementation, so a link and a form submit can never
// disagree about how filters get encoded into the URL.
export function withFilters(current: Filters, overrides: Partial<Filters>): string {
  const merged: Filters = { ...current, ...overrides };
  const params = new URLSearchParams();

  Object.entries(merged).forEach(([key, value]) => {
    if (value) params.set(key, value);
  });

  const query = params.toString();
  return query ? `/?${query}` : "/";
}
