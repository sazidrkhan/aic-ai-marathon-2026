import { FileText, ScanLine, Table, GitMerge, Sparkles, ChevronRight } from "lucide-react";

const steps = [
  { label: "Payment Proof", Icon: FileText },
  { label: "OCR Extract", Icon: ScanLine },
  { label: "Bank Statement", Icon: Table },
  { label: "Match", Icon: GitMerge },
  { label: "Chutes.AI Report", Icon: Sparkles },
];

export function WorkflowMiniFlow() {
  return (
    <div className="glass rounded-xl p-3 overflow-x-auto scrollbar-thin">
      <div className="flex items-center gap-1.5 min-w-max">
        {steps.map((s, i) => (
          <div key={s.label} className="flex items-center gap-1.5">
            <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md border border-white/10 bg-white/5 text-[11px] text-foreground/90">
              <s.Icon className="w-3.5 h-3.5 text-cyan-300" />
              <span>{s.label}</span>
            </div>
            {i < steps.length - 1 && (
              <ChevronRight className="w-3.5 h-3.5 text-purple-300/70" />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
