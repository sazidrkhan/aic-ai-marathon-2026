import { useRef, useState } from "react";
import {
  FileText,
  Table as TableIcon,
  FileJson,
  Upload,
  Play,
  Loader2,
  AlertTriangle,
  CheckCircle2,
  Sparkles,
} from "lucide-react";
import { extractProof, SAMPLE_PAYLOAD, type OcrExtractResponse } from "@/lib/reconmate-api";

type Mode = "proof" | "bank" | "advanced";

const CURRENCIES = ["MYR", "USD", "SGD", "EUR", "GBP", "JPY", "AUD", "INR", "CNY"];

interface ParsedCsv {
  headers: string[];
  rows: string[][];
  totalRows: number;
}

function parseCsv(text: string): ParsedCsv {
  const lines = text.split(/\r?\n/).map((l) => l.trim()).filter((l) => l.length > 0);
  if (lines.length === 0) throw new Error("CSV is empty");
  const splitLine = (line: string): string[] => {
    const out: string[] = [];
    let cur = "";
    let inQ = false;
    for (let i = 0; i < line.length; i++) {
      const c = line[i];
      if (c === '"') {
        if (inQ && line[i + 1] === '"') {
          cur += '"';
          i++;
        } else inQ = !inQ;
      } else if (c === "," && !inQ) {
        out.push(cur);
        cur = "";
      } else cur += c;
    }
    out.push(cur);
    return out.map((s) => s.trim());
  };
  const headers = splitLine(lines[0]);
  const rows = lines.slice(1).map(splitLine);
  return { headers, rows, totalRows: rows.length };
}

interface Props {
  onRun: (payload: unknown) => void;
  reconcileLoading: boolean;
}

const MODES: { id: Mode; label: string; icon: typeof FileText }[] = [
  { id: "proof", label: "Payment Proof", icon: FileText },
  { id: "bank", label: "Bank Statement", icon: TableIcon },
  { id: "advanced", label: "Advanced Payload", icon: FileJson },
];

export function AgentInputConsole({ onRun, reconcileLoading }: Props) {
  const [mode, setMode] = useState<Mode>("advanced");
  const [focused, setFocused] = useState(false);

  // Proof state
  const proofInputRef = useRef<HTMLInputElement>(null);
  const [proofFile, setProofFile] = useState<File | null>(null);
  const [proofLoading, setProofLoading] = useState(false);
  const [proofResult, setProofResult] = useState<OcrExtractResponse | null>(null);
  const [proofError, setProofError] = useState<string | null>(null);

  // Bank state
  const [bankFile, setBankFile] = useState<File | null>(null);
  const [parsedCsv, setParsedCsv] = useState<ParsedCsv | null>(null);
  const [bankError, setBankError] = useState<string | null>(null);

  // Advanced state
  const [company, setCompany] = useState(SAMPLE_PAYLOAD.company_name);
  const [currency, setCurrency] = useState(SAMPLE_PAYLOAD.base_currency);
  const [json, setJson] = useState(JSON.stringify(SAMPLE_PAYLOAD, null, 2));
  const [jsonError, setJsonError] = useState<string | null>(null);

  async function handleExtractProof() {
    if (!proofFile) return;
    setProofLoading(true);
    setProofError(null);
    setProofResult(null);
    try {
      const r = await extractProof(proofFile);
      setProofResult(r);
    } catch (e) {
      setProofError((e as Error).message);
    } finally {
      setProofLoading(false);
    }
  }

  async function handleBankFile(f: File | null) {
    setBankError(null);
    setParsedCsv(null);
    setBankFile(f);
    if (!f) return;
    try {
      const text = await f.text();
      setParsedCsv(parseCsv(text));
    } catch (e) {
      setBankError("Could not parse CSV: " + (e as Error).message);
    }
  }

  function handleLoadSample() {
    setCompany(SAMPLE_PAYLOAD.company_name);
    setCurrency(SAMPLE_PAYLOAD.base_currency);
    setJson(JSON.stringify(SAMPLE_PAYLOAD, null, 2));
    setJsonError(null);
  }

  function handleRunReconcile() {
    let parsed: Record<string, unknown>;
    try {
      parsed = JSON.parse(json);
    } catch (e) {
      setJsonError("Invalid JSON: " + (e as Error).message);
      return;
    }
    setJsonError(null);
    parsed.company_name = company || parsed.company_name;
    parsed.base_currency = currency || parsed.base_currency;
    onRun(parsed);
  }

  const proofStubbed = (proofResult?.status || "").toLowerCase() === "stubbed";

  const ringClass = focused
    ? "shadow-[0_0_0_1px_rgba(34,211,238,0.6),0_0_60px_-10px_rgba(168,85,247,0.6),0_0_80px_-20px_rgba(34,211,238,0.5)]"
    : "shadow-[0_0_0_1px_rgba(168,85,247,0.3),0_0_40px_-12px_rgba(168,85,247,0.4)]";

  return (
    <div className="relative">
      {/* Outer glow halo */}
      <div
        aria-hidden
        className="pointer-events-none absolute -inset-4 rounded-[2rem] bg-[radial-gradient(ellipse_at_top,rgba(168,85,247,0.25),transparent_60%),radial-gradient(ellipse_at_bottom,rgba(34,211,238,0.2),transparent_60%)] blur-2xl opacity-80"
      />

      <div
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        className={`relative rounded-2xl bg-gradient-to-b from-[rgba(20,16,40,0.85)] to-[rgba(8,10,28,0.9)] backdrop-blur-xl border border-purple-400/40 transition-shadow duration-500 ${ringClass}`}
      >
        {/* Header */}
        <div className="px-5 pt-4 pb-3 flex items-center justify-between border-b border-white/5">
          <div className="flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-400" />
            </span>
            <span className="text-[10px] uppercase tracking-[0.25em] text-cyan-300 font-semibold">
              ReconMate Agent Console
            </span>
          </div>
          <Sparkles className="w-3.5 h-3.5 text-purple-300/70" />
        </div>

        <p className="px-5 pt-3 text-xs text-muted-foreground">
          Choose an input mode and let the agent execute the reconciliation workflow.
        </p>

        {/* Active mode pane */}
        <div className="px-5 py-4 min-h-[260px]">
          {mode === "proof" && (
            <div className="space-y-3">
              <label
                htmlFor="console-proof-file"
                className="block cursor-pointer rounded-xl border border-dashed border-white/15 hover:border-cyan-400/60 bg-black/30 p-6 text-center transition-colors"
              >
                <FileText className="w-7 h-7 mx-auto text-purple-300" />
                <div className="mt-2 text-sm font-medium text-white">Upload Payment Proof</div>
                <div className="text-[11px] text-muted-foreground mt-0.5">PDF, PNG, JPG, JPEG</div>
                {proofFile && (
                  <div className="mt-2 text-xs text-cyan-200 truncate">{proofFile.name}</div>
                )}
                <input
                  ref={proofInputRef}
                  id="console-proof-file"
                  type="file"
                  accept=".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg"
                  className="hidden"
                  onChange={(e) => {
                    setProofResult(null);
                    setProofError(null);
                    setProofFile(e.target.files?.[0] ?? null);
                  }}
                />
              </label>

              {proofError && (
                <div className="rounded-lg border border-red-400/40 bg-red-500/10 p-3 text-xs text-red-200">
                  {proofError}
                </div>
              )}

              {proofResult && (
                <div className="space-y-2">
                  {proofStubbed ? (
                    <div className="inline-flex items-start gap-2 rounded-md border border-amber-400/40 bg-amber-500/10 px-2.5 py-1.5 text-[11px] text-amber-200">
                      <AlertTriangle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
                      <span>
                        Stubbed OCR — backend accepted the file but real OCR is not enabled yet
                      </span>
                    </div>
                  ) : (
                    <div className="inline-flex items-center gap-1.5 rounded-md border border-emerald-400/40 bg-emerald-500/10 px-2.5 py-1 text-[11px] text-emerald-200">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      OCR {proofResult.status || "ok"}
                    </div>
                  )}
                  <div className="rounded-lg border border-white/10 bg-black/40 p-3 text-xs space-y-1">
                    {proofResult.filename && (
                      <div>
                        <span className="text-muted-foreground">filename: </span>
                        <span className="text-cyan-200">{proofResult.filename}</span>
                      </div>
                    )}
                    {proofResult.message && (
                      <div className="text-muted-foreground">{proofResult.message}</div>
                    )}
                    {proofResult.ocr_text && (
                      <pre className="mt-2 max-h-40 overflow-auto scrollbar-thin whitespace-pre-wrap text-[11px] text-cyan-100/80">
                        {proofResult.ocr_text}
                      </pre>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          {mode === "bank" && (
            <div className="space-y-3">
              <label
                htmlFor="console-bank-file"
                className="block cursor-pointer rounded-xl border border-dashed border-white/15 hover:border-purple-400/60 bg-black/30 p-6 text-center transition-colors"
              >
                <Upload className="w-7 h-7 mx-auto text-cyan-300" />
                <div className="mt-2 text-sm font-medium text-white">Upload Bank Statement CSV</div>
                <div className="text-[11px] text-muted-foreground mt-0.5">
                  .csv only — preview parsed locally
                </div>
                {bankFile && (
                  <div className="mt-2 text-xs text-cyan-200 truncate">{bankFile.name}</div>
                )}
                <input
                  id="console-bank-file"
                  type="file"
                  accept=".csv,text/csv"
                  className="hidden"
                  onChange={(e) => handleBankFile(e.target.files?.[0] ?? null)}
                />
              </label>

              {bankError && (
                <div className="inline-flex items-start gap-2 rounded-md border border-amber-400/40 bg-amber-500/10 px-2.5 py-1.5 text-[11px] text-amber-200">
                  <AlertTriangle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
                  <span>{bankError}</span>
                </div>
              )}

              {parsedCsv && (
                <div className="rounded-lg border border-white/10 bg-black/40 overflow-hidden">
                  <div className="px-3 py-2 text-[11px] text-muted-foreground border-b border-white/10">
                    Showing first {Math.min(5, parsedCsv.rows.length)} of {parsedCsv.totalRows} rows
                  </div>
                  <div className="overflow-x-auto scrollbar-thin">
                    <table className="w-full text-[11px]">
                      <thead className="bg-white/5">
                        <tr>
                          {parsedCsv.headers.map((h, i) => (
                            <th
                              key={i}
                              className="px-2 py-1.5 text-left font-medium text-cyan-200 whitespace-nowrap"
                            >
                              {h}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {parsedCsv.rows.slice(0, 5).map((r, i) => (
                          <tr key={i} className="border-t border-white/5">
                            {r.map((c, j) => (
                              <td
                                key={j}
                                className="px-2 py-1.5 text-foreground/80 whitespace-nowrap"
                              >
                                {c}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}

          {mode === "advanced" && (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-2">
                <div className="space-y-1.5">
                  <label className="text-[11px] uppercase tracking-wider text-muted-foreground">
                    Company
                  </label>
                  <input
                    value={company}
                    onChange={(e) => setCompany(e.target.value)}
                    onFocus={() => setFocused(true)}
                    className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-cyan-400/60"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-[11px] uppercase tracking-wider text-muted-foreground">
                    Base Currency
                  </label>
                  <select
                    value={currency}
                    onChange={(e) => setCurrency(e.target.value)}
                    className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-cyan-400/60"
                  >
                    {CURRENCIES.map((c) => (
                      <option key={c} value={c} className="bg-background">
                        {c}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <label className="text-[11px] uppercase tracking-wider text-muted-foreground">
                    Structured JSON Payload
                  </label>
                  <button
                    onClick={handleLoadSample}
                    className="text-[11px] px-2 py-0.5 rounded-md border border-white/15 hover:border-cyan-400/60 text-cyan-200 transition-colors"
                  >
                    Load Sample Payload
                  </button>
                </div>
                <textarea
                  value={json}
                  onChange={(e) => setJson(e.target.value)}
                  onFocus={() => setFocused(true)}
                  rows={12}
                  spellCheck={false}
                  className="w-full font-mono text-[11px] bg-black/50 border border-white/10 rounded-lg px-3 py-2 focus:outline-none focus:border-purple-400/60 scrollbar-thin"
                />
                {jsonError && <p className="text-xs text-red-300">{jsonError}</p>}
              </div>
            </div>
          )}
        </div>

        {/* Footer controls */}
        <div className="px-3 py-3 border-t border-white/5 flex items-center justify-between gap-2 flex-wrap">
          {/* Mode pills */}
          <div className="flex items-center gap-1 bg-black/40 border border-white/10 rounded-full p-1">
            {MODES.map((m) => {
              const Icon = m.icon;
              const active = mode === m.id;
              return (
                <button
                  key={m.id}
                  onClick={() => setMode(m.id)}
                  className={`relative inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[11px] font-medium transition-all ${
                    active
                      ? "bg-gradient-to-r from-purple-500/40 to-cyan-500/40 text-white shadow-[0_0_15px_rgba(168,85,247,0.4)] border border-cyan-400/40"
                      : "text-muted-foreground hover:text-white"
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">{m.label}</span>
                </button>
              );
            })}
          </div>

          {/* Action button */}
          {mode === "proof" && (
            <button
              disabled={!proofFile || proofLoading}
              onClick={handleExtractProof}
              className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-purple-600 to-cyan-500 text-white text-sm font-semibold neon-glow disabled:opacity-50 disabled:cursor-not-allowed hover:scale-[1.02] transition-transform"
            >
              {proofLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" /> Extracting…
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" /> Extract Proof Text
                </>
              )}
            </button>
          )}
          {mode === "bank" && (
            <button
              disabled
              className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-purple-600/70 to-cyan-500/70 text-white text-sm font-semibold opacity-80 cursor-default"
              title="CSV is previewed locally"
            >
              <TableIcon className="w-4 h-4" />
              {parsedCsv ? `Previewed ${parsedCsv.totalRows} rows` : "Preview Bank CSV"}
            </button>
          )}
          {mode === "advanced" && (
            <button
              onClick={handleRunReconcile}
              disabled={reconcileLoading}
              className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-purple-600 to-cyan-500 text-white text-sm font-semibold neon-glow disabled:opacity-60 disabled:cursor-not-allowed hover:scale-[1.02] transition-transform"
            >
              {reconcileLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" /> Reasoning…
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" /> Run Reconciliation
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}