import { useMemo, useState } from 'react'
import {
  LineChart, Line, XAxis, YAxis, Tooltip, Legend,
  ResponsiveContainer, ReferenceLine, CartesianGrid,
} from 'recharts'
import type { BasketTimeSeriesResponse } from '../types'

const LINES = [
  { key: 'dead_zone', label: 'Dead Zone', color: '#d63939' },
  { key: 'compression_zone', label: 'Compression', color: '#d49b1a' },
  { key: 'adaptation_zone', label: 'Adaptation', color: '#2b7fd4' },
  { key: 'fortress_zone', label: 'Fortress', color: '#1a9d3f' },
  { key: 'ai_etfs', label: 'AI ETFs', color: '#8b5cf6' },
  { key: 'sp500', label: 'S&P 500', color: '#6b7280' },
]

const RANGES = [
  { label: 'ALL', days: 0 },
  { label: '3M', days: 90 },
  { label: '1M', days: 30 },
  { label: '1W', days: 7 },
]

interface Props {
  data: BasketTimeSeriesResponse | null
  loading: boolean
}

export default function BasketChart({ data, loading }: Props) {
  const [range, setRange] = useState(0)

  const chartData = useMemo(() => {
    if (!data?.series?.length) return []
    const series = data.series
    if (range === 0) return series
    const cutoff = new Date()
    cutoff.setDate(cutoff.getDate() - range)
    const cutoffStr = cutoff.toISOString().slice(0, 10)
    return series.filter(p => p.date >= cutoffStr)
  }, [data, range])

  const { yMin, yMax } = useMemo(() => {
    if (!chartData.length) return { yMin: 80, yMax: 120 }
    let min = 100, max = 100
    for (const point of chartData) {
      for (const line of LINES) {
        const val = point[line.key as keyof typeof point] as number | undefined
        if (val !== undefined) {
          if (val < min) min = val
          if (val > max) max = val
        }
      }
    }
    const padding = (max - min) * 0.1 || 5
    return { yMin: Math.floor(min - padding), yMax: Math.ceil(max + padding) }
  }, [chartData])

  if (loading) {
    return (
      <div className="p-6">
        <div className="h-64 flex items-center justify-center text-arena-muted text-[13px]">
          Loading baskets...
        </div>
      </div>
    )
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-[15px] font-semibold text-arena-text">
            SaaSpocalypse Baskets
          </h2>
          <p className="text-[12px] text-arena-muted mt-0.5">
            Indexed to 100 on {data?.baseline_date || '2026-01-30'}
          </p>
        </div>
        <div className="flex rounded-lg overflow-hidden border border-arena-border">
          {RANGES.map((r) => (
            <button
              key={r.label}
              onClick={() => setRange(r.days)}
              className={`px-3 py-1.5 text-[12px] font-medium transition-colors ${
                range === r.days
                  ? 'bg-surface-raised text-arena-text'
                  : 'text-arena-muted hover:text-arena-text-tertiary'
              }`}
            >
              {r.label}
            </button>
          ))}
        </div>
      </div>

      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" strokeOpacity={0.6} />
          <XAxis
            dataKey="date"
            tick={{ fill: '#9ca3af', fontSize: 11 }}
            tickFormatter={(v: string) => v.slice(5)}
            axisLine={{ stroke: '#e5e7eb' }}
            tickLine={{ stroke: '#e5e7eb' }}
          />
          <YAxis
            domain={[yMin, yMax]}
            tick={{ fill: '#9ca3af', fontSize: 11 }}
            axisLine={{ stroke: '#e5e7eb' }}
            tickLine={{ stroke: '#e5e7eb' }}
          />
          <ReferenceLine y={100} stroke="#d1d5db" strokeDasharray="4 4" />
          <Tooltip
            contentStyle={{
              backgroundColor: '#ffffff',
              border: '1px solid #f0f0f0',
              borderRadius: '8px',
              fontSize: '12px',
              fontFamily: 'Inter, sans-serif',
              color: '#1a1a2e',
              boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
            }}
            labelStyle={{ color: '#6b7280', fontSize: '11px' }}
          />
          <Legend
            wrapperStyle={{ fontSize: '11px', paddingTop: '10px', color: '#6b7280' }}
          />
          {LINES.map((line) => (
            <Line
              key={line.key}
              type="monotone"
              dataKey={line.key}
              name={line.label}
              stroke={line.color}
              dot={false}
              strokeWidth={2}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
