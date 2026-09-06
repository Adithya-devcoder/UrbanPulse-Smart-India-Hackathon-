import { clsx } from 'clsx';
import type { IncidentStatus } from '../../types';

interface StatusBadgeProps {
  status: IncidentStatus;
  size?: 'sm' | 'md';
}

const config: Record<IncidentStatus, { label: string; dot: string; classes: string }> = {
  'new':          { label: 'New',          dot: 'bg-cyan-primary',    classes: 'bg-cyan-muted text-cyan-primary border-cyan-primary/30' },
  'under-review': { label: 'Under Review', dot: 'bg-amber-warning',   classes: 'bg-amber-muted text-amber-warning border-amber-warning/30' },
  'verified':     { label: 'Verified',     dot: 'bg-cyan-secondary',  classes: 'bg-cyan-muted/50 text-cyan-secondary border-cyan-secondary/30' },
  'assigned':     { label: 'Assigned',     dot: 'bg-purple-400',      classes: 'bg-purple-900/30 text-purple-300 border-purple-500/30' },
  'in-progress':  { label: 'In Progress',  dot: 'bg-amber-warning',   classes: 'bg-amber-muted text-amber-warning border-amber-warning/30' },
  'resolved':     { label: 'Resolved',     dot: 'bg-success',         classes: 'bg-success/10 text-success border-success/30' },
  'rejected':     { label: 'Rejected',     dot: 'bg-text-muted',      classes: 'bg-bg-elevated text-text-muted border-border' },
};

export default function StatusBadge({ status, size = 'sm' }: StatusBadgeProps) {
  const { label, dot, classes } = config[status];
  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1.5 font-medium border rounded-md',
        size === 'sm' ? 'px-2 py-0.5 text-[10px]' : 'px-2.5 py-1 text-xs',
        classes
      )}
    >
      <span className={clsx('w-1.5 h-1.5 rounded-full flex-shrink-0', dot)} />
      {label}
    </span>
  );
}
