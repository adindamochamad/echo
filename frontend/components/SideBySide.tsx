import { ClimaxData } from "@/lib/api";
import { IconArrowRight } from "./icons";

interface SideBySideProps {
  data: ClimaxData;
}

const warnaseverity: Record<string, string> = {
  P0: "bg-red-500/15 text-red-400 border-red-500/25",
  P1: "bg-amber-500/15 text-amber-400 border-amber-500/25",
  P2: "bg-blue-500/15 text-blue-400 border-blue-500/25",
  P3: "bg-emerald-500/15 text-emerald-400 border-emerald-500/25",
};

export function SideBySide({ data }: SideBySideProps) {
  const persenMatch = Math.round(data.similarity_score * 100);

  return (
    <div className="mx-auto grid max-w-5xl items-stretch gap-4 md:grid-cols-[1fr_auto_1fr]">

      {/* ── Insiden sekarang ── */}
      <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-md animate-fade-up">
        <div className="absolute inset-0 bg-gradient-to-br from-red-950/20 to-transparent" />
        <div className="relative">
          <div className="mb-4 flex items-center gap-2.5">
            <span className="relative flex h-2.5 w-2.5">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-red-400 opacity-70" />
              <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-red-500" />
            </span>
            <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-red-400">
              Today&apos;s Incident
            </p>
          </div>

          <h3 className="text-base font-bold leading-snug text-white">{data.title}</h3>
          <p className="mt-1 font-mono text-xs text-slate-500">{data.incident_date}</p>

          <div className="mt-4 flex flex-wrap items-center gap-2">
            {data.severity && (
              <span className={`inline-flex items-center rounded-lg border px-2.5 py-1 font-mono text-xs font-bold ${warnaseverity[data.severity] ?? "bg-slate-500/15 text-slate-400 border-slate-500/25"}`}>
                {data.severity}
              </span>
            )}
            {data.systems_affected.map((s) => (
              <span key={s} className="tag-system-dark">{s}</span>
            ))}
          </div>

          <p className="mt-4 text-sm leading-relaxed text-slate-400 line-clamp-3">{data.summary}</p>
        </div>
      </div>

      {/* ── Connector ── */}
      <div className="hidden flex-col items-center justify-center px-2 md:flex">
        <div className="flex flex-col items-center gap-2">
          <div className="h-14 w-px bg-gradient-to-b from-transparent via-red-500/40 to-transparent" />
          <div className="flex h-11 w-11 items-center justify-center rounded-full border border-red-500/30 bg-red-500/10 backdrop-blur-sm shadow-glow">
            <IconArrowRight className="h-4 w-4 text-red-400" />
          </div>
          <p className="whitespace-nowrap text-[9px] font-black uppercase tracking-[0.2em] text-red-500/70">
            ECHO
          </p>
          <div className="h-14 w-px bg-gradient-to-b from-transparent via-red-500/40 to-transparent" />
        </div>
      </div>

      {/* ── Match historis ── */}
      <div className="relative overflow-hidden rounded-2xl border-2 border-red-500/40 bg-gradient-to-br from-red-950/40 via-slate-900/60 to-slate-900/60 p-6 backdrop-blur-md animate-fade-up shadow-glow">
        {/* Decorative glow */}
        <div className="pointer-events-none absolute -right-12 -top-12 h-40 w-40 rounded-full bg-red-500/15 blur-2xl" />

        <div className="relative">
          <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-red-400">
            ECHO Found a Match
          </p>

          <div className="mt-3 flex items-baseline gap-1">
            <p className="font-mono text-6xl font-black tracking-tight text-gradient-red">
              {persenMatch}
            </p>
            <span className="font-mono text-2xl font-bold text-red-500">%</span>
          </div>
          <p className="mt-1 text-xs text-slate-500">similarity score</p>

          <div className="mt-5 h-1.5 w-full overflow-hidden rounded-full bg-white/8">
            <div
              className="h-full rounded-full bg-gradient-to-r from-red-500 to-rose-400"
              style={{ width: `${persenMatch}%` }}
            />
          </div>

          <div className="mt-5 rounded-xl border border-white/8 bg-white/5 p-4">
            <h3 className="text-sm font-bold leading-snug text-white">{data.matched_incident_title}</h3>
            <p className="mt-1 text-xs text-slate-500">
              {data.days_between} days ago · {data.matched_incident_date}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
