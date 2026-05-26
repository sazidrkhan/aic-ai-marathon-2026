import { motion } from "framer-motion";
import { ScanLine, Calculator, GitMerge, FileText, Activity } from "lucide-react";
import mascotImg from "@/assets/robot-mascot.png";

const CHIPS = [
  { icon: ScanLine, label: "OCR Ready", className: "top-4 -left-2 sm:left-0", color: "from-cyan-400/30 to-cyan-500/10 border-cyan-400/50 text-cyan-200" },
  { icon: Calculator, label: "FX Rule Engine", className: "top-1/3 -right-2 sm:-right-4", color: "from-purple-400/30 to-purple-500/10 border-purple-400/50 text-purple-200" },
  { icon: GitMerge, label: "Bank Match", className: "bottom-24 -left-4 sm:-left-6", color: "from-blue-400/30 to-blue-500/10 border-blue-400/50 text-blue-200" },
  { icon: FileText, label: "Chutes.AI Report", className: "bottom-10 -right-2 sm:right-2", color: "from-fuchsia-400/30 to-fuchsia-500/10 border-fuchsia-400/50 text-fuchsia-200" },
];

export function RobotMascot() {
  return (
    <div className="relative w-full max-w-md mx-auto aspect-square">
      {/* Orbiting rings */}
      <motion.div
        className="absolute inset-0 rounded-full border border-purple-500/20"
        animate={{ rotate: 360 }}
        transition={{ duration: 28, repeat: Infinity, ease: "linear" }}
      />
      <motion.div
        className="absolute inset-8 rounded-full border border-cyan-400/20"
        animate={{ rotate: -360 }}
        transition={{ duration: 22, repeat: Infinity, ease: "linear" }}
      />

      {/* Glow backdrop */}
      <div className="absolute inset-6 rounded-full bg-gradient-to-br from-purple-600/30 via-fuchsia-500/10 to-cyan-400/30 blur-3xl" />

      {/* Mascot image */}
      <motion.div
        className="absolute inset-0 grid place-items-center"
        animate={{ y: [0, -10, 0] }}
        transition={{ duration: 5, repeat: Infinity, ease: "easeInOut" }}
      >
        <img
          src={mascotImg}
          alt="ReconMate AI treasury agent mascot"
          width={1024}
          height={1024}
          className="w-[88%] h-[88%] object-contain drop-shadow-[0_20px_60px_rgba(168,85,247,0.45)]"
        />
      </motion.div>

      {/* Floating chips */}
      {CHIPS.map((c, i) => (
        <motion.div
          key={c.label}
          className={`absolute ${c.className} z-10`}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: [0, -6, 0] }}
          transition={{ delay: 0.2 + i * 0.15, duration: 3 + i * 0.4, repeat: Infinity, ease: "easeInOut" }}
        >
          <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full backdrop-blur-md bg-gradient-to-r ${c.color} border shadow-lg`}>
            <c.icon className="w-3.5 h-3.5" />
            <span className="text-[11px] font-semibold whitespace-nowrap">{c.label}</span>
          </div>
        </motion.div>
      ))}

      {/* Status indicator */}
      <motion.div
        className="absolute top-2 right-4 z-10 flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-black/60 backdrop-blur-md border border-emerald-400/50"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.8 }}
      >
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
          <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-400" />
        </span>
        <span className="text-[10px] uppercase tracking-widest text-emerald-200 font-semibold">Online</span>
      </motion.div>

      {/* Tiny floating activity icon */}
      <motion.div
        className="absolute bottom-2 left-1/2 -translate-x-1/2 z-10 flex items-center gap-1.5 px-3 py-1 rounded-full glass border border-cyan-400/40"
        animate={{ y: [0, -4, 0] }}
        transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
      >
        <Activity className="w-3 h-3 text-cyan-300" />
        <span className="text-[10px] uppercase tracking-widest text-cyan-200">Treasury Agent</span>
      </motion.div>
    </div>
  );
}