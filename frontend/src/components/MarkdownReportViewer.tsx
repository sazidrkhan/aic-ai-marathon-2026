import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export function MarkdownReportViewer({ markdown }: { markdown?: string }) {
  if (!markdown) {
    return (
      <div className="text-sm text-muted-foreground italic">No report content returned.</div>
    );
  }
  return (
    <div className="prose prose-invert prose-sm max-w-none scrollbar-thin
      prose-headings:text-white prose-headings:font-semibold
      prose-h1:text-2xl prose-h1:bg-gradient-to-r prose-h1:from-purple-300 prose-h1:to-cyan-300 prose-h1:bg-clip-text prose-h1:text-transparent
      prose-h2:text-xl prose-h2:text-cyan-200 prose-h2:border-b prose-h2:border-white/10 prose-h2:pb-1
      prose-h3:text-base prose-h3:text-purple-200
      prose-p:text-foreground/90 prose-strong:text-white
      prose-a:text-cyan-300 prose-a:no-underline hover:prose-a:underline
      prose-code:text-cyan-200 prose-code:bg-white/5 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:before:content-none prose-code:after:content-none
      prose-pre:bg-black/40 prose-pre:border prose-pre:border-white/10
      prose-table:text-sm prose-th:text-cyan-200 prose-th:border-white/10 prose-td:border-white/10
      prose-li:marker:text-purple-400
      prose-blockquote:border-l-purple-500 prose-blockquote:text-foreground/80
      ">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{markdown}</ReactMarkdown>
    </div>
  );
}
