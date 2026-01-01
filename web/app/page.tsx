'use client'

import { useState } from 'react'

export default function Home() {
  const [text, setText] = useState('')
  const [audioUrl, setAudioUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleGenerate = async () => {
    if (!text.trim()) return

    setLoading(true)
    setError('')
    try {
      const formData = new FormData()
      formData.append('text', text)
      formData.append('engine', 'gtts')
      formData.append('language', 'en')

      const response = await fetch('http://localhost:8000/api/tts', {
        method: 'POST',
        body: formData,
      })

      const data = await response.json()
      if (data.success) {
        setAudioUrl(`http://localhost:8000${data.audio_url}`)
      } else {
        setError('Failed to generate speech')
      }
    } catch (err) {
      setError('Error connecting to backend. Make sure the backend server is running on port 8000.')
      console.error('Error generating speech:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen p-8 bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="max-w-4xl mx-auto">
        <header className="text-center mb-12">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            🎙️ VoxLabs
          </h1>
          <p className="text-xl text-gray-600">
            Professional AI Voice Cloning Platform
          </p>
        </header>

        <div className="bg-white rounded-2xl shadow-xl p-8">
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Enter Text
            </label>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
              rows={4}
              placeholder="Type something to convert to speech..."
            />
          </div>

          <button
            onClick={handleGenerate}
            disabled={loading || !text.trim()}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
          >
            {loading ? 'Generating...' : 'Generate Speech'}
          </button>

          {error && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-700 text-sm">{error}</p>
            </div>
          )}

          {audioUrl && (
            <div className="mt-8 p-6 bg-gray-50 rounded-lg">
              <h3 className="text-lg font-semibold mb-4 text-gray-900">Generated Audio</h3>
              <audio controls className="w-full" src={audioUrl}>
                Your browser does not support the audio element.
              </audio>
              <p className="text-sm text-gray-500 mt-2">
                ⚠️ AI-Generated Audio
              </p>
            </div>
          )}
        </div>

        <footer className="text-center mt-12 text-gray-600">
          <p>Made with ❤️ for ethical AI voice technology</p>
        </footer>
      </div>
    </main>
  )
}
