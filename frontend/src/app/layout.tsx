import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "BLLRO Mutation Assistant",
  description: "Workflow management for land mutation and verification officers",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="border-b border-emerald-900/10 bg-forest text-white">
          <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
            <Link href="/" className="font-semibold tracking-tight">
              BLLRO Mutation Assistant
            </Link>
            <nav className="flex gap-4 text-sm text-emerald-100">
              <Link href="/" className="hover:text-white">
                Work queue
              </Link>
              <Link href="/applications/new" className="hover:text-white">
                New intake
              </Link>
            </nav>
          </div>
        </header>
        <main className="mx-auto max-w-6xl px-4 py-8">{children}</main>
      </body>
    </html>
  );
}
