import type { OverviewResponse } from "@/types";

function currency(n: number): string {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(n);
}

// Matches screenshot 1 exactly: Vehicles | Tolls Paid | Tolls Expected |
// Tolls Overpaid (%) | Tolls Refunded. Refunded is always $0 here — see
// types.ts, there's no refund/dispute data anywhere in this pipeline.
export function OverviewStrip({ data }: { data: OverviewResponse }) {
  const stats = [
    { label: "Vehicles", value: data.vehicles.toLocaleString(), color: "text-gantry-700" },
    { label: "Tolls Paid", value: currency(data.tollsPaid), color: "text-gantry-700" },
    { label: "Tolls Expected", value: currency(data.tollsExpected), color: "text-gantry-700" },
    {
      label: "Tolls Overpaid",
      value: `${currency(data.tollsOverpaid)} (${data.overpaidPct.toFixed(1)}%)`,
      color: "text-caution-600",
    },
    { label: "Tolls Refunded", value: currency(data.tollsRefunded), color: "text-moss-600" },
  ];

  return (
    <div className="grid grid-cols-2 gap-6 rounded border border-line bg-white p-6 shadow-sm sm:grid-cols-5">
      {stats.map((s) => (
        <div key={s.label} className="text-center">
          <p className={`font-mono text-2xl font-semibold ${s.color}`}>{s.value}</p>
          <p className="mt-1 text-sm text-ink/60">{s.label}</p>
        </div>
      ))}
    </div>
  );
}
