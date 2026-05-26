import { createFileRoute } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { AlertCircle, Loader2, Sparkles } from "lucide-react";
import { Layout } from "@/components/Layout";
import { AgentInputConsole } from "@/components/AgentInputConsole";
import { WorkflowMiniFlow } from "@/components/WorkflowMiniFlow";
import { ResultSummaryCards } from "@/components/ResultSummaryCards";
import { AgentTraceTimeline } from "@/components/AgentTraceTimeline";
import { MarkdownReportViewer } from "@/components/MarkdownReportViewer";
import {
  MatchedTransactionCards,
  UnmatchedTransactionCards,
} from "@/components/TransactionCards";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { MascotStatusCard } from "@/components/MascotStatusCard";
import {
  runReconciliation, checkHealth,
  API_BASE_URL,
  type ReconcileResponse,
  type HealthResponse,
} from "@/lib/reconmate-api";

export const Route = createFileRoute("/dashboard")({
  component: Dashboard,
  head: () => ({
    meta: [{ title: "ReconMate Dashboard — Agentic Reconciliation Demo" }],
  }),
});

function Dashboard() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ReconcileResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [backendOk, setBackendOk] = useState<boolean | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const h = await checkHealth();
      if (!cancelled) setBackendOk(h?.status === "ok");
    })();
    const timer = setInterval(async () => {
      const h = await checkHealth();
      if (!cancelled) setBackendOk(h?.status === "ok");
    }, 10_000);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, []);

  async function handleRun(payload: unknown) {
    setLoading(true);
    setError(null);
    try {
      const res = await runReconciliation(payload);
      setResult(res);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Layout>
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-10">
        {/* Hero / intro */}
        <div className="mx-auto max-w-4xl text-center mb-2">
          <div className="text-xs uppercase tracking-[0.25em] text-cyan-300">Agent Console</div>
          <h1 className="font-display mt-2 text-3xl sm:text-5xl tracking-[0.04em]">
            Run the <span className="neon-text">ReconMate Agent</span>
          </h1>
          <p className="mt-3 text-sm sm:text-base text-muted-foreground max-w-2xl mx-auto">
            Your AI treasury copilot — extract, calculate, match, and report on cross-border
            payments in one centered workflow.
          </p>
        </div>

        {/* Backend status badge */}
        <div className="mx-auto max-w-md mb-6 flex justify-center">
          {backendOk === true && (
            <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-[11px] text-emerald-300">
              <span className="relative flex h-1.5 w-1.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-emerald-400" />
              </span>
              Backend connected
            </span>
          )}
          {backendOk === false && (
            <span className="inline-flex items-center gap-1.5 rounded-full border border-red-500/30 bg-red-500/10 px-3 py-1 text-[11px] text-red-300">
              <span className="relative flex h-1.5 w-1.5">
                <span className="absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-red-400" />
              </span>
              Backend unreachable — start the FastAPI server
            </span>
          )}
        </div>

        {/* Centered status card */}
        <div className="mx-auto max-w-md mb-6">
          <MascotStatusCard subtitle="Standing by for your payload" />
        </div>

        {/* Centerpiece: Agent Console */}
        <div className="mx-auto max-w-4xl">
          <AgentInputConsole onRun={handleRun} reconcileLoading={loading} />
        </div>

        {/* Workflow progress */}
        <div className="mx-auto max-w-5xl mt-10">
          <WorkflowMiniFlow />
        </div>

        {/* Results area — stacked below */}
        <div className="mx-auto max-w-5xl mt-8 space-y-6 min-w-0">
              {error && (
              <div className="glass rounded-xl p-4 border border-red-400/40 flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-300 shrink-0 mt-0.5" />
                <div>
                  <div className="text-sm font-semibold text-red-200">Could not reach agent</div>
                  <p className="text-xs text-red-200/80 mt-1 break-all">{error}</p>
                  <p className="text-[11px] text-muted-foreground mt-2">
                    Expected backend at{" "}
                    <code className="text-cyan-200 bg-white/5 px-1 rounded">{API_BASE_URL}</code>.
                    Check console (F12) for detailed request log.
                  </p>
                </div>
              </div>
            )}

            {loading && !result && (
              <div className="glass-card rounded-2xl p-10 grid place-items-center text-center animate-pulse-glow">
                <Loader2 className="w-8 h-8 text-cyan-300 animate-spin" />
                <div className="mt-4 text-lg font-semibold neon-text">
                  ReconMate Agent is reasoning…
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  Extracting · Calculating · Matching · Generating
                </p>
              </div>
            )}

            {!loading && !result && !error && (
              <div className="glass-card rounded-2xl p-10 text-center">
                <Sparkles className="w-8 h-8 mx-auto text-purple-300" />
                <div className="mt-3 text-lg font-semibold text-white">Awaiting input</div>
                <p className="mt-1 text-sm text-muted-foreground">
                  Load the sample payload and click <strong>Run Reconciliation</strong> to launch
                  the agent.
                </p>
              </div>
            )}

            {result && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-6"
              >
                <ResultSummaryCards result={result} />

                {typeof result.summary === "string" && result.summary && (
                  <div className="glass-card rounded-2xl p-5">
                    <div className="text-xs uppercase tracking-[0.2em] text-cyan-300 mb-2">
                      Summary
                    </div>
                    <p className="text-sm text-foreground/90">{result.summary}</p>
                  </div>
                )}
                {result.summary && typeof result.summary === "object" && (
                  <div className="glass-card rounded-2xl p-5">
                    <div className="text-xs uppercase tracking-[0.2em] text-cyan-300 mb-2">
                      Summary
                    </div>
                    <pre className="text-[11px] text-cyan-100/80 overflow-x-auto scrollbar-thin">
                      {JSON.stringify(result.summary, null, 2)}
                    </pre>
                  </div>
                )}

                {/* Agent trace — prominent */}
                <div className="glass-card rounded-2xl p-5">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <div className="text-xs uppercase tracking-[0.2em] text-purple-300">
                        Agent Tool Trace
                      </div>
                      <h2 className="text-lg font-semibold text-white">
                        How the agent reasoned
                      </h2>
                    </div>
                    <span className="text-xs text-muted-foreground">
                      {result.agent_trace?.length ?? 0} steps
                    </span>
                  </div>
                  <AgentTraceTimeline trace={result.agent_trace} />
                </div>

                {/* Reports */}
                {(result.documents?.reconciliation_report ||
                  result.documents?.discrepancy_summary) && (
                  <div className="glass-card rounded-2xl p-5">
                    <div className="text-xs uppercase tracking-[0.2em] text-cyan-300 mb-3">
                      Generated Documents
                    </div>
                    <Tabs defaultValue="reconciliation">
                      <TabsList className="bg-white/5 border border-white/10">
                        <TabsTrigger value="reconciliation">Reconciliation Report</TabsTrigger>
                        <TabsTrigger value="discrepancy">Discrepancy Summary</TabsTrigger>
                      </TabsList>
                      <TabsContent value="reconciliation" className="pt-4">
                        <MarkdownReportViewer
                          markdown={result.documents?.reconciliation_report?.content}
                        />
                      </TabsContent>
                      <TabsContent value="discrepancy" className="pt-4">
                        <MarkdownReportViewer markdown={result.documents?.discrepancy_summary?.content} />
                      </TabsContent>
                    </Tabs>
                  </div>
                )}

                {/* Transactions */}
                {(result.matched_transactions?.length ||
                  result.unmatched_transactions?.length) && (
                  <div className="glass-card rounded-2xl p-5 space-y-5">
                    <div className="text-xs uppercase tracking-[0.2em] text-cyan-300">
                      Transaction Results
                    </div>
                    <MatchedTransactionCards items={result.matched_transactions} />
                    <UnmatchedTransactionCards items={result.unmatched_transactions} />
                  </div>
                )}
              </motion.div>
            )}
        </div>
      </div>
    </Layout>
  );
}
