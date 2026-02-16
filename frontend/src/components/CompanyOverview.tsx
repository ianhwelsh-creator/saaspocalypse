interface Props {
  overview: string
}

export default function CompanyOverview({ overview }: Props) {
  const paragraphs = overview.split('\n').filter(Boolean)

  return (
    <div className="bg-surface-secondary rounded-xl border border-arena-border p-6">
      <h3 className="text-[15px] font-semibold text-arena-text mb-3">
        Company Overview
      </h3>
      <div className="space-y-3">
        {paragraphs.map((p, i) => (
          <p key={i} className="text-[13px] text-arena-text-secondary leading-relaxed">
            {p}
          </p>
        ))}
      </div>
    </div>
  )
}
