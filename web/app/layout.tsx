import type { Metadata } from "next";
import { Bricolage_Grotesque, Archivo, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const bricolage = Bricolage_Grotesque({
  subsets: ["latin"],
  weight: ["600", "700", "800"],
  variable: "--font-bricolage",
  display: "swap",
});

const archivo = Archivo({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-archivo",
  display: "swap",
});

const jetbrains = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-jetbrains",
  display: "swap",
});

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
      <body
        className={`${bricolage.variable} ${archivo.variable} ${jetbrains.variable}`}
      >
        {children}
      </body>
    </html>
  );
}
