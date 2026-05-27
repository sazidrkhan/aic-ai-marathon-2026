import { CheckCircle2, AlertTriangle, Sparkles, Shield, Brain } from "lucide-react";
import type { ReconcileResponse } from "@/lib/reconmate-api";
import { StatusBadge } from "./StatusBadge";

export function ResultSummaryCards({ result }: { result: ReconcileResponse }) {
  const summary = (typeof result.summary === "object" ? result.summary : {}) as Record<string, unknown>;
  const matched = (summary.matched_count as number) ?? result.matched_transactions?.length ?? 0;
  const possible = (summary.possible_match_count as number) ?? result.possible_matches?.length ?? 0;
  const unmatched = ((summary.unmatched_payment_proof_count as number) ?? 0) + ((summary.unmatched_bank_row_count as number) ?? 0);
  const isComputed = result.computed_by_backend === true;
  const isChutes = (result.source === "chutes_agent" || result.report_source === "chutes_agent") && result.fallback_used === false;
  const isGemini = (result.source === "gemini_agent" || result.report_source === "gemini_agent") && result.fallback_used === false;
  const isFallback = result.fallback_used === true;

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
      <div className="glass-card rounded-xl p-4">
        <div className="text-xs text-muted-foreground uppercase tracking-wider">Matched</div>
        <div className="mt-1 flex items-center gap-2">
          <CheckCircle2 className="w-5 h-5 text-emerald-400" />
          <div className="text-2xl font-bold text-white">{matched}</div>
        </div>
      </div>
      <div className="glass-card rounded-xl p-4">
        <div className="text-xs text-muted-foreground uppercase tracking-wider">Possible</div>
        <div className="mt-1 flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-amber-400" />
          <div className="text-2xl font-bold text-white">{possible}</div>
        </div>
      </div>
      <div className="glass-card rounded-xl p-4">
        <div className="text-xs text-muted-foreground uppercase tracking-wider">Unmatched</div>
        <div className="mt-1 flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-amber-400" />
          <div className="text-2xl font-bold text-white">{unmatched}</div>
        </div>
      </div>
      <div className="glass-card rounded-xl p-4 col-span-2 flex flex-col gap-2 justify-center">
        {isComputed && (
          <StatusBadge tone="purple" icon={Brain}>
            Computed by backend agent orchestrator
          </StatusBadge>
        )}
        {isChutes && (
          <StatusBadge tone="cyan" icon={Sparkles}>
            Generated using Chutes-powered ReconMate Agent
          </StatusBadge>
        )}
        {isGemini && (
          <StatusBadge tone="purple" icon={Sparkles}>
            Generated using Gemini-powered ReconMate Agent
          </StatusBadge>
        )}
        {isFallback && (
          <StatusBadge tone="amber" icon={Shield}>
            Template fallback used because LLM generation was unavailable
          </StatusBadge>
        )}
        {!isChutes && !isGemini && !isFallback && !isComputed && (
          <StatusBadge tone="slate">
            Source: {result.source ?? "unknown"}
          </StatusBadge>
        )}
        {result.llm_error && (
          <div className="text-[11px] text-amber-300/80 line-clamp-2" title={result.llm_error}>
            LLM note: {result.llm_error}
          </div>
        )}
      </div>
    </div>
  );
}
