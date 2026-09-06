import { clsx } from 'clsx';

interface RiskScoreProps {
  score: number;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

function getRiskColor(score: number) {
  if (score >= 85) return { ring: '#D9534F', bg: 'bg-coral-muted', text: 'text-coral-critical', label: 'Critical' };
  if (score >= 70) return { ring: '#D47A45', bg: 'bg-cyan-muted',  text: 'text-cyan-primary',   label: 'High' };
  if (score >= 55) return { ring: '#C7B89D', bg: 'bg-amber-muted', text: 'text-amber-warning',   label: 'Elevated' };
  if (score >= 40) return { ring: '#9E9A8E', bg: 'bg-bg-elevated', text: 'text-text-secondary',  label: 'Moderate' };
  return           { ring: '#6F9E75', bg: 'bg-success/10',         text: 'text-success',          label: 'Low' };
}

export default function RiskScore({ score, size = 'md', showLabel = true }: RiskScoreProps) {
  const { ring, text, label } = getRiskColor(score);
  const radius = size === 'lg' ? 40 : size === 'md' ? 28 : 18;
  const stroke = size === 'lg' ? 4 : 3;
  const circumference = 2 * Math.PI * radius;
  const dash = (score / 100) * circumference;
  const svgSize = (radius + stroke + 2) * 2;

  return (
    <div className="flex items-center gap-2">
      <div className="relative inline-flex items-center justify-center">
        <svg width={svgSize} height={svgSize} style={{ transform: 'rotate(-90deg)' }}>
          <circle
            cx={svgSize / 2}
            cy={svgSize / 2}
            r={radius}
            fill="none"
            stroke="#383530"
            strokeWidth={stroke}
          />
          <circle
            cx={svgSize / 2}
            cy={svgSize / 2}
            r={radius}
            fill="none"
            stroke={ring}
            strokeWidth={stroke}
            strokeDasharray={`${dash} ${circumference}`}
            strokeLinecap="round"
            style={{ transition: 'stroke-dasharray 0.6s ease' }}
          />
        </svg>
        <span className={clsx('absolute font-semibold', text,
          size === 'lg' ? 'text-xl' : size === 'md' ? 'text-sm' : 'text-[10px]'
        )}>
          {score}
        </span>
      </div>
      {showLabel && (
        <span className={clsx('text-xs font-medium', text)}>{label}</span>
      )}
    </div>
  );
}
