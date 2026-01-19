'use client'

import { useState, useEffect } from 'react'

interface Language {
  code: string
  name: string
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function Home() {
  const [text, setText] = useState('')
  const [translatedText, setTranslatedText] = useState('')
  const [sourceLang, setSourceLang] = useState('khm_Khmr') // Khmer default
  const [targetLang, setTargetLang] = useState('eng_Latn') // English default
  const [languages, setLanguages] = useState<Language[]>([])
  const [loading, setLoading] = useState(false)
  const [loadingLanguages, setLoadingLanguages] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [retryCount, setRetryCount] = useState(0)

  const fetchLanguages = async (retryDelay = 2000, maxRetries = 10) => {
    setLoadingLanguages(true)
    let attempts = 0

    const attemptFetch = async (): Promise<void> => {
      try {
        // Create abort controller for timeout
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), 5000) // 5 second timeout

        const response = await fetch(`${API_URL}/languages`, {
          signal: controller.signal
        })

        clearTimeout(timeoutId)

        if (!response.ok) {
          if (response.status === 503) {
            throw new Error('BACKEND_LOADING')
          }
          throw new Error(`HTTP error! status: ${response.status}`)
        }

        const data = await response.json()
        setLanguages(data.languages)
        setError(null)
        setLoadingLanguages(false)
        setRetryCount(0)
      } catch (err: any) {
        attempts++
        const isBackendLoading = err.message === 'BACKEND_LOADING' ||
          err.name === 'AbortError' ||
          err.message.includes('fetch')

        if (isBackendLoading && attempts < maxRetries) {
          // Backend is still loading, retry with exponential backoff
          const delay = Math.min(retryDelay * Math.pow(1.5, attempts - 1), 10000)
          setRetryCount(attempts)
          setError(`Backend model is loading... Retrying (${attempts}/${maxRetries})...`)
          setTimeout(attemptFetch, delay)
        } else {
          // Max retries reached or other error
          console.error('Error fetching languages:', err)
          setError(
            attempts >= maxRetries
              ? 'Backend is taking longer than expected to load. Please check the backend terminal and ensure the model is downloading/loading properly.'
              : 'Failed to fetch languages. Make sure the backend server is running at http://localhost:8000'
          )
          setLoadingLanguages(false)
        }
      }
    }

    await attemptFetch()
  }

  useEffect(() => {
    fetchLanguages()
  }, [])

  // Clear translated text when source text is cleared
  useEffect(() => {
    if (!text.trim()) {
      setTranslatedText('')
      setError(null) // Also clear any errors when clearing text
    }
  }, [text])

  const handleTranslate = async () => {
    if (!text.trim()) {
      setError('Please enter text to translate')
      return
    }

    if (languages.length === 0) {
      setError('Languages not loaded yet. Please wait...')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 30000) // 30 second timeout for translation

      const response = await fetch(`${API_URL}/translate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text,
          source_lang: sourceLang,
          target_lang: targetLang,
        }),
        signal: controller.signal
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        // Try to get error message from response
        let errorMessage = 'Translation failed'
        try {
          const errorData = await response.json()
          if (errorData.detail) {
            errorMessage = errorData.detail
          } else if (errorData.message) {
            errorMessage = errorData.message
          }
        } catch (e) {
          // If response is not JSON, use status-based message
          if (response.status === 503) {
            errorMessage = 'Backend model is not loaded yet. Please wait...'
          } else if (response.status === 400) {
            errorMessage = 'Invalid request. Please check your text and language settings.'
          } else if (response.status === 500) {
            errorMessage = 'Translation service error. Please try again or check the backend logs.'
          } else {
            errorMessage = `Translation failed with status ${response.status}`
          }
        }
        throw new Error(errorMessage)
      }

      const data = await response.json()
      setTranslatedText(data.translated_text)
      setError(null) // Clear any previous errors
    } catch (err: any) {
      console.error('Translation error:', err)
      if (err.name === 'AbortError') {
        setError('Translation request timed out. The text might be too long or the backend is slow. Please try again.')
      } else if (err.message) {
        setError(err.message)
      } else {
        setError('Failed to translate. Make sure the backend server is running at http://localhost:8000')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleSwapLanguages = () => {
    const temp = sourceLang
    setSourceLang(targetLang)
    setTargetLang(temp)
  }

  const handleRetryLanguages = () => {
    setRetryCount(0)
    fetchLanguages()
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-gray-800 dark:text-white mb-2">
              Translation App
            </h1>
            <p className="text-gray-600 dark:text-gray-300">
              Translate text between multiple languages
            </p>
          </div>

          {/* Error/Status Message */}
          {error && (
            <div className={`mb-4 p-4 rounded-lg ${error.includes('loading') || error.includes('Retrying')
                ? 'bg-yellow-100 border border-yellow-400 text-yellow-800'
                : 'bg-red-100 border border-red-400 text-red-700'
              }`}>
              <div className="flex items-center justify-between">
                <span>{error}</span>
                {error.includes('taking longer') && (
                  <button
                    onClick={handleRetryLanguages}
                    className="ml-4 px-3 py-1 bg-yellow-500 hover:bg-yellow-600 text-white rounded text-sm font-medium transition-colors"
                  >
                    Retry
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Main Translation Card */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 mb-6">
            {/* Language Selectors */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  From
                </label>
                <select
                  value={sourceLang}
                  onChange={(e) => setSourceLang(e.target.value)}
                  disabled={loadingLanguages || languages.length === 0}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loadingLanguages ? (
                    <option>Loading languages...</option>
                  ) : languages.length === 0 ? (
                    <option>No languages available</option>
                  ) : (
                    languages.map((lang) => (
                      <option key={lang.code} value={lang.code}>
                        {lang.name}
                      </option>
                    ))
                  )}
                </select>
              </div>

              <div className="flex items-end justify-center">
                <button
                  onClick={handleSwapLanguages}
                  className="p-2 text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-gray-700 rounded-lg transition-colors"
                  title="Swap languages"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="h-6 w-6"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"
                    />
                  </svg>
                </button>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  To
                </label>
                <select
                  value={targetLang}
                  onChange={(e) => setTargetLang(e.target.value)}
                  disabled={loadingLanguages || languages.length === 0}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loadingLanguages ? (
                    <option>Loading languages...</option>
                  ) : languages.length === 0 ? (
                    <option>No languages available</option>
                  ) : (
                    languages.map((lang) => (
                      <option key={lang.code} value={lang.code}>
                        {lang.name}
                      </option>
                    ))
                  )}
                </select>
              </div>
            </div>

            {/* Text Areas */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Source Text
                  </label>
                  <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
                    {text.length} characters
                  </span>
                </div>
                <textarea
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  placeholder="Enter text to translate..."
                  className="w-full h-48 px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Translated Text
                  </label>
                  <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
                    {translatedText.length} characters
                  </span>
                </div>
                <textarea
                  value={translatedText}
                  readOnly
                  placeholder="Translation will appear here..."
                  className="w-full h-48 px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white placeholder-gray-400 resize-none"
                />
              </div>
            </div>

            {/* Translate Button */}
            <div className="flex justify-center">
              <button
                onClick={handleTranslate}
                disabled={loading || !text.trim()}
                className="px-8 py-3 bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white font-semibold rounded-lg shadow-md transition-colors duration-200 flex items-center gap-2"
              >
                {loading ? (
                  <>
                    <svg
                      className="animate-spin h-5 w-5"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      ></circle>
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      ></path>
                    </svg>
                    Translating...
                  </>
                ) : (
                  'Translate'
                )}
              </button>
            </div>
          </div>

          {/* Info Card */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-semibold text-gray-800 dark:text-white mb-3">
              How to use
            </h2>
            <ul className="space-y-2 text-gray-600 dark:text-gray-300">
              <li className="flex items-start">
                <span className="mr-2">•</span>
                <span>Enter or paste text in the source text area</span>
              </li>
              <li className="flex items-start">
                <span className="mr-2">•</span>
                <span>Select source and target languages</span>
              </li>
              <li className="flex items-start">
                <span className="mr-2">•</span>
                <span>Click Translate to see the result</span>
              </li>
              <li className="flex items-start">
                <span className="mr-2">•</span>
                <span>Use the swap button to exchange languages</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </main>
  )
}
