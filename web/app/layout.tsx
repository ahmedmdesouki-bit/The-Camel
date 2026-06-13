import type { Metadata } from "next";
import { Spectral, IBM_Plex_Sans, IBM_Plex_Mono } from "next/font/google";
import "./globals.css";

// The Camel three-voice type system (DESIGN-GUIDE.md §VISUAL FOUNDATIONS):
//   Spectral      — the brand voice: wordmark, headings, long-form prose (scholarly authority).
//   IBM Plex Sans — UI furniture: eyebrows, nav, table headers, micro-labels.
//   IBM Plex Mono — every figure that matters: tickers, money, hit-rates, verdicts, limit names.
// Loaded via next/font (self-hosted at build → no layout shift, no external CDN call at runtime).
const spectral = Spectral({
  subsets: ["latin"],
  weight: ["400", "600", "700"],
  variable: "--font-spectral",
  display: "swap",
});
const plexSans = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-plex-sans",
  display: "swap",
});
const plexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-plex-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "The Camel — operator window",
  description: "Private read-only/control window for The Camel (paper only).",
  robots: { index: false, follow: false }, // private app — keep it out of search engines
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${spectral.variable} ${plexSans.variable} ${plexMono.variable}`}>
      <body>{children}</body>
    </html>
  );
}
