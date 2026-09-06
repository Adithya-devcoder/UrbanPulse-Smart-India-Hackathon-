import { useState } from 'react';
import Layout from '../components/layout/Layout';
import { mockHeatmapZones } from '../data/heatmap';
import type { HeatmapZone } from '../types';
import { clsx } from 'clsx';
import { TrendingUp, TrendingDown } from 'lucide-react';

type TimeRange = 'today' | '7d' | '30d' | '3m';
type RiskType = 'all' | 'accidents' | 'potholes' | 'waterlogging' | 'traffic' | 'infrastructure';

const MAP_W = 700;
const MAP_H = 520;

const intensityColors = {
  low:      { fill: 'rgba(199,184,157,', stroke: '#C7B89D' },
  medium:   { fill: 'rgba(212,122,69,',  stroke: '#D47A45' },
  high:     { fill: 'rgba(217,83,79,',   stroke: '#D9534F' },
  critical: { fill: 'rgba(160,45,43,',   stroke: '#A02D2B' },
};

// Scale factor for intensity based on filters
const timeScales: Record<TimeRange, number> = { today: 1, '7d': 1.3, '30d': 1.6, '3m': 1.8 };
const typeMultipliers: Record<RiskType, Record<string, number>> = {
  all:            { hz: 1 },
  accidents:      { 'hz-2': 1.4, 'hz-1': 0.8, 'hz-3': 1.2 },
  potholes:       { 'hz-4': 1.5, 'hz-6': 1.4 },
  waterlogging:   { 'hz-1': 1.6, 'hz-4': 1.3 },
  traffic:        { 'hz-3': 1.5, 'hz-2': 1.2 },
  infrastructure: { 'hz-7': 1.4 },
};

function getZoneScale(zone: HeatmapZone, timeRange: TimeRange, riskType: RiskType): number {
  const base = timeScales[timeRange];
  const multipliers = typeMultipliers[riskType] || {};
  const mul = multipliers[zone.id] ?? (riskType === 'all' ? 1 : 0.5);
  return base * mul;
}

export default function RiskHeatmap() {
  const [timeRange, setTimeRange] = useState<TimeRange>('today');
  const [riskType, setRiskType] = useState<RiskType>('all');
  const [selectedZone, setSelectedZone] = useState<HeatmapZone | null>(null);

  const zones = mockHeatmapZones;

  return (
    <Layout title="Risk Heatmap" subtitle="Geographic visualization of urban road risk concentration">
      <div className="p-6 space-y-4">

        {/* Filter controls */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-1 bg-bg-card border border-border rounded-xl p-1">
            {(['today', '7d', '30d', '3m'] as TimeRange[]).map((t) => (
              <button
                key={t}
                onClick={() => setTimeRange(t)}
                className={clsx(
                  'px-3 py-1.5 rounded-lg text-xs font-medium transition-all',
                  timeRange === t ? 'bg-cyan-primary text-bg-primary' : 'text-text-muted hover:text-text-secondary'
                )}
              >
                {t === 'today' ? 'Today' : t === '7d' ? '7 Days' : t === '30d' ? '30 Days' : '3 Months'}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-1 bg-bg-card border border-border rounded-xl p-1 flex-wrap">
            {(['all', 'accidents', 'potholes', 'waterlogging', 'traffic', 'infrastructure'] as RiskType[]).map((t) => (
              <button
                key={t}
                onClick={() => setRiskType(t)}
                className={clsx(
                  'px-3 py-1.5 rounded-lg text-xs font-medium transition-all capitalize',
                  riskType === t ? 'bg-cyan-primary text-bg-primary' : 'text-text-muted hover:text-text-secondary'
                )}
              >
                {t === 'all' ? 'All' : t}
              </button>
            ))}
          </div>

          {selectedZone && (
            <button onClick={() => setSelectedZone(null)} className="px-3 py-1.5 text-xs text-text-muted hover:text-text-primary border border-border rounded-xl transition-all">
              Clear selection
            </button>
          )}
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-[1fr_300px] gap-4">
          {/* Heatmap */}
          <div className="bg-[#171717] border border-border rounded-2xl overflow-hidden relative">
            <svg viewBox={`0 0 ${MAP_W} ${MAP_H}`} className="w-full">
              <defs>
                <pattern id="heatGrid" width="40" height="40" patternUnits="userSpaceOnUse">
                  <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1E1E1E" strokeWidth="0.5" />
                </pattern>
              </defs>
              <rect width={MAP_W} height={MAP_H} fill="url(#heatGrid)" />

              {/* Road network */}
              <path d="M 140 190 L 240 260 L 340 330" fill="none" stroke="#2B2A27" strokeWidth="8" strokeLinecap="round" />
              <path d="M 500 100 L 510 250 L 520 400" fill="none" stroke="#2B2A27" strokeWidth="7" strokeLinecap="round" />
              <path d="M 90 370 L 160 420 L 230 470" fill="none" stroke="#2B2A27" strokeWidth="6" strokeLinecap="round" />
              <path d="M 340 200 L 460 215 L 580 225" fill="none" stroke="#2B2A27" strokeWidth="6" strokeLinecap="round" />
              <path d="M 280 330 L 400 355 L 490 370" fill="none" stroke="#2B2A27" strokeWidth="6" strokeLinecap="round" />
              <path d="M 400 270 L 470 295" fill="none" stroke="#2B2A27" strokeWidth="5" strokeLinecap="round" />
              {/* Secondaries */}
              <path d="M 190 270 L 290 340" fill="none" stroke="#222222" strokeWidth="3" />
              <path d="M 380 190 L 400 340" fill="none" stroke="#222222" strokeWidth="3" />
              <path d="M 240 260 L 400 280" fill="none" stroke="#222222" strokeWidth="3" />

              {/* Heat blobs */}
              {zones.map((zone) => {
                const scale = getZoneScale(zone, timeRange, riskType);
                const cx = zone.coordinates.x * MAP_W;
                const cy = zone.coordinates.y * MAP_H;
                const r = zone.radius * scale;
                const cfg = intensityColors[zone.intensity];
                const isSelected = selectedZone?.id === zone.id;
                return (
                  <g key={zone.id} onClick={() => setSelectedZone(zone)} className="cursor-pointer">
                    {/* Outer glow */}
                    <circle cx={cx} cy={cy} r={r * 1.4} fill={`${cfg.fill}0.04)`} />
                    <circle cx={cx} cy={cy} r={r * 1.1} fill={`${cfg.fill}0.10)`} />
                    <circle cx={cx} cy={cy} r={r}       fill={`${cfg.fill}0.22)`} />
                    <circle cx={cx} cy={cy} r={r * 0.6} fill={`${cfg.fill}0.40)`} />
                    <circle cx={cx} cy={cy} r={r * 0.3} fill={`${cfg.fill}0.65)`} />
                    {/* Center */}
                    <circle
                      cx={cx} cy={cy} r={6}
                      fill={isSelected ? '#fff' : cfg.stroke}
                      stroke={isSelected ? cfg.stroke : '#0D1520'}
                      strokeWidth={isSelected ? 2 : 1}
                      opacity={0.9}
                    />
                    {/* Label */}
                    <text x={cx} y={cy - r * 1.5 - 6} textAnchor="middle" fontSize="9" fill={cfg.stroke} fontFamily="Inter, sans-serif" fontWeight="600">
                      {zone.name}
                    </text>
                    <text x={cx} y={cy - r * 1.5 + 4} textAnchor="middle" fontSize="8" fill={cfg.stroke} fontFamily="Inter, sans-serif" opacity="0.7">
                      {zone.riskScore}/100
                    </text>
                  </g>
                );
              })}

              {/* Compass */}
              <g transform="translate(660, 35)">
                <circle cx="0" cy="0" r="16" fill="#222222" stroke="#383530" strokeWidth="1" />
                <text x="0" y="-7" textAnchor="middle" dominantBaseline="middle" fontSize="8" fill="#D47A45" fontWeight="700">N</text>
                <text x="0" y="7" textAnchor="middle" dominantBaseline="middle" fontSize="7" fill="#6B6760">S</text>
                <text x="-9" y="0" textAnchor="middle" dominantBaseline="middle" fontSize="7" fill="#6B6760">W</text>
                <text x="9" y="0" textAnchor="middle" dominantBaseline="middle" fontSize="7" fill="#6B6760">E</text>
              </g>
            </svg>

            {/* Heat legend */}
            <div className="absolute bottom-4 left-4 flex items-center gap-3 bg-bg-elevated/90 border border-border rounded-xl px-3 py-2">
              <span className="text-text-muted text-[10px]">Intensity:</span>
              {[
                { label: 'Low',      color: '#C7B89D' },
                { label: 'Medium',   color: '#D47A45' },
                { label: 'High',     color: '#D9534F' },
                { label: 'Critical', color: '#A02D2B' },
              ].map((l) => (
                <div key={l.label} className="flex items-center gap-1">
                  <span className="w-3 h-3 rounded-full" style={{ background: l.color, opacity: 0.7 }} />
                  <span className="text-text-muted text-[10px]">{l.label}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Sidebar: zone details */}
          <div className="space-y-3">
            {selectedZone ? (
              <div className="bg-bg-card border border-border rounded-2xl p-4 space-y-4">
                <div>
                  <h3 className="text-text-primary font-semibold text-sm">{selectedZone.name}</h3>
                  <div className="text-text-muted text-[10px] mt-0.5 capitalize">{selectedZone.intensity} risk zone</div>
                </div>

                {/* Risk score ring */}
                <div className="flex items-center gap-3">
                  <div className="relative">
                    <svg width={80} height={80} style={{ transform: 'rotate(-90deg)' }}>
                      <circle cx={40} cy={40} r={34} fill="none" stroke="#383530" strokeWidth={6} />
                      <circle cx={40} cy={40} r={34} fill="none"
                        stroke={selectedZone.riskScore >= 85 ? '#D9534F' : selectedZone.riskScore >= 70 ? '#D47A45' : '#C7B89D'}
                        strokeWidth={6}
                        strokeDasharray={`${(selectedZone.riskScore/100)*2*Math.PI*34} ${2*Math.PI*34}`}
                        strokeLinecap="round"
                      />
                    </svg>
                    <div className="absolute inset-0 flex flex-col items-center justify-center">
                      <span className="text-xl font-bold text-text-primary">{selectedZone.riskScore}</span>
                      <span className="text-[9px] text-text-muted">/100</span>
                    </div>
                  </div>
                  <div className="flex-1 space-y-1 text-xs">
                    <div className="flex justify-between"><span className="text-text-muted">Incidents</span><span className="text-text-primary font-semibold">{selectedZone.incidentCount}</span></div>
                    <div className="flex justify-between"><span className="text-text-muted">Potholes</span><span className="text-text-primary font-semibold">{selectedZone.potholeCount}</span></div>
                    <div className="flex justify-between"><span className="text-text-muted">Waterlogging</span><span className="text-text-primary font-semibold">{selectedZone.waterloggingCount}</span></div>
                    <div className="flex justify-between"><span className="text-text-muted">Avg Response</span><span className="text-text-primary font-semibold">{selectedZone.avgResponseTime} min</span></div>
                  </div>
                </div>

                <div className="flex items-center gap-2 p-2 bg-bg-elevated rounded-lg">
                  {selectedZone.trend > 0 ? <TrendingUp size={14} className="text-coral-critical" /> : <TrendingDown size={14} className="text-success" />}
                  <span className={clsx('text-xs font-semibold', selectedZone.trend > 0 ? 'text-coral-critical' : 'text-success')}>
                    {selectedZone.trend > 0 ? '+' : ''}{selectedZone.trend}% this week
                  </span>
                </div>

                <button
                  onClick={() => {}}
                  className="w-full py-2 bg-cyan-primary text-bg-primary text-xs font-semibold rounded-xl hover:bg-cyan-secondary transition-all"
                >
                  View Area Intelligence
                </button>
              </div>
            ) : (
              <div className="bg-bg-card border border-border rounded-2xl p-4 text-center text-text-muted text-xs">
                <div className="text-2xl mb-2">🔥</div>
                Click a hotspot to view zone details
              </div>
            )}

            {/* Zone list */}
            <div className="bg-bg-card border border-border rounded-2xl overflow-hidden">
              <div className="px-4 py-3 border-b border-border text-text-muted text-[10px] font-semibold uppercase tracking-widest">Risk Zones</div>
              {zones.sort((a,b) => b.riskScore - a.riskScore).map((z) => {
                const cfg = intensityColors[z.intensity];
                return (
                  <button
                    key={z.id}
                    onClick={() => setSelectedZone(z)}
                    className={clsx('w-full flex items-center gap-3 px-4 py-2.5 text-xs border-b border-border/50 last:border-b-0 hover:bg-bg-elevated text-left transition-all',
                      selectedZone?.id === z.id && 'bg-bg-elevated'
                    )}
                  >
                    <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: cfg.stroke }} />
                    <span className="text-text-secondary flex-1 truncate">{z.name}</span>
                    <span className="font-mono font-semibold" style={{ color: cfg.stroke }}>{z.riskScore}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
