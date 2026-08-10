import Link from "next/link";
import type { Filters, MismatchListResponse } from "@/types";
import { withFilters } from "@/lib/url";
import { EmptyState } from "@/components/empty-state";

const SORTABLE_COLUMNS: { key: string; label: string }[] = [
  { key: "entry_time", label: "Date" },
  { key: "unit", label: "Unit" },
  { key: "mismatch_type", label: "Type" },
  { key: "billed_amount", label: "Billed" },
  { key: "delta_amount", label: "Delta" },
];

// Maps each mismatch type to a color that reflects what it actually means,
// not an arbitrary rotation: green for confirmed-correct, amber for the
// agency's known fallback-billing pattern, brick for a confirmed overcharge,
// and neutral gray for "we don't have enough data to judge yet."
const TYPE_STYLES: Record<string, string> = {
  reconciled: "bg-moss-100 text-moss-600",
  max_toll: "bg-caution-100 text-caution-600",
  misread: "bg-brick-100 text-brick-600",
  duplicate: "bg-brick-100 text-brick-600",
  unmatched: "bg-line text-ink/60",
  unassigned: "bg-line text-ink/60",
};

function typeStyle(type: string): string {
  return TYPE_STYLES[type] ?? "bg-line text-ink/60";
}

function formatCurrency(amount?: number): string {
  if (amount === undefined) return "—";
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(amount);
}

export function MismatchTable({
  data,
  filters,
}: {
  data: MismatchListResponse;
  filters: Filters;
}) {
  if (data.items.length === 0) {
    return <EmptyState message="No mismatches match these filters." />;
  }

  const currentSort = filters.sort ?? "entry_time";
  const currentOrder = filters.order ?? "desc";
  const totalPages = Math.max(1, Math.ceil(data.total / data.limit));

  return (
    <div className="overflow-hidden rounded border border-line bg-white shadow-sm">
      <table className="min-w-full divide-y divide-line text-sm">
        <thead className="bg-gantry-50">
          <tr>
            {SORTABLE_COLUMNS.map((col) => {
              const isActive = currentSort === col.key;
              const nextOrder = isActive && currentOrder === "asc" ? "desc" : "asc";
              return (
                <th
                  key={col.key}
                  className="px-4 py-2.5 text-left font-display text-xs font-semibold uppercase tracking-wide text-gantry-700"
                >
                  <Link
                    href={withFilters(filters, { sort: col.key, order: nextOrder, page: undefined })}
                    className="inline-flex items-center gap-1 hover:text-gantry-800"
                  >
                    {col.label}
                    {isActive && <span>{currentOrder === "asc" ? "↑" : "↓"}</span>}
                  </Link>
                </th>
              );
            })}
            <th className="px-4 py-2.5 text-left font-display text-xs font-semibold uppercase tracking-wide text-gantry-700">
              Transaction
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-line">
          {data.items.map((m, i) => (
            <tr key={m.transactionId} className={i % 2 === 1 ? "bg-paper/60" : undefined}>
              <td className="whitespace-nowrap px-4 py-2.5 text-ink/80">
                {new Date(m.entryTime).toLocaleDateString()}
              </td>
              <td className="whitespace-nowrap px-4 py-2.5 font-mono text-ink/80">{m.unit}</td>
              <td className="whitespace-nowrap px-4 py-2.5">
                <span
                  className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${typeStyle(m.mismatchType)}`}
                >
                  {m.mismatchType}
                </span>
              </td>
              <td className="whitespace-nowrap px-4 py-2.5 font-mono text-ink/80">
                {formatCurrency(m.billedAmount)}
              </td>
              <td className="whitespace-nowrap px-4 py-2.5 font-mono text-ink/80">
                {formatCurrency(m.deltaAmount)}
              </td>
              <td className="whitespace-nowrap px-4 py-2.5 font-mono text-xs text-ink/50">
                {m.transactionId}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="flex items-center justify-between border-t border-line bg-gantry-50 px-4 py-2.5 text-sm text-ink/70">
        <span>
          Page {data.page} of {totalPages} ({data.total.toLocaleString()} total)
        </span>
        <div className="flex gap-2">
          <PageLink filters={filters} page={data.page - 1} disabled={data.page <= 1} label="Prev" />
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
      href={withFilters(filters, { page: String(page) })}
      className="rounded px-2 py-1 font-medium text-gantry-700 hover:bg-gantry-100"
    >
      {label}
    </Link>
  );
}
