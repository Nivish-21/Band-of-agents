import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ClaimBand — cross-framework multi-agent claim adjudication",
  description:
    "Four specialist AI agents, three frameworks, two vendors — collaborating in one Band room to adjudicate an auto-insurance claim. APPROVE / DENY / ESCALATE-to-human, from real captured runs.",
  openGraph: {
    title: "ClaimBand",
    description:
      "Four AI agents across three frameworks adjudicate an insurance claim in one Band room.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
