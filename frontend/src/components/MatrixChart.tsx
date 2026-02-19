import { useState, useCallback, useRef, useMemo } from 'react'
import type { ReferenceCompany, EvaluationResult, CohortMatrixCompany } from '../types'

const ZONE_COLORS: Record<string, string> = {
  dead: '#d63939',
  compression: '#d49b1a',
  adaptation: '#2b7fd4',
  fortress: '#1a9d3f',
}

interface Props {
  referenceCompanies: ReferenceCompany[]
  evaluation?: EvaluationResult | null
  cohortCompanies?: CohortMatrixCompany[]
  hideReference?: boolean
}

export default function MatrixChart({ referenceCompanies, evaluation, cohortCompanies, hideReference }: Props) {
  const [hoveredTicker, setHoveredTicker] = useState<string | null>(null)
  const [hoveredCompany, setHoveredCompany] = useState<ReferenceCompany | null>(null)
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 })
  const [showReference, setShowReference] = useState(!hideReference)
  const containerRef = useRef<HTMLDivElement>(null)

  // Chart dimensions — larger for better readability at full width
  const W = 800
  const H = 600
  const pad = { top: 40, right: 40, bottom: 60, left: 60 }
  const plotW = W - pad.left - pad.right
  const plotH = H - pad.top - pad.bottom
  const R = 18 // logo circle radius
  const RC = 22 // cohort company circle radius (slightly larger)

  // Coordinate converters (score 0-100 → pixel position)
  const toX = (s: number) => pad.left + (s / 100) * plotW
  const toY = (s: number) => pad.top + ((100 - s) / 100) * plotH

  // Convert SVG coords to percentage for HTML overlay positioning
  const toPctX = (s: number) => (toX(s) / W) * 100
  const toPctY = (s: number) => (toY(s) / H) * 100

  const handleMouseEnter = useCallback((company: ReferenceCompany, e: React.MouseEvent) => {
    setHoveredTicker(company.ticker)
    setHoveredCompany(company)
    setTooltipPos({ x: e.clientX, y: e.clientY })
  }, [])

  const handleMouseLeave = useCallback(() => {
    setHoveredTicker(null)
    setHoveredCompany(null)
  }, [])

  const hasCohort = cohortCompanies && cohortCompanies.length > 0

  // Compute position adjustments to spread overlapping cohort circles apart
  const positionAdjustments = useMemo(() => {
    const adjustments = new Map<number, { dxPct: number; dyPct: number; labelOffset: number }>()
    if (!cohortCompanies || cohortCompanies.length === 0) return adjustments

    const items = cohortCompanies.map((c, i) => ({
      index: i,
      xPct: toPctX(c.x),
      yPct: toPctY(c.y),
    }))

    // Sort by x then y for grouping
    const sorted = [...items].sort((a, b) => a.xPct - b.xPct || a.yPct - b.yPct)

    const PROXIMITY_X = 6 // % horizontal proximity threshold for overlap
    const PROXIMITY_Y = 5 // % vertical proximity threshold for overlap
    const MIN_SPREAD = 3.0 // minimum % to spread circles apart (for pairs)

    // Group nearby items into clusters
    const visited = new Set<number>()

    for (let i = 0; i < sorted.length; i++) {
      if (visited.has(sorted[i].index)) continue

      const cluster: typeof sorted = [sorted[i]]
      visited.add(sorted[i].index)

      for (let j = i + 1; j < sorted.length; j++) {
        if (visited.has(sorted[j].index)) continue
        // Check proximity against any member of the cluster
        const isNear = cluster.some(
          (m) =>
            Math.abs(sorted[j].xPct - m.xPct) < PROXIMITY_X &&
            Math.abs(sorted[j].yPct - m.yPct) < PROXIMITY_Y
        )
        if (isNear) {
          cluster.push(sorted[j])
          visited.add(sorted[j].index)
        }
      }

      if (cluster.length === 1) {
        // No overlap — no adjustment needed
        adjustments.set(cluster[0].index, { dxPct: 0, dyPct: 0, labelOffset: 0 })
      } else {
        // Spread circles radially from cluster center
        const cx = cluster.reduce((s, m) => s + m.xPct, 0) / cluster.length
        const cy = cluster.reduce((s, m) => s + m.yPct, 0) / cluster.length

        // Scale spread based on cluster size so they don't fly too far
        const spreadPct = MIN_SPREAD + (cluster.length - 2) * 0.5

        cluster.forEach((item, idx) => {
          // Distribute evenly in a circle around the center
          const angle = (idx / cluster.length) * 2 * Math.PI - Math.PI / 2
          const dxPct = Math.cos(angle) * spreadPct
          const dyPct = Math.sin(angle) * spreadPct
          adjustments.set(item.index, {
            dxPct,
            dyPct,
            labelOffset: 0, // labels sit directly under their own circle
          })
        })
      }
    }

    return adjustments
  }, [cohortCompanies])

  return (
    <div ref={containerRef} className="relative w-full">
      {/* Toggle for reference companies when cohort is shown */}
      {hasCohort && (
        <div className="flex items-center gap-2 mb-2">
          <button
            onClick={() => setShowReference(!showReference)}
            className={`text-[11px] px-2.5 py-1 rounded-md font-medium transition-colors ${
              showReference
                ? 'bg-surface-raised text-arena-text'
                : 'text-arena-muted hover:text-arena-text-tertiary'
            }`}
          >
            {showReference ? 'Hide' : 'Show'} Reference Companies
          </button>
        </div>
      )}

      {/* SVG layer — grid, axes, labels, quadrants */}
      <svg
        width="100%"
        viewBox={`0 0 ${W} ${H}`}
        className="block"
      >
        {/* Background */}
        <rect x={0} y={0} width={W} height={H} fill="#ffffff" rx={8} />

        {/* Quadrant backgrounds */}
        <rect x={pad.left} y={toY(50)} width={plotW / 2} height={plotH / 2}
          fill="#d63939" opacity={0.05} />
        <rect x={pad.left} y={pad.top} width={plotW / 2} height={plotH / 2}
          fill="#d49b1a" opacity={0.05} />
        <rect x={toX(50)} y={toY(50)} width={plotW / 2} height={plotH / 2}
          fill="#2b7fd4" opacity={0.05} />
        <rect x={toX(50)} y={pad.top} width={plotW / 2} height={plotH / 2}
          fill="#1a9d3f" opacity={0.05} />

        {/* Grid lines */}
        <line x1={toX(50)} y1={pad.top} x2={toX(50)} y2={pad.top + plotH}
          stroke="#e5e7eb" strokeDasharray="4 4" />
        <line x1={pad.left} y1={toY(50)} x2={pad.left + plotW} y2={toY(50)}
          stroke="#e5e7eb" strokeDasharray="4 4" />

        {/* Axes */}
        <line x1={pad.left} y1={pad.top + plotH} x2={pad.left + plotW} y2={pad.top + plotH}
          stroke="#d1d5db" />
        <line x1={pad.left} y1={pad.top} x2={pad.left} y2={pad.top + plotH}
          stroke="#d1d5db" />

        {/* Axis labels */}
        <text x={W / 2} y={H - 8} textAnchor="middle" fill="#9ca3af" fontSize={12}
          fontFamily="Inter, sans-serif">
          Workflow Complexity →
        </text>
        <text x={14} y={H / 2} textAnchor="middle" fill="#9ca3af" fontSize={12}
          fontFamily="Inter, sans-serif" transform={`rotate(-90, 14, ${H / 2})`}>
          Data Moat Depth →
        </text>

        {/* Quadrant labels */}
        <text x={toX(25)} y={toY(25) + 4} textAnchor="middle" fill="#d63939" fontSize={11}
          fontWeight="600" opacity={0.45} fontFamily="Inter, sans-serif">
          DEAD ZONE
        </text>
        <text x={toX(25)} y={toY(75) + 4} textAnchor="middle" fill="#d49b1a" fontSize={11}
          fontWeight="600" opacity={0.45} fontFamily="Inter, sans-serif">
          COMPRESSION
        </text>
        <text x={toX(75)} y={toY(25) + 4} textAnchor="middle" fill="#2b7fd4" fontSize={11}
          fontWeight="600" opacity={0.45} fontFamily="Inter, sans-serif">
          ADAPTATION
        </text>
        <text x={toX(75)} y={toY(75) + 4} textAnchor="middle" fill="#1a9d3f" fontSize={11}
          fontWeight="600" opacity={0.45} fontFamily="Inter, sans-serif">
          FORTRESS
        </text>

        {/* Evaluated company marker (gold) — single evaluator mode */}
        {evaluation && (() => {
          const ex = toX(evaluation.x_score)
          const ey = toY(evaluation.y_score)
          return (
            <g>
              <defs>
                <filter id="glow-eval" x="-50%" y="-50%" width="200%" height="200%">
                  <feDropShadow dx="0" dy="0" stdDeviation="5" floodColor="#d49b1a" floodOpacity="0.6" />
                  <feDropShadow dx="0" dy="0" stdDeviation="10" floodColor="#d49b1a" floodOpacity="0.3" />
                </filter>
              </defs>
              <circle cx={ex} cy={ey} r={R + 8} fill="none" stroke="#d49b1a"
                strokeWidth={2} opacity={0.4} filter="url(#glow-eval)"
                className="animate-pulse" />
              <circle cx={ex} cy={ey} r={R + 2} fill="#d49b1a" opacity={0.9} />
              <text x={ex} y={ey + 1} textAnchor="middle" dominantBaseline="central"
                fill="white" fontSize={15} fontWeight="700">
                ★
              </text>
              <text x={ex} y={ey + R + 18} textAnchor="middle" fill="#1a1a2e"
                fontSize={12} fontWeight="bold" fontFamily="Inter, sans-serif">
                {evaluation.company_name}
              </text>
            </g>
          )
        })()}
      </svg>

      {/* HTML overlay layer — company logos positioned absolutely */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{ aspectRatio: `${W}/${H}` }}
      >
        {/* Reference companies (can be toggled off in cohort mode) */}
        {showReference && referenceCompanies.map((c) => {
          const isHovered = hoveredTicker === c.ticker
          const zoneColor = ZONE_COLORS[c.zone] || ZONE_COLORS.dead
          const pxX = toPctX(c.x)
          const pxY = toPctY(c.y)

          return (
            <div
              key={`ref-${c.ticker}`}
              className="absolute pointer-events-auto cursor-pointer"
              style={{
                left: `${pxX}%`,
                top: `${pxY}%`,
                transform: `translate(-50%, -50%) ${isHovered ? 'scale(1.15)' : 'scale(1)'}`,
                transition: 'transform 0.2s ease, box-shadow 0.2s ease',
                zIndex: isHovered ? 10 : 1,
                opacity: hasCohort ? 0.5 : 1,
              }}
              onMouseEnter={(e) => handleMouseEnter(c, e)}
              onMouseMove={(e) => setTooltipPos({ x: e.clientX, y: e.clientY })}
              onMouseLeave={handleMouseLeave}
            >
              <div
                className="relative flex items-center justify-center"
                style={{
                  width: R * 2,
                  height: R * 2,
                  borderRadius: '50%',
                  background: 'white',
                  border: `${isHovered ? 2.5 : 1.5}px solid ${isHovered ? zoneColor : '#e5e7eb'}`,
                  boxShadow: isHovered
                    ? `0 0 0 3px ${zoneColor}30, 0 0 16px ${zoneColor}50, 0 0 32px ${zoneColor}25`
                    : '0 1px 3px rgba(0,0,0,0.06)',
                  transition: 'border 0.2s ease, box-shadow 0.2s ease',
                  overflow: 'hidden',
                }}
              >
                {c.logo_url ? (
                  <img
                    src={c.logo_url}
                    alt={c.name}
                    className="block"
                    style={{ width: R * 1.4, height: R * 1.4, objectFit: 'contain' }}
                    draggable={false}
                    onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
                  />
                ) : (
                  <span style={{ color: zoneColor, fontSize: 8, fontWeight: 700, fontFamily: "'DM Mono', monospace" }}>
                    {c.ticker}
                  </span>
                )}
              </div>
            </div>
          )
        })}

        {/* Cohort companies — larger circles with zone-colored borders */}
        {cohortCompanies?.map((c, i) => {
          const key = `cohort-${c.name}-${i}`
          const isHovered = hoveredTicker === key
          const zoneColor = ZONE_COLORS[c.zone] || ZONE_COLORS.dead
          const adj = positionAdjustments.get(i)
          const pxX = toPctX(c.x) + (adj?.dxPct || 0)
          const pxY = toPctY(c.y) + (adj?.dyPct || 0)
          const labelOffset = adj?.labelOffset || 0

          return (
            <div
              key={key}
              className="absolute pointer-events-auto cursor-pointer"
              style={{
                left: `${pxX}%`,
                top: `${pxY}%`,
                transform: `translate(-50%, -50%) ${isHovered ? 'scale(1.15)' : 'scale(1)'}`,
                transition: 'all 0.3s ease',
                zIndex: isHovered ? 20 : 5,
              }}
              onMouseEnter={(e) => {
                setHoveredTicker(key)
                setHoveredCompany(c)
                setTooltipPos({ x: e.clientX, y: e.clientY })
              }}
              onMouseMove={(e) => setTooltipPos({ x: e.clientX, y: e.clientY })}
              onMouseLeave={handleMouseLeave}
            >
              <div
                className="relative flex items-center justify-center"
                style={{
                  width: RC * 2,
                  height: RC * 2,
                  borderRadius: '50%',
                  background: 'white',
                  border: `2.5px solid ${zoneColor}`,
                  boxShadow: isHovered
                    ? `0 0 0 4px ${zoneColor}30, 0 0 20px ${zoneColor}50, 0 0 40px ${zoneColor}25`
                    : `0 0 0 2px ${zoneColor}20, 0 0 8px ${zoneColor}15`,
                  transition: 'border 0.2s ease, box-shadow 0.2s ease',
                  overflow: 'hidden',
                }}
              >
                {c.logo_url ? (
                  <img
                    src={c.logo_url}
                    alt={c.name}
                    className="block"
                    style={{ width: RC * 1.3, height: RC * 1.3, objectFit: 'contain' }}
                    draggable={false}
                    onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
                  />
                ) : (
                  <span style={{ color: zoneColor, fontSize: 9, fontWeight: 700, fontFamily: "'DM Mono', monospace" }}>
                    {c.ticker}
                  </span>
                )}
              </div>
              {/* Company name label below circle — offset to avoid overlap */}
              <div
                className="absolute text-center whitespace-nowrap"
                style={{
                  top: RC * 2 + 6 + labelOffset,
                  left: '50%',
                  transform: 'translateX(-50%)',
                  fontSize: 10,
                  fontWeight: 600,
                  color: '#1a1a2e',
                  fontFamily: 'Inter, sans-serif',
                }}
              >
                {c.name}
              </div>
            </div>
          )
        })}
      </div>

      {/* Tooltip */}
      {hoveredCompany && (
        <div
          className="fixed z-50 bg-white border border-arena-border rounded-xl p-4 max-w-xs"
          style={{
            left: tooltipPos.x + 16,
            top: tooltipPos.y - 12,
            pointerEvents: 'none',
            boxShadow: '0 8px 24px rgba(0,0,0,0.12)',
          }}
        >
          <div className="flex items-center gap-2.5 mb-2.5">
            {hoveredCompany.logo_url && (
              <img
                src={hoveredCompany.logo_url}
                alt=""
                className="w-7 h-7 rounded-md"
                style={{ objectFit: 'contain' }}
              />
            )}
            <div>
              <div className="font-semibold text-arena-text text-[13px]">
                {hoveredCompany.name}
              </div>
              <div className="text-[11px] text-arena-muted font-mono">
                {hoveredCompany.ticker}
              </div>
            </div>
          </div>
          <ul className="space-y-1">
            {hoveredCompany.bullets.map((b, i) => (
              <li key={i} className="text-[12px] text-arena-text-tertiary flex gap-1.5">
                <span className="text-arena-muted mt-0.5 flex-shrink-0">•</span>
                <span>{b}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
