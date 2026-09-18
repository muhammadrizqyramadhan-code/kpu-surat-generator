import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Generator Surat Resmi - KPU Provinsi Riau",
  description: "Sistem Otomatisasi Penyusunan Surat Resmi Berbasis Natural Language Processing — Komisi Pemilihan Umum Provinsi Riau",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="id">
      <body className="min-h-screen bg-slate-50 text-slate-900 antialiased">
        {children}
      </body>
    </html>
  );
}
