import { cn } from "@/lib/utils";
import type { LucideIcon } from "lucide-react";

type Tone = "purple" | "cyan" | "green" | "amber" | "red" | "slate";

const tones: Record<Tone, string> = {
  purple: "border-purple-400/50 bg-purple-500/10 text-purple-200",
  cyan: "border-cyan-400/50 bg-cyan-500/10 text-cyan-200",
  green: "border-emerald-400/50 bg-emerald-500/10 text-emerald-200",
  amber: "border-amber-400/50 bg-amber-500/10 text-amber-200",
  red: "border-red-400/50 bg-red-500/10 text-red-200",
  slate: "border-white/15 bg-white/5 text-muted-foreground",
};

export function StatusBadge({
  tone = "slate",
  icon: Icon,
  children,
  className,
}: {
  tone?: Tone;
  icon?: LucideIcon;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md border text-xs font-medium",
        tones[tone],
        className,
      )}
    >
      {Icon && <Icon className="w-3.5 h-3.5" />}
      {children}
    </span>
  );
}
