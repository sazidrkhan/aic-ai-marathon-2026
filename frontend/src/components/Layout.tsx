import { Navbar } from "./Navbar";

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen relative">
      <div className="pointer-events-none fixed inset-0 grid-bg opacity-30" />
      <div className="relative z-10">
        <Navbar />
        <main>{children}</main>
        <footer className="border-t border-white/10 mt-20 py-8 text-center text-xs text-muted-foreground">
          ReconMate · Global Treasury Reconciliation Agent · AI Marathon
        </footer>
      </div>
    </div>
  );
}
