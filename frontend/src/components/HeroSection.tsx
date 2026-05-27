import { Link } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { ArrowRight, Sparkles } from "lucide-react";
import { RobotMascot } from "./RobotMascot";

export function HeroSection() {
  return (
    <section className="relative overflow-hidden">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 pt-16 pb-24 lg:pt-24 lg:pb-32 grid lg:grid-cols-2 gap-12 items-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full glass text-xs text-cyan-300 mb-6">
            <Sparkles className="w-3 h-3" /> Agentic AI · Global Treasury
          </div>
          <h1 className="font-display text-5xl sm:text-6xl lg:text-7xl leading-[1.05] tracking-[0.06em]">
            <span className="neon-text">ReconMate</span>
          </h1>
          <p className="mt-4 text-xl sm:text-2xl text-foreground/90 font-medium">
            <span className="neon-text font-display-tight">Agentic</span> Cross-Border{" "}
            <span className="neon-text font-display-tight">Reconciliation</span> for SMEs
          </p>
          <p className="mt-6 text-base text-muted-foreground max-w-xl">
            FX rates shift. Bank fees bite. Your{" "}
            <span className="text-purple-300 font-medium">USD 10 invoice</span> shows up as{" "}
            <span className="text-cyan-300 font-medium">RM 42.50</span> in your bank. ReconMate's
            autonomous treasury agent reconciles every payment, end to end.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link
              to="/dashboard"
              className="group inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-purple-600 to-cyan-500 text-white font-semibold neon-glow hover:scale-[1.02] transition-transform"
            >
              Launch Agent
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </Link>
            <Link
              to="/architecture"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl glass text-foreground font-semibold hover:border-cyan-400/60 border border-transparent transition-colors"
            >
              View Architecture
            </Link>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, delay: 0.15 }}
        >
          <RobotMascot />
        </motion.div>
      </div>
    </section>
  );
}
