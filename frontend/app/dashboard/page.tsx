"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { ArrowLeft, ArrowRight, X, Database } from "lucide-react";
import { api, ClimaxData, Incident, PatternScore, PostmortemOut, ApiError } from "@/lib/api";
import { getUser, isAuthenticated } from "@/lib/auth";
import { IncidentTimeline } from "@/components/IncidentTimeline";
import { RecurrenceAlert } from "@/components/RecurrenceAlert";
import { PatternScoreGauge } from "@/components/PatternScoreGauge";
import { SkeletonGauge, SkeletonAlertCard } from "@/components/Skeleton";
import { SeverityBadge } from "@/components/SeverityBadge";
import {
  IconLogo,
  IconHome,
  IconList,
  IconBell,
  IconChart,
  IconPlus,
  IconArrowRight,
  IconShield,
} from "@/components/icons";

type BagianDashboard = "overview" | "incidents" | "alerts" | "score" | "my";

export default function DashboardPage() {
  const [climax, setClimax] = useState<ClimaxData | null>(null);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [score, setScore] = useState<PatternScore | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [panelTerbuka, setPanelTerbuka] = useState(false);
  const [bagianAktif, setBagianAktif] = useState<BagianDashboard>("overview");
  const [myPostmortems, setMyPostmortems] = useState<PostmortemOut[]>([]);
  const [myLoading, setMyLoading] = useState(false);
  const [loggedIn, setLoggedIn] = useState(false);
  const [orgName, setOrgName] = useState<string | null>(null);

  const refIncidents = useRef<HTMLDivElement>(null);

  const muatData = useCallback(() => {
    setLoading(true);
    setError(null);
    Promise.all([api.getClimax(), api.getIncidents(), api.getPatternScore()])
      .then(([c, i, s]) => {
        setClimax(c);
        setIncidents(i);
        setScore(s);
      })
      .catch((err) => {
        const pesan = err instanceof ApiError ? err.message : "Failed to load dashboard data.";
        setError(pesan);
      })
      .finally(() => setLoading(false));
  }, []);

  const muatMyPostmortems = useCallback(() => {
    setMyLoading(true);
    api.postmortems.list()
      .then(setMyPostmortems)
      .catch(() => setMyPostmortems([]))
      .finally(() => setMyLoading(false));
  }, []);

  useEffect(() => { muatData(); }, [muatData]);

  useEffect(() => {
    const auth = isAuthenticated();
    setLoggedIn(auth);
    if (auth) {
      const u = getUser();
      setOrgName(u?.org_name ?? null);
      muatMyPostmortems();
    }
  }, [muatMyPostmortems]);

  useEffect(() => {
    if (bagianAktif === "my" && loggedIn) muatMyPostmortems();
  }, [bagianAktif, loggedIn, muatMyPostmortems]);

  useEffect(() => {
    if (!panelTerbuka) return;
    const tutup = (e: KeyboardEvent) => { if (e.key === "Escape") setPanelTerbuka(false); };
    window.addEventListener("keydown", tutup);
    return () => window.removeEventListener("keydown", tutup);
  }, [panelTerbuka]);

  const adaAlert = !error && climax && climax.unimplemented_items.length > 0;

  const scrollKeBagian = (bagian: BagianDashboard) => {
    setBagianAktif(bagian);
    setPanelTerbuka(false);
  };

  const judulHeader: Record<BagianDashboard, string> = {
    overview: "Overview",
    incidents: "Incident History",
    alerts: "ECHO Alerts",
    score: "Pattern Score",
    my: "My Workspace",
  };

  const menuNav: {
    id: BagianDashboard;
    label: string;
    icon: typeof IconHome;
    badge?: number;
  }[] = [
    { id: "overview", label: "Overview", icon: IconHome },
    { id: "incidents", label: "Incidents", icon: IconList },
    {
      id: "alerts",
      label: "ECHO Alerts",
      icon: IconBell,
      badge: adaAlert ? climax!.unimplemented_items.length : 0,
    },
    { id: "score", label: "Pattern Score", icon: IconChart },
    ...(loggedIn ? [{ id: "my" as BagianDashboard, label: "My History", icon: IconList, badge: myPostmortems.length }] : []),
  ];

  const nilaiSkor = score?.score ?? 0;
  const warnaScore = nilaiSkor < 40 ? "text-red-400" : nilaiSkor < 60 ? "text-amber-400" : "text-emerald-400";
  const labelScore = nilaiSkor < 40 ? "Critical" : nilaiSkor < 60 ? "Warning" : "Good";

  return (
    <div className="flex min-h-screen bg-[#020818]">

      {/* ── Sidebar ── */}
      <aside className="flex w-64 shrink-0 flex-col border-r border-white/6 bg-[#030c1a]">
        <div className="flex items-center gap-3 border-b border-white/6 px-5 py-4">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl border border-amber-500/25 bg-amber-500/10 text-amber-400">
            <IconLogo className="h-4 w-4" />
          </span>
          <div>
            <span className="font-mono text-sm font-bold text-white">ECHO</span>
            <p className="text-[10px] font-medium uppercase tracking-wider text-slate-600">
              {orgName ?? "Demo Workspace"}
            </p>
          </div>
        </div>

        <nav className="flex-1 space-y-1 p-3">
          {menuNav.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => scrollKeBagian(item.id)}
              className={`flex w-full cursor-pointer items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition-all ${
                bagianAktif === item.id
                  ? "border border-white/8 bg-white/8 font-semibold text-white"
                  : "text-slate-500 hover:bg-white/4 hover:text-slate-300"
              }`}
            >
              <item.icon className="h-4 w-4 shrink-0" />
              <span>{item.label}</span>
              {item.badge ? (
                <span className="ml-auto flex h-5 min-w-[20px] items-center justify-center rounded-full bg-red-500 px-1.5 text-[10px] font-bold text-white">
                  {item.badge}
                </span>
              ) : null}
            </button>
          ))}

          <Link
            href="/submit"
            className="mt-4 flex items-center justify-center gap-2 rounded-xl bg-gradient-to-br from-amber-400 to-amber-600 px-3 py-2.5 text-sm font-bold text-white shadow-lg shadow-amber-500/20 transition hover:from-amber-300 hover:to-amber-500"
          >
            <IconPlus className="h-4 w-4" />
            Submit New
          </Link>
        </nav>

        {/* Pattern score ringkas di sidebar */}
        <div className="border-t border-white/6 p-4">
          {loading ? (
            <SkeletonGauge />
          ) : score ? (
            <div className="rounded-xl border border-white/8 bg-white/4 p-4 text-center">
              <p className={`font-mono text-3xl font-black ${warnaScore}`}>{score.score}</p>
              <p className={`mt-0.5 text-[10px] font-bold uppercase tracking-widest ${warnaScore}`}>
                {labelScore}
              </p>
              <p className="mt-2 text-xs text-slate-600">Pattern Score</p>
              <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-white/8">
                <div
                  className={`h-full rounded-full ${
                    nilaiSkor < 40 ? "bg-red-500" : nilaiSkor < 60 ? "bg-amber-500" : "bg-emerald-500"
                  }`}
                  style={{ width: `${score.score}%` }}
                />
              </div>
            </div>
          ) : null}
        </div>
      </aside>

      {/* ── Main content ── */}
      <div className="relative flex flex-1 flex-col overflow-hidden">
        <div className="absolute inset-0 bg-grid-dark opacity-40 pointer-events-none" />

        {/* Header */}
        <header className="relative z-10 flex items-center justify-between border-b border-white/6 bg-[#020818]/80 px-6 py-4 backdrop-blur-md">
          <div className="flex items-center gap-3">
            <h1 className="text-lg font-bold text-white">{judulHeader[bagianAktif]}</h1>
            {bagianAktif === "alerts" && adaAlert && (
              <span className="rounded-full border border-red-500/25 bg-red-500/10 px-2.5 py-0.5 text-xs font-bold text-red-400">
                {climax!.unimplemented_items.length} active
              </span>
            )}
          </div>
          <Link href="/" className="inline-flex items-center gap-1.5 text-sm font-medium text-slate-500 transition hover:text-slate-300">
            <ArrowLeft className="h-4 w-4" aria-hidden />
            Back to home
          </Link>
        </header>

        <div className="relative z-10 flex flex-1 overflow-hidden">
          <main className="flex-1 overflow-auto p-6 space-y-6">

            {loading && (
              <div className="space-y-4">
                <SkeletonAlertCard />
                <SkeletonAlertCard />
              </div>
            )}

            {!loading && error && (
              <div className="flex flex-col items-center rounded-2xl border border-red-500/20 bg-red-500/8 py-16 text-center">
                <p className="text-sm text-red-400">{error}</p>
                <button
                  onClick={muatData}
                  className="mt-5 rounded-xl border border-white/10 bg-white/8 px-6 py-2.5 text-sm font-semibold text-white hover:bg-white/12"
                >
                  Retry
                </button>
              </div>
            )}

            {/* ── Overview ── */}
            {!loading && !error && bagianAktif === "overview" && (
              <div className="space-y-6 animate-fade-up">
                {score && (
                  <div className="grid gap-4 sm:grid-cols-3">
                    {[
                      { label: "Pattern Score", nilai: score.score, suffix: "/100" },
                      { label: "Recurrence Rate", nilai: `${Math.round(score.recurrence_rate * 100)}%`, suffix: "" },
                      { label: "Incidents Tracked", nilai: score.total_postmortems, suffix: "" },
                    ].map((stat) => (
                      <div
                        key={stat.label}
                        className="rounded-2xl border border-white/8 bg-white/4 px-5 py-4"
                      >
                        <p className="text-[10px] font-bold uppercase tracking-widest text-slate-600">
                          {stat.label}
                        </p>
                        <p className="mt-2 font-mono text-3xl font-bold text-white">
                          {stat.nilai}
                          {stat.suffix && (
                            <span className="text-base font-normal text-slate-600">{stat.suffix}</span>
                          )}
                        </p>
                      </div>
                    ))}
                  </div>
                )}

                {adaAlert && climax && (
                  <div
                    className="card-dark group cursor-pointer border border-red-500/20 bg-gradient-to-br from-red-950/30 via-transparent to-transparent p-5 rounded-2xl transition"
                    onClick={() => scrollKeBagian("alerts")}
                  >
                    <p className="text-xs font-bold uppercase tracking-widest text-red-400">Active alert</p>
                    <p className="mt-2 font-bold text-white">{climax.title}</p>
                    <p className="mt-1 text-sm text-slate-500">
                      {Math.round(climax.similarity_score * 100)}% match · {climax.days_between} days since prior incident
                    </p>
                    <span className="mt-4 inline-flex items-center gap-1.5 text-sm font-semibold text-red-400 group-hover:text-red-300 transition">
                      View alert
                      <IconArrowRight className="h-4 w-4" />
                    </span>
                  </div>
                )}

                <div>
                  <div className="mb-4 flex items-center justify-between">
                    <h2 className="font-bold text-white">Recent Incidents</h2>
                    <button
                      type="button"
                      onClick={() => scrollKeBagian("incidents")}
                      className="text-sm font-medium text-slate-500 transition hover:text-slate-300"
                    >
                      View all
                    </button>
                  </div>
                  <IncidentTimeline incidents={incidents} limit={3} />
                </div>
              </div>
            )}

            {/* ── ECHO Alerts ── */}
            {!loading && !error && bagianAktif === "alerts" && adaAlert && climax && (
              <div className="space-y-6 animate-fade-up">
                <div
                  className="card-dark group cursor-pointer border border-red-500/20 bg-gradient-to-br from-red-950/30 via-transparent to-transparent p-5 rounded-2xl transition"
                  onClick={() => setPanelTerbuka(true)}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <span className="mb-3 inline-flex items-center gap-1.5 rounded-full border border-red-500/25 bg-red-500/10 px-2.5 py-1 font-mono text-xs font-bold text-red-400">
                        <span className="h-1.5 w-1.5 rounded-full bg-red-500 pulse-dot" />
                        {Math.round(climax.similarity_score * 100)}% match
                      </span>
                      <p className="font-bold text-white">{climax.title}</p>
                      <p className="mt-1 flex items-center gap-1.5 text-sm text-slate-500">
                        <ArrowRight className="h-3.5 w-3.5 shrink-0" aria-hidden />
                        {climax.matched_incident_title}
                      </p>
                      <p className="mt-3 text-sm text-slate-500">
                        {climax.unimplemented_items.length} unimplemented action items from prior incident
                      </p>
                    </div>
                    <span className="flex shrink-0 items-center gap-1.5 text-sm font-semibold text-red-400 group-hover:text-red-300 transition">
                      View match
                      <IconArrowRight className="h-4 w-4" />
                    </span>
                  </div>
                </div>
                <RecurrenceAlert
                  similarityScore={climax.similarity_score}
                  daysBetween={climax.days_between}
                  matchedDate={climax.matched_incident_date}
                  unimplementedItems={climax.unimplemented_items}
                  echoVerdict={climax.echo_verdict}
                />
              </div>
            )}

            {!loading && !error && bagianAktif === "alerts" && !adaAlert && (
              <div className="flex flex-col items-center rounded-2xl border border-white/8 bg-white/4 py-20 text-center animate-fade-up">
                <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl border border-emerald-500/25 bg-emerald-500/10 text-emerald-400">
                  <IconShield className="h-6 w-6" />
                </div>
                <h2 className="text-xl font-bold text-white">No active alerts</h2>
                <p className="mt-2 max-w-sm text-sm text-slate-500">
                  Your team is learning from failures. Keep it up.
                </p>
              </div>
            )}

            {/* ── Incidents ── */}
            {!loading && !error && bagianAktif === "incidents" && (
              <div ref={refIncidents} id="incident-history" className="animate-fade-up">
                <div className="mb-4 flex items-center justify-between">
                  <p className="text-sm text-slate-500">{incidents.length} incidents tracked</p>
                </div>
                <IncidentTimeline incidents={incidents} />
              </div>
            )}

            {/* ── My Workspace ── */}
            {bagianAktif === "my" && (
              <div className="animate-fade-up space-y-4">
                <div className="flex items-center justify-between">
                  <p className="text-sm text-slate-500">
                    {myLoading ? "Loading…" : `${myPostmortems.length} post-mortem${myPostmortems.length !== 1 ? "s" : ""} saved`}
                  </p>
                  <Link
                    href="/submit"
                    className="inline-flex items-center gap-1.5 rounded-xl border border-amber-500/30 bg-amber-500/10 px-3 py-1.5 text-xs font-semibold text-amber-300 transition hover:bg-amber-500/20"
                  >
                    <IconPlus className="h-3.5 w-3.5" />
                    New
                  </Link>
                </div>

                {myLoading && <SkeletonAlertCard />}

                {!myLoading && myPostmortems.length === 0 && (
                  <div className="flex flex-col items-center rounded-2xl border border-white/8 bg-white/4 py-20 text-center">
                    <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl border border-amber-500/20 bg-amber-500/8 text-amber-400">
                      <Database className="h-6 w-6" />
                    </div>
                    <h2 className="text-lg font-bold text-white">No post-mortems yet</h2>
                    <p className="mt-2 max-w-sm text-sm text-slate-500">
                      Submit your first post-mortem to start building your team&apos;s institutional memory.
                    </p>
                    <Link
                      href="/submit"
                      className="mt-6 inline-flex items-center gap-2 rounded-xl bg-gradient-to-br from-amber-400 to-amber-600 px-5 py-2.5 text-sm font-bold text-white shadow-lg shadow-amber-500/20 transition hover:from-amber-300 hover:to-amber-500"
                    >
                      <IconPlus className="h-4 w-4" />
                      Submit first post-mortem
                    </Link>
                  </div>
                )}

                {!myLoading && myPostmortems.map((pm) => (
                  <Link
                    key={pm.id}
                    href={`/postmortems/${pm.id}`}
                    className="block rounded-2xl border border-white/8 bg-white/4 p-5 space-y-3 transition hover:bg-white/6 hover:border-white/14"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          {pm.severity && <SeverityBadge severity={pm.severity} />}
                          {pm.has_recurrence && (
                            <span className="inline-flex items-center gap-1 rounded-full border border-red-500/25 bg-red-500/10 px-2 py-0.5 text-[10px] font-bold text-red-400">
                              <span className="h-1.5 w-1.5 rounded-full bg-red-500" />
                              Recurrence
                            </span>
                          )}
                        </div>
                        <h3 className="mt-2 font-semibold text-white leading-snug">{pm.title}</h3>
                        <p className="mt-0.5 text-xs text-slate-500">{pm.incident_date}</p>
                      </div>
                    </div>

                    {pm.summary && (
                      <p className="text-sm text-slate-400 leading-relaxed line-clamp-2">{pm.summary}</p>
                    )}

                    {pm.systems_affected.length > 0 && (
                      <div className="flex flex-wrap gap-1.5">
                        {pm.systems_affected.map((s) => (
                          <span key={s} className="tag-system-dark text-[10px]">{s}</span>
                        ))}
                      </div>
                    )}

                    {pm.recurrence_matches.length > 0 && (
                      <div className="border-t border-white/8 pt-3">
                        <p className="text-xs font-semibold text-red-400">
                          {pm.recurrence_matches.length} recurrence match{pm.recurrence_matches.length !== 1 ? "es" : ""} ·{" "}
                          top score {Math.round(pm.recurrence_matches[0].similarity_score * 100)}%
                        </p>
                      </div>
                    )}
                  </Link>
                ))}
              </div>
            )}

            {/* ── Pattern Score ── */}
            {!loading && !error && bagianAktif === "score" && score && (
              <div className="mx-auto max-w-md animate-fade-up">
                <div className="rounded-2xl border border-white/8 bg-white/4 p-8">
                  <PatternScoreGauge
                    score={score.score}
                    recurrenceRate={score.recurrence_rate}
                    actionCompletion={score.avg_action_completion}
                    totalIncidents={score.total_postmortems}
                    variant="dark"
                  />
                </div>
              </div>
            )}
          </main>

          {/* Detail panel */}
          {panelTerbuka && climax && (
            <aside
              className="w-[400px] shrink-0 overflow-auto border-l border-white/8 bg-[#030c1a] p-5 shadow-2xl"
              role="dialog"
              aria-label="Recurrence match details"
            >
              <button
                onClick={() => setPanelTerbuka(false)}
                className="mb-5 inline-flex items-center gap-2 text-sm font-medium text-slate-500 transition hover:text-slate-300"
              >
                <X className="h-4 w-4" aria-hidden />
                Close
              </button>
              <RecurrenceAlert
                similarityScore={climax.similarity_score}
                daysBetween={climax.days_between}
                matchedDate={climax.matched_incident_date}
                unimplementedItems={climax.unimplemented_items}
                echoVerdict={climax.echo_verdict}
              />
              {score && (
                <div className="mt-6 rounded-2xl border border-white/8 bg-white/4 p-5">
                  <PatternScoreGauge
                    score={score.score}
                    recurrenceRate={score.recurrence_rate}
                    actionCompletion={score.avg_action_completion}
                    totalIncidents={score.total_postmortems}
                    variant="dark"
                  />
                </div>
              )}
            </aside>
          )}
        </div>
      </div>
    </div>
  );
}
