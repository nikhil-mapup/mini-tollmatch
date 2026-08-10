import Link from "next/link";
import type { InvoiceOverviewResponse } from "@/types";
import { MatchMismatchBarIcon } from "@/components/match-mismatch-bar-icon";

export function InvoiceOverviewCard({ data }: { data: InvoiceOverviewResponse }) {
  return (
    <div className="flex h-full flex-col rounded border border-line bg-white shadow-sm">
      <div className="border-b border-line px-4 py-3">
        <h2 className="font-display text-sm font-semibold uppercase tracking-wide text-ink">
          Invoice Overview
        </h2>
      </div>

      <div className="flex-1 p-4">
        <MatchMismatchBarIcon />

        <div className="mt-3 flex items-center justify-between border-b border-line py-2.5">
          <div className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-sm bg-moss-500" />
            <span className="text-sm text-ink">Toll Match</span>
          </div>
          <span className="font-mono text-sm text-ink">
            {data.matchCount.toLocaleString()}{" "}
            <span className="text-ink/50">({data.matchPct.toFixed(0)}%)</span>
          </span>
        </div>

        <div className="flex items-center justify-between border-b border-line py-2.5">
          <div className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-sm bg-brick-500" />
            <span className="text-sm text-ink">Toll Mismatch</span>
          </div>
          <span className="font-mono text-sm text-ink">
            {data.mismatchCount.toLocaleString()}{" "}
            <span className="text-ink/50">({data.mismatchPct.toFixed(0)}%)</span>
          </span>
        </div>

        <div className="flex items-center justify-between py-2.5">
          <span className="text-sm font-medium text-ink">Total toll invoices</span>
          <span className="font-mono text-sm text-ink">{data.totalInvoices.toLocaleString()}</span>
        </div>
      </div>

      <Link
        href="/invoices"
        className="border-t border-line px-4 py-3 text-sm font-medium text-gantry-700 hover:underline"
      >
        More Details
      </Link>
    </div>
  );
}
