import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "RetenSight – Dashboard Analitik Churn Pelanggan",
  description:
    "Eksplorasi pelanggan, prediksi churn, segmentasi, estimasi tagihan, dan evaluasi algoritma pada dataset IBM Telco.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="id">
      <body className="antialiased">{children}</body>
    </html>
  );
}
