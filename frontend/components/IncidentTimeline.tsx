import { Incident } from "@/lib/api";
import { RefreshCw } from "lucide-react";

interface IncidentTimelineProps {
  incidents: Incident[];
  limit?: number;
}

const warnaSeverityDot: Record<string, string> = {
  P0: "bg-red-500 ring-red-500/20",
  P1: "bg-amber-500 ring-amber-500/20",
  P2: "bg-blue-500 ring-blue-500/20",
  P3: "bg-emerald-500 ring-emerald-500/20",
};

const warnaSeverityBadge: Record<string, string> = {
  P0: "border-red-500/20 bg-red-500/10 text-red-400",
  P1: "border-amber-500/20 bg-amber-500/10 text-amber-400",
  P2: "border-blue-500/20 bg-blue-500/10 text-blue-400",
  P3: "border-emerald-500/20 bg-emerald-500/10 text-emerald-400",
};

export function IncidentTimeline({ incidents, limit }: IncidentTimelineProps) {
  const daftar = limit ? incidents.slice(0, limit) : incidents;

  return (
    <div className="space-y-2">
      {daftar.map((insiden) => (
        <div
          key={insiden.id}
          className="flex gap-4 rounded-xl border border-white/8 bg-white/4 px-4 py-3.5 transition hover:border-white/12 hover:bg-white/6"
        >
          {/* Titik status */}
          <div className="mt-1 flex shrink-0 flex-col items-center">
            <div
              className={`h-2.5 w-2.5 rounded-full ring-4 ${
                warnaSeverityDot[insiden.severity] ?? "bg-slate-500 ring-slate-500/20"
              } ${insiden.has_recurrence ? "pulse-dot" : ""}`}
            />
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <h4 className="text-sm font-semibold text-slate-200 truncate">{insiden.title}</h4>
              {insiden.has_recurrence && (
                <span className="inline-flex shrink-0 items-center gap-1 rounded-full border border-red-500/20 bg-red-500/10 px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider text-red-400">
                  <RefreshCw className="h-2.5 w-2.5" aria-hidden />
                  Recurrence
                </span>
              )}
            </div>
            <div className="mt-1.5 flex flex-wrap items-center gap-2">
              <span className="font-mono text-xs text-slate-600">{insiden.incident_date}</span>
              <span
                className={`rounded-lg border px-2 py-0.5 font-mono text-[10px] font-bold ${
                  warnaSeverityBadge[insiden.severity] ?? "border-slate-500/20 bg-slate-500/10 text-slate-400"
                }`}
              >
                {insiden.severity}
              </span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
