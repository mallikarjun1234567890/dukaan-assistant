export function Toast({
  message,
  tone = 'info',
}: {
  message: string
  tone?: 'info' | 'error' | 'success'
}) {
  const colors = {
    info: 'bg-slate-900 text-white',
    error: 'bg-rose-600 text-white',
    success: 'bg-teal-700 text-white',
  }
  return (
    <div className={`fixed bottom-5 right-5 z-50 max-w-sm rounded-xl px-4 py-3 text-sm shadow-lg ${colors[tone]}`}>
      {message}
    </div>
  )
}
