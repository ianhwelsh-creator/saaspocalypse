interface Props {
  items: string[]
}

export default function DiligenceList({ items }: Props) {
  return (
    <div className="bg-surface-secondary rounded-xl border border-arena-border p-6">
      <h3 className="text-[15px] font-semibold text-arena-text mb-4">
        AI-Proof Diligence Checklist
      </h3>
      <ol className="space-y-3">
        {items.map((item, i) => (
          <li key={i} className="flex gap-3">
            <span className="flex-shrink-0 w-6 h-6 rounded-full bg-surface-tertiary flex items-center justify-center text-[11px] font-semibold text-arena-text-tertiary">
              {i + 1}
            </span>
            <p className="text-[13px] text-arena-text-secondary leading-relaxed pt-0.5">
              {item}
            </p>
          </li>
        ))}
      </ol>
    </div>
  )
}
