import { getToken } from "@/lib/auth";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const TIMEOUT_MS = 30000;
const UKURAN_MAX_FILE = 5 * 1024 * 1024;

export interface ActionItem {
  description: string;
  owner?: string;
  status: string;
  ticket_ref?: string | null;
}

export interface ClimaxData {
  title: string;
  incident_date: string;
  severity: string;
  summary: string;
  systems_affected: string[];
  similarity_score: number;
  days_between: number;
  matched_incident_title: string;
  matched_incident_date: string;
  unimplemented_items: ActionItem[];
  echo_verdict: string;
}

export interface Incident {
  id: string;
  title: string;
  incident_date: string;
  severity: string;
  summary: string;
  root_causes: string[];
  action_items: ActionItem[];
  systems_affected?: string[];
  has_recurrence?: boolean;
}

export interface PatternScore {
  score: number;
  total_postmortems: number;
  total_recurrences: number;
  recurrence_rate: number;
  avg_action_completion: number;
}

export interface RecurrenceMatch {
  incident_id: string;
  title: string;
  incident_date: string;
  similarity_score: number;
  days_between: number;
  unimplemented_items: ActionItem[];
}

export interface AnalyzeResult {
  summary: string;
  root_causes: string[];
  action_items: ActionItem[];
  severity: string | null;
  systems_affected: string[];
  recurrence_matches: RecurrenceMatch[];
}

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function fetchApi<T>(path: string, options?: RequestInit, withAuth = false): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);

  const headers: Record<string, string> = {
    ...(options?.headers as Record<string, string>),
  };
  if (withAuth) {
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  try {
    const respons = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
      signal: controller.signal,
    });

    if (respons.status === 429) {
      throw new ApiError("Demo limit reached. Try again in a minute.", 429);
    }

    if (!respons.ok) {
      let pesan = `API error: ${respons.status}`;
      try {
        const body = await respons.json();
        if (body.detail) pesan = typeof body.detail === "string" ? body.detail : pesan;
      } catch {
        /* respons bukan JSON */
      }
      throw new ApiError(pesan, respons.status);
    }

    return respons.json();
  } catch (err) {
    if (err instanceof ApiError) throw err;
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new ApiError("Request timed out. Check your connection.", 408);
    }
    throw new ApiError("Network error. Is the backend running?", 0);
  } finally {
    clearTimeout(timer);
  }
}

// ── Postmortem types ──────────────────────────────────────────────────────────

export interface PostmortemOut {
  id: string;
  title: string;
  incident_date: string;
  severity: string | null;
  summary: string;
  root_causes: string[];
  action_items: ActionItem[];
  systems_affected: string[];
  has_recurrence: boolean;
  recurrence_matches: RecurrenceMatch[];
}

// ── Auth types ────────────────────────────────────────────────────────────────

export interface AuthUser {
  id: string;
  email: string;
  org_name: string | null;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

// ── API client ────────────────────────────────────────────────────────────────

export const api = {
  auth: {
    register: (email: string, password: string, org_name?: string) =>
      fetchApi<TokenResponse>("/api/v1/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, org_name }),
      }),
    login: (email: string, password: string) =>
      fetchApi<TokenResponse>("/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      }),
    me: () => fetchApi<AuthUser>("/api/v1/auth/me", {}, true),
  },
  getClimax: () => fetchApi<ClimaxData>("/api/v1/demo/climax"),
  getIncidents: () => fetchApi<Incident[]>("/api/v1/demo/incidents"),
  getPatternScore: () => fetchApi<PatternScore>("/api/v1/demo/pattern-score"),
  analyze: (raw_content: string, severity_hint?: string | null) =>
    fetchApi<AnalyzeResult>("/api/v1/demo/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        raw_content,
        ...(severity_hint ? { severity_hint } : {}),
      }),
    }),
  importFile: async (file: File): Promise<AnalyzeResult> => {
    if (file.size > UKURAN_MAX_FILE) {
      throw new ApiError("File too large. Max 5MB.", 413);
    }
    const formData = new FormData();
    formData.append("file", file);
    return fetchApi<AnalyzeResult>("/api/v1/postmortems/demo-import", {
      method: "POST",
      body: formData,
    });
  },
  postmortems: {
    submit: (title: string, incident_date: string, raw_content: string, severity?: string | null) =>
      fetchApi<PostmortemOut>("/api/v1/postmortems", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, incident_date, raw_content, ...(severity ? { severity } : {}) }),
      }, true),
    list: () => fetchApi<PostmortemOut[]>("/api/v1/postmortems", {}, true),
    get: (id: string) => fetchApi<PostmortemOut>(`/api/v1/postmortems/${id}`, {}, true),
  },
};
