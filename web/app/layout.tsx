import type { Metadata } from "next";
import { Cinzel, Montserrat, IBM_Plex_Mono } from "next/font/google";
import "./globals.css";

// The Camel brand type system (BRAND GUIDELINES p4 — Typography):
//   Cinzel (Display) — PRIMARY face: wordmark, headlines, display figures (elegant, authoritative, timeless).
//   Montserrat       — SUPPORTING face: body, UI furniture, labels, captions (clean, modern, highly legible).
//   IBM Plex Mono    — the functional data voice for tabular figures (tickers, money, hit-rates, ledger).
//                      The brand sheet specifies only the two faces above; the operator view needs tabular
//                      number alignment, so we keep a mono as a third, purely-functional voice.
// Loaded via next/font (self-hosted at build → no layout shift, no runtime CDN call).
const cinzel = Cinzel({
  subsets: ["latin"],
  weight: ["400", "600", "700"],
  variable: "--font-cinzel",
  display: "swap",
});
const montserrat = Montserrat({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-montserrat",
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
    <html lang="en" className={`${cinzel.variable} ${montserrat.variable} ${plexMono.variable}`}>
      <body>{children}</body>
    </html>
  );
}
