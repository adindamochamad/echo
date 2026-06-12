type EventName = "demo_viewed" | "recurrence_alert_seen" | "submit_analyzed" | "page_view";

export function track(namaEvent: EventName, properti?: Record<string, unknown>) {
  if (typeof window === "undefined") return;
  // Novus/Pendo analytics
  const pendo = (window as unknown as { pendo?: { track?: (e: string, p?: Record<string, unknown>) => void } }).pendo;
  if (pendo?.track) {
    pendo.track(namaEvent, properti);
  }
  if (process.env.NODE_ENV === "development") {
    console.log("[analytics]", namaEvent, properti);
  }
}
