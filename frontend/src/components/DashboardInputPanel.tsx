import { useState } from "react";
import { Play, FileJson, Loader2 } from "lucide-react";
import { SAMPLE_PAYLOAD } from "@/lib/reconmate-api";

interface Props {
  onRun: (payload: unknown) => void;
  loading: boolean;
}

const CURRENCIES = ["MYR", "USD", "SGD", "EUR", "GBP", "JPY", "AUD", "INR", "CNY"];

export function DashboardInputPanel({ onRun, loading }: Props) {
  const [company, setCompany] = useState(SAMPLE_PAYLOAD.company_name);
  const [currency, setCurrency] = useState(SAMPLE_PAYLOAD.base_currency);
  const [json, setJson] = useState(JSON.stringify(SAMPLE_PAYLOAD, null, 2));
  const [jsonError, setJsonError] = useState<string | null>(null);

  const handleLoadSample = () => {
    setCompany(SAMPLE_PAYLOAD.company_name);
    setCurrency(SAMPLE_PAYLOAD.base_currency);
    setJson(JSON.stringify(SAMPLE_PAYLOAD, null, 2));
    setJsonError(null);
  };

  const handleRun = () => {
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
  };

  return (
    <div className="glass-card rounded-2xl p-5 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-cyan-300">
          <FileJson className="w-3.5 h-3.5" /> Advanced Demo Payload
        </div>
        <span className="text-[10px] uppercase tracking-wider text-purple-300/80">Step 3</span>
      </div>
      <p className="text-[11px] text-muted-foreground -mt-1">
        Used by the current backend contract for reliable demo reconciliation.
      </p>

      <div className="space-y-1.5">
        <label className="text-xs text-muted-foreground">Company Name</label>
        <input
          value={company}
          onChange={(e) => setCompany(e.target.value)}
          className="w-full bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-cyan-400/60"
        />
      </div>

      <div className="space-y-1.5">
        <label className="text-xs text-muted-foreground">Base Currency</label>
        <select
          value={currency}
          onChange={(e) => setCurrency(e.target.value)}
          className="w-full bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-cyan-400/60"
        >
          {CURRENCIES.map((c) => (
            <option key={c} value={c} className="bg-background">
              {c}
            </option>
          ))}
        </select>
      </div>

      <div className="space-y-1.5">
        <label className="text-xs text-muted-foreground">Structured JSON Payload</label>
        <textarea
          value={json}
          onChange={(e) => setJson(e.target.value)}
          rows={14}
          spellCheck={false}
          className="w-full font-mono text-[11px] bg-black/40 border border-white/10 rounded-lg px-3 py-2 focus:outline-none focus:border-purple-400/60 scrollbar-thin"
        />
        {jsonError && <p className="text-xs text-red-300">{jsonError}</p>}
      </div>

      <div className="flex flex-col sm:flex-row gap-2">
        <button
          onClick={handleLoadSample}
          className="flex-1 px-4 py-2.5 rounded-lg border border-white/15 hover:border-cyan-400/60 text-sm font-medium transition-colors"
        >
          Load Sample Payload
        </button>
        <button
          onClick={handleRun}
          disabled={loading}
          className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-gradient-to-r from-purple-600 to-cyan-500 text-white text-sm font-semibold neon-glow disabled:opacity-60 disabled:cursor-not-allowed hover:scale-[1.01] transition-transform"
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" /> Reasoning…
            </>
          ) : (
            <>
              <Play className="w-4 h-4" /> Run Reconciliation
            </>
          )}
        </button>
      </div>
    </div>
  );
}
