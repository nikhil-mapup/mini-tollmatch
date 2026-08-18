import type {
  CostOverviewByCostCenterResponse,
  CostOverviewResponse,
  Filters,
  InvoiceListResponse,
  InvoiceOverviewResponse,
  MismatchListResponse,
  OverviewResponse,
  SummaryResponse,
  Trip,
  TypeCount,
} from "@/types";

// Server-only env var — these fetches only ever run in server components,
// so this never needs the NEXT_PUBLIC_ prefix and never reaches the browser.
const API_URL = process.env.API_URL ?? "http://localhost:8080";

// Builds one query string from Filters, shared by every function below —
// summary and list must serialize filters identically, or they could
// silently query different data for what looks like the same filter state.
function buildQuery(filters: Filters): string {
  const params = new URLSearchParams();
  if (filters.unit) params.set("unit", filters.unit);
  if (filters.type) params.set("type", filters.type);
  if (filters.start) params.set("start", filters.start);
  if (filters.end) params.set("end", filters.end);
  if (filters.sort) params.set("sort", filters.sort);
  if (filters.order) params.set("order", filters.order);
  if (filters.page) params.set("page", filters.page);
  if (filters.transactionId) params.set("transactionId", filters.transactionId);
  if (filters.tagNo) params.set("tagNo", filters.tagNo);
  return params.toString();
}

async function fetchJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`API request failed: ${res.status} ${res.statusText} (${path})`);
  }
  return res.json() as Promise<T>;
}

export function getSummary(filters: Filters): Promise<SummaryResponse> {
  return fetchJSON(`/api/summary?${buildQuery(filters)}`);
}

export function getMismatches(filters: Filters): Promise<MismatchListResponse> {
  return fetchJSON(`/api/mismatches?${buildQuery(filters)}`);
}

export function getUnits(): Promise<{ units: string[] }> {
  return fetchJSON(`/api/units`);
}

export function getMismatchTypes(filters: Filters): Promise<{ types: TypeCount[] }> {
  return fetchJSON(`/api/mismatch-types?${buildQuery(filters)}`);
}

export function getTrips(unit: string): Promise<{ trips: Trip[] }> {
  return fetchJSON(`/api/trips?unit=${encodeURIComponent(unit)}`);
}

// --- Screenshot-matched dashboard endpoints ---

export function getOverview(filters: Filters): Promise<OverviewResponse> {
  return fetchJSON(`/api/overview?${buildQuery(filters)}`);
}

export function getCostOverview(filters: Filters): Promise<CostOverviewResponse> {
  return fetchJSON(`/api/cost-overview?${buildQuery(filters)}`);
}

export function getCostOverviewByCostCenter(
  filters: Filters
): Promise<CostOverviewByCostCenterResponse> {
  return fetchJSON(`/api/cost-overview/by-cost-center?${buildQuery(filters)}`);
}

export function getInvoiceOverview(filters: Filters): Promise<InvoiceOverviewResponse> {
  return fetchJSON(`/api/invoice-overview?${buildQuery(filters)}`);
}

export function getMismatchBreakdown(
  filters: Filters
): Promise<{ breakdown: { type: string; count: number }[] }> {
  return fetchJSON(`/api/mismatch-breakdown?${buildQuery(filters)}`);
}

export function getTopUnits(filters: Filters, limit = 10): Promise<{ units: { unit: string; tollsPaid: number; tollsMismatch: number }[] }> {
  return fetchJSON(`/api/top-units?${buildQuery(filters)}&limit=${limit}`);
}

export function getInvoices(
  filters: Filters,
  tab: string,
  search: string
): Promise<InvoiceListResponse> {
  const params = new URLSearchParams(buildQuery(filters));
  params.set("tab", tab);
  if (search) params.set("search", search);
  return fetchJSON(`/api/invoices?${params.toString()}`);
}