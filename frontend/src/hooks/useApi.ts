import { useState, useCallback } from 'react'

export function useApi() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const post = useCallback(async <T = unknown>(url: string, body?: unknown): Promise<T | null> => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: body ? JSON.stringify(body) : undefined,
      })
      if (!res.ok) {
        const errBody = await res.json().catch(() => ({}))
        throw new Error(errBody.detail || `HTTP ${res.status}`)
      }
      return await res.json() as T
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Request failed'
      setError(msg)
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  const put = useCallback(async <T = unknown>(url: string, body?: unknown): Promise<T | null> => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(url, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: body ? JSON.stringify(body) : undefined,
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      return await res.json() as T
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Request failed'
      setError(msg)
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  const del = useCallback(async (url: string): Promise<boolean> => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(url, { method: 'DELETE' })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      return true
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Request failed'
      setError(msg)
      return false
    } finally {
      setLoading(false)
    }
  }, [])

  return { post, put, del, loading, error }
}
