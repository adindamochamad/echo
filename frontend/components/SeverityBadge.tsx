interface SeverityBadgeProps {
  severity: string;
}

const kelasMap: Record<string, string> = {
  P0: "badge-p0",
  P1: "badge-p1",
  P2: "badge-p2",
  P3: "badge-p3",
};

const labelMap: Record<string, string> = {
  P0: "P0 Critical",
  P1: "P1 High",
  P2: "P2 Medium",
  P3: "P3 Low",
};

export function SeverityBadge({ severity }: SeverityBadgeProps) {
  const kelas = kelasMap[severity] || "badge-p2";
  const label = labelMap[severity] || severity;
  return <span className={kelas}>{label}</span>;
}
