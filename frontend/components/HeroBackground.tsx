"use client";

import dynamic from "next/dynamic";
import { Suspense, useEffect, useRef, useState } from "react";
import { CanvasErrorBoundary } from "./three/CanvasErrorBoundary";

const EchoCanvas = dynamic(() => import("./three/EchoCanvas"), {
  ssr: false,
  loading: () => <div className="absolute inset-0 bg-[#020818]" />,
});

/** Latar hero — Three.js gelap dengan partikel bercahaya */
export function HeroBackground() {
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
      { threshold: 0.05 }
    );
    observer.observe(kontainerRef.current);
    return () => observer.disconnect();
  }, [gerakDimatikan]);

  if (gerakDimatikan) {
    return (
      <div className="pointer-events-none absolute inset-0" aria-hidden>
        <div className="absolute inset-0 bg-[#020818]" />
        <div className="absolute inset-0 bg-grid-dark opacity-60" />
        <div className="absolute inset-x-0 bottom-0 h-48 bg-gradient-to-t from-[#020818] to-transparent" />
      </div>
    );
  }

  return (
    <div ref={kontainerRef} className="pointer-events-none absolute inset-0" aria-hidden>
      <CanvasErrorBoundary variant="hero">
        <Suspense fallback={<div className="absolute inset-0 bg-[#020818]" />}>
          <EchoCanvas variant="hero" aktif={aktif} />
        </Suspense>
      </CanvasErrorBoundary>
      {/* Overlay gelap ringan agar teks tetap terbaca */}
      <div className="absolute inset-0 bg-gradient-to-b from-[#020818]/55 via-[#020818]/30 to-[#020818]/70" />
      <div className="absolute inset-x-0 bottom-0 h-40 bg-gradient-to-t from-[#020818] to-transparent" />
    </div>
  );
}
