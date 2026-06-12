import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { ToastProvider } from "@/components/Toast";
import { NovusScript } from "@/components/NovusScript";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "ECHO — Institutional Memory for Engineering Teams",
  description: "Connect today's incident to the post-mortem your team wrote — and forgot — months ago.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={inter.variable}>
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="font-sans antialiased">
        <ToastProvider>
          <ErrorBoundary>
            <main>{children}</main>
          </ErrorBoundary>
        </ToastProvider>
        <NovusScript />
      </body>
    </html>
  );
}
