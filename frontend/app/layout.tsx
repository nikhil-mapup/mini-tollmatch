import type { Metadata } from "next";
import "./globals.css";
import { Header } from "@/components/header";

export const metadata: Metadata = {
  title: "TollMatch",
  description: "Toll reconciliation dashboard",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        {/* Loaded via <link>, not next/font/google, so font fetching
            happens in the browser at runtime rather than during the build. */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700&family=Public+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body
        className="min-h-screen bg-paper font-sans text-ink"
        style={
          {
            "--font-display": '"Barlow Condensed", sans-serif',
            "--font-body": '"Public Sans", sans-serif',
            "--font-mono": '"IBM Plex Mono", monospace',
          } as React.CSSProperties
        }
      >
        <Header />
        {children}
      </body>
    </html>
  );
}
