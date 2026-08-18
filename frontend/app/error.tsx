"use client";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="mx-auto flex max-w-6xl flex-col items-center justify-center gap-4 px-6 py-24 text-center">
      <p className="font-display text-lg font-semibold uppercase tracking-wide text-brick-500">
        Couldn&apos;t load the dashboard
      </p>
      <p className="max-w-md text-sm text-ink/60">{error.message}</p>
      <button
        onClick={reset}
        className="rounded border border-gantry-600 px-4 py-1.5 text-sm font-medium text-gantry-700 hover:bg-gantry-50"
      >
        Try again
      </button>
    </main>
  );
}
