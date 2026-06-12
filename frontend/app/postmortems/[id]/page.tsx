"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Check } from "lucide-react";
import { api, PostmortemOut, ApiError } from "@/lib/api";
import { isAuthenticated } from "@/lib/auth";
import { Navbar } from "@/components/Navbar";
import { RecurrenceAlert } from "@/components/RecurrenceAlert";
import { SeverityBadge } from "@/components/SeverityBadge";
import { ActionItemStatusBadge } from "@/components/ActionItemStatusBadge";
import { SkeletonAlertCard } from "@/components/Skeleton";

export default function PostmortemDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [pm, setPm] = useState<PostmortemOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/login");
      return;
    }
    api.postmortems
      .get(id)
      .then(setPm)
      .catch((err) => {
        setError(err instanceof ApiError ? err.message : "Failed to load post-mortem.");
      })
      .finally(() => setLoading(false));
  }, [id, router]);

  const matchUtama = pm?.recurrence_matches?.[0];

  const buatVerdict = () => {
    if (!matchUtama) return "";
    const n = matchUtama.unimplemented_items.length;
    if (n === 0)
      return `Matches a prior incident from ${matchUtama.incident_date}, but all action items were completed.`;
    return `${n} unimplemented action ${n === 1 ? "item" : "items"} from the ${matchUtama.incident_date} incident suggest this recurrence was preventable.`;
  };

  return (
    <div className="relative min-h-screen bg-[#020818]">
      <div className="absolute inset-0 bg-grid-dark opacity-50" />
      <div className="pointer-events-none absolute left-1/2 top-0 h-96 w-96 -translate-x-1/2 rounded-full bg-amber-500/6 blur-3xl" />

      <div className="relative z-10">
        <Navbar />

        <div className="mx-auto max-w-2xl px-6 pb-20 pt-24">
          <Link
            href="/dashboard"
            className="mb-8 inline-flex items-center gap-1.5 text-xs font-medium text-slate-500 transition hover:text-slate-300"
          >
            <ArrowLeft className="h-3.5 w-3.5" aria-hidden />
            Back to dashboard
          </Link>

          {loading && (
            <div className="space-y-4">
              <SkeletonAlertCard />
              <SkeletonAlertCard />
            </div>
          )}

          {!loading && error && (
            <div className="rounded-2xl border border-red-500/20 bg-red-500/8 px-6 py-8 text-center">
              <p className="text-sm text-red-400">{error}</p>
              <Link
                href="/dashboard"
                className="mt-4 inline-flex items-center gap-1.5 text-xs font-medium text-slate-400 hover:text-slate-200"
              >
                <ArrowLeft className="h-3.5 w-3.5" />
                Go back
              </Link>
            </div>
          )}

          {!loading && pm && (
            <div className="space-y-6 animate-fade-up">
              {/* Header */}
              <div>
                <div className="flex flex-wrap items-center gap-2 mb-3">
                  {pm.severity && <SeverityBadge severity={pm.severity} />}
                  {pm.has_recurrence && (
                    <span className="inline-flex items-center gap-1.5 rounded-full border border-red-500/25 bg-red-500/10 px-2.5 py-1 text-xs font-bold text-red-400">
                      <span className="h-1.5 w-1.5 rounded-full bg-red-500" />
                      Recurrence detected
                    </span>
                  )}
                  {!pm.has_recurrence && (
                    <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/25 bg-emerald-500/10 px-2.5 py-1 text-xs font-bold text-emerald-400">
                      <Check className="h-3 w-3" />
                      No recurrence
                    </span>
                  )}
                </div>
                <h1 className="text-2xl font-bold tracking-tight text-white leading-snug">{pm.title}</h1>
                <p className="mt-1.5 text-sm text-slate-500">{pm.incident_date}</p>
              </div>

              {/* Recurrence alert */}
              {matchUtama && (
                <RecurrenceAlert
                  similarityScore={matchUtama.similarity_score}
                  daysBetween={matchUtama.days_between}
                  matchedDate={matchUtama.incident_date}
                  unimplementedItems={matchUtama.unimplemented_items}
                  echoVerdict={buatVerdict()}
                />
              )}

              {/* All recurrence matches if >1 */}
              {pm.recurrence_matches.length > 1 && (
                <div className="rounded-2xl border border-white/8 bg-white/4 p-5 space-y-3">
                  <p className="text-xs font-bold uppercase tracking-widest text-slate-500">
                    All recurrence matches ({pm.recurrence_matches.length})
                  </p>
                  {pm.recurrence_matches.map((m) => (
                    <div key={m.incident_id} className="flex items-center justify-between gap-3 rounded-xl border border-white/6 bg-white/3 px-4 py-3">
                      <div>
                        <p className="text-sm font-semibold text-white">{m.title}</p>
                        <p className="text-xs text-slate-500">{m.incident_date} · {m.days_between}d ago</p>
                      </div>
                      <span className="rounded-full border border-red-500/25 bg-red-500/10 px-2.5 py-1 font-mono text-xs font-bold text-red-400">
                        {Math.round(m.similarity_score * 100)}%
                      </span>
                    </div>
                  ))}
                </div>
              )}

              {/* Main content card */}
              <div className="rounded-2xl border border-white/10 bg-white/5 p-6 space-y-5">
                {/* Summary */}
                <div>
                  <h2 className="mb-2 text-[10px] font-bold uppercase tracking-widest text-slate-600">Summary</h2>
                  <p className="text-sm leading-relaxed text-slate-300">{pm.summary}</p>
                </div>

                {/* Root causes */}
                {pm.root_causes.length > 0 && (
                  <div className="border-t border-white/8 pt-5">
                    <h2 className="mb-3 text-[10px] font-bold uppercase tracking-widest text-slate-600">Root Causes</h2>
                    <ul className="space-y-2.5">
                      {pm.root_causes.map((rc) => (
                        <li key={rc} className="flex items-start gap-3 text-sm text-slate-400">
                          <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-red-500" />
                          {rc}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Action items */}
                {pm.action_items.length > 0 && (
                  <div className="border-t border-white/8 pt-5">
                    <h2 className="mb-3 text-[10px] font-bold uppercase tracking-widest text-slate-600">Action Items</h2>
                    <div className="divide-y divide-white/5 rounded-xl border border-white/8 overflow-hidden">
                      {pm.action_items.map((ai) => (
                        <div key={ai.description} className="flex flex-wrap items-center gap-3 px-4 py-3.5 text-sm">
                          <ActionItemStatusBadge status={ai.status} />
                          <span className="flex-1 text-slate-300">{ai.description}</span>
                          {ai.owner && (
                            <span className="text-xs font-medium text-slate-500">{ai.owner}</span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Systems affected */}
                {pm.systems_affected.length > 0 && (
                  <div className="border-t border-white/8 pt-5">
                    <h2 className="mb-3 text-[10px] font-bold uppercase tracking-widest text-slate-600">Systems Affected</h2>
                    <div className="flex flex-wrap gap-2">
                      {pm.systems_affected.map((s) => (
                        <span key={s} className="tag-system-dark">{s}</span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
