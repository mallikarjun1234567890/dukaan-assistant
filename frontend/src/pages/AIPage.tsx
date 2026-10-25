import { Sparkles } from 'lucide-react'
import { useState } from 'react'
import type { FormEvent } from 'react'
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

export function AIPage() {
  const [message, setMessage] = useState(suggestions[0])
  const [turns, setTurns] = useState<ChatTurn[]>([])
  const [error, setError] = useState('')
  const [sending, setSending] = useState(false)

  async function send(event?: FormEvent, preset?: string) {
    event?.preventDefault()
    const text = (preset ?? message).trim()
    if (!text) return
    setSending(true)
    setError('')
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

  return (
    <div className="mx-auto max-w-3xl space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Ask Dukaan AI</h1>
        <p className="mt-1 text-sm text-slate-500">
          Python calculates the shop snapshot. The model only explains it, using Gemini, then Groq, hosted
          Hugging Face, then local Ollama. It cannot change stock, create invoices, or approve reorders.
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        {suggestions.map((item) => (
          <button
            key={item}
            type="button"
            onClick={() => void send(undefined, item)}
            className="rounded-full bg-white px-3 py-1.5 text-xs font-medium text-teal-800 ring-1 ring-slate-200 hover:bg-teal-50"
          >
            {item}
          </button>
        ))}
      </div>

      <section className="min-h-72 space-y-3 rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
        {turns.length === 0 ? (
          <div className="flex h-48 flex-col items-center justify-center text-center text-slate-500">
            <Sparkles className="mb-2 text-teal-700" />
            <p>Ask about restocking, inventory value, or today&apos;s sales.</p>
          </div>
        ) : (
          turns.map((turn, index) => (
            <article
              key={`${turn.role}-${index}`}
              className={`rounded-2xl px-4 py-3 text-sm whitespace-pre-wrap ${
                turn.role === 'user' ? 'ml-8 bg-teal-700 text-white' : 'mr-8 bg-slate-50 text-slate-800'
              }`}
            >
              {turn.text}
              {turn.provider || turn.sources?.length ? (
                <p className="mt-2 text-xs text-slate-500">
                  {turn.provider ? `Answered by ${turn.provider}${turn.model ? ` (${turn.model})` : ''}` : ''}
                  {turn.provider && turn.sources?.length ? ' · ' : ''}
                  {turn.sources?.length ? `Sources: ${turn.sources.join(' · ')}` : ''}
                </p>
              ) : null}
            </article>
          ))
        )}
        {sending ? <p className="text-sm text-slate-400">Thinking with current shop data…</p> : null}
      </section>

      {error ? (
        <p className="rounded-xl bg-amber-50 px-4 py-3 text-sm text-amber-800" role="alert">
          {error}
        </p>
      ) : null}

      <form onSubmit={(event) => void send(event)} className="flex gap-2">
        <label className="sr-only" htmlFor="ai-message">
          Message
        </label>
        <input
          id="ai-message"
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          maxLength={4000}
          placeholder="Ask about stock, sales, or reorders"
          className="flex-1 rounded-xl border border-slate-200 bg-white px-3 py-3"
        />
        <button
          type="submit"
          disabled={sending || !message.trim()}
          className="rounded-xl bg-teal-700 px-4 py-3 font-semibold text-white disabled:opacity-60"
        >
          Send
        </button>
      </form>
    </div>
  )
}
