import { clsx } from 'clsx';

const chainSteps = [
  { label: 'Camera Feed', icon: '📷', status: 'done' },
  { label: 'Object Detection', icon: '🔍', status: 'done' },
  { label: 'Vehicle Tracking', icon: '🚗', status: 'done' },
  { label: 'Event Detection', icon: '⚡', status: 'done' },
  { label: 'Evidence Timeline', icon: '📋', status: 'done' },
  { label: 'AI Classification', icon: '🧠', status: 'done' },
  { label: 'Admin Verification', icon: '✓', status: 'pending' },
  { label: 'Response', icon: '🚨', status: 'waiting' },
];

const stepColors = {
  done: 'border-success text-success bg-success/10',
  pending: 'border-amber-warning text-amber-warning bg-amber-muted animate-pulse-slow',
  waiting: 'border-border text-text-muted bg-bg-elevated',
};

export default function EvidenceChain() {
  return (
    <div className="bg-bg-card border border-border rounded-2xl p-4">
      <h3 className="text-text-primary font-semibold text-sm mb-4">Evidence Chain</h3>
      <div className="flex flex-col gap-0">
        {chainSteps.map((step, i) => (
          <div key={step.label} className="flex flex-col items-center">
            <div className={clsx(
              'flex items-center gap-2.5 w-full px-3 py-2 rounded-xl border text-xs transition-all',
              stepColors[step.status as keyof typeof stepColors]
            )}>
              <span className="text-sm">{step.icon}</span>
              <span className="font-medium">{step.label}</span>
              <span className={clsx(
                'ml-auto text-[9px] font-semibold uppercase',
                step.status === 'done' ? 'text-success' : step.status === 'pending' ? 'text-amber-warning' : 'text-text-muted'
              )}>
                {step.status === 'done' ? '✓' : step.status === 'pending' ? '●' : '○'}
              </span>
            </div>
            {i < chainSteps.length - 1 && (
              <div className={clsx('w-px h-3 transition-colors', step.status === 'done' ? 'bg-success/40' : 'bg-border')} />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
