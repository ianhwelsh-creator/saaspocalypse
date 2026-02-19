const SOURCE_STYLES: Record<string, { color: string; label: string }> = {
  hackernews: { color: '#ea580c', label: 'HN' },
  techcrunch: { color: '#1a9d3f', label: 'TC' },
  reddit: { color: '#d63939', label: 'RD' },
  podcast: { color: '#8b5cf6', label: 'POD' },
  twitter: { color: '#0284c7', label: 'X' },
  rss: { color: '#d49b1a', label: 'RSS' },
  // Institutional sources
  wsj: { color: '#1a1a1a', label: 'WSJ' },
  reuters: { color: '#ff8000', label: 'REU' },
  ft: { color: '#d4996e', label: 'FT' },
  bloomberg: { color: '#1a1a1a', label: 'BBG' },
  cnbc: { color: '#005594', label: 'CNBC' },
  institutional: { color: '#6b5b95', label: 'INST' },
}

export default function SourceBadge({ source }: { source: string }) {
  const style = SOURCE_STYLES[source] || { color: '#9ca3af', label: source.toUpperCase().slice(0, 3) }
  return (
    <span
      className="text-[10px] font-mono font-medium px-1.5 py-0.5 rounded-md"
      style={{
        color: style.color,
        backgroundColor: `${style.color}12`,
      }}
    >
      {style.label}
    </span>
  )
}
