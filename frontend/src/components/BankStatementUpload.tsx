import { useState } from "react";
import { Upload, Table as TableIcon, AlertTriangle } from "lucide-react";

interface ParsedCsv {
  headers: string[];
  rows: string[][];
  totalRows: number;
}

function parseCsv(text: string): ParsedCsv {
  const lines = text
    .split(/\r?\n/)
    .map((l) => l.trim())
    .filter((l) => l.length > 0);
  if (lines.length === 0) throw new Error("CSV is empty");

  const splitLine = (line: string): string[] => {
    const out: string[] = [];
    let cur = "";
    let inQ = false;
    for (let i = 0; i < line.length; i++) {
      const c = line[i];
      if (c === '"') {
        if (inQ && line[i + 1] === '"') {
          cur += '"';
          i++;
        } else inQ = !inQ;
      } else if (c === "," && !inQ) {
        out.push(cur);
        cur = "";
      } else cur += c;
    }
    out.push(cur);
    return out.map((s) => s.trim());
  };

  const headers = splitLine(lines[0]);
  const rows = lines.slice(1).map(splitLine);
  return { headers, rows, totalRows: rows.length };
}

export function BankStatementUpload() {
  const [file, setFile] = useState<File | null>(null);
  const [parsed, setParsed] = useState<ParsedCsv | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleFile(f: File | null) {
    setError(null);
    setParsed(null);
    setFile(f);
    if (!f) return;
    try {
      const text = await f.text();
      setParsed(parseCsv(text));
    } catch (e) {
      setError("Could not parse CSV: " + (e as Error).message);
    }
  }

  return (
    <div className="glass-card rounded-2xl p-5 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-cyan-300">
          <TableIcon className="w-3.5 h-3.5" /> Bank Statement
        </div>
        <span className="text-[10px] uppercase tracking-wider text-purple-300/80">Step 2</span>
      </div>

      <label
        htmlFor="bank-file"
        className="block cursor-pointer rounded-xl border border-dashed border-white/15 hover:border-purple-400/60 bg-black/30 p-5 text-center transition-colors"
      >
        <Upload className="w-6 h-6 mx-auto text-cyan-300" />
        <div className="mt-2 text-sm font-medium text-white">Upload Bank Statement CSV</div>
        <div className="text-[11px] text-muted-foreground mt-0.5">.csv only — preview parsed locally</div>
        {file && <div className="mt-2 text-xs text-cyan-200 truncate">{file.name}</div>}
        <input
          id="bank-file"
          type="file"
          accept=".csv,text/csv"
          className="hidden"
          onChange={(e) => handleFile(e.target.files?.[0] ?? null)}
        />
      </label>

      {error && (
        <div className="inline-flex items-start gap-2 rounded-md border border-amber-400/40 bg-amber-500/10 px-2.5 py-1.5 text-[11px] text-amber-200">
          <AlertTriangle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {parsed && (
        <div className="rounded-lg border border-white/10 bg-black/40 overflow-hidden">
          <div className="px-3 py-2 text-[11px] text-muted-foreground border-b border-white/10">
            Showing first {Math.min(5, parsed.rows.length)} of {parsed.totalRows} rows
          </div>
          <div className="overflow-x-auto scrollbar-thin">
            <table className="w-full text-[11px]">
              <thead className="bg-white/5">
                <tr>
                  {parsed.headers.map((h, i) => (
                    <th key={i} className="px-2 py-1.5 text-left font-medium text-cyan-200 whitespace-nowrap">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {parsed.rows.slice(0, 5).map((r, i) => (
                  <tr key={i} className="border-t border-white/5">
                    {r.map((c, j) => (
                      <td key={j} className="px-2 py-1.5 text-foreground/80 whitespace-nowrap">
                        {c}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
