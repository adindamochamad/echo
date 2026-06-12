"use client";

import dynamic from "next/dynamic";
import { Suspense, useEffect, useRef, useState } from "react";
import { CanvasErrorBoundary } from "./three/CanvasErrorBoundary";

const EchoCanvas = dynamic(() => import("./three/EchoCanvas"), {
  ssr: false,
  loading: () => (
    <div className="absolute inset-0 bg-gradient-to-b from-white via-slate-50 to-slate-100" />
  ),
});

type VariantLatar = "hero" | "section" | "dashboard" | "submit";

interface ThreeBackgroundProps {
  variant?: VariantLatar;
}

const OVERLAY: Record<VariantLatar, string> = {
  hero: "bg-gradient-to-b from-white/85 via-white/50 to-slate-50/65",
  section: "bg-gradient-to-b from-slate-100/75 via-slate-50/45 to-slate-100/70",
  dashboard: "bg-gradient-to-br from-slate-50/80 via-white/55 to-slate-100/72",
  submit: "bg-gradient-to-tr from-slate-50/82 via-white/52 to-slate-100/75",
};

const GRADIENT_STATIS: Record<VariantLatar, string> = {
  hero: "bg-gradient-to-b from-white via-slate-50/80 to-slate-100",
  section: "bg-gradient-to-b from-slate-100 via-slate-50/70 to-slate-100",
  dashboard: "bg-gradient-to-br from-slate-50 via-white/70 to-slate-100",
  submit: "bg-gradient-to-tr from-slate-50 via-white/75 to-slate-100",
};

export function ThreeBackground({ variant = "hero" }: ThreeBackgroundProps) {
  const kontainerRef = useRef<HTMLDivElement>(null);
  const [aktif, setAktif] = useState(true);
  const [gerakDimatikan, setGerakDimatikan] = useState(false);

  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const perbarui = () => setGerakDimatikan(media.matches);
    perbarui();
    media.addEventListener("change", perbarui);
    return () => media.removeEventListener("change", perbarui);
  }, []);

  useEffect(() => {
    if (gerakDimatikan || !kontainerRef.current) return;

    const observer = new IntersectionObserver(
      ([entry]) => setAktif(entry.isIntersecting),
      { threshold: 0.05, rootMargin: "100px" }
    );
    observer.observe(kontainerRef.current);
    return () => observer.disconnect();
  }, [gerakDimatikan]);

  if (gerakDimatikan) {
    return (
      <div
        className={`pointer-events-none absolute inset-0 overflow-hidden ${GRADIENT_STATIS[variant]}`}
        aria-hidden
      >
        <div className="absolute inset-0 bg-grid opacity-[0.12]" />
      </div>
    );
  }

  return (
    <div
      ref={kontainerRef}
      className="pointer-events-none absolute inset-0 overflow-hidden"
      aria-hidden
    >
      <CanvasErrorBoundary variant={variant}>
        <Suspense fallback={<div className="absolute inset-0 bg-slate-50" />}>
          <EchoCanvas variant={variant} aktif={aktif} />
        </Suspense>
      </CanvasErrorBoundary>
      <div className={`absolute inset-0 ${OVERLAY[variant]}`} />
      <div className="absolute inset-0 bg-grid opacity-[0.12]" />
    </div>
  );
}
