import { Check, Circle, Loader2, Minus, X, type LucideIcon } from "lucide-react";

interface ActionItemStatusBadgeProps {
  status: string;
}

function normalisasiStatus(status: string): string {
  return status.toUpperCase().replace(/_/g, " ");
}

const kelasMap: Record<string, string> = {
  COMPLETED: "status-completed",
  "IN PROGRESS": "status-in-progress",
  OPEN: "status-open",
  ABANDONED: "status-abandoned",
  "NEVER STARTED": "status-never-started",
};

const konfigurasiStatus: Record<string, { Ikon: LucideIcon; label: string }> = {
  COMPLETED: { Ikon: Check, label: "Completed" },
  "IN PROGRESS": { Ikon: Loader2, label: "In Progress" },
  OPEN: { Ikon: Circle, label: "Open" },
  ABANDONED: { Ikon: X, label: "Abandoned" },
  "NEVER STARTED": { Ikon: Minus, label: "Never Started" },
};

export function ActionItemStatusBadge({ status }: ActionItemStatusBadgeProps) {
  const normal = normalisasiStatus(status);
  const kelas = kelasMap[normal] || "status-open";
  const konfig = konfigurasiStatus[normal];
  const Ikon = konfig?.Ikon ?? Circle;
  const label = konfig?.label ?? status;

  return (
    <span className={`inline-flex items-center gap-1.5 ${kelas}`}>
      <Ikon
        className={`h-3 w-3 shrink-0 ${normal === "IN PROGRESS" ? "animate-spin" : ""}`}
        aria-hidden
      />
      {label}
    </span>
  );
}
