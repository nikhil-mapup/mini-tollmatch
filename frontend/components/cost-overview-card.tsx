import type { CostOverviewResponse } from "@/types";
import { MatchMismatchBarIcon } from "@/components/match-mismatch-bar-icon";

function currency(n: number): string {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(n);
}

export function CostOverviewCard({ data }: { data: CostOverviewResponse }) {
  return (
    <div className="rounded border border-line bg-white shadow-sm">
      <div className="border-b border-line px-4 py-3">
        <h2 className="font-display text-sm font-semibold uppercase tracking-wide text-ink">
          Cost Overview
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
            {currency(data.matchAmount)} <span className="text-ink/50">({data.matchPct.toFixed(2)}%)</span>
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

        <div className="flex items-center justify-between py-2.5">
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
