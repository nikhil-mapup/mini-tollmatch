// The small two-color bar icon shown before "Toll Match"/"Toll Mismatch"
// in the original product's cards — reused across CostOverviewCard,
// CostOverviewByCostCenterCard, and InvoiceOverviewCard rather than
// duplicated three times.
export function MatchMismatchBarIcon() {
  return (
    <div className="flex h-4 w-2.5 overflow-hidden rounded-sm">
      <div className="w-1/2 bg-moss-500" />
      <div className="w-1/2 bg-brick-500" />
    </div>
  );
}
