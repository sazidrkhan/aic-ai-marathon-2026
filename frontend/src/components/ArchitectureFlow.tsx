import { motion } from "framer-motion";
import {
  User,
  Server,
  ScanLine,
  Calculator,
  GitMerge,
  Brain,
  FileText,
  ChevronRight,
} from "lucide-react";

const NODES = [
  { icon: User, label: "User / SME", sub: "Uploads payment proofs + bank statement" },
  { icon: Server, label: "FastAPI Backend", sub: "Orchestrates the agentic workflow" },
  { icon: ScanLine, label: "OCR / Parser", sub: "PaddleOCR extracts proof fields" },
  { icon: Calculator, label: "FX / Fee Rules", sub: "Converts currencies + bank fee tolerance" },
  { icon: GitMerge, label: "Matching Engine", sub: "Pairs proofs with bank transactions" },
  { icon: Brain, label: "Chutes.AI Document Agent", sub: "Generates the final finance-friendly report from structured facts" },
  { icon: FileText, label: "Artifacts", sub: "Reconciliation & discrepancy reports" },
];

export function ArchitectureFlow() {
  return (
    <div className="premium-card-group grid gap-3 md:grid-cols-2 lg:grid-cols-4">
      {NODES.map((n, i) => (
        <motion.div
          key={n.label}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.06 }}
          className="premium-card relative glass-card rounded-2xl p-5"
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500/30 to-cyan-400/30 border border-purple-400/40 grid place-items-center">
              <n.icon className="w-5 h-5 text-cyan-200" />
            </div>
            <div className="text-[10px] uppercase tracking-widest text-muted-foreground">
              Step {String(i + 1).padStart(2, "0")}
            </div>
          </div>
          <div className="mt-3 font-semibold text-white">{n.label}</div>
          <div className="text-xs text-muted-foreground mt-1">{n.sub}</div>
          {i < NODES.length - 1 && (
            <ChevronRight className="hidden lg:block absolute -right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-purple-400/60" />
          )}
        </motion.div>
      ))}
    </div>
  );
}
