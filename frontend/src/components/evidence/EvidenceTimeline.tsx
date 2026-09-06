import { clsx } from 'clsx';
import type { TimelineEvent } from '../../types';

interface Props {
  events: TimelineEvent[];
  activeEventId: string | null;
  onSelectEvent: (event: TimelineEvent) => void;
}

export default function EvidenceTimeline({ events, activeEventId, onSelectEvent }: Props) {
  return (
    <div className="bg-bg-card border border-border rounded-2xl p-4">
      <h3 className="text-text-primary font-semibold text-sm mb-4">AI Evidence Timeline</h3>
      <div className="relative">
        {/* Vertical connector line */}
        <div className="absolute left-5 top-4 bottom-4 w-px bg-border" />

        <div className="space-y-2">
          {events.map((event, idx) => {
            const isActive = event.id === activeEventId;
            const isPast = events.findIndex(e => e.id === activeEventId) > idx;
            return (
              <button
                key={event.id}
                onClick={() => onSelectEvent(event)}
                className={clsx(
                  'w-full flex items-start gap-3 p-3 rounded-xl border transition-all text-left group relative',
                  isActive
                    ? 'bg-cyan-muted border-cyan-primary/40 shadow-cyan-glow'
                    : 'bg-bg-elevated border-transparent hover:border-border hover:bg-bg-elevated'
                )}
              >
                {/* Timeline node */}
                <div className={clsx(
                  'flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center text-lg z-10 border-2 transition-all',
                  isActive ? 'border-cyan-primary bg-cyan-muted shadow-cyan-glow-md' : isPast ? 'border-border bg-bg-card' : 'border-border bg-bg-primary'
                )}>
                  {event.icon}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0 pt-0.5">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className={clsx('font-mono font-semibold text-xs', isActive ? 'text-cyan-primary' : 'text-text-muted')}>
                      {event.timestamp}
                    </span>
                    {event.vehicleRef && (
                      <span className={clsx(
                        'text-[9px] px-1.5 py-0.5 rounded font-semibold',
                        event.vehicleRef === 'A' ? 'bg-cyan-muted text-cyan-primary' : 'bg-purple-900/40 text-purple-300'
                      )}>
                        VEH-{event.vehicleRef}
                      </span>
                    )}
                  </div>
                  <div className={clsx('text-xs font-medium', isActive ? 'text-text-primary' : 'text-text-secondary')}>
                    {event.label}
                  </div>

                  {/* Expanded observation when active */}
                  {isActive && (
                    <div className="mt-2 p-2 bg-bg-primary rounded-lg border border-border">
                      <div className="text-[10px] text-text-muted mb-1 font-medium uppercase tracking-widest">AI Observation</div>
                      <p className="text-text-secondary text-[11px] leading-relaxed">{event.observation}</p>
                    </div>
                  )}
                </div>

                {/* Active indicator */}
                {isActive && (
                  <div className="absolute right-3 top-3 w-1.5 h-1.5 rounded-full bg-cyan-primary animate-pulse-slow" />
                )}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
