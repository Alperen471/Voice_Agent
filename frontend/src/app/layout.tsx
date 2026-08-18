import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Toaster } from "sonner";
import { Nav } from "@/components/Nav";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Sesli Asistan Paneli",
  description: "Sesli asistanın sistem promptu, canlı görüşme ve konuşma geçmişi yönetim paneli",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="tr" className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col bg-background">
        <Nav />
        <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col px-6 py-8">{children}</main>
        <Toaster richColors position="top-right" />
      </body>
    </html>
  );
}
