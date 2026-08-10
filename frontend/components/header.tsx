// The one deliberate visual moment on the page: a solid header band styled
// after an overhead highway gantry sign, with a thin amber rule underneath
// echoing the reflective strip on toll signage. Everything below it stays
// quiet and functional — the restraint is the point.
export function Header() {
  return (
    <header className="border-b-2 border-caution-500 bg-gantry-700">
      <div className="mx-auto flex max-w-6xl items-baseline gap-3 px-6 py-5">
        <h1 className="font-display text-2xl font-semibold tracking-wide text-white">
          TollMatch
        </h1>
      </div>
    </header>
  );
}
