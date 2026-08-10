import type { Filters } from "@/types";

// Takes the current filter state and a set of overrides, returns a query
// string with everything else preserved. Used by table sort links, the
// filter bar's client-side navigation, and pagination — one implementation,
// so different UI pieces can never disagree about how filters get encoded.
// basePath defaults to "/" for the main dashboard; the invoices page passes
// "/invoices" so navigation stays on the right route.
export function withFilters(
  current: Filters,
  overrides: Partial<Filters>,
  basePath = "/"
): string {
  const merged: Filters = { ...current, ...overrides };
  const params = new URLSearchParams();

  Object.entries(merged).forEach(([key, value]) => {
    if (value) params.set(key, value);
  });

  const query = params.toString();
  return query ? `${basePath}?${query}` : basePath;
}
