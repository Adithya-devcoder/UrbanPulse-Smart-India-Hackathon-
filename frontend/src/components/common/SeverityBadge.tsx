import { clsx } from 'clsx';
import type { SeverityLevel } from '../../types';

interface SeverityBadgeProps {
  severity: SeverityLevel;
  size?: 'sm' | 'md';
}

const config: Record<SeverityLevel, { label: string; classes: string }> = {
  critical: { label: 'Critical', classes: 'bg-coral-muted text-coral-critical border-coral-critical/30' },
  high:     { label: 'High',     classes: 'bg-amber-muted text-amber-warning border-amber-warning/30' },
  medium:   { label: 'Medium',   classes: 'bg-yellow-900/30 text-yellow-400 border-yellow-500/30' },
  low:      { label: 'Low',      classes: 'bg-success/10 text-success border-success/30' },
};

export default function SeverityBadge({ severity, size = 'sm' }: SeverityBadgeProps) {
  const { label, classes } = config[severity];
  return (
    <span
      className={clsx(
        'inline-flex items-center font-medium border rounded-md',
        size === 'sm' ? 'px-2 py-0.5 text-[10px]' : 'px-2.5 py-1 text-xs',
        classes
      )}
    >
      {label}
    </span>
  );
}
