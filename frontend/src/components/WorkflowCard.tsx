import type { LucideIcon } from "lucide-react";

export function WorkflowCard({
  icon: Icon,
  title,
  description,
  step,
}: {
  icon: LucideIcon;
  title: string;
  description: string;
  step?: number;
}) {
  return (
    <div className="premium-card glass-card rounded-2xl p-6 h-full relative overflow-hidden">
      {step !== undefined && (
        <span className="absolute top-3 right-4 text-5xl font-bold text-white/5">
          {String(step).padStart(2, "0")}
        </span>
      )}
      <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-purple-500/20 to-cyan-400/20 border border-purple-400/30 grid place-items-center mb-4">
        <Icon className="w-5 h-5 text-cyan-300" />
      </div>
      <h3 className="font-semibold text-base text-white mb-1.5">{title}</h3>
      <p className="text-sm text-muted-foreground leading-relaxed">{description}</p>
    </div>
  );
}
