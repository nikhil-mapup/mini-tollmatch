import type { SummaryResponse } from "@/types";
import { EmptyState } from "@/components/empty-state";

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(amount);
}

// Each card's left accent maps to what the metric actually means, not
// decoration: gantry green for money moving as expected, caution amber for
// the count of things needing review, brick red for money at stake, and a
// neutral ink accent for the "top type" label itself.
const CARD_ACCENTS = ["border-l-gantry-600", "border-l-caution-500", "border-l-brick-500", "border-l-ink"];

export function SummaryCards({ summary }: { summary: SummaryResponse }) {
  if (summary.mismatchCount === 0 && summary.totalTollSpend === 0) {
    return <EmptyState message="No toll activity for these filters yet." />;
  }

  const cards = [
    { label: "Total Toll Spend", value: formatCurrency(summary.totalTollSpend) },
    { label: "Mismatches", value: summary.mismatchCount.toLocaleString() },
    { label: "Mismatch $", value: formatCurrency(summary.mismatchAmount) },
    { label: "Top Type", value: summary.topType || "—" },
  ];

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
      {cards.map((card, i) => (
        <div
          key={card.label}
          className={`rounded border-l-4 border-y border-r border-line bg-white p-4 shadow-sm ${CARD_ACCENTS[i]}`}
        >
          <p className="font-display text-xs font-semibold uppercase tracking-wider text-ink/60">
            {card.label}
          </p>
          <p className="mt-1 font-mono text-2xl font-semibold text-ink">{card.value}</p>
        </div>
      ))}
    </div>
  );
}
