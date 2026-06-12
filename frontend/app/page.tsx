"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { api, ClimaxData, ApiError } from "@/lib/api";
import { track } from "@/lib/analytics";
import { Navbar } from "@/components/Navbar";
import { SideBySide } from "@/components/SideBySide";
import { RecurrenceAlert } from "@/components/RecurrenceAlert";
import { SkeletonDemoSection, SkeletonAlertCard } from "@/components/Skeleton";
import { IconDocument, IconSearch, IconRefresh, IconArrowRight } from "@/components/icons";
import { HeroBackground } from "@/components/HeroBackground";
import { TrendingDown } from "lucide-react";

export default function LandingPage() {
  const [data, setData] = useState<ClimaxData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [pesanError, setPesanError] = useState("");
  const alertRef = useRef<HTMLDivElement>(null);

  const muatDemo = () => {
    setLoading(true);
    setError(false);
    api
      .getClimax()
      .then(setData)
      .catch((err) => {
        setError(true);
        setPesanError(err instanceof ApiError ? err.message : "Demo temporarily unavailable");
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    track("demo_viewed");
    muatDemo();
  }, []);

  useEffect(() => {
    if (!alertRef.current) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) track("recurrence_alert_seen");
      },
      { threshold: 0.5 }
    );
    observer.observe(alertRef.current);
    return () => observer.disconnect();
  }, [data]);

  const scrollKeDemo = () => {
    document.getElementById("demo-section")?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <div className="relative min-h-screen bg-[#020818]">
      <Navbar />

      {/* ── Hero ─────────────────────────────────── */}
      <section className="relative overflow-hidden">
        <HeroBackground />

        <div className="relative z-10 mx-auto max-w-5xl px-6 pb-24 pt-24 text-center md:pt-36">

          {/* Eyebrow badge */}
          <div className="animate-fade-up mb-8 inline-flex items-center gap-2.5 rounded-full border border-amber-500/25 bg-amber-500/10 px-4 py-2 text-xs font-semibold text-amber-300 backdrop-blur-sm">
            <span className="h-1.5 w-1.5 rounded-full bg-amber-400 animate-pulse-slow" />
            Institutional Memory for Engineering Teams
          </div>

          {/* Headline */}
          <h1 className="animate-fade-up text-5xl font-extrabold leading-[1.05] tracking-tight text-white md:text-7xl">
            Your team keeps making
            <span className="block mt-1 text-gradient-amber">
              the same mistakes.
            </span>
          </h1>

          <p className="animate-fade-up mx-auto mt-7 max-w-2xl text-lg leading-relaxed text-slate-400 md:text-xl">
            ECHO connects today&apos;s incident to the post-mortem your team wrote — and forgot — 8 months ago.
          </p>

          {/* CTAs */}
          <div className="animate-fade-up mt-12 flex flex-col items-center justify-center gap-4 sm:flex-row">
            <button onClick={scrollKeDemo} className="btn-primary min-w-[200px] text-base py-3.5">
              See it live
              <IconArrowRight className="h-4 w-4" />
            </button>
            <Link href="/submit" className="btn-secondary min-w-[200px] text-base py-3.5">
              Submit a post-mortem
            </Link>
          </div>

          {/* Stats */}
          <div className="animate-fade-up mx-auto mt-20 grid max-w-lg grid-cols-3 gap-px overflow-hidden rounded-2xl border border-white/8 bg-white/8">
            {[
              {
                nilai: data ? `${Math.round(data.similarity_score * 100)}%` : "—",
                label: "Match accuracy",
              },
              {
                nilai: data ? `${data.days_between}d` : "—",
                label: "Pattern gap",
              },
              { nilai: "8+", label: "Incidents tracked" },
            ].map((stat, i) => (
              <div
                key={stat.label}
                className={`bg-white/3 px-6 py-5 text-center ${i === 1 ? "border-x border-white/8" : ""}`}
              >
                <p className="stat-number font-mono text-3xl font-bold">{stat.nilai}</p>
                <p className="mt-1.5 text-[10px] font-semibold uppercase tracking-[0.15em] text-slate-500">
                  {stat.label}
                </p>
              </div>
            ))}
          </div>

          {/* Scroll indicator */}
          <div className="mt-16 flex flex-col items-center gap-2 animate-fade-in">
            <p className="text-xs font-medium uppercase tracking-[0.2em] text-slate-600">Scroll to demo</p>
            <div className="h-10 w-px bg-gradient-to-b from-slate-600 to-transparent" />
          </div>
        </div>
      </section>

      {/* ── Demo section ─────────────────────────── */}
      <section id="demo-section" className="relative overflow-hidden bg-[#020818] py-24 px-6">
        <div className="absolute inset-0 bg-grid-dark opacity-60" />
        <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/15 to-transparent" />
        <div className="absolute inset-x-0 bottom-0 h-px bg-gradient-to-r from-transparent via-white/15 to-transparent" />

        {/* Subtle glow blobs */}
        <div className="pointer-events-none absolute left-1/4 top-1/3 h-64 w-64 rounded-full bg-red-600/8 blur-3xl" />
        <div className="pointer-events-none absolute right-1/4 top-1/2 h-64 w-64 rounded-full bg-blue-600/8 blur-3xl" />

        <div className="relative z-10 mx-auto max-w-5xl">
          <div className="mb-14 text-center">
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-red-500/20 bg-red-500/10 px-3 py-1.5 text-xs font-bold uppercase tracking-widest text-red-400">
              <span className="h-1.5 w-1.5 rounded-full bg-red-500 pulse-dot" />
              Live demo
            </div>
            <h2 className="text-3xl font-bold text-white md:text-4xl">
              November 8, 2025.{" "}
              <span className="text-gradient-red">Checkout is down. Again.</span>
            </h2>
            <p className="mx-auto mt-3 max-w-xl text-base text-slate-500">
              {data
                ? `ECHO instantly surfaces the ${data.matched_incident_date} incident — and the action items your team never completed.`
                : "ECHO instantly surfaces the prior incident — and the action items your team never completed."}
            </p>
          </div>

          {loading && (
            <>
              <SkeletonDemoSection />
              <div className="mt-8">
                <SkeletonAlertCard />
              </div>
            </>
          )}

          {error && (
            <div className="rounded-2xl border border-red-500/20 bg-red-500/8 px-8 py-6 text-center">
              <p className="text-sm text-red-400">{pesanError || "Demo temporarily unavailable"}</p>
              <button
                onClick={muatDemo}
                className="mt-4 rounded-xl border border-white/10 bg-white/8 px-5 py-2 text-xs font-semibold text-white hover:bg-white/12"
              >
                Retry
              </button>
            </div>
          )}

          {data && !loading && (
            <>
              <SideBySide data={data} />
              <div ref={alertRef} className="mt-10">
                <RecurrenceAlert
                  similarityScore={data.similarity_score}
                  daysBetween={data.days_between}
                  matchedDate={data.matched_incident_date}
                  unimplementedItems={data.unimplemented_items}
                  echoVerdict={data.echo_verdict}
                />
              </div>
            </>
          )}
        </div>
      </section>

      {/* ── How it works ─────────────────────────── */}
      <section className="relative overflow-hidden bg-slate-50 py-28 px-6">
        <div className="absolute inset-0 bg-grid-light" />
        <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-transparent via-amber-400/50 to-transparent" />

        <div className="relative z-10 mx-auto max-w-5xl">
          <div className="mb-16 text-center">
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-400">How it works</p>
            <h2 className="mt-3 text-3xl font-bold text-navy md:text-4xl">
              From messy notes to{" "}
              <span className="bg-gradient-to-r from-navy to-slate-600 bg-clip-text text-transparent">
                institutional memory
              </span>
            </h2>
            <p className="mx-auto mt-3 max-w-md text-base text-slate-500">
              Three steps. Under 30 seconds. No setup required.
            </p>
          </div>

          <div className="relative grid gap-6 md:grid-cols-3">
            {/* Connector line */}
            <div className="absolute left-[16.67%] right-[16.67%] top-[52px] hidden h-px bg-gradient-to-r from-amber-300/50 via-amber-400/70 to-amber-300/50 md:block" />

            {[
              {
                icon: IconDocument,
                title: "Submit",
                desc: "Paste any post-mortem. Messy notes, Slack threads, or exported docs — all work.",
                step: "01",
                color: "from-amber-400/20 to-amber-600/10 border-amber-300/40",
                iconColor: "text-amber-600 bg-amber-50",
              },
              {
                icon: IconSearch,
                title: "ECHO Analyzes",
                desc: "Root causes extracted. Action items identified. Severity classified automatically.",
                step: "02",
                color: "from-blue-400/20 to-blue-600/10 border-blue-300/40",
                iconColor: "text-blue-600 bg-blue-50",
              },
              {
                icon: IconRefresh,
                title: "Pattern Matched",
                desc: "Your entire incident history searched. Recurrences surfaced before you repeat them.",
                step: "03",
                color: "from-red-400/20 to-red-600/10 border-red-300/40",
                iconColor: "text-red-600 bg-red-50",
              },
            ].map((item) => (
              <div
                key={item.title}
                className={`relative overflow-hidden rounded-2xl border bg-gradient-to-br p-7 ${item.color} bg-white shadow-card transition-all duration-300 hover:shadow-card-hover hover:-translate-y-1`}
              >
                <div className="absolute right-5 top-5 font-mono text-5xl font-black text-slate-100">
                  {item.step}
                </div>
                <div className={`relative mb-5 flex h-12 w-12 items-center justify-center rounded-xl ${item.iconColor}`}>
                  <item.icon className="h-6 w-6" />
                </div>
                <h3 className="relative text-lg font-bold text-navy">{item.title}</h3>
                <p className="relative mt-2 text-sm leading-relaxed text-slate-600">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Social proof / testimonial ─────────────── */}
      <section className="relative overflow-hidden bg-[#020818] py-20 px-6">
        <div className="absolute inset-0 bg-grid-dark opacity-40" />
        <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent" />

        <div className="relative z-10 mx-auto max-w-4xl text-center">
          <div className="mb-10 flex items-center justify-center gap-2">
            {[
              { label: "Mean Time to Recognize", nilai: "60%", color: "text-emerald-400", turun: true },
              { label: "Repeated incidents", nilai: "40%", color: "text-amber-400", turun: true },
              { label: "Pattern detection speed", nilai: "< 3s", color: "text-blue-400", turun: false },
            ].map((metric, i) => (
              <div
                key={metric.label}
                className={`flex-1 rounded-xl border border-white/8 bg-white/4 px-4 py-5 ${i === 1 ? "scale-105 border-white/12 bg-white/6" : ""}`}
              >
                <p className={`flex items-center justify-center gap-1 font-mono text-3xl font-black ${metric.color}`}>
                  {metric.turun && <TrendingDown className="h-6 w-6" aria-hidden />}
                  {metric.nilai}
                </p>
                <p className="mt-1.5 text-xs font-medium text-slate-500">{metric.label}</p>
              </div>
            ))}
          </div>

          <blockquote className="mx-auto max-w-2xl text-xl font-medium leading-relaxed text-slate-400">
            &ldquo;We kept hitting the same database connection issues every few months. ECHO{" "}
            <span className="text-white font-semibold">found the pattern on the first day</span>{" "}
            and showed us 3 action items we&apos;d never completed.&rdquo;
          </blockquote>
          <p className="mt-4 text-sm font-medium text-slate-600">
            — Engineering Lead, Series B startup
          </p>
        </div>
      </section>

      {/* ── CTA Footer ───────────────────────────── */}
      <section className="relative overflow-hidden bg-[#020818] px-6 py-28 text-center">
        <div className="absolute inset-0 bg-grid-dark opacity-30" />

        {/* Center glow */}
        <div className="pointer-events-none absolute left-1/2 top-1/2 h-96 w-96 -translate-x-1/2 -translate-y-1/2 rounded-full bg-amber-500/10 blur-3xl" />
        <div className="pointer-events-none absolute left-1/2 top-1/2 h-64 w-64 -translate-x-1/2 -translate-y-1/2 rounded-full bg-amber-500/15 blur-2xl" />

        <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-amber-500/40 to-transparent" />

        <div className="relative mx-auto max-w-xl">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-amber-500/25 bg-amber-500/10 px-4 py-1.5 text-xs font-semibold text-amber-300">
            <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
            Early Access Open
          </div>
          <h2 className="text-4xl font-extrabold tracking-tight text-white md:text-5xl">
            Stop repeating
            <span className="block text-gradient-amber">your past mistakes.</span>
          </h2>
          <p className="mt-4 text-base leading-relaxed text-slate-500">
            Free to try. No credit card. Works with your existing post-mortems.
          </p>
          <div className="mt-10 flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
            <Link
              href="/submit"
              className="btn-primary min-w-[220px] py-4 text-base"
            >
              Get started free
              <IconArrowRight className="h-4 w-4" />
            </Link>
            <Link href="/dashboard" className="btn-secondary min-w-[180px] py-4 text-base">
              View dashboard
            </Link>
          </div>
          <p className="mt-6 text-xs text-slate-600">
            Trusted by 50+ engineering teams · SOC 2 in progress
          </p>
        </div>
      </section>
    </div>
  );
}
