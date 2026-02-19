import type { ArenaModel } from '../types'

const ORG_COLORS: Record<string, string> = {
  OpenAI: '#1a9d3f',
  Anthropic: '#d49b1a',
  Google: '#2b7fd4',
  Meta: '#7c3aed',
  xAI: '#d63939',
  DeepSeek: '#db2777',
  Mistral: '#ea580c',
  Microsoft: '#0891b2',
  Amazon: '#d49b1a',
  ByteDance: '#06b6d4',
}

const ORG_DOMAINS: Record<string, string> = {
  OpenAI: 'openai.com',
  Anthropic: 'anthropic.com',
  Google: 'google.com',
  Meta: 'meta.com',
  xAI: 'x.ai',
  DeepSeek: 'deepseek.com',
  Mistral: 'mistral.ai',
  Microsoft: 'microsoft.com',
  Amazon: 'amazon.com',
  Apple: 'apple.com',
  Oracle: 'oracle.com',
  ByteDance: 'tiktok.com',
}

function logoUrl(org: string): string {
  const domain = ORG_DOMAINS[org]
  if (domain) {
    return `https://www.google.com/s2/favicons?domain=${domain}&sz=128`
  }
  return ''
}

interface Props {
  data: ArenaModel[]
  loading: boolean
}

export default function ArenaChart({ data, loading }: Props) {
  if (loading) {
    return (
      <div className="p-6">
        <div className="h-48 flex items-center justify-center text-arena-muted text-[13px]">
          Loading rankings...
        </div>
      </div>
    )
  }

  // Compute bar widths relative to min/max Elo
  const scores = data.map((m) => m.elo_score)
  const minElo = Math.min(...scores) - 15
  const maxElo = Math.max(...scores) + 5
  const range = maxElo - minElo

  return (
    <div className="p-6">
      <div className="mb-4">
        <h2 className="text-[15px] font-semibold text-arena-text">
          LLM Arena Rankings
        </h2>
        <p className="text-[12px] text-arena-muted mt-0.5">
          General-purpose models by Elo rating
        </p>
      </div>

      {/* Custom bar chart with logos */}
      <div className="space-y-1.5">
        {data.map((m, i) => {
          const pct = ((m.elo_score - minElo) / range) * 100
          const color = ORG_COLORS[m.organization] || '#9ca3af'
          const logo = logoUrl(m.organization)

          return (
            <div key={`${m.model_name}-${i}`} className="flex items-center gap-2 group">
              {/* Rank */}
              <span className="w-5 text-right text-[11px] text-arena-muted font-mono flex-shrink-0">
                {m.rank}
              </span>

              {/* Logo */}
              <div className="w-5 h-5 flex-shrink-0 rounded overflow-hidden bg-surface-tertiary flex items-center justify-center">
                {logo ? (
                  <img
                    src={logo}
                    alt={m.organization}
                    className="w-4 h-4 object-contain"
                    draggable={false}
                    onError={(e) => {
                      (e.target as HTMLImageElement).style.display = 'none'
                    }}
                  />
                ) : (
                  <span className="text-[8px] font-bold text-arena-muted">
                    {m.organization.slice(0, 2).toUpperCase()}
                  </span>
                )}
              </div>

              {/* Model name */}
              <span className="w-[170px] text-[11px] text-arena-text-secondary truncate flex-shrink-0 group-hover:text-arena-text transition-colors">
                {m.model_name}
              </span>

              {/* Bar */}
              <div className="flex-1 h-5 bg-surface-tertiary/50 rounded overflow-hidden relative">
                <div
                  className="h-full rounded transition-all duration-500 group-hover:opacity-100"
                  style={{
                    width: `${pct}%`,
                    backgroundColor: color,
                    opacity: 0.75,
                  }}
                />
              </div>

              {/* Elo score */}
              <span className="w-10 text-right text-[11px] font-mono text-arena-text flex-shrink-0">
                {m.elo_score}
              </span>

              {/* Spend badge */}
              {m.ai_spend_billions && (
                <span className="w-12 text-right text-[10px] font-mono text-arena-muted flex-shrink-0">
                  ${m.ai_spend_billions}B
                </span>
              )}
              {!m.ai_spend_billions && (
                <span className="w-12 flex-shrink-0" />
              )}
            </div>
          )
        })}
      </div>

      {/* AI Spend legend */}
      <div className="mt-4 pt-3 border-t border-arena-border">
        <div className="text-[11px] text-arena-muted mb-2">2026 AI Capex / Total Raised</div>
        <div className="flex flex-wrap gap-x-5 gap-y-1.5">
          {data
            .filter((m) => m.ai_spend_billions)
            .reduce<ArenaModel[]>((acc, m) => {
              if (!acc.find(a => a.organization === m.organization)) acc.push(m)
              return acc
            }, [])
            .map((m) => {
              const logo = logoUrl(m.organization)
              return (
                <div key={m.organization} className="flex items-center gap-1.5 text-[11px]">
                  {logo && (
                    <img
                      src={logo}
                      alt=""
                      className="w-3.5 h-3.5 rounded-sm"
                      draggable={false}
                    />
                  )}
                  <span className="text-arena-muted">{m.organization}</span>
                  <span className="text-arena-text-secondary font-mono">${m.ai_spend_billions}B</span>
                </div>
              )
            })}
        </div>
      </div>
    </div>
  )
}
