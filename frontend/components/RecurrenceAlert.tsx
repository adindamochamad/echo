import { AlertTriangle } from "lucide-react";
import { ActionItem } from "@/lib/api";
import { ActionItemStatusBadge } from "./ActionItemStatusBadge";

interface RecurrenceAlertProps {
  similarityScore: number;
  daysBetween: number;
  matchedDate: string;
  unimplementedItems: ActionItem[];
  echoVerdict: string;
}

export function RecurrenceAlert({
  similarityScore,
  daysBetween,
  matchedDate,
  unimplementedItems,
  echoVerdict,
}: RecurrenceAlertProps) {
  const persenMatch = Math.round(similarityScore * 100);

  return (
    <div className="echo-alert mx-auto max-w-3xl animate-fade-in">
      {/* Header */}
      <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-red-500/25 bg-red-500/10 px-3 py-1.5 text-xs font-bold text-red-400">
            <span className="h-1.5 w-1.5 rounded-full bg-red-500 pulse-dot" />
            Recurrence Detected
          </div>
          <h3 className="text-xl font-bold text-white">ECHO Detected a Pattern</h3>
          <p className="mt-1 text-sm text-slate-500">
            {daysBetween} days since {matchedDate}
          </p>
        </div>
        <div className="text-right">
          <p className="font-mono text-4xl font-black text-gradient-red">{persenMatch}%</p>
          <p className="text-[10px] font-bold uppercase tracking-widest text-slate-600">match score</p>
        </div>
      </div>

      {/* Progress bar */}
      <div className="mb-6 h-1 w-full overflow-hidden rounded-full bg-white/8">
        <div
          className="h-full rounded-full bg-gradient-to-r from-red-600 to-rose-400 transition-all duration-1000"
          style={{ width: `${persenMatch}%` }}
        />
      </div>

      {/* Action items yang belum dikerjakan */}
      <div className="overflow-hidden rounded-xl border border-red-500/15 bg-white/4">
        <div className="border-b border-red-500/10 px-5 py-3">
          <p className="text-xs font-bold uppercase tracking-wider text-red-400/80">
            {unimplementedItems.length} Unimplemented Action Item{unimplementedItems.length !== 1 ? "s" : ""}
          </p>
        </div>
        {unimplementedItems.map((item, idx) => (
          <div
            key={idx}
            className={`flex flex-wrap items-center gap-3 px-5 py-4 ${
              idx < unimplementedItems.length - 1 ? "border-b border-white/5" : ""
            }`}
          >
            <ActionItemStatusBadge status={item.status} />
            <span className="flex-1 text-sm text-slate-300">{item.description}</span>
            {item.owner && (
              <span className="rounded-full border border-white/10 bg-white/8 px-2.5 py-0.5 text-xs font-medium text-slate-400">
                {item.owner}
              </span>
            )}
            {item.ticket_ref ? (
              <span className="font-mono text-xs text-blue-400">{item.ticket_ref}</span>
            ) : (
              <span className="text-xs font-medium text-red-500/70">No ticket</span>
            )}
          </div>
        ))}
      </div>

      {/* Verdict */}
      <div className="mt-5 flex items-start gap-3 rounded-xl border border-amber-500/15 bg-amber-500/6 px-5 py-4">
        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-400" aria-hidden />
        <p className="text-sm leading-relaxed text-amber-300/90 italic">{echoVerdict}</p>
      </div>
    </div>
  );
}
