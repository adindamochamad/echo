"use client";

import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { ArrowLeft, Check, Lock } from "lucide-react";
import { api, AnalyzeResult, PostmortemOut, ApiError } from "@/lib/api";
import { isAuthenticated } from "@/lib/auth";
import { track } from "@/lib/analytics";
import { useToast } from "@/components/Toast";
import { Navbar } from "@/components/Navbar";
import { RecurrenceAlert } from "@/components/RecurrenceAlert";
import { SeverityBadge } from "@/components/SeverityBadge";
import { ActionItemStatusBadge } from "@/components/ActionItemStatusBadge";
import { IconUpload, IconArrowRight } from "@/components/icons";

type TabAktif = "paste" | "file";
const UKURAN_MAX_FILE = 5 * 1024 * 1024;
type AnalysisResult = AnalyzeResult | PostmortemOut;

function isPostmortemOut(r: AnalysisResult): r is PostmortemOut {
  return "id" in r;
}

export default function SubmitPage() {
  const [tabAktif, setTabAktif] = useState<TabAktif>("paste");
  const [teks, setTeks] = useState("");
  const [judul, setJudul] = useState("");
  const [tanggal, setTanggal] = useState(new Date().toISOString().slice(0, 10));
  const [severity, setSeverity] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [hasil, setHasil] = useState<AnalysisResult | null>(null);
  const [userLoggedIn, setUserLoggedIn] = useState(false);
  const [fileTerpilih, setFileTerpilih] = useState<File | null>(null);
  const [previewFile, setPreviewFile] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const inputFileRef = useRef<HTMLInputElement>(null);
  const idPermintaanRef = useRef(0);
  const { addToast } = useToast();

  useEffect(() => {
    setUserLoggedIn(isAuthenticated());
  }, []);

  const analisis = async (konten: string) => {
    const idPermintaan = ++idPermintaanRef.current;
    setLoading(true);
    setHasil(null);
    try {
      let data: AnalysisResult;

      if (userLoggedIn) {
        // Real endpoint: saves to DB + real pgvector search
        const title = judul.trim() || `Incident ${tanggal}`;
        data = await api.postmortems.submit(title, tanggal, konten, severity);
        addToast("Post-mortem saved to your workspace", "success");
      } else {
        // Demo endpoint: stateless analysis against demo data
        data = await api.analyze(konten, severity);
      }

      if (idPermintaan !== idPermintaanRef.current) return;
      setHasil(data);
      track("submit_analyzed", { has_recurrence: (data.recurrence_matches?.length ?? 0) > 0, authenticated: userLoggedIn });
    } catch (err) {
      if (idPermintaan !== idPermintaanRef.current) return;
      const pesan = err instanceof ApiError ? err.message : "Analysis failed. Try again.";
      addToast(pesan, "error");
    } finally {
      if (idPermintaan === idPermintaanRef.current) setLoading(false);
    }
  };

  const handleSubmitPaste = () => {
    if (teks.trim().length < 50) {
      addToast("Post-mortem must be at least 50 characters.", "warning");
      return;
    }
    analisis(teks);
  };

  const handleFileSelect = async (file: File) => {
    if (file.size > UKURAN_MAX_FILE) {
      addToast("File too large. Max 5MB.", "warning");
      return;
    }
    setFileTerpilih(file);
    try {
      const teksPreview = await file.text();
      setPreviewFile(teksPreview.slice(0, 300));
    } catch {
      addToast("Could not read file.", "error");
      setFileTerpilih(null);
      setPreviewFile("");
    }
  };

  const handleSubmitFile = async () => {
    if (!fileTerpilih) return;
    const idPermintaan = ++idPermintaanRef.current;
    setLoading(true);
    setHasil(null);
    try {
      let data: AnalysisResult;
      if (userLoggedIn) {
        const konten = await fileTerpilih.text();
        const title = judul.trim() || fileTerpilih.name.replace(/\.(txt|md)$/, "");
        data = await api.postmortems.submit(title, tanggal, konten, severity);
        addToast("Post-mortem saved to your workspace", "success");
      } else {
        data = await api.importFile(fileTerpilih);
      }
      if (idPermintaan !== idPermintaanRef.current) return;
      setHasil(data);
      track("submit_analyzed", { has_recurrence: (data.recurrence_matches?.length ?? 0) > 0, authenticated: userLoggedIn });
    } catch (err) {
      if (idPermintaan !== idPermintaanRef.current) return;
      const pesan = err instanceof ApiError ? err.message : "File import failed.";
      addToast(pesan, "error");
    } finally {
      if (idPermintaan === idPermintaanRef.current) setLoading(false);
    }
  };

  const tingkatSeverity = ["P0", "P1", "P2", "P3"];
  const warnaSeverity: Record<string, string> = {
    P0: "border-red-400 bg-red-500/15 text-red-300",
    P1: "border-amber-400 bg-amber-500/15 text-amber-300",
    P2: "border-blue-400 bg-blue-500/15 text-blue-300",
    P3: "border-emerald-400 bg-emerald-500/15 text-emerald-300",
  };

  const matches = hasil?.recurrence_matches ?? [];
  const matchUtama = matches[0];

  const buatVerdictRecurrence = () => {
    if (!matchUtama) return "";
    const jumlah = matchUtama.unimplemented_items.length;
    if (jumlah === 0) {
      return `This incident matches a prior failure from ${matchUtama.incident_date}, but all action items were completed.`;
    }
    const suffix = jumlah === 1 ? "item" : "items";
    return `${jumlah} unimplemented action ${suffix} from the ${matchUtama.incident_date} incident suggest this recurrence was preventable.`;
  };

  return (
    <div className="relative min-h-screen bg-[#020818]">
      <div className="absolute inset-0 bg-grid-dark opacity-50" />
      <div className="pointer-events-none absolute left-1/2 top-0 h-96 w-96 -translate-x-1/2 rounded-full bg-amber-500/6 blur-3xl" />

      <div className="relative z-10">
        <Navbar />

        <div className="mx-auto max-w-2xl px-6 pb-20 pt-24">
          {/* Header */}
          <div className="mb-10">
            <Link
              href="/"
              className="mb-6 inline-flex items-center gap-1.5 text-xs font-medium text-slate-500 transition hover:text-slate-300"
            >
              <ArrowLeft className="h-3.5 w-3.5" aria-hidden />
              Back to home
            </Link>
            <div className="flex items-center gap-3 mb-2">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-amber-500/25 bg-amber-500/10">
                <IconUpload className="h-5 w-5 text-amber-400" />
              </div>
              <div>
                <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">New analysis</p>
                <h1 className="text-2xl font-bold tracking-tight text-white">Submit Post-Mortem</h1>
              </div>
            </div>
            <p className="mt-2 text-sm text-slate-500">
              ECHO will analyze your incident and check if your team has seen this failure before.
            </p>

            {/* Auth badge */}
            {userLoggedIn ? (
              <div className="mt-4 inline-flex items-center gap-2 rounded-full border border-emerald-500/25 bg-emerald-500/10 px-3 py-1.5 text-xs font-semibold text-emerald-300">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                Saved to your workspace · Real similarity search
              </div>
            ) : (
              <div className="mt-4 inline-flex items-center gap-2 rounded-full border border-slate-700 bg-slate-800/50 px-3 py-1.5 text-xs font-medium text-slate-400">
                <Lock className="h-3 w-3" />
                Demo mode —{" "}
                <Link href="/register" className="font-semibold text-amber-400 hover:text-amber-300">
                  sign up
                </Link>{" "}
                to save results
              </div>
            )}
          </div>

          {/* Tabs */}
          <div className="mb-6 inline-flex rounded-xl border border-white/10 bg-white/5 p-1">
            {(["paste", "file"] as TabAktif[]).map((tab) => (
              <button
                key={tab}
                onClick={() => setTabAktif(tab)}
                className={`rounded-lg px-5 py-2 text-sm font-semibold transition-all ${
                  tabAktif === tab
                    ? "bg-white/12 text-white shadow-sm"
                    : "text-slate-500 hover:text-slate-300"
                }`}
              >
                {tab === "paste" ? "Paste text" : "Import file"}
              </button>
            ))}
          </div>

          {/* Input card */}
          <div className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-sm">
            {tabAktif === "paste" && (
              <div className="space-y-5">
                {/* Title + date — only shown when authenticated */}
                {userLoggedIn && (
                  <div className="grid grid-cols-2 gap-3">
                    <div className="col-span-2">
                      <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-slate-500">
                        Title
                      </label>
                      <input
                        type="text"
                        value={judul}
                        onChange={(e) => setJudul(e.target.value)}
                        placeholder="e.g. Payment Service Outage"
                        className="w-full rounded-xl border border-white/10 bg-white/6 px-4 py-2.5 text-sm text-white placeholder-slate-600 outline-none transition focus:border-amber-500/50 focus:ring-2 focus:ring-amber-500/20"
                      />
                    </div>
                    <div>
                      <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-slate-500">
                        Incident date
                      </label>
                      <input
                        type="date"
                        value={tanggal}
                        onChange={(e) => setTanggal(e.target.value)}
                        className="w-full rounded-xl border border-white/10 bg-white/6 px-4 py-2.5 text-sm text-white outline-none transition focus:border-amber-500/50 focus:ring-2 focus:ring-amber-500/20"
                      />
                    </div>
                  </div>
                )}

                <textarea
                  value={teks}
                  onChange={(e) => setTeks(e.target.value)}
                  placeholder="Paste your post-mortem notes here. Don't worry about formatting — ECHO will extract the structure. Include: what happened, timeline, root causes, action items, and who was involved."
                  className="min-h-[240px] w-full resize-y rounded-xl border border-white/8 bg-white/5 p-4 font-mono text-sm leading-relaxed text-slate-300 placeholder:text-slate-600 focus:border-amber-500/40 focus:bg-white/8 focus:outline-none focus:ring-1 focus:ring-amber-500/20 transition"
                />
                <div>
                  <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-600">
                    Severity (optional)
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {tingkatSeverity.map((s) => (
                      <button
                        key={s}
                        onClick={() => setSeverity(severity === s ? null : s)}
                        className={`rounded-lg border px-4 py-1.5 font-mono text-xs font-bold transition ${
                          severity === s
                            ? warnaSeverity[s]
                            : "border-white/10 bg-white/5 text-slate-500 hover:border-white/20 hover:text-slate-300"
                        }`}
                      >
                        {s}
                      </button>
                    ))}
                  </div>
                </div>
                <button
                  onClick={handleSubmitPaste}
                  disabled={loading}
                  className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-br from-amber-400 to-amber-600 py-3.5 text-sm font-bold text-white shadow-lg shadow-amber-500/25 transition hover:from-amber-300 hover:to-amber-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? (
                    <>
                      <span className="h-4 w-4 rounded-full border-2 border-white/30 border-t-white animate-spin" />
                      Analyzing...
                    </>
                  ) : (
                    <>
                      {userLoggedIn ? "Analyze & Save" : "Analyze with ECHO"}
                      <IconArrowRight className="h-4 w-4" />
                    </>
                  )}
                </button>
                {loading && (
                  <p className="text-center text-xs text-slate-600">
                    {userLoggedIn
                      ? "Extracting structure, generating embedding, searching your history..."
                      : "ECHO is analyzing your incident and searching for patterns..."}
                  </p>
                )}
              </div>
            )}

            {tabAktif === "file" && (
              <div>
                <div
                  onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                  onDragLeave={() => setDragOver(false)}
                  onDrop={(e) => {
                    e.preventDefault();
                    setDragOver(false);
                    const file = e.dataTransfer.files[0];
                    if (file) handleFileSelect(file);
                  }}
                  onClick={() => inputFileRef.current?.click()}
                  className={`cursor-pointer rounded-xl border-2 border-dashed p-12 text-center transition-all ${
                    dragOver
                      ? "border-amber-500/50 bg-amber-500/8"
                      : "border-white/10 hover:border-white/20 hover:bg-white/4"
                  }`}
                >
                  <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl border border-white/10 bg-white/8 text-slate-500">
                    <IconUpload className="h-6 w-6" />
                  </div>
                  <p className="font-semibold text-slate-300">Drop your post-mortem file here</p>
                  <p className="mt-1 text-sm text-slate-600">.txt or .md — max 5MB</p>
                  <p className="mt-3 text-sm font-medium text-amber-400/80">or browse files</p>
                  <input
                    ref={inputFileRef}
                    type="file"
                    accept=".txt,.md,text/plain"
                    className="hidden"
                    onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
                  />
                </div>
                {fileTerpilih && (
                  <div className="mt-5 space-y-4">
                    <div className="flex items-center gap-2 rounded-xl border border-white/8 bg-white/5 px-4 py-3 text-sm">
                      <span className="font-semibold text-slate-300">{fileTerpilih.name}</span>
                      <span className="text-slate-600">
                        ({(fileTerpilih.size / 1024).toFixed(1)} KB)
                      </span>
                    </div>
                    <pre className="max-h-28 overflow-auto rounded-xl border border-white/8 bg-black/30 p-3 font-mono text-xs leading-relaxed text-slate-500">
                      {previewFile}
                    </pre>

                    {/* Title + date + severity for authenticated users */}
                    {userLoggedIn && (
                      <div className="space-y-3">
                        <div className="grid grid-cols-2 gap-3">
                          <div className="col-span-2">
                            <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-slate-500">
                              Title
                            </label>
                            <input
                              type="text"
                              value={judul}
                              onChange={(e) => setJudul(e.target.value)}
                              placeholder={fileTerpilih.name.replace(/\.(txt|md)$/, "")}
                              className="w-full rounded-xl border border-white/10 bg-white/6 px-4 py-2.5 text-sm text-white placeholder-slate-600 outline-none transition focus:border-amber-500/50 focus:ring-2 focus:ring-amber-500/20"
                            />
                          </div>
                          <div>
                            <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-slate-500">
                              Incident date
                            </label>
                            <input
                              type="date"
                              value={tanggal}
                              onChange={(e) => setTanggal(e.target.value)}
                              className="w-full rounded-xl border border-white/10 bg-white/6 px-4 py-2.5 text-sm text-white outline-none transition focus:border-amber-500/50 focus:ring-2 focus:ring-amber-500/20"
                            />
                          </div>
                          <div>
                            <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-slate-500">
                              Severity
                            </label>
                            <div className="flex gap-1.5 flex-wrap pt-1">
                              {tingkatSeverity.map((s) => (
                                <button
                                  key={s}
                                  onClick={() => setSeverity(severity === s ? null : s)}
                                  className={`rounded-lg border px-3 py-1.5 font-mono text-xs font-bold transition ${
                                    severity === s
                                      ? warnaSeverity[s]
                                      : "border-white/10 bg-white/5 text-slate-500 hover:border-white/20 hover:text-slate-300"
                                  }`}
                                >
                                  {s}
                                </button>
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>
                    )}

                    <button
                      onClick={handleSubmitFile}
                      disabled={loading}
                      className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-br from-amber-400 to-amber-600 py-3.5 text-sm font-bold text-white shadow-lg shadow-amber-500/25 transition hover:from-amber-300 hover:to-amber-500 disabled:opacity-50"
                    >
                      {loading ? (
                        <>
                          <span className="h-4 w-4 rounded-full border-2 border-white/30 border-t-white animate-spin" />
                          Analyzing...
                        </>
                      ) : userLoggedIn ? "Analyze & Save" : "Analyze this file"}
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Hasil */}
          {hasil && (
            <div className="mt-8 space-y-6 animate-fade-up">
              {/* Saved badge for authenticated users */}
              {isPostmortemOut(hasil) && (
                <div className="flex items-center gap-2 rounded-xl border border-emerald-500/20 bg-emerald-500/8 px-4 py-3 text-sm font-medium text-emerald-300">
                  <Check className="h-4 w-4" />
                  Saved to workspace
                  <div className="ml-auto flex items-center gap-3">
                    <Link
                      href={`/postmortems/${hasil.id}`}
                      className="text-xs text-emerald-400 hover:text-emerald-200 underline underline-offset-2"
                    >
                      View details →
                    </Link>
                    <Link
                      href="/dashboard"
                      className="text-xs text-slate-400 hover:text-slate-200 underline underline-offset-2"
                    >
                      Dashboard
                    </Link>
                  </div>
                </div>
              )}

              {matchUtama ? (
                <RecurrenceAlert
                  similarityScore={matchUtama.similarity_score}
                  daysBetween={matchUtama.days_between}
                  matchedDate={matchUtama.incident_date}
                  unimplementedItems={matchUtama.unimplemented_items}
                  echoVerdict={buatVerdictRecurrence()}
                />
              ) : (
                <div className="flex items-center gap-3 rounded-2xl border border-emerald-500/20 bg-emerald-500/8 px-6 py-5 text-sm font-medium text-emerald-300">
                  <div className="flex h-7 w-7 items-center justify-center rounded-full border border-emerald-500/30 bg-emerald-500/15 text-emerald-400">
                    <Check className="h-4 w-4" aria-hidden />
                  </div>
                  No recurrences detected — this appears to be a new failure pattern
                </div>
              )}

              <div className="rounded-2xl border border-white/10 bg-white/5 p-6 space-y-5">
                <h2 className="font-bold text-white text-lg">Extracted structure</h2>
                <p className="text-sm leading-relaxed text-slate-400">{hasil.summary}</p>

                {hasil.severity && (
                  <div className="flex items-center gap-2">
                    <SeverityBadge severity={hasil.severity} />
                  </div>
                )}

                <div className="border-t border-white/8 pt-5">
                  <h3 className="text-[10px] font-bold uppercase tracking-widest text-slate-600 mb-3">
                    Root Causes
                  </h3>
                  <ul className="space-y-2.5">
                    {hasil.root_causes.map((rc) => (
                      <li key={rc} className="flex items-start gap-3 text-sm text-slate-400">
                        <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-red-500" />
                        {rc}
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="border-t border-white/8 pt-5">
                  <h3 className="text-[10px] font-bold uppercase tracking-widest text-slate-600 mb-3">
                    Action Items
                  </h3>
                  <div className="divide-y divide-white/5 rounded-xl border border-white/8 overflow-hidden">
                    {hasil.action_items.map((ai) => (
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

                {hasil.systems_affected.length > 0 && (
                  <div className="border-t border-white/8 pt-5">
                    <h3 className="text-[10px] font-bold uppercase tracking-widest text-slate-600 mb-3">
                      Systems Affected
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      {hasil.systems_affected.map((s) => (
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
