import Link from "next/link";
import type { Filters, InvoiceListResponse } from "@/types";
import { withFilters } from "@/lib/url";
import { EmptyState } from "@/components/empty-state";

// Columns kept: Txn ID, Unit, Tolls paid, Expected, Overpaid, Match type,
// Invoice status, Trip details, Tag/Plate ID, Class, Entry — everything
// screenshot 7 shows that we actually have real data for.
//
// Columns deliberately NOT built: Map (needs a GPS trace/polyline we don't
// serve from this endpoint), Export, Create Dispute Request, Open in
// TollPay, Enable Edit Invoices, Match Type filter dropdown — none of these
// have real backing functionality here, per the request to skip them.
const SORTABLE_COLUMNS: { key: string; label: string }[] = [
  { key: "entry_time", label: "Entry" },
  { key: "unit", label: "Unit" },
  { key: "billed_amount", label: "Tolls paid" },
  { key: "delta_amount", label: "Overpaid" },
  { key: "mismatch_type", label: "Match type" },
];

const TYPE_STYLES: Record<string, string> = {
  matched: "bg-moss-100 text-moss-600",
  max_toll: "bg-caution-100 text-caution-600",
  misread: "bg-brick-100 text-brick-600",
  duplicate: "bg-brick-100 text-brick-600",
  unmatched: "bg-line text-ink/60",
  unassigned: "bg-line text-ink/60",
};

function currency(n?: number): string {
  if (n === undefined) return "—";
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(n);
}

export function InvoicesTable({ data, filters }: { data: InvoiceListResponse; filters: Filters }) {
  if (data.items.length === 0) {
    return <EmptyState message="No data to display" />;
  }

  const currentSort = filters.sort ?? "entry_time";
  const currentOrder = filters.order ?? "desc";
  const totalPages = Math.max(1, Math.ceil(data.total / data.limit));

  return (
    <div className="overflow-hidden rounded border border-line bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-line text-sm">
          <thead className="bg-gantry-50">
            <tr>
              {SORTABLE_COLUMNS.map((col) => {
                const isActive = currentSort === col.key;
                const nextOrder = isActive && currentOrder === "asc" ? "desc" : "asc";
                return (
                  <th
                    key={col.key}
                    className="whitespace-nowrap px-4 py-2.5 text-left font-display text-xs font-semibold uppercase tracking-wide text-gantry-700"
                  >
                    <Link
                      href={withFilters(
                        filters,
                        { sort: col.key, order: nextOrder, page: undefined },
                        "/invoices"
                      )}
                      className="inline-flex items-center gap-1 hover:text-gantry-800"
                    >
                      {col.label}
                      {isActive && <span>{currentOrder === "asc" ? "↑" : "↓"}</span>}
                    </Link>
                  </th>
                );
              })}
              <th className="whitespace-nowrap px-4 py-2.5 text-left font-display text-xs font-semibold uppercase tracking-wide text-gantry-700">
                Expected
              </th>
              <th className="whitespace-nowrap px-4 py-2.5 text-left font-display text-xs font-semibold uppercase tracking-wide text-gantry-700">
                Status
              </th>
              <th className="whitespace-nowrap px-4 py-2.5 text-left font-display text-xs font-semibold uppercase tracking-wide text-gantry-700">
                Trip details
              </th>
              <th className="whitespace-nowrap px-4 py-2.5 text-left font-display text-xs font-semibold uppercase tracking-wide text-gantry-700">
                Post Date
              </th>
              <th className="whitespace-nowrap px-4 py-2.5 text-left font-display text-xs font-semibold uppercase tracking-wide text-gantry-700">
                Tag/Plate ID
              </th>
              <th className="whitespace-nowrap px-4 py-2.5 text-left font-display text-xs font-semibold uppercase tracking-wide text-gantry-700">
                Class
              </th>
              <th className="whitespace-nowrap px-4 py-2.5 text-left font-display text-xs font-semibold uppercase tracking-wide text-gantry-700">
                Txn ID
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {data.items.map((row, i) => (
              <tr key={row.transactionId} className={i % 2 === 1 ? "bg-paper/60" : undefined}>
                <td className="whitespace-nowrap px-4 py-2.5 text-ink/80">
                  {new Date(row.entryTime).toLocaleString()}
                </td>
                <td className="whitespace-nowrap px-4 py-2.5 font-mono text-ink/80">
                  <Link
                    href={`/units/${encodeURIComponent(row.unit)}`}
                    className="hover:text-gantry-700 hover:underline"
                  >
                    {row.unit}
                  </Link>
                </td>
                <td className="whitespace-nowrap px-4 py-2.5 font-mono text-ink/80">
                  {currency(row.tollsPaid)}
                </td>
                <td className="whitespace-nowrap px-4 py-2.5 font-mono text-ink/80">
                  {currency(row.overpaid)}
                </td>
                <td className="whitespace-nowrap px-4 py-2.5">
                  <span
                    className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                      TYPE_STYLES[row.matchType] ?? "bg-line text-ink/60"
                    }`}
                  >
                    {row.matchType}
                  </span>
                </td>
                <td className="whitespace-nowrap px-4 py-2.5 font-mono text-ink/80">
                  {currency(row.expected)}
                </td>
                <td className="whitespace-nowrap px-4 py-2.5 text-ink/80">{row.status}</td>
                <td className="whitespace-nowrap px-4 py-2.5">
                  {row.tripId ? (
                    <Link
                      href={`/units/${encodeURIComponent(row.unit)}`}
                      className="text-gantry-700 hover:underline"
                    >
                      View
                    </Link>
                  ) : (
                    <span className="text-ink/30">—</span>
                  )}
                </td>
                <td className="whitespace-nowrap px-4 py-2.5 text-ink/80">
                  {row.postDate ? new Date(row.postDate).toLocaleDateString() : "—"}
                </td>
                <td className="whitespace-nowrap px-4 py-2.5 text-ink/80">{row.tagNo ?? "—"}</td>
                <td className="whitespace-nowrap px-4 py-2.5 text-ink/80">{row.tollClass ?? "—"}</td>
                <td className="whitespace-nowrap px-4 py-2.5 font-mono text-xs text-ink/50">
                  {row.transactionId}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between border-t border-line bg-gantry-50 px-4 py-2.5 text-sm text-ink/70">
        <span>
          Rows {(data.page - 1) * data.limit + 1}–{Math.min(data.page * data.limit, data.total)} of{" "}
          {data.total.toLocaleString()}
        </span>
        <div className="flex gap-2">
          <PageLink filters={filters} page={data.page - 1} disabled={data.page <= 1} label="Prev" />
          <span>
            Page {data.page} of {totalPages}
          </span>
          <PageLink
            filters={filters}
            page={data.page + 1}
            disabled={data.page >= totalPages}
            label="Next"
          />
        </div>
      </div>
    </div>
  );
}

function PageLink({
  filters,
  page,
  disabled,
  label,
}: {
  filters: Filters;
  page: number;
  disabled: boolean;
  label: string;
}) {
  if (disabled) {
    return <span className="cursor-not-allowed px-2 py-1 text-ink/25">{label}</span>;
  }
  return (
    <Link
      href={withFilters(filters, { page: String(page) }, "/invoices")}
      className="rounded px-2 py-1 font-medium text-gantry-700 hover:bg-gantry-100"
    >
      {label}
    </Link>
  );
}