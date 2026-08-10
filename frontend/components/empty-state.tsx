// Used everywhere a query can legitimately return nothing — no mismatches
// for these filters is a real, expected state, not an error. Per the hard
// requirement: no blank screens, ever. The route icon is the one small
// thematic touch here — restrained, not decorative for its own sake.
export function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded border border-dashed border-line bg-white py-16 text-center">
      <svg
        width="28"
        height="28"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        className="text-gantry-300"
        aria-hidden="true"
      >
        <path d="M4 20 L10 4 L14 20 L20 4" strokeLinecap="round" strokeLinejoin="round" />
        <circle cx="12" cy="12" r="1.4" fill="currentColor" stroke="none" />
      </svg>
      <p className="text-sm text-ink/50">{message}</p>
    </div>
  );
}
