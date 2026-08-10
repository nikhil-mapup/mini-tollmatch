import Link from "next/link";
import { EmptyState } from "@/components/empty-state";

interface TopUnitRow {
  unit: string;
  tollsPaid: number;
  tollsMismatch: number;
}

function currency(n: number): string {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(n);
}

export function TopUnitsTable({ units }: { units: TopUnitRow[] }) {
  return (
    <div className="rounded border border-line bg-white shadow-sm">
      <div className="border-b border-line px-4 py-3">
        <h2 className="font-display text-sm font-semibold uppercase tracking-wide text-ink">
          Top Units by Mismatch
        </h2>
      </div>

      {units.length === 0 ? (
        <div className="p-4">
          <EmptyState message="No data to display" />
        </div>
      ) : (
        <table className="min-w-full divide-y divide-line text-sm">
          <thead className="bg-gantry-50">
            <tr>
              <th className="px-4 py-2.5 text-left font-display text-xs font-semibold uppercase tracking-wide text-gantry-700">
                Unit
              </th>
              <th className="px-4 py-2.5 text-right font-display text-xs font-semibold uppercase tracking-wide text-gantry-700">
                Tolls Paid
              </th>
              <th className="px-4 py-2.5 text-right font-display text-xs font-semibold uppercase tracking-wide text-gantry-700">
                Tolls Mismatch
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {units.map((u) => (
              <tr key={u.unit}>
                <td className="whitespace-nowrap px-4 py-2.5 font-mono text-ink">
                  <Link
                    href={`/units/${encodeURIComponent(u.unit)}`}
                    className="hover:text-gantry-700 hover:underline"
                  >
                    {u.unit}
                  </Link>
                </td>
                <td className="whitespace-nowrap px-4 py-2.5 text-right font-mono text-ink/80">
                  {currency(u.tollsPaid)}
                </td>
                <td className="whitespace-nowrap px-4 py-2.5 text-right font-mono text-brick-600">
                  {currency(u.tollsMismatch)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
