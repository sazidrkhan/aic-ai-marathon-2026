import { Link } from "@tanstack/react-router";
import { Sparkles } from "lucide-react";

export function Navbar() {
  return (
    <header className="sticky top-0 z-50 border-b border-white/10 backdrop-blur-xl bg-background/60">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 group">
          <div className="relative w-9 h-9 rounded-lg bg-gradient-to-br from-purple-500 to-cyan-400 grid place-items-center neon-glow">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <span className="font-display text-lg tracking-[0.08em]">
            Recon<span className="neon-text">Mate</span>
          </span>
        </Link>
        <nav className="flex items-center gap-1 sm:gap-2 text-sm">
          {[
            { to: "/", label: "Home" },
            { to: "/dashboard", label: "Dashboard" },
            { to: "/architecture", label: "Architecture" },
          ].map((l) => (
            <Link
              key={l.to}
              to={l.to}
              activeOptions={{ exact: true }}
              activeProps={{ className: "text-white bg-white/10 border-white/20" }}
              inactiveProps={{ className: "text-muted-foreground hover:text-white" }}
              className="px-3 py-1.5 rounded-md border border-transparent transition-colors"
            >
              {l.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
