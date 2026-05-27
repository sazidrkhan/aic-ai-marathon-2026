import { createFileRoute } from "@tanstack/react-router";
import { Wrench, Workflow, FileCheck2, ShieldCheck } from "lucide-react";
import { Layout } from "@/components/Layout";
import { ArchitectureFlow } from "@/components/ArchitectureFlow";
import { WorkflowCard } from "@/components/WorkflowCard";
import { MascotStatusCard } from "@/components/MascotStatusCard";

export const Route = createFileRoute("/architecture")({
  component: Architecture,
  head: () => ({
    meta: [{ title: "ReconMate Architecture — Why this is Agentic" }],
  }),
});

const AGENTIC_REASONS = [
  {
    icon: Wrench,
    title: "Tool-Based Reasoning",
    description:
      "The custom ReconMate orchestrator calls OCR, FX, fee, and matching tools. Chutes.AI generates the final finance-friendly report from structured facts.",
  },
  {
    icon: Workflow,
    title: "Workflow Execution",
    description: "Multi-step orchestration: extract → calculate → match → report → flag.",
  },
  {
    icon: FileCheck2,
    title: "Actionable Artifacts",
    description: "Outputs are real reports a finance team can sign off on, not just chat replies.",
  },
  {
    icon: ShieldCheck,
    title: "Safe Fallback",
    description:
      "If the LLM is unreachable, a deterministic template ensures the workflow still ships.",
  },
];

function Architecture() {
  return (
    <Layout>
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-12 space-y-16">
        <div className="grid lg:grid-cols-[1fr_320px] gap-6 items-start">
          <div>
            <div className="text-xs uppercase tracking-[0.25em] text-cyan-300">System Design</div>
            <h1 className="font-display mt-2 text-3xl sm:text-4xl tracking-[0.04em]">
              How <span className="neon-text">ReconMate</span> reconciles the world
            </h1>
            <p className="mt-3 text-sm text-muted-foreground max-w-2xl">
              A FastAPI orchestrator that drives an agentic loop — from OCR'd payment proof to
              board-ready reconciliation report.
            </p>
          </div>
          <MascotStatusCard subtitle="Orchestrating the agentic loop" />
        </div>

        <section>
          <h2 className="font-display text-lg text-white mb-4 tracking-[0.08em]">Architecture Flow</h2>
          <ArchitectureFlow />
        </section>

        <section>
          <h2 className="font-display text-lg text-white mb-4 tracking-[0.08em]">
            Why this is <span className="neon-text">agentic</span>?
          </h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {AGENTIC_REASONS.map((r) => (
              <WorkflowCard
                key={r.title}
                icon={r.icon}
                title={r.title}
                description={r.description}
              />
            ))}
          </div>
        </section>
      </div>
    </Layout>
  );
}
