"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import type { Filters } from "@/types";
import { withFilters } from "@/lib/url";

// Submits on Enter or button click, not on every keystroke — a fresh
// server-side query per character typed would be wasteful. This is the
// one place on the invoices page search is client-driven; everything else
// still follows the same URL-is-the-state navigation pattern.
export function InvoiceSearchBox({ filters }: { filters: Filters }) {
  const router = useRouter();
  const [value, setValue] = useState(filters.search ?? "");

  function submit() {
    router.push(withFilters(filters, { search: value || undefined, page: undefined }, "/invoices"));
  }

  return (
    <div className="flex gap-2">
      <input
        type="text"
        placeholder="Search Txn ID or Unit..."
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && submit()}
        className="w-64 rounded border border-line px-3 py-1.5 text-sm focus:border-gantry-600 focus:outline-none focus:ring-1 focus:ring-gantry-600"
      />
      <button
        onClick={submit}
        className="rounded border border-gantry-600 px-3 py-1.5 text-sm font-medium text-gantry-700 hover:bg-gantry-50"
      >
        Search
      </button>
    </div>
  );
}
