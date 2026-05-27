import { motion } from "framer-motion";
import { Bot, Globe2, ShieldCheck } from "lucide-react";

export function TreasuryMascot() {
  return (
    <div className="relative w-full max-w-md mx-auto aspect-square">
      {/* Orbiting rings */}
      <motion.div
        className="absolute inset-0 rounded-full border border-purple-500/30"
        animate={{ rotate: 360 }}
        transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
      />
      <motion.div
        className="absolute inset-6 rounded-full border border-cyan-400/30"
        animate={{ rotate: -360 }}
        transition={{ duration: 14, repeat: Infinity, ease: "linear" }}
      />
      <motion.div
        className="absolute inset-12 rounded-full border border-blue-500/20"
        animate={{ rotate: 360 }}
        transition={{ duration: 28, repeat: Infinity, ease: "linear" }}
      />

      {/* Orbit nodes */}
      <motion.div
        className="absolute top-1/2 left-0 -translate-y-1/2 -translate-x-1/2"
        animate={{ rotate: 360 }}
        transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
        style={{ transformOrigin: "50% 50%" }}
      />
      <div className="absolute top-2 left-1/2 -translate-x-1/2 w-3 h-3 rounded-full bg-purple-400 shadow-[0_0_15px_rgba(168,85,247,0.9)]" />
      <div className="absolute bottom-6 right-6 w-2.5 h-2.5 rounded-full bg-cyan-300 shadow-[0_0_15px_rgba(34,211,238,0.9)]" />
      <div className="absolute bottom-10 left-4 w-2 h-2 rounded-full bg-blue-400 shadow-[0_0_15px_rgba(59,130,246,0.9)]" />

      {/* Center mascot */}
      <motion.div
        className="absolute inset-1/4 rounded-3xl glass-card grid place-items-center animate-pulse-glow"
        animate={{ y: [0, -8, 0] }}
        transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
      >
        <div className="flex flex-col items-center gap-2">
          <div className="relative">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-purple-600 via-fuchsia-500 to-cyan-400 grid place-items-center">
              <Bot className="w-9 h-9 text-white" />
            </div>
            <div className="absolute -bottom-1 -right-1 w-6 h-6 rounded-full bg-cyan-400 grid place-items-center border-2 border-background">
              <Globe2 className="w-3.5 h-3.5 text-black" />
            </div>
          </div>
          <div className="text-[10px] uppercase tracking-[0.2em] text-cyan-300 flex items-center gap-1">
            <ShieldCheck className="w-3 h-3" /> Treasury Agent
          </div>
        </div>
      </motion.div>
    </div>
  );
}
