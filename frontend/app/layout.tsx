// frontend/app/layout.tsx

import "./globals.css";
import type { Metadata } from "next";
import { Analytics } from "@vercel/analytics/react";

export const metadata: Metadata = {
  title: "T79AI Console",
  description: "Autonomous DevT79 intelligence.",
  openGraph: {
    title: "T79AI",
    description: "Autonomous DevT79 intelligence.",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "T79AI",
      },
    ],
  },
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full">
      <body className="min-h-screen bg-neutral-950 text-neutral-50">
        {children}
        <Analytics />
      </body>
    </html>
  );
}
