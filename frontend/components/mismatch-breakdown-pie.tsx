"use client";

import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts";
import type { MismatchBreakdownItem } from "@/types";
import { EmptyState } from "@/components/empty-state";

// Relabeled from the original product's "by Invoice Status" — that requires
// a dispute/refund lifecycle (Disputed/Refunded/Denied/etc) that doesn't
// exist anywhere in this pipeline. This shows the real breakdown we do
// have: mismatch_type, including "reconciled" for the clean invoices.
const COLORS: Record<string, string> = {
  reconciled: "#3D8361", // moss-500
  max_toll: "#E3A008", // caution-500
  misread: "#A6402C", // brick-500
  duplicate: "#8E3524", // brick-600
  unmatched: "#9CA3AF", // neutral gray
  unassigned: "#D1D5DB", // lighter neutral gray
};

function labelFor(type: string): string {
  return type
    .split("_")
    .map((w) => w[0].toUpperCase() + w.slice(1))
    .join(" ");
}

export function MismatchBreakdownPie({ data }: { data: MismatchBreakdownItem[] }) {
  // Defense in depth: the backend now guarantees a real array (never
  // null), but this component shouldn't crash even if that guarantee is
  // ever violated by a future change on the API side.
  const safeData = data ?? [];
  const total = safeData.reduce((sum, d) => sum + d.count, 0);

  return (
    <div className="rounded border border-line bg-white shadow-sm">
      <div className="border-b border-line px-4 py-3">
        <h2 className="font-display text-sm font-semibold uppercase tracking-wide text-ink">
          Tolls Breakdown by Mismatch Type
        </h2>
      </div>

      <div className="p-4">
        {total === 0 ? (
          <EmptyState message="No data to display" />
        ) : (
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={safeData}
                  dataKey="count"
                  nameKey="type"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={2}
                >
                  {safeData.map((entry) => (
                    <Cell key={entry.type} fill={COLORS[entry.type] ?? "#D1D5DB"} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value: number, name: string) => [value, labelFor(name)]}
                />
                <Legend formatter={(value: string) => labelFor(value)} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
}