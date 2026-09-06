import { clsx } from 'clsx';
import type { LucideIcon } from 'lucide-react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface KPICardProps {
  icon: LucideIcon;
  iconColor?: string;
  iconBg?: string;
  title: string;
  value: string | number;
  trend?: string;
  trendUp?: boolean | null; // null = neutral
  description: string;
  sparkData?: number[];
  sparkColor?: string;
  onClick?: () => void;
}

function Sparkline({ data, color }: { data: number[]; color: string }) {
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  const w = 80;
  const h = 30;
  const points = data
    .map((v, i) => {
      const x = (i / (data.length - 1)) * w;
      const y = h - ((v - min) / range) * h;
      return `${x},${y}`;
    })
    .join(' ');

  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} className="opacity-60">
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export default function KPICard({
  icon: Icon,
  iconColor = 'text-cyan-primary',
  iconBg = 'bg-cyan-muted',
  title,
  value,
  trend,
  trendUp,
  description,
  sparkData,
  sparkColor = '#35D6E8',
  onClick,
}: KPICardProps) {
  return (
    <button
      onClick={onClick}
      className={clsx(
        'bg-bg-card border border-border rounded-2xl p-5 text-left w-full transition-all duration-200 hover:border-cyan-primary/30 hover:shadow-cyan-glow group',
        onClick && 'cursor-pointer'
      )}
    >
      <div className="flex items-start justify-between mb-3">
        <div className={clsx('w-9 h-9 rounded-xl flex items-center justify-center', iconBg)}>
          <Icon size={18} className={iconColor} />
        </div>
        {sparkData && <Sparkline data={sparkData} color={sparkColor} />}
      </div>

      <div className="mb-1">
        <div className="text-3xl font-semibold text-text-primary tracking-tight leading-none">
          {value}
        </div>
      </div>

      <div className="text-text-secondary text-xs font-medium mb-1">{title}</div>

      <div className="flex items-center gap-1.5 mt-2">
        {trend && (
          <span
            className={clsx(
              'flex items-center gap-0.5 text-[10px] font-medium',
              trendUp === true ? 'text-success' : trendUp === false ? 'text-coral-critical' : 'text-text-muted'
            )}
          >
            {trendUp === true && <TrendingUp size={10} />}
            {trendUp === false && <TrendingDown size={10} />}
            {trendUp === null && <Minus size={10} />}
            {trend}
          </span>
        )}
        <span className="text-text-muted text-[10px]">{description}</span>
      </div>
    </button>
  );
}
