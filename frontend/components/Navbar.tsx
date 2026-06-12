"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { IconLogo } from "./icons";
import { getUser, clearAuth, isAuthenticated } from "@/lib/auth";
import type { AuthUser } from "@/lib/auth";

export function Navbar() {
  const [ter_scroll, setTerScroll] = useState(false);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const pathname = usePathname();
  const router = useRouter();

  const halaman_gelap =
    pathname === "/" || pathname === "/submit" || pathname.startsWith("/dashboard");

  useEffect(() => {
    const handleScroll = () => setTerScroll(window.scrollY > 20);
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  useEffect(() => {
    setUser(getUser());
  }, [pathname]);

  const gelap = halaman_gelap;
  const navbar_transparan = pathname === "/" && !ter_scroll;

  function handleSignOut() {
    clearAuth();
    setUser(null);
    setMenuOpen(false);
    router.push("/");
  }

  return (
    <nav
      className={`fixed top-0 z-50 w-full h-16 transition-all duration-300 ${
        gelap
          ? navbar_transparan
            ? "border-b border-transparent bg-transparent"
            : "border-b border-white/8 bg-[#020818]/85 backdrop-blur-xl"
          : "border-b border-slate-200/80 bg-white/90 backdrop-blur-xl"
      }`}
    >
      <div className="mx-auto flex h-full max-w-6xl items-center justify-between px-6">

        {/* Logo */}
        <Link href="/" className="group flex items-center gap-3">
          <span className={`flex h-8 w-8 items-center justify-center rounded-lg transition ${
            gelap
              ? "bg-amber-500/20 text-amber-400 group-hover:bg-amber-500/30"
              : "bg-navy text-amber-400"
          }`}>
            <IconLogo className="h-4 w-4" />
          </span>
          <span className={`font-mono text-base font-bold tracking-tight transition ${
            gelap ? "text-white" : "text-navy"
          }`}>
            ECHO
          </span>
        </Link>

        {/* Nav links */}
        <div className="hidden items-center gap-8 text-sm font-medium md:flex">
          {[
            { href: "/dashboard", label: "Dashboard" },
            { href: "/submit", label: "Submit" },
          ].map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={`transition-colors ${
                gelap
                  ? "text-slate-400 hover:text-white"
                  : "text-slate-600 hover:text-navy"
              }`}
            >
              {link.label}
            </Link>
          ))}
        </div>

        {/* Auth area */}
        <div className="flex items-center gap-3">
          {user ? (
            <div className="relative">
              <button
                onClick={() => setMenuOpen((v) => !v)}
                className={`flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium transition ${
                  gelap
                    ? "text-slate-300 hover:bg-white/8"
                    : "text-slate-700 hover:bg-slate-100"
                }`}
              >
                <span className="flex h-7 w-7 items-center justify-center rounded-full bg-amber-500/20 text-xs font-bold text-amber-300">
                  {user.email[0].toUpperCase()}
                </span>
                <span className="hidden sm:block max-w-[140px] truncate">{user.email}</span>
                <svg className="h-3.5 w-3.5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {menuOpen && (
                <div className="absolute right-0 mt-2 w-52 rounded-xl border border-white/10 bg-[#0d1117] p-1 shadow-2xl">
                  {user.org_name && (
                    <div className="px-3 py-2 text-xs text-slate-500">{user.org_name}</div>
                  )}
                  <Link
                    href="/dashboard"
                    onClick={() => setMenuOpen(false)}
                    className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-300 hover:bg-white/8"
                  >
                    Dashboard
                  </Link>
                  <Link
                    href="/submit"
                    onClick={() => setMenuOpen(false)}
                    className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-300 hover:bg-white/8"
                  >
                    Submit post-mortem
                  </Link>
                  <div className="my-1 border-t border-white/8" />
                  <button
                    onClick={handleSignOut}
                    className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-red-400 hover:bg-red-500/10"
                  >
                    Sign out
                  </button>
                </div>
              )}
            </div>
          ) : (
            <>
              <Link
                href="/login"
                className={`hidden text-sm font-medium transition sm:block ${
                  gelap ? "text-slate-500 hover:text-white" : "text-slate-600 hover:text-navy"
                }`}
              >
                Sign in
              </Link>
              <Link
                href="/register"
                className={`rounded-xl px-4 py-2 text-sm font-semibold transition-all ${
                  gelap
                    ? "border border-amber-500/30 bg-amber-500/15 text-amber-300 hover:bg-amber-500/25 hover:border-amber-500/50"
                    : "bg-amber-500 text-white shadow-sm shadow-amber-500/25 hover:bg-amber-600"
                }`}
              >
                Get started free
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
