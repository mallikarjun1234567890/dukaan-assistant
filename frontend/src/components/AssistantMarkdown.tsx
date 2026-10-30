import type { Components } from 'react-markdown'
import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

function safeHref(href?: string): string | undefined {
  if (!href) return undefined
  if (/^(https?:|mailto:)/i.test(href)) return href
  return undefined
}

const components: Components = {
  h1: ({ children }) => <h2 className="mt-3 text-base font-bold text-slate-900 first:mt-0">{children}</h2>,
  h2: ({ children }) => <h3 className="mt-3 text-sm font-bold text-slate-900 first:mt-0">{children}</h3>,
  h3: ({ children }) => <h4 className="mt-3 text-sm font-semibold text-slate-900 first:mt-0">{children}</h4>,
  p: ({ children }) => <p className="mt-2 text-sm leading-6 text-slate-800 first:mt-0">{children}</p>,
  ul: ({ children }) => <ul className="mt-2 list-disc space-y-1 pl-5 text-sm leading-6">{children}</ul>,
  ol: ({ children }) => <ol className="mt-2 list-decimal space-y-1 pl-5 text-sm leading-6">{children}</ol>,
  li: ({ children }) => <li className="text-slate-800">{children}</li>,
  strong: ({ children }) => <strong className="font-semibold text-slate-900">{children}</strong>,
  em: ({ children }) => <em className="italic">{children}</em>,
  hr: () => <hr className="my-3 border-slate-200" />,
  blockquote: ({ children }) => (
    <blockquote className="mt-2 border-l-2 border-teal-600 pl-3 text-sm text-slate-700">{children}</blockquote>
  ),
  code: ({ className, children }) => {
    const block = Boolean(className)
    if (block) {
      return (
        <code className="block overflow-x-auto rounded-lg bg-slate-900 px-3 py-2 text-xs text-slate-100">{children}</code>
      )
    }
    return <code className="rounded bg-slate-100 px-1 py-0.5 font-mono text-xs text-slate-800">{children}</code>
  },
  pre: ({ children }) => <pre className="mt-2 overflow-x-auto">{children}</pre>,
  a: ({ href, children }) => {
    const url = safeHref(href)
    if (!url) return <span>{children}</span>
    return (
      <a href={url} target="_blank" rel="noopener noreferrer" className="font-medium text-teal-800 underline">
        {children}
      </a>
    )
  },
  table: ({ children }) => (
    <div className="mt-3 max-w-full overflow-x-auto">
      <table className="min-w-full border-collapse text-left text-sm">{children}</table>
    </div>
  ),
  thead: ({ children }) => <thead className="bg-slate-50 text-xs uppercase text-slate-500">{children}</thead>,
  tbody: ({ children }) => <tbody>{children}</tbody>,
  tr: ({ children }) => <tr className="border-b border-slate-200 last:border-0">{children}</tr>,
  th: ({ children }) => <th className="whitespace-nowrap px-3 py-2 font-semibold">{children}</th>,
  td: ({ children }) => <td className="px-3 py-2 text-slate-800">{children}</td>,
}

export function AssistantMarkdown({ text }: { text: string }) {
  return (
    <div className="max-w-none">
      <Markdown remarkPlugins={[remarkGfm]} components={components}>
        {text}
      </Markdown>
    </div>
  )
}
