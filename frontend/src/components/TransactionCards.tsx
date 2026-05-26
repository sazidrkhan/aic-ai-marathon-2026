import { ArrowRight, CheckCircle2, AlertTriangle } from "lucide-react";
import type { MatchedTransaction, UnmatchedTransaction } from "@/lib/reconmate-api";

function fmt(n?: number) {
  if (n === undefined || n === null) return "—";
  return n.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 });
}

export function MatchedTransactionCards({ items }: { items?: MatchedTransaction[] }) {
  if (!items || items.length === 0) return null;
  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-emerald-300 flex items-center gap-2">
        <CheckCircle2 className="w-4 h-4" /> Matched Transactions ({items.length})
      </h3>
      <div className="premium-card-group grid sm:grid-cols-2 gap-3">
        {items.map((t, i) => (
          <div key={i} className="premium-card glass-card rounded-xl p-4 border-emerald-400/20">
            <div className="flex items-center justify-between gap-2">
              <div className="font-medium text-white truncate">{t.sender_name ?? t.proof_id}</div>
              {t.match_confidence !== undefined && (
                <span className="text-xs px-2 py-0.5 rounded-md bg-emerald-500/15 text-emerald-300 border border-emerald-400/30">
                  {(t.match_confidence * 100).toFixed(0)}%
                </span>
              )}
            </div>
            <div className="mt-2 flex items-center gap-2 text-sm">
              <span className="text-cyan-300 font-mono">
                {fmt(t.amount)} {t.currency}
              </span>
              <ArrowRight className="w-3.5 h-3.5 text-muted-foreground" />
              <span className="text-purple-300 font-mono">{fmt(t.actual_amount_local)}</span>
              <span className="text-[11px] text-muted-foreground">
                (expected {fmt(t.expected_amount_local)})
              </span>
            </div>
            {t.reason_codes && t.reason_codes.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1">
                {t.reason_codes.map((r) => (
                  <span
                    key={r}
                    className="text-[10px] px-1.5 py-0.5 rounded bg-white/5 border border-white/10 text-muted-foreground"
                  >
                    {r}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export function UnmatchedTransactionCards({ items }: { items?: UnmatchedTransaction[] }) {
  if (!items || items.length === 0) return null;
  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-amber-300 flex items-center gap-2">
        <AlertTriangle className="w-4 h-4" /> Unmatched / Discrepancies ({items.length})
      </h3>
      <div className="premium-card-group grid sm:grid-cols-2 gap-3">
        {items.map((t, i) => (
          <div key={i} className="premium-card glass-card rounded-xl p-4 border-amber-400/20">
            <div className="font-medium text-white">{t.sender_name ?? t.proof_id}</div>
            <div className="mt-2 text-sm">
              <span className="text-cyan-300 font-mono">
                {fmt(t.amount)} {t.currency}
              </span>
              {t.expected_amount_local !== undefined && (
                <span className="text-[11px] text-muted-foreground ml-2">
                  → expected {fmt(t.expected_amount_local)}
                </span>
              )}
            </div>
            {t.reason && (
              <p className="mt-2 text-xs text-amber-200/80 leading-relaxed">{t.reason}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
