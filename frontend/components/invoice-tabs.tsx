import Link from "next/link";
import type { Filters } from "@/types";
import { withFilters } from "@/lib/url";

// Only "All / Matched / Mismatched" — the original product's other tabs
// (Fleet Resolving, Fleet Resolved, Disputed, Refunded, Denied,
// Non-Actionable) all require a dispute/refund workflow that doesn't exist
// in this pipeline's data. Building them would mean fake, always-empty tabs.
const TABS: { key: string; label: string }[] = [
  { key: "all", label: "All" },
  { key: "matched", label: "Matched" },
  { key: "mismatched", label: "Mismatched" },
];

export function InvoiceTabs({ filters }: { filters: Filters }) {
  const activeTab = filters.tab ?? "all";

  return (
    <div className="flex gap-6 border-b border-line">
      {TABS.map((tab) => (
        <Link
          key={tab.key}
          href={withFilters(filters, { tab: tab.key, page: undefined }, "/invoices")}
          className={`border-b-2 pb-2 text-sm font-medium ${
            activeTab === tab.key
              ? "border-gantry-600 text-gantry-700"
              : "border-transparent text-ink/50 hover:text-ink"
          }`}
        >
          {tab.label}
        </Link>
      ))}
    </div>
  );
}
