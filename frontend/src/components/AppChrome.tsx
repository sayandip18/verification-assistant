"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth";

export function AppChrome({ children }: { children: React.ReactNode }) {
  const { officer, ready, logout } = useAuth();
  const pathname = usePathname();

  if (!ready) {
    return <p className="px-4 py-8 text-sm text-ink/60">Loading session…</p>;
  }

  if (pathname === "/login") {
    return <>{children}</>;
  }

  if (!officer) {
    return <p className="px-4 py-8 text-sm text-ink/60">Redirecting to sign in…</p>;
  }

  return (
    <>
      <header className="border-b border-emerald-900/10 bg-forest text-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
          <Link href="/" className="font-semibold tracking-tight">
            BLLRO Mutation Assistant
          </Link>
          <nav className="flex items-center gap-4 text-sm text-emerald-100">
            <Link href="/" className="hover:text-white">
              Work queue
            </Link>
            <Link href="/applications/new" className="hover:text-white">
              New intake
            </Link>
            <span className="hidden text-emerald-50 sm:inline">{officer.full_name}</span>
            <button type="button" onClick={() => logout()} className="rounded border border-white/30 px-2 py-1 hover:bg-white/10">
              Sign out
            </button>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-8">{children}</main>
    </>
  );
}
