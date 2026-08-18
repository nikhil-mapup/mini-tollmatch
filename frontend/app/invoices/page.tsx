import type { Filters } from "@/types";
import { getInvoices } from "@/lib/api";
import { DateRangeFilter } from "@/components/date-range-filter";
import { InvoiceTabs } from "@/components/invoice-tabs";
import { InvoiceExactFilters } from "@/components/invoice-exact-filters";
import { InvoicesTable } from "@/components/invoices-table";

function parseFilters(searchParams: Record<string, string | string[] | undefined>): Filters {
  const get = (key: string) => {
    const v = searchParams[key];
    return Array.isArray(v) ? v[0] : v;
  };
  return {
    unit: get("unit"),
    type: get("type"),
    start: get("start"),
    end: get("end"),
    sort: get("sort"),
    order: get("order"),
    page: get("page"),
    tab: get("tab"),
    transactionId: get("transactionId"),
    tagNo: get("tagNo"),
  };
}

export default async function InvoicesPage({
  searchParams,
}: {
  searchParams: Record<string, string | string[] | undefined>;
}) {
  const filters = parseFilters(searchParams);
  const tab = filters.tab ?? "all";

  const page = filters.page ? parseInt(filters.page, 10) : 1;
  // No free-text search param anymore — the exact filters below (Unit,
  // Transaction ID, Tag/Plate ID) replaced it; passing an empty string
  // keeps getInvoices' signature unchanged without reintroducing search.
  const invoices = await getInvoices({ ...filters, page: String(page) }, tab, "");

  return (
    <div className="mx-auto max-w-6xl space-y-6 px-6 py-8">
      <h1 className="font-display text-xl font-semibold uppercase tracking-wide text-ink">
        Invoices
      </h1>

      <InvoiceTabs filters={filters} />

      {/* From/To here filters by Post Date, not entry_time — deliberately,
          for this page specifically (see invoice_view_repository.go). */}
      <DateRangeFilter filters={filters} basePath="/invoices" />

      <InvoiceExactFilters filters={filters} />

      <InvoicesTable data={invoices} filters={filters} />
    </div>
  );
}