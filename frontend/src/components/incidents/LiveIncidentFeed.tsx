import { useNavigate } from 'react-router-dom';
import { useApp } from '../../context/AppContext';
import { formatDistanceToNow } from 'date-fns';
import { clsx } from 'clsx';
import type { Incident } from '../../types';

const incidentConfig = {
  'accident':      { icon: '🔴', color: 'border-coral-critical/30 hover:border-coral-critical/60', dot: 'bg-coral-critical' },
  'hit-and-run':   { icon: '🔴', color: 'border-coral-critical/30 hover:border-coral-critical/60', dot: 'bg-coral-critical' },
  'pothole':       { icon: '🟠', color: 'border-amber-warning/30 hover:border-amber-warning/60',   dot: 'bg-amber-warning' },
  'waterlogging':  { icon: '💧', color: 'border-cyan-primary/30 hover:border-cyan-primary/60',     dot: 'bg-cyan-primary' },
  'traffic':       { icon: '🟡', color: 'border-yellow-500/30 hover:border-yellow-500/60',         dot: 'bg-yellow-400' },
  'infrastructure':{ icon: '🔧', color: 'border-purple-500/30 hover:border-purple-500/60',         dot: 'bg-purple-400' },
  'road-hazard':   { icon: '🚧', color: 'border-amber-warning/30 hover:border-amber-warning/60',   dot: 'bg-amber-warning' },
};

const subtitleMap: Record<string, (inc: Incident) => string> = {
  'accident':      () => 'Accident detected',
  'hit-and-run':   (i) => `AI Confidence: ${i.aiConfidence}%`,
  'pothole':       (i) => `Risk Score: ${Math.round(i.aiConfidence * 0.9)}`,
  'waterlogging':  () => 'Severity: High',
  'traffic':       () => 'Delay: 18 min',
  'infrastructure':() => 'Inspection needed',
  'road-hazard':   () => 'Clearance required',
};

interface Props {
  incidents: Incident[];
  maxItems?: number;
}

export default function LiveIncidentFeed({ incidents, maxItems = 8 }: Props) {
  const navigate = useNavigate();
  const { setActiveIncidentId } = useApp();

  function handleClick(id: string) {
    setActiveIncidentId(id);
    navigate('/evidence');
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-text-primary font-semibold text-sm">Live Incident Feed</h3>
        <div className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-coral-critical animate-pulse" />
          <span className="text-text-muted text-[10px]">Live</span>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto space-y-2 pr-0.5">
        {incidents.slice(0, maxItems).map((inc) => {
          const cfg = incidentConfig[inc.type] || incidentConfig.accident;
          const subtitle = subtitleMap[inc.type]?.(inc) ?? '';
          const isDemo = inc.id === 'INC-2048';
          return (
            <button
              key={inc.id}
              onClick={() => handleClick(inc.id)}
              className={clsx(
                'w-full flex items-start gap-3 p-3 rounded-xl border bg-bg-card transition-all text-left group',
                cfg.color,
                isDemo && 'ring-1 ring-coral-critical/20'
              )}
            >
              <span className="text-lg flex-shrink-0 leading-none mt-0.5">{cfg.icon}</span>
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2">
                  <span className="text-text-primary text-xs font-semibold leading-tight group-hover:text-cyan-primary transition-colors">
                    {inc.title}
                    {isDemo && <span className="ml-1.5 text-[9px] bg-coral-muted text-coral-critical px-1 py-0.5 rounded font-medium">DEMO</span>}
                  </span>
                  <span className="text-text-muted text-[9px] flex-shrink-0 whitespace-nowrap">
                    {formatDistanceToNow(inc.detectedAt, { addSuffix: true })}
                  </span>
                </div>
                <div className="text-text-muted text-[10px] mt-0.5">{inc.location}</div>
                <div className="text-text-secondary text-[10px] mt-1">{subtitle}</div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
