import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "YC × WORKBank Postmortem — Stanford Zone Framework vs. Startup Outcomes",
  description:
    "Preregistered empirical test of Stanford SALT Lab's 4-zone framework on 1,223 YC companies (W24–F25). Primary hypotheses null; Red zone shuts down at 3.9% vs 9.0% elsewhere.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
