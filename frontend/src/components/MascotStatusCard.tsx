import { motion } from "framer-motion";
import mascotImg from "@/assets/robot-mascot.png";

interface Props {
  title?: string;
  subtitle?: string;
  size?: "sm" | "md";
}

export function MascotStatusCard({
  title = "ReconMate Agent",
  subtitle = "Online · Ready to reconcile",
  size = "md",
}: Props) {
  const imgSize = size === "sm" ? "w-14 h-14" : "w-20 h-20";
  return (
    <div className="glass-card rounded-2xl p-4 flex items-center gap-4 relative overflow-hidden">
      <div className="absolute -top-10 -right-10 w-32 h-32 rounded-full bg-gradient-to-br from-purple-500/20 to-cyan-400/20 blur-2xl" />
      <motion.img
        src={mascotImg}
        alt="ReconMate agent"
        width={1024}
        height={1024}
        loading="lazy"
        className={`${imgSize} object-contain drop-shadow-[0_8px_20px_rgba(168,85,247,0.5)] relative z-10`}
        animate={{ y: [0, -4, 0] }}
        transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
      />
      <div className="relative z-10 min-w-0">
        <div className="flex items-center gap-2">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-400" />
          </span>
          <span className="text-[10px] uppercase tracking-widest text-emerald-300 font-semibold">
            Online
          </span>
        </div>
        <div className="mt-1 font-semibold text-white text-sm">{title}</div>
        <div className="text-xs text-muted-foreground">{subtitle}</div>
      </div>
    </div>
  );
}