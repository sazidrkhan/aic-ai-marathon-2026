import { motion } from "framer-motion";
import { Activity, CheckCircle2, AlertCircle, Loader2, Wrench } from "lucide-react";
import type { AgentTraceItem } from "@/lib/reconmate-api";

function statusInfo(status?: string) {
  const s = (status || "").toLowerCase();
  if (s.includes("ok") || s.includes("success") || s.includes("done") || s.includes("complete"))
    return { tone: "text-emerald-300 border-emerald-400/40", Icon: CheckCircle2 };
  if (s.includes("error") || s.includes("fail"))
    return { tone: "text-red-300 border-red-400/40", Icon: AlertCircle };
  if (s.includes("running") || s.includes("pending"))
    return { tone: "text-cyan-300 border-cyan-400/40", Icon: Loader2 };
  return { tone: "text-purple-300 border-purple-400/40", Icon: Activity };
}

export function AgentTraceTimeline({ trace }: { trace?: AgentTraceItem[] }) {
  if (!trace || trace.length === 0) {
    return (
      <div className="glass rounded-xl p-6 text-sm text-muted-foreground italic">
        No agent trace returned yet. Run reconciliation to see the agent's reasoning steps.
      </div>
    );
  }

  return (
    <ol className="relative space-y-3">
      <div className="absolute left-[15px] top-2 bottom-2 w-px bg-gradient-to-b from-purple-500/60 via-cyan-400/40 to-transparent" />
      {trace.map((item, i) => {
        const name = item.tool || item.agent || item.name || `Step ${i + 1}`;
        const { tone, Icon } = statusInfo(item.status);
        return (
          <motion.li
            key={i}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.05 }}
            className="relative pl-12"
          >
            <div
              className={`absolute left-0 top-2 w-8 h-8 rounded-full grid place-items-center border bg-background/80 ${tone}`}
            >
              <Icon className="w-4 h-4" />
            </div>
            <div className="glass-card rounded-xl p-4">
              <div className="flex items-center justify-between gap-3 flex-wrap">
                <div className="flex items-center gap-2 font-medium text-white">
                  <Wrench className="w-3.5 h-3.5 text-cyan-300" />
                  {name}
                </div>
                {item.status && (
                  <span className={`text-[11px] uppercase tracking-wider ${tone.split(" ")[0]}`}>
                    {item.status}
                  </span>
                )}
              </div>
              {item.message && (
                <p className="mt-1.5 text-sm text-muted-foreground">{String(item.message)}</p>
              )}
              {item.output !== undefined && (
                <pre className="mt-2 text-[11px] bg-black/40 border border-white/10 rounded-md p-2 overflow-x-auto scrollbar-thin text-cyan-100/80">
                  {typeof item.output === "string"
                    ? item.output
                    : JSON.stringify(item.output, null, 2)}
                </pre>
              )}
            </div>
          </motion.li>
        );
      })}
    </ol>
  );
}
