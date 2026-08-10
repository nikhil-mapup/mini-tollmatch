import type { Filters } from "@/types";
import { getInvoices } from "@/lib/api";
import { DateRangeFilter } from "@/components/date-range-filter";
import { InvoiceTabs } from "@/components/invoice-tabs";
import { InvoiceSearchBox } from "@/components/invoice-search-box";
import { InvoicesTable } from "@/components/invoices-table";

function parseFilters(searchParams: Record<string, string | string[] | undefined>): Filters {
  const get = (key: string) => {
    const v = searchParams[key];
    return Array.isArray(v) ? v[0] : v;
  };
  return {
    start: get("start"),
    end: get("end"),
    sort: get("sort"),
    order: get("order"),
    page: get("page"),
    tab: get("tab"),
    search: get("search"),
  };
}

export default async function InvoicesPage({
  searchParams,
}: {
  searchParams: Record<string, string | string[] | undefined>;
}) {
  const filters = parseFilters(searchParams);
  const tab = filters.tab ?? "all";
  const search = filters.search ?? "";

  const page = filters.page ? parseInt(filters.page, 10) : 1;
  const invoices = await getInvoices(
    { ...filters, page: String(page) },
    tab,
    search
  );

  return (
    <div className="mx-auto max-w-6xl space-y-6 px-6 py-8">
      <h1 className="font-display text-xl font-semibold uppercase tracking-wide text-ink">
        Invoices
      </h1>

      <InvoiceTabs filters={filters} />

      <div className="flex flex-wrap items-start justify-between gap-4">
        <DateRangeFilter filters={filters} basePath="/invoices" />
        <InvoiceSearchBox filters={filters} />
      </div>

      <InvoicesTable data={invoices} filters={filters} />
    </div>
  );
}
