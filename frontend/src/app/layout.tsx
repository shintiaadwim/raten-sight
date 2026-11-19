import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "RetenSight – Dashboard Analitik Churn Pelanggan",
  description:
    "Dashboard Analitik Churn Pelanggan berbasis IBM Telco Customer Churn dataset. Didukung Logistic Regression, K-Means, dan Ridge Regression.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="id">
      <body className="antialiased">{children}</body>
    </html>
  );
}
