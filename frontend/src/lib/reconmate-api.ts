export const API_BASE_URL =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "http://127.0.0.1:8000";

export interface HealthResponse {
  status: string;
  [key: string]: unknown;
}

export async function checkHealth(): Promise<HealthResponse | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/health`, { method: "GET" });
    if (!res.ok) return null;
    return (await res.json()) as HealthResponse;
  } catch {
    return null;
  }
}

export interface OcrExtractResponse {
  filename?: string;
  status?: string;
  engine?: string | null;
  confidence?: number | null;
  ocr_text?: string;
  lines?: string[];
  fields?: {
    sender_name?: string | null;
    amount?: string | null;
    currency?: string | null;
    reference?: string | null;
    date?: string | null;
  };
  message?: string;
  [key: string]: unknown;
}

export async function extractProof(file: File): Promise<OcrExtractResponse> {
  const fd = new FormData();
  fd.append("file", file);
  const res = await request(`${API_BASE_URL}/api/ocr-extract`, {
    method: "POST",
    body: fd,
  });
  const text = await res.text();
  let data: OcrExtractResponse;
  try {
    data = JSON.parse(text);
  } catch {
    throw new Error(`Invalid JSON from /api/ocr-extract (${res.status}): ${text.slice(0, 200)}`);
  }
  if (!res.ok) {
    const detail = (data as { detail?: string; error?: string }).detail;
    throw new Error(detail || (data as { error?: string }).error || `OCR backend returned ${res.status}`);
  }
  return data;
}

export interface AgentTraceItem {
  tool?: string;
  agent?: string;
  name?: string;
  status?: string;
  message?: string;
  output?: unknown;
  [key: string]: unknown;
}

export interface MatchedTransaction {
  proof_id?: string;
  bank_row_id?: string;
  sender_name?: string;
  amount?: number;
  currency?: string;
  expected_amount_local?: number | string;
  actual_amount_local?: number | string;
  match_confidence?: number;
  confidence?: string;
  classification?: string;
  reference_found?: boolean;
  date_within_tolerance?: boolean;
  sender_match?: boolean;
  amount_within_tolerance?: boolean;
  fee_difference?: number | string | null;
  reason_codes?: string[];
  reasoning_facts?: string[];
  [key: string]: unknown;
}

export interface UnmatchedTransaction {
  proof_id?: string;
  sender_name?: string;
  amount?: number;
  currency?: string;
  expected_amount_local?: number;
  reason?: string;
  reason_codes?: string[];
  [key: string]: unknown;
}

export interface BackendDocument {
  generated: boolean;
  source: string;
  content: string;
}

export interface ReconcileResponse {
  run_id?: string;
  company_name?: string;
  base_currency?: string;
  computed_by_backend?: boolean;
  summary?: string | Record<string, unknown>;
  documents?: {
    reconciliation_report?: BackendDocument;
    discrepancy_summary?: BackendDocument;
    [key: string]: unknown;
  };
  agent_trace?: AgentTraceItem[];
  source?: string;
  report_source?: string;
  fallback_used?: boolean;
  llm_error?: string | null;
  model?: string | null;
  error?: string;
  transactions?: MatchedTransaction[];
  matched_transactions?: MatchedTransaction[];
  unmatched_transactions?: UnmatchedTransaction[];
  unmatched_payment_proofs?: UnmatchedTransaction[];
  unmatched_bank_rows?: UnmatchedTransaction[];
  possible_matches?: MatchedTransaction[];
  [key: string]: unknown;
}

async function request(url: string, options: RequestInit): Promise<Response> {
  console.debug("[ReconMate] →", options.method || "GET", url);
  try {
    const res = await fetch(url, options);
    console.debug("[ReconMate] ←", res.status, url);
    return res;
  } catch (err) {
    console.error("[ReconMate] ✗", url, (err as Error).message);
    throw err;
  }
}

export async function runReconciliation(payload: unknown): Promise<ReconcileResponse> {
  const url = `${API_BASE_URL}/api/reconcile/agent`;
  const res = await request(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const text = await res.text();
  let data: ReconcileResponse;
  try {
    data = JSON.parse(text);
  } catch {
    throw new Error(`Invalid JSON from backend (${res.status}): ${text.slice(0, 200)}`);
  }
  if (!res.ok) {
    const detail = (data as Record<string, unknown>).detail;
    const detailMsg = typeof detail === "string"
      ? detail
      : Array.isArray(detail)
        ? (detail as Array<{ msg?: string; loc?: unknown[] }>).map((d) => `[${(d.loc || []).join(".")}] ${d.msg || ""}`).join("; ")
        : null;
    throw new Error(detailMsg || data.error || data.llm_error || `Backend returned ${res.status}`);
  }
  // Normalize agent response: split transactions by classification
  if (data.transactions && !data.matched_transactions) {
    const matched: MatchedTransaction[] = [];
    const possible: MatchedTransaction[] = [];
    const unmatched: UnmatchedTransaction[] = [];
    for (const t of data.transactions) {
      if (t.classification === "matched") matched.push(t);
      else if (t.classification === "possible") possible.push(t);
      else unmatched.push({ proof_id: t.proof_id, reason_codes: t.reason_codes });
    }
    data.matched_transactions = matched;
    data.possible_matches = possible;
    data.unmatched_transactions = unmatched;
  }
  return data;
}

export const SAMPLE_PAYLOAD = {
  run_id: "demo_001",
  company_name: "Demo SME Trading Sdn Bhd",
  base_currency: "MYR",
  date_tolerance_days: 3,
  fee_tolerance: { percent: 0.02, fixed: 20 },
  fx_rates: [
    { pair: "USD_MYR", rate: 4.45, date: "2026-05-27" },
  ],
  payment_proofs: [
    {
      proof_id: "proof_001",
      sender_name: "ABC Trading Ltd",
      amount: 1000,
      currency: "USD",
      reference: "INV-2026-001",
      payment_date: "2026-05-20",
    },
    {
      proof_id: "proof_002",
      sender_name: "XYZ Global",
      amount: 500,
      currency: "MYR",
      reference: "PO-9876",
      payment_date: "2026-05-21",
    },
  ],
  bank_rows: [
    {
      bank_row_id: "bank_001",
      amount_local: 4450,
      currency: "MYR",
      settlement_date: "2026-05-22",
      description: "INV-2026-001 ABC Trading Ltd",
    },
    {
      bank_row_id: "bank_002",
      amount_local: 500,
      currency: "MYR",
      settlement_date: "2026-05-23",
      description: "PO-9876 XYZ Global",
    },
  ],
};
