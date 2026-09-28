import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MeetingIQ — AI Meeting Intelligence",
  description:
    "An AI meeting-preparation agent that remembers the history of professional relationships and uses persistent memory to prepare you for future meetings.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="antialiased">{children}</body>
    </html>
  );
}
