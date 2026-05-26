import { createFileRoute } from "@tanstack/react-router";
import {
  FileText,
  ScanLine,
  Calculator,
  GitMerge,
  AlertTriangle,
  CreditCard,
  Banknote,
  Receipt,
  ListChecks,
} from "lucide-react";
import { Layout } from "@/components/Layout";
import { HeroSection } from "@/components/HeroSection";
import { WorkflowCard } from "@/components/WorkflowCard";

export const Route = createFileRoute("/")({
  component: Landing,
  head: () => ({
    meta: [
      { title: "ReconMate — Agentic Cross-Border Reconciliation for SMEs" },
      {
        name: "description",
        content:
          "ReconMate is an autonomous treasury agent that reconciles cross-border SME payments — FX, fees, OCR proofs, matching, and discrepancy reports.",
      },
    ],
  }),
});

const PROBLEMS = [
  {
    icon: CreditCard,
    title: "FX Rates Drift",
    description: "Invoice in USD, deposit in MYR — rates change between issue and settle.",
  },
  {
    icon: Banknote,
    title: "Bank Fees Bite",
    description: "Correspondent and SWIFT fees silently shave amounts off every transfer.",
  },
  {
    icon: Receipt,
    title: "Payment Proofs",
    description: "PDFs, screenshots, swift advices — scattered evidence in mixed formats.",
  },
  {
    icon: ListChecks,
    title: "Manual Matching",
    description: "Finance teams hand-match rows in Excel for hours every month-end.",
  },
];

const WORKFLOW = [
  { icon: ScanLine, title: "Extract", description: "PaddleOCR pulls fields from every payment proof." },
  { icon: Calculator, title: "Calculate", description: "Applies FX + fee tolerance to expected amounts." },
  { icon: GitMerge, title: "Match", description: "Pairs proofs with bank rows using reference + amount." },
  { icon: FileText, title: "Generate Report", description: "Chutes.AI generates the reconciliation narrative from structured reconciliation facts." },
  {
    icon: AlertTriangle,
    title: "Flag Discrepancy",
    description: "Unmatched items surface as actionable discrepancy summaries.",
  },
];

const TECH = ["FastAPI", "Chutes.AI", "ReconMate Agent", "PaddleOCR"];

function Landing() {
  return (
    <Layout>
      <HeroSection />

      {/* Problems */}
      <section className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-16">
        <div className="max-w-2xl">
          <div className="text-xs uppercase tracking-[0.25em] text-cyan-300">The Problem</div>
          <h2 className="font-display mt-2 text-3xl sm:text-4xl tracking-[0.04em]">
            Cross-border payments don't reconcile themselves
          </h2>
        </div>
        <div className="premium-card-group mt-8 grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {PROBLEMS.map((p) => (
            <WorkflowCard key={p.title} icon={p.icon} title={p.title} description={p.description} />
          ))}
        </div>
      </section>

      {/* Workflow */}
      <section className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-16">
        <div className="max-w-2xl">
          <div className="text-xs uppercase tracking-[0.25em] text-purple-300">Agent Workflow</div>
          <h2 className="font-display mt-2 text-3xl sm:text-4xl tracking-[0.04em]">
            Five autonomous steps. <span className="neon-text">Zero spreadsheets.</span>
          </h2>
        </div>
        <div className="premium-card-group mt-8 grid sm:grid-cols-2 lg:grid-cols-5 gap-4">
          {WORKFLOW.map((w, i) => (
            <WorkflowCard
              key={w.title}
              icon={w.icon}
              title={w.title}
              description={w.description}
              step={i + 1}
            />
          ))}
        </div>
      </section>

      {/* Tech badges */}
      <section className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-12">
        <div className="glass rounded-2xl p-6 flex flex-wrap items-center justify-center gap-3">
          <span className="text-xs uppercase tracking-[0.2em] text-muted-foreground mr-2">
            Powered by
          </span>
          {TECH.map((t) => (
            <span
              key={t}
              className="px-3 py-1.5 rounded-full text-sm font-medium border border-purple-400/30 bg-gradient-to-r from-purple-500/10 to-cyan-500/10 text-white"
            >
              {t}
            </span>
          ))}
        </div>
      </section>
    </Layout>
  );
}
