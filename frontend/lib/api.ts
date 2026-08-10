import type {
  Filters,
  MismatchListResponse,
  SummaryResponse,
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
  return params.toString();
}

function isPresent<T>(value: T | null | undefined): value is T {
  return value !== null && value !== undefined;
}

async function fetchJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`API request failed: ${res.status} ${res.statusText} (${path})`);
  }
  return res.json() as Promise<T>;
}

export function getSummary(filters: Filters): Promise<SummaryResponse> {
  return fetchJSON<Partial<SummaryResponse> | null>(`/api/summary?${buildQuery(filters)}`).then((data) => ({
    totalTollSpend: data?.totalTollSpend ?? 0,
    mismatchCount: data?.mismatchCount ?? 0,
    mismatchAmount: data?.mismatchAmount ?? 0,
    topType: data?.topType ?? "",
  }));
}

export function getMismatches(filters: Filters): Promise<MismatchListResponse> {
  return fetchJSON<Partial<MismatchListResponse> | null>(`/api/mismatches?${buildQuery(filters)}`).then((data) => ({
    items: (data?.items ?? []).filter(isPresent).map((item) => ({
      ...item,
      transactionId: item.transactionId ?? "",
      unit: item.unit ?? "",
      mismatchType: item.mismatchType ?? "",
      billedAmount: item.billedAmount ?? 0,
      entryTime: item.entryTime ?? "",
      status: item.status ?? "",
      detectedAt: item.detectedAt ?? "",
    })),
    total: data?.total ?? 0,
    page: data?.page ?? 1,
    limit: data?.limit ?? 20,
  }));
}

export function getUnits(): Promise<{ units: string[] }> {
  return fetchJSON<{ units?: (string | null)[] | null } | null>(`/api/units`).then((data) => ({
    units: (data?.units ?? []).filter((unit): unit is string => Boolean(unit)),
  }));
}

export function getMismatchTypes(filters: Filters): Promise<{ types: TypeCount[] }> {
  return fetchJSON<{ types?: (Partial<TypeCount> | null)[] | null } | null>(`/api/mismatch-types?${buildQuery(filters)}`).then(
    (data) => ({
      types: (data?.types ?? []).filter(isPresent).map((type) => ({
        type: type.type ?? "",
        count: type.count ?? 0,
      })),
    }),
  );
}
