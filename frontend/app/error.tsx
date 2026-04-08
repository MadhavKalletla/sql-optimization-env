'use client'

export default function ErrorPage({
  error,
  reset,
}: {
  error: Error
  reset: () => void
}) {
  return (
    <div
      className="min-h-screen flex items-center justify-center"
      style={{ background: '#0A0B1A' }}
    >
      <div
        className="text-center p-8 rounded-2xl"
        style={{
          background: '#0F1229',
          border: '1px solid #FF525230',
        }}
      >
        <div className="text-4xl mb-4">⚠</div>

        <div
          className="font-bold text-lg mb-2"
          style={{ color: '#FF5252' }}
        >
          Something went wrong
        </div>

        <div
          className="text-sm mb-6"
          style={{ color: '#8892A4' }}
        >
          {error.message}
        </div>

        <button
          onClick={reset}
          className="px-6 py-2 rounded-lg text-sm font-bold"
          style={{
            background: 'linear-gradient(135deg, #4A90D9, #00D4FF)',
            color: '#fff',
          }}
        >
          Try again
        </button>
      </div>
    </div>
  )
}