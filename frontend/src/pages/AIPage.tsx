import { ChevronDown, Sparkles } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import type { FormEvent, KeyboardEvent, UIEvent } from 'react'
import { AssistantMarkdown } from '../components/AssistantMarkdown'
import { ApiError, api } from '../services/api'

interface ChatTurn {
  role: 'user' | 'assistant'
  text: string
  sources?: string[]
  provider?: string
  model?: string
}

const suggestions = [
  'Which products need restocking today?',
  'What is the total value of my inventory?',
  'Which products have the lowest stock?',
  "Summarize today's sales.",
  'Why should I reorder cooking oil?',
  "Give me a summary of my shop's current performance.",
]

const NEAR_BOTTOM_PX = 96

export function AIPage() {
  const [message, setMessage] = useState('')
  const [turns, setTurns] = useState<ChatTurn[]>([])
  const [error, setError] = useState('')
  const [sending, setSending] = useState(false)
  const [pinnedToBottom, setPinnedToBottom] = useState(true)
  const [showJump, setShowJump] = useState(false)
  const scrollerRef = useRef<HTMLDivElement>(null)
  const endRef = useRef<HTMLDivElement>(null)

  function isNearBottom(node: HTMLDivElement): boolean {
    return node.scrollHeight - node.scrollTop - node.clientHeight < NEAR_BOTTOM_PX
  }

  function scrollToLatest(behavior: ScrollBehavior = 'smooth') {
    endRef.current?.scrollIntoView({ behavior, block: 'end' })
    setPinnedToBottom(true)
    setShowJump(false)
  }

  useEffect(() => {
    if (!pinnedToBottom) {
      if (turns.length > 0 || sending) setShowJump(true)
      return
    }
    const node = scrollerRef.current
    if (!node) return
    node.scrollTop = node.scrollHeight
    setShowJump(false)
  }, [turns, sending, pinnedToBottom])

  function onScroll(event: UIEvent<HTMLDivElement>) {
    const near = isNearBottom(event.currentTarget)
    setPinnedToBottom(near)
    if (near) setShowJump(false)
  }

  async function send(event?: FormEvent, preset?: string) {
    event?.preventDefault()
    if (sending) return
    const text = (preset ?? message).trim()
    if (!text) return
    setSending(true)
    setError('')
    setPinnedToBottom(true)
    setTurns((current) => [...current, { role: 'user', text }])
    setMessage('')
    try {
      const result = await api.chat(text)
      setTurns((current) => [
        ...current,
        {
          role: 'assistant',
          text: result.reply,
          sources: result.sources,
          provider: result.provider,
          model: result.model,
        },
      ])
    } catch (err) {
      const detail =
        err instanceof ApiError
          ? err.message
          : 'The AI request failed. Inventory and billing still work.'
      setError(detail)
    } finally {
      setSending(false)
    }
  }

  function onComposerKey(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      void send()
    }
  }

  return (
    <div className="flex h-full min-h-0 flex-col overflow-hidden">
      <div className="shrink-0">
        <h1 className="text-2xl font-bold text-slate-900">Ask Dukaan AI</h1>
        <p className="mt-1 text-sm text-slate-500">
          Python calculates the shop snapshot. The model only explains it. It cannot change stock, create
          invoices, or approve reorders.
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          {suggestions.map((item) => (
            <button
              key={item}
              type="button"
              disabled={sending}
              onClick={() => void send(undefined, item)}
              className="rounded-full bg-white px-3 py-1.5 text-xs font-medium text-teal-800 ring-1 ring-slate-200 hover:bg-teal-50 disabled:opacity-60"
            >
              {item}
            </button>
          ))}
        </div>
      </div>

      <div className="relative mt-4 min-h-0 flex-1">
        <div
          ref={scrollerRef}
          onScroll={onScroll}
          className="absolute inset-0 overflow-x-hidden overflow-y-auto pr-1"
          aria-live="polite"
        >
          {turns.length === 0 && !sending ? (
            <div className="flex h-full min-h-48 flex-col items-center justify-center text-center text-slate-500">
              <Sparkles className="mb-2 text-teal-700" />
              <p>Ask about restocking, inventory value, or today&apos;s sales.</p>
            </div>
          ) : (
            <div className="space-y-3 pb-2">
              {turns.map((turn, index) =>
                turn.role === 'user' ? (
                  <article key={`user-${index}`} className="flex justify-end">
                    <div className="max-w-[min(36rem,85%)] rounded-2xl bg-teal-700 px-4 py-3 text-sm leading-6 whitespace-pre-wrap text-white">
                      {turn.text}
                    </div>
                  </article>
                ) : (
                  <article key={`assistant-${index}`} className="flex justify-start">
                    <div className="max-w-[min(46rem,100%)] rounded-2xl bg-white px-4 py-3 ring-1 ring-slate-200">
                      <AssistantMarkdown text={turn.text} />
                      {turn.provider || turn.sources?.length ? (
                        <p className="mt-3 text-xs text-slate-400">
                          {turn.provider
                            ? `Answered by ${turn.provider}${turn.model ? ` (${turn.model})` : ''}`
                            : ''}
                          {turn.provider && turn.sources?.length ? ' · ' : ''}
                          {turn.sources?.length ? `Sources: ${turn.sources.join(' · ')}` : ''}
                        </p>
                      ) : null}
                    </div>
                  </article>
                ),
              )}
              {sending ? (
                <p className="text-sm text-slate-400" aria-live="polite">
                  Thinking with current shop data…
                </p>
              ) : null}
              <div ref={endRef} />
            </div>
          )}
        </div>
        {showJump ? (
          <button
            type="button"
            onClick={() => scrollToLatest()}
            className="absolute bottom-3 left-1/2 z-10 inline-flex -translate-x-1/2 items-center gap-1 rounded-full bg-[#0b3b36] px-3 py-1.5 text-xs font-semibold text-white shadow"
          >
            <ChevronDown size={14} />
            Jump to latest
          </button>
        ) : null}
      </div>

      {error ? (
        <p className="mt-3 shrink-0 rounded-xl bg-amber-50 px-4 py-3 text-sm text-amber-800" role="alert">
          {error}
        </p>
      ) : null}

      <form onSubmit={(event) => void send(event)} className="mt-3 flex shrink-0 gap-2 pb-[env(safe-area-inset-bottom)]">
        <label className="sr-only" htmlFor="ai-message">
          Message
        </label>
        <textarea
          id="ai-message"
          rows={2}
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          onKeyDown={onComposerKey}
          maxLength={4000}
          placeholder="Ask about stock, sales, or reorders"
          className="max-h-32 min-h-12 flex-1 resize-y rounded-xl border border-slate-200 bg-white px-3 py-3 outline-none ring-teal-700 focus:ring-2"
        />
        <button
          type="submit"
          disabled={sending || !message.trim()}
          className="self-end rounded-xl bg-teal-700 px-4 py-3 font-semibold text-white hover:bg-teal-800 disabled:opacity-60"
        >
          {sending ? 'Sending…' : 'Send'}
        </button>
      </form>
    </div>
  )
}
