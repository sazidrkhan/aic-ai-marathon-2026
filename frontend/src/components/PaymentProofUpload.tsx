import { useRef, useState } from "react";
import { Upload, FileText, Loader2, AlertTriangle, CheckCircle2 } from "lucide-react";
import { extractProof, type OcrExtractResponse } from "@/lib/reconmate-api";

export function PaymentProofUpload() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<OcrExtractResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleExtract() {
    if (!file) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const r = await extractProof(file);
      setResult(r);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  const stubbed = (result?.status || "").toLowerCase() === "stubbed";

  return (
    <div className="glass-card rounded-2xl p-5 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-cyan-300">
          <Upload className="w-3.5 h-3.5" /> Payment Proof
        </div>
        <span className="text-[10px] uppercase tracking-wider text-purple-300/80">Step 1</span>
      </div>

      <label
        htmlFor="proof-file"
        className="block cursor-pointer rounded-xl border border-dashed border-white/15 hover:border-cyan-400/60 bg-black/30 p-5 text-center transition-colors"
      >
        <FileText className="w-6 h-6 mx-auto text-purple-300" />
        <div className="mt-2 text-sm font-medium text-white">Upload Payment Proof</div>
        <div className="text-[11px] text-muted-foreground mt-0.5">PDF, PNG, JPG, JPEG</div>
        {file && (
          <div className="mt-2 text-xs text-cyan-200 truncate">{file.name}</div>
        )}
        <input
          ref={inputRef}
          id="proof-file"
          type="file"
          accept=".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg"
          className="hidden"
          onChange={(e) => {
            setResult(null);
            setError(null);
            setFile(e.target.files?.[0] ?? null);
          }}
        />
      </label>

      <button
        disabled={!file || loading}
        onClick={handleExtract}
        className="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-gradient-to-r from-purple-600/80 to-cyan-500/80 text-white text-sm font-semibold disabled:opacity-50 disabled:cursor-not-allowed hover:scale-[1.01] transition-transform"
      >
        {loading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" /> Extracting…
          </>
        ) : (
          <>Extract Proof Text</>
        )}
      </button>

      {error && (
        <div className="rounded-lg border border-red-400/40 bg-red-500/10 p-3 text-xs text-red-200">
          {error}
        </div>
      )}

      {result && (
        <div className="space-y-2">
          {stubbed ? (
            <div className="inline-flex items-start gap-2 rounded-md border border-amber-400/40 bg-amber-500/10 px-2.5 py-1.5 text-[11px] text-amber-200">
              <AlertTriangle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
              <span>
                Stubbed OCR — backend accepted the file but real OCR is not enabled yet
              </span>
            </div>
          ) : (
            <div className="inline-flex items-center gap-1.5 rounded-md border border-emerald-400/40 bg-emerald-500/10 px-2.5 py-1 text-[11px] text-emerald-200">
              <CheckCircle2 className="w-3.5 h-3.5" />
              OCR {result.status || "ok"}
            </div>
          )}

          <div className="rounded-lg border border-white/10 bg-black/40 p-3 text-xs space-y-1">
            {result.filename && (
              <div>
                <span className="text-muted-foreground">filename: </span>
                <span className="text-cyan-200">{result.filename}</span>
              </div>
            )}
            {result.status && (
              <div>
                <span className="text-muted-foreground">status: </span>
                <span className="text-cyan-200">{result.status}</span>
              </div>
            )}
            {result.message && (
              <div className="text-muted-foreground">{result.message}</div>
            )}
            {result.ocr_text && (
              <pre className="mt-2 max-h-40 overflow-auto scrollbar-thin whitespace-pre-wrap text-[11px] text-cyan-100/80">
                {result.ocr_text}
              </pre>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
