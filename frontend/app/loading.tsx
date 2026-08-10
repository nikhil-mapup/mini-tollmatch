import { LoadingSkeleton } from "@/components/loading-skeleton";

// Next.js automatically wraps page.tsx in a Suspense boundary using this
// file as the fallback — shown while the server-side fetches in page.tsx
// are in flight. No manual loading state needed in the page itself.
export default function Loading() {
  return <LoadingSkeleton />;
}
