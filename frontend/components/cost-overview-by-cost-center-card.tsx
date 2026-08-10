"use client";

import { useState } from "react";
import type { CostOverviewByCostCenterResponse } from "@/types";
import { MatchMismatchBarIcon } from "@/components/match-mismatch-bar-icon";
import { EmptyState } from "@/components/empty-state";

function currency(n: number): string {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(n);
}

// The only client component among the new cards — needed for the table's
// search box, which filters an already-fetched, typically-small list of
// cost centers. A server round-trip for filtering a handful of rows would
// be needless — this is a plain client-side text filter, not a fresh query.
export function CostOverviewByCostCenterCard({
  data,
}: {
  data: CostOverviewByCostCenterResponse;
}) {
  const [search, setSearch] = useState("");

  const filteredRows = data.rows.filter((r) =>
    r.costCenter.toLowerCase().includes(search.toLowerCase())
  );

  const totals = data.rows.reduce(
    (acc, r) => ({
      totalTxns: acc.totalTxns + r.totalTxns,
      units: acc.units + r.units,
      totalTollsPaid: acc.totalTollsPaid + r.totalTollsPaid,
      tollsOverpaid: acc.tollsOverpaid + r.tollsOverpaid,
    }),
    { totalTxns: 0, units: 0, totalTollsPaid: 0, tollsOverpaid: 0 }
  );

  return (
    <div className="rounded border border-line bg-white shadow-sm">
      <div className="border-b border-line px-4 py-3">
        <h2 className="font-display text-sm font-semibold uppercase tracking-wide text-ink">
          Cost Overview by Cost Center
        </h2>
      </div>

      <div className="p-4">
        <MatchMismatchBarIcon />

        <div className="mt-3 flex items-center justify-between border-b border-line py-2.5">
          <div className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-sm bg-moss-500" />
            <span className="text-sm text-ink">Toll Match</span>
          </div>
          <span className="font-mono text-sm text-ink">
            {currency(data.matchAmount)}{" "}
            <span className="text-ink/50">({data.matchPct.toFixed(2)}%)</span>
          </span>
        </div>

        <div className="flex items-center justify-between border-b border-line py-2.5">
          <div className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-sm bg-brick-500" />
            <span className="text-sm text-ink">Toll Mismatch</span>
          </div>
          <span className="font-mono text-sm text-ink">
            {currency(data.mismatchAmount)}{" "}
            <span className="text-ink/50">({data.mismatchPct.toFixed(2)}%)</span>
          </span>
        </div>

        <div className="flex items-center justify-end py-3">
          <input
            type="text"
            placeholder="Search cost center..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="rounded border border-line px-2 py-1 text-sm focus:border-gantry-600 focus:outline-none focus:ring-1 focus:ring-gantry-600"
          />
        </div>

        {data.rows.length === 0 ? (
          <EmptyState message="No cost center data for these filters." />
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-line text-left font-display text-xs font-semibold uppercase tracking-wide text-gantry-700">
                  <th className="py-2">Cost center</th>
                  <th className="py-2 text-right">Total txns</th>
                  <th className="py-2 text-right">Units</th>
                  <th className="py-2 text-right">Total tolls paid</th>
                  <th className="py-2 text-right">Tolls overpaid</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {filteredRows.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-6 text-center text-ink/50">
                      No cost center found
                    </td>
                  </tr>
                ) : (
                  filteredRows.map((row) => (
                    <tr key={row.costCenter}>
                      <td className="py-2 text-ink">{row.costCenter}</td>
                      <td className="py-2 text-right font-mono text-ink/80">{row.totalTxns}</td>
                      <td className="py-2 text-right font-mono text-ink/80">{row.units}</td>
                      <td className="py-2 text-right font-mono text-ink/80">
                        {currency(row.totalTollsPaid)}
                      </td>
                      <td className="py-2 text-right font-mono text-ink/80">
                        {currency(row.tollsOverpaid)}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
              <tfoot>
                <tr className="border-t-2 border-line font-medium text-ink">
                  <td className="py-2">Total</td>
                  <td className="py-2 text-right font-mono">{totals.totalTxns}</td>
                  <td className="py-2 text-right font-mono">{totals.units}</td>
                  <td className="py-2 text-right font-mono">{currency(totals.totalTollsPaid)}</td>
                  <td className="py-2 text-right font-mono">{currency(totals.tollsOverpaid)}</td>
                </tr>
              </tfoot>
            </table>
          </div>
        )}

        <div className="mt-3 flex items-center justify-between border-t border-line py-2.5">
          <span className="text-sm font-medium text-ink">Total units</span>
          <span className="font-mono text-sm text-ink">{data.totalUnits.toLocaleString()}</span>
        </div>
        <div className="flex items-center justify-between py-2.5">
          <span className="text-sm font-medium text-ink">Paid tolls</span>
          <span className="font-mono text-sm text-ink">{currency(data.paidTolls)}</span>
        </div>
      </div>
    </div>
  );
}
