/** @type {import('next').NextConfig} */
const nextConfig = {
  // Prints every server-side fetch() call to the terminal running
  // `npm run dev` — the only practical way to "see" these requests, since
  // page.tsx is a server component and its fetches never reach the
  // browser's Network tab at all.
  logging: {
    fetches: {
      fullUrl: true,
    },
  },
};
module.exports = nextConfig;
