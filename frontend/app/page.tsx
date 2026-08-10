import type { Filters } from "@/types";
import {
  getOverview,
  getCostOverview,
  getCostOverviewByCostCenter,
  getInvoiceOverview,
  getMismatchBreakdown,
  getTopUnits,
} from "@/lib/api";
import { DateRangeFilter } from "@/components/date-range-filter";
import { OverviewStrip } from "@/components/overview-strip";
import { CostOverviewCard } from "@/components/cost-overview-card";
import { CostOverviewByCostCenterCard } from "@/components/cost-overview-by-cost-center-card";
import { InvoiceOverviewCard } from "@/components/invoice-overview-card";
import { MismatchBreakdownPie } from "@/components/mismatch-breakdown-pie";
import { TopUnitsTable } from "@/components/top-units-table";

function parseFilters(searchParams: Record<string, string | string[] | undefined>): Filters {
  const get = (key: string) => {
    const v = searchParams[key];
    return Array.isArray(v) ? v[0] : v;
  };
  return { start: get("start"), end: get("end") };
}

export default async function DashboardPage({
  searchParams,
}: {
  searchParams: Record<string, string | string[] | undefined>;
}) {
  const filters = parseFilters(searchParams);

  const [overview, costOverview, costByCenter, invoiceOverview, breakdown, topUnits] =
    await Promise.all([
      getOverview(filters),
      getCostOverview(filters),
      getCostOverviewByCostCenter(filters),
      getInvoiceOverview(filters),
      getMismatchBreakdown(filters),
      getTopUnits(filters),
    ]);

  return (
    <div className="mx-auto max-w-6xl space-y-6 px-6 py-8">
      <DateRangeFilter filters={filters} />

      <OverviewStrip data={overview} />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <CostOverviewCard data={costOverview} />
        <InvoiceOverviewCard data={invoiceOverview} />
      </div>

      <CostOverviewByCostCenterCard data={costByCenter} />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <MismatchBreakdownPie data={breakdown.breakdown} />
        <TopUnitsTable units={topUnits.units} />
      </div>
    </div>
  );
}
