import { useState } from 'react'
import { useApi } from '../hooks/useApi'

interface Props {
  subject: string
  html: string
}

export default function NewsletterEditor({ subject, html }: Props) {
  const [email, setEmail] = useState('')
  const [sent, setSent] = useState(false)
  const { post, loading, error } = useApi()

  const handleSend = async () => {
    if (!email) return
    const result = await post('/api/newsletter/send', {
      html,
      recipient_email: email,
      subject,
    })
    if (result) setSent(true)
  }

  return (
    <div className="space-y-4">
      {/* Preview */}
      <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
        <h3 className="text-lg font-semibold text-white mb-2">Preview</h3>
        <p className="text-sm text-gray-400 mb-4">Subject: {subject}</p>
        <div
          className="bg-white rounded-lg p-6 text-gray-900 text-sm overflow-auto max-h-[500px]"
          dangerouslySetInnerHTML={{ __html: html }}
        />
      </div>

      {/* Send */}
      <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
        <h3 className="text-lg font-semibold text-white mb-3">Send Newsletter</h3>
        {sent ? (
          <div className="text-emerald-400 text-sm">Newsletter sent successfully!</div>
        ) : (
          <div className="flex gap-3">
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="recipient@example.com"
              className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-gray-600"
            />
            <button
              onClick={handleSend}
              disabled={loading || !email}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors"
            >
              {loading ? 'Sending...' : 'Send'}
            </button>
          </div>
        )}
        {error && <div className="text-red-400 text-xs mt-2">{error}</div>}
      </div>
    </div>
  )
}
