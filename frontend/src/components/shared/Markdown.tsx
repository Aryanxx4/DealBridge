import ReactMarkdown, { defaultUrlTransform } from "react-markdown";
import remarkGfm from "remark-gfm";

/** Markdown without raw HTML. `[n]` citation markers become buttons when onCite is given. */
export function Markdown({ text, onCite }: { text: string; onCite?: (n: number) => void }) {
  const src = onCite ? text.replace(/\[(\d{1,2})\](?!\()/g, "[[$1]](cite:$1)") : text;
  return (
    <div className="prose-sm max-w-none space-y-2 leading-relaxed [&_a]:text-primary [&_a]:underline [&_li]:ml-4 [&_ol]:list-decimal [&_ul]:list-disc">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        skipHtml
        urlTransform={(url) => (url.startsWith("cite:") ? url : defaultUrlTransform(url))}
        components={{
          a: ({ href, children }) => {
            if (href?.startsWith("cite:") && onCite) {
              const n = Number(href.slice(5));
              return (
                <button type="button" onClick={() => onCite(n)} className="mx-0.5 rounded bg-indigo-50 px-1 text-xs font-semibold text-indigo-700 no-underline hover:bg-indigo-100" aria-label={`Show source ${n}`}>
                  {n}
                </button>
              );
            }
            return (
              <a href={href} target="_blank" rel="noopener noreferrer">
                {children}
              </a>
            );
          },
        }}
      >
        {src}
      </ReactMarkdown>
    </div>
  );
}
