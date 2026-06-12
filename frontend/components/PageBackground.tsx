"use client";

/** Wrapper latar — Three.js network graph + overlay readability */

import { ThreeBackground } from "./ThreeBackground";

interface PageBackgroundProps {
  variant?: "hero" | "section" | "dashboard" | "submit";
}

export function PageBackground({ variant = "hero" }: PageBackgroundProps) {
  return <ThreeBackground variant={variant} />;
}
