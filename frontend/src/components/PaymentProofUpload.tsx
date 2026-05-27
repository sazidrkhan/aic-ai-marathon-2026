import { useRef, useState } from "react";
import { Upload, FileText, Loader2, AlertTriangle, CheckCircle2 } from "lucide-react";
import { extractProof, type OcrExtractResponse } from "@/lib/reconmate-api";

interface ProofResult {
  fileName: string;
  data?: OcrExtractResponse;
  error?: string;
}

function getParsedFields(result: OcrExtractResponse): Array<[string, string]> {
  const fields = result.fields;
  const rows: Array<[string, string | null | undefined]> = fields
    ? [
        ["sender", fields.sender_name],
        ["amount", [fields.currency, fields.amount].filter(Boolean).join(" ")],
        ["reference", fields.reference],
        ["date", fields.date],
      ]
    : [];
  return rows.filter((entry): entry is [string, string] => Boolean(entry[1]));
}

function ProofResultCard({ item }: { item: ProofResult }) {
  if (item.error) {
    return (
      <div className="rounded-lg border border-red-400/40 bg-red-500/10 p-3 text-xs text-red-200">
        <div className="font-medium text-red-100">{item.fileName}</div>
        <div className="mt-1">{item.error}</div>
      </div>
    );
  }

  const result = item.data;
  if (!result) return null;

  const unavailable = (result.status || "").toLowerCase() === "unavailable";
  const parsedFields = getParsedFields(result);

  return (
    <div className="space-y-2">
      {unavailable ? (
        <div className="inline-flex items-start gap-2 rounded-md border border-amber-400/40 bg-amber-500/10 px-2.5 py-1.5 text-[11px] text-amber-200">
          <AlertTriangle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
          <span>OCR unavailable - install optional OCR dependencies on the backend</span>
        </div>
      ) : (
        <div className="inline-flex items-center gap-1.5 rounded-md border border-emerald-400/40 bg-emerald-500/10 px-2.5 py-1 text-[11px] text-emerald-200">
          <CheckCircle2 className="w-3.5 h-3.5" />
          OCR {result.status || "ok"}
        </div>
      )}

      <div className="rounded-lg border border-white/10 bg-black/40 p-3 text-xs space-y-1">
        <div>
          <span className="text-muted-foreground">filename: </span>
          <span className="text-cyan-200">{result.filename || item.fileName}</span>
        </div>
        {result.status && (
          <div>
            <span className="text-muted-foreground">status: </span>
            <span className="text-cyan-200">{result.status}</span>
          </div>
        )}
        {result.engine && (
          <div>
            <span className="text-muted-foreground">engine: </span>
            <span className="text-cyan-200">{result.engine}</span>
          </div>
        )}
        {typeof result.confidence === "number" && (
          <div>
            <span className="text-muted-foreground">confidence: </span>
            <span className="text-cyan-200">{Math.round(result.confidence * 100)}%</span>
          </div>
        )}
        {result.message && <div className="text-muted-foreground">{result.message}</div>}
        {parsedFields.length > 0 && (
          <div className="mt-2 grid gap-1 border-t border-white/10 pt-2">
            {parsedFields.map(([label, value]) => (
              <div key={label} className="flex justify-between gap-3">
                <span className="text-muted-foreground">{label}: </span>
                <span className="text-right text-cyan-100">{value}</span>
              </div>
            ))}
          </div>
        )}
        {result.ocr_text && (
          <pre className="mt-2 max-h-40 overflow-auto scrollbar-thin whitespace-pre-wrap text-[11px] text-cyan-100/80">
            {result.ocr_text}
          </pre>
        )}
      </div>
    </div>
  );
}

export function PaymentProofUpload() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<ProofResult[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function handleExtract() {
    if (files.length === 0) return;
    setLoading(true);
    setError(null);
    setResults([]);
    const nextResults: ProofResult[] = [];

    for (const file of files) {
      try {
        const data = await extractProof(file);
        nextResults.push({ fileName: file.name, data });
      } catch (e) {
        nextResults.push({ fileName: file.name, error: (e as Error).message });
      }
      setResults([...nextResults]);
    }

    setLoading(false);
  }

  function addFiles(nextFiles: File[]) {
    setResults([]);
    setError(null);
    setFiles((currentFiles) => {
      const seen = new Set(currentFiles.map((file) => `${file.name}:${file.size}:${file.lastModified}`));
      const uniqueNewFiles = nextFiles.filter((file) => {
        const key = `${file.name}:${file.size}:${file.lastModified}`;
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      });
      return [...currentFiles, ...uniqueNewFiles];
    });
    if (inputRef.current) {
      inputRef.current.value = "";
    }
  }

  const fileLabel =
    files.length === 0
      ? null
      : files.length === 1
        ? files[0].name
        : `${files.length} payment proofs selected`;

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
        <div className="mt-2 text-sm font-medium text-white">Upload Payment Proofs</div>
        <div className="text-[11px] text-muted-foreground mt-0.5">PDF, PNG, JPG, JPEG</div>
        <div className="text-[11px] text-muted-foreground mt-0.5">Pick one file, then click again to add another</div>
        {fileLabel && <div className="mt-2 text-xs text-cyan-200 truncate">{fileLabel}</div>}
        {files.length > 1 && (
          <div className="mt-1 text-[11px] text-muted-foreground">
            {files.map((file) => file.name).join(", ")}
          </div>
        )}
        <input
          ref={inputRef}
          id="proof-file"
          type="file"
          multiple
          accept=".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg"
          className="hidden"
          onChange={(e) => {
            addFiles(Array.from(e.target.files ?? []));
          }}
        />
      </label>

      {files.length > 0 && (
        <div className="rounded-lg border border-white/10 bg-black/30 p-3 text-xs">
          <div className="mb-2 flex items-center justify-between gap-3">
            <span className="text-muted-foreground">Selected proofs</span>
            <button
              type="button"
              disabled={loading}
              onClick={() => {
                setFiles([]);
                setResults([]);
                setError(null);
              }}
              className="text-[11px] text-cyan-200 hover:text-cyan-100 disabled:opacity-50"
            >
              Clear all
            </button>
          </div>
          <div className="grid gap-1">
            {files.map((file) => (
              <div key={`${file.name}:${file.size}:${file.lastModified}`} className="flex items-center justify-between gap-3">
                <span className="truncate text-cyan-100">{file.name}</span>
                <button
                  type="button"
                  disabled={loading}
                  onClick={() => {
                    setFiles((currentFiles) => currentFiles.filter((item) => item !== file));
                    setResults([]);
                  }}
                  className="shrink-0 text-[11px] text-red-200 hover:text-red-100 disabled:opacity-50"
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      <button
        disabled={files.length === 0 || loading}
        onClick={handleExtract}
        className="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-gradient-to-r from-purple-600/80 to-cyan-500/80 text-white text-sm font-semibold disabled:opacity-50 disabled:cursor-not-allowed hover:scale-[1.01] transition-transform"
      >
        {loading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" /> Extracting {results.length + 1} of {files.length}...
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

      {results.length > 0 && (
        <div className="space-y-3">
          {results.map((item) => (
            <ProofResultCard key={item.fileName} item={item} />
          ))}
        </div>
      )}
    </div>
  );
}
