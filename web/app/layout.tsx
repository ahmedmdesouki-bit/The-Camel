import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "The Camel — operator window",
  description: "Private read-only/control window for The Camel (paper only).",
  robots: { index: false, follow: false }, // private app — keep it out of search engines
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
