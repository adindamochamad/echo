interface PatternScoreGaugeProps {
  score: number;
  recurrenceRate: number;
  actionCompletion: number;
  totalIncidents: number;
  variant?: "light" | "dark";
}

function warnaSkor(skor: number): string {
  if (skor < 40) return "var(--score-critical)";
  if (skor < 60) return "var(--score-warning)";
  if (skor < 80) return "var(--score-good)";
  return "var(--score-excellent)";
}

function labelSkor(skor: number): string {
  if (skor < 40) return "CRITICAL";
  if (skor < 60) return "WARNING";
  if (skor < 80) return "GOOD";
  return "EXCELLENT";
}

export function PatternScoreGauge({
  score,
  recurrenceRate,
  actionCompletion,
  totalIncidents,
  variant = "light",
}: PatternScoreGaugeProps) {
  const radius = 50;
  const circumference = 2 * Math.PI * radius;
  const dash = (score / 100) * circumference;
  const offset = circumference - dash;
  const warna = warnaSkor(score);
  const gelap = variant === "dark";

  const warnaTrack = gelap ? "#1e293b" : "#E2E8F0";
  const warnaAngka = gelap ? "#f8fafc" : "#0f172a";
  const warnaSuffix = gelap ? "#64748b" : "#94a3b8";
  const warnaLabel = gelap ? "text-slate-500" : "text-slate-400";
  const warnaNilai = gelap ? "text-slate-200" : "text-slate-900";

  return (
    <div className="flex flex-col items-center">
      <svg viewBox="0 0 120 120" className="h-32 w-32">
        <circle cx="60" cy="60" r={radius} fill="none" stroke={warnaTrack} strokeWidth="8" />
        <circle
          cx="60"
          cy="60"
          r={radius}
          fill="none"
          stroke={warna}
          strokeWidth="8"
          strokeDasharray={`${dash} ${circumference}`}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform="rotate(-90 60 60)"
        />
        <text
          x="60"
          y="58"
          textAnchor="middle"
          fill={warnaAngka}
          fontSize="28"
          fontFamily="monospace"
          fontWeight="bold"
        >
          {score}
        </text>
        <text x="60" y="74" textAnchor="middle" fill={warnaSuffix} fontSize="14">
          /100
        </text>
      </svg>
      <p className="mt-2 text-xs font-bold tracking-widest" style={{ color: warna }}>
        {labelSkor(score)}
      </p>
      <div className="mt-4 grid w-full grid-cols-3 gap-4 text-center">
        <div>
          <p className={`text-xs uppercase ${warnaLabel}`}>Recurrence Rate</p>
          <p className={`text-lg font-mono font-semibold ${warnaNilai}`}>
            {(recurrenceRate * 100).toFixed(0)}%
          </p>
        </div>
        <div>
          <p className={`text-xs uppercase ${warnaLabel}`}>Action Completion</p>
          <p className={`text-lg font-mono font-semibold ${warnaNilai}`}>
            {(actionCompletion * 100).toFixed(0)}%
          </p>
        </div>
        <div>
          <p className={`text-xs uppercase ${warnaLabel}`}>Total Incidents</p>
          <p className={`text-lg font-mono font-semibold ${warnaNilai}`}>{totalIncidents}</p>
        </div>
      </div>
    </div>
  );
}
