"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import type { Filters } from "@/types";
import { withFilters } from "@/lib/url";

// The known mismatch types are a small, fixed set — unlike units, which
// vary per fleet, these don't need a server round-trip to populate a
// dropdown. Matches the same six values reconciliation_service.py actually
// produces (see models/mismatch.py's type comment).
const MATCH_TYPES = ["matched", "max_toll", "misread", "duplicate", "unmatched", "unassigned"];

// Four exact-match filters. Post Date was removed from here deliberately —
// the From/To range above (DateRangeFilter) now filters this page by
// post_date directly, so a separate single-day field here would just be
// the same duplicate-control problem Unit/Transaction ID used to have
// against the free-text search box (also removed).
export function InvoiceExactFilters({ filters }: { filters: Filters }) {
  const router = useRouter();
  const [unit, setUnit] = useState(filters.unit ?? "");
  const [transactionId, setTransactionId] = useState(filters.transactionId ?? "");
  const [tagNo, setTagNo] = useState(filters.tagNo ?? "");
  const [matchType, setMatchType] = useState(filters.type ?? "");

  function apply() {
    router.push(
      withFilters(
        filters,
        {
          unit: unit || undefined,
          transactionId: transactionId || undefined,
          tagNo: tagNo || undefined,
          type: matchType || undefined,
          page: undefined,
        },
        "/invoices"
      )
    );
  }

  function clear() {
    setUnit("");
    setTransactionId("");
    setTagNo("");
    setMatchType("");
    router.push(
      withFilters(
        filters,
        {
          unit: undefined,
          transactionId: undefined,
          tagNo: undefined,
          type: undefined,
          page: undefined,
        },
        "/invoices"
      )
    );
  }

  const inputStyle =
    "rounded border border-line px-2 py-1.5 text-sm focus:border-gantry-600 focus:outline-none focus:ring-1 focus:ring-gantry-600";
  const labelStyle = "font-display text-xs font-semibold uppercase tracking-wide text-ink/60";
  const onEnter = (e: React.KeyboardEvent) => e.key === "Enter" && apply();

  const hasActiveFilter = Boolean(
    filters.unit || filters.transactionId || filters.tagNo || filters.type
  );

  return (
    <div className="flex flex-wrap items-end gap-3 rounded border border-line bg-white p-4 shadow-sm">
      <label className="flex flex-col gap-1">
        <span className={labelStyle}>Unit</span>
        <input
          type="text"
          value={unit}
          onChange={(e) => setUnit(e.target.value)}
          onKeyDown={onEnter}
          className={`${inputStyle} w-28`}
          placeholder="Exact unit"
        />
      </label>

      <label className="flex flex-col gap-1">
        <span className={labelStyle}>Transaction ID</span>
        <input
          type="text"
          value={transactionId}
          onChange={(e) => setTransactionId(e.target.value)}
          onKeyDown={onEnter}
          className={`${inputStyle} w-40`}
          placeholder="Exact txn ID"
        />
      </label>

      <label className="flex flex-col gap-1">
        <span className={labelStyle}>Tag/Plate ID</span>
        <input
          type="text"
          value={tagNo}
          onChange={(e) => setTagNo(e.target.value)}
          onKeyDown={onEnter}
          className={`${inputStyle} w-32`}
          placeholder="Exact tag ID"
        />
      </label>

      <label className="flex flex-col gap-1">
        <span className={labelStyle}>Match Type</span>
        <select
          value={matchType}
          onChange={(e) => setMatchType(e.target.value)}
          className={inputStyle}
        >
          <option value="">All types</option>
          {MATCH_TYPES.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
      </label>

      <button
        onClick={apply}
        className="rounded border border-gantry-600 px-3 py-1.5 text-sm font-medium text-gantry-700 hover:bg-gantry-50"
      >
        Apply
      </button>

      {hasActiveFilter && (
        <button onClick={clear} className="text-sm font-medium text-brick-500 underline hover:text-brick-600">
          Clear
        </button>
      )}
    </div>
  );
}