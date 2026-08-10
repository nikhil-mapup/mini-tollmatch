import Link from "next/link";

// The one deliberate visual moment on the page: a solid header band styled
// after an overhead highway gantry sign, with a thin amber rule underneath
// echoing the reflective strip on toll signage. Everything below it stays
// quiet and functional — the restraint is the point.
export function Header() {
  return (
    <header className="border-b-2 border-caution-500 bg-gantry-700">
      <div className="mx-auto flex max-w-6xl items-baseline gap-6 px-6 py-5">
        <div className="flex items-baseline gap-3">
          <h1 className="font-display text-2xl font-semibold uppercase tracking-wide text-white">
            TollMatch
          </h1>
          <span className="font-sans text-sm text-gantry-100">Reconciliation</span>
        </div>
        <nav className="flex gap-4 font-display text-sm font-medium uppercase tracking-wide text-gantry-100">
          <Link href="/" className="hover:text-white">
            Dashboard
          </Link>
          <Link href="/invoices" className="hover:text-white">
            Invoices
          </Link>
          <Link href="/units" className="hover:text-white">
            Vehicles
          </Link>
        </nav>
      </div>
    </header>
  );
}
