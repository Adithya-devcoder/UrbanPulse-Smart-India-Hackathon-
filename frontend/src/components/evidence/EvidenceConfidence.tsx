interface ConfidenceItem {
  label: string;
  value: number;
  color: string;
}

interface Props {
  items: ConfidenceItem[];
  overall: number;
}

export default function EvidenceConfidence({ items, overall }: Props) {
  return (
    <div className="bg-bg-card border border-border rounded-2xl p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-text-primary font-semibold text-sm">AI Evidence Confidence</h3>
        <div className="flex items-center gap-1.5 px-2.5 py-1 bg-cyan-muted rounded-lg border border-cyan-primary/20">
          <span className="w-1.5 h-1.5 rounded-full bg-cyan-primary animate-pulse-slow" />
          <span className="text-cyan-primary text-[11px] font-semibold">Overall: {overall}%</span>
        </div>
      </div>

      <div className="space-y-3">
        {items.map((item) => (
          <div key={item.label}>
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-text-secondary text-xs">{item.label}</span>
              <span className="text-text-primary text-xs font-semibold font-mono">{item.value}%</span>
            </div>
            <div className="h-2 bg-bg-elevated rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-700"
                style={{ width: `${item.value}%`, background: item.color }}
              />
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 pt-3 border-t border-border">
        <div className="flex items-center gap-2">
          <div className="flex-1 h-3 bg-bg-elevated rounded-full overflow-hidden">
            <div
              className="h-full rounded-full"
              style={{ width: `${overall}%`, background: `linear-gradient(90deg, #D47A45, #6F9E75)` }}
            />
          </div>
          <span className="text-text-muted text-[10px]">AI-generated assessment</span>
        </div>
      </div>
    </div>
  );
}
