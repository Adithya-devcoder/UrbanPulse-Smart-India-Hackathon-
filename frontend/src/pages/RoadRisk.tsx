import { useState } from 'react';
import Layout from '../components/layout/Layout';
import { mockRoads } from '../data/roads';
import type { Road } from '../types';
import RiskScore from '../components/common/RiskScore';
import { RoadTrendChart, RiskBarChart } from '../components/charts/Charts';
import { Brain, TrendingUp, TrendingDown, ChevronRight } from 'lucide-react';
import { clsx } from 'clsx';

const riskBarData = mockRoads.map((r) => ({
  label: r.name.split(' ')[0],
  value: r.riskScore,
  color: r.riskScore >= 85 ? '#D9534F' : r.riskScore >= 70 ? '#D47A45' : r.riskScore >= 55 ? '#C7B89D' : '#6F9E75',
}));

export default function RoadRisk() {
  const [selected, setSelected] = useState<Road | null>(mockRoads[0]);

  return (
    <Layout title="Road Risk Intelligence" subtitle="AI-powered risk scoring and road condition analysis">
      <div className="p-6 grid grid-cols-1 xl:grid-cols-[1fr_360px] gap-6">

        {/* Left: Road table */}
        <div className="space-y-4">
          {/* Chart */}
          <div className="bg-bg-card border border-border rounded-2xl p-4">
            <div className="text-text-primary font-semibold text-sm mb-3">Risk Score Comparison</div>
            <RiskBarChart data={riskBarData} />
          </div>

          {/* Road list */}
          <div className="bg-bg-card border border-border rounded-2xl overflow-hidden">
            <div className="px-4 py-3 border-b border-border">
              <div className="grid grid-cols-[1fr_80px_80px_80px_80px_80px_60px_36px] text-[10px] text-text-muted font-semibold uppercase tracking-wider gap-2">
                <span>Road</span>
                <span className="text-center">Risk</span>
                <span className="text-center">Accidents</span>
                <span className="text-center">Potholes</span>
                <span className="text-center">Waterlog</span>
                <span className="text-center">Traffic</span>
                <span className="text-center">Trend</span>
                <span />
              </div>
            </div>
            {mockRoads.map((road) => (
              <button
                key={road.id}
                onClick={() => setSelected(road)}
                className={clsx(
                  'w-full px-4 py-3 border-b border-border/50 last:border-0 transition-all hover:bg-bg-elevated text-left',
                  selected?.id === road.id && 'bg-bg-elevated ring-inset ring-1 ring-cyan-primary/20'
                )}
              >
                <div className="grid grid-cols-[1fr_80px_80px_80px_80px_80px_60px_36px] items-center gap-2">
                  <div>
                    <div className="text-text-primary text-xs font-medium">{road.name}</div>
                    <div className="text-text-muted text-[9px] mt-0.5">{road.length} km</div>
                  </div>
                  <div className="flex justify-center">
                    <RiskScore score={road.riskScore} size="sm" showLabel={false} />
                  </div>
                  <span className="text-center text-text-secondary text-xs">{road.accidentCount}</span>
                  <span className="text-center text-text-secondary text-xs">{road.potholeCount}</span>
                  <span className="text-center text-text-secondary text-xs">{road.waterloggingCount}</span>
                  <span className="text-center text-text-secondary text-xs">{road.trafficIncidents}</span>
                  <div className="flex items-center justify-center gap-0.5">
                    {road.trend > 0
                      ? <TrendingUp size={11} className="text-coral-critical" />
                      : <TrendingDown size={11} className="text-success" />
                    }
                    <span className={clsx('text-[10px] font-semibold', road.trend > 0 ? 'text-coral-critical' : 'text-success')}>
                      {road.trend > 0 ? '+' : ''}{road.trend}%
                    </span>
                  </div>
                  <ChevronRight size={14} className={clsx('transition-colors', selected?.id === road.id ? 'text-cyan-primary' : 'text-text-muted')} />
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Right: Detail panel */}
        {selected && (
          <div className="space-y-4">
            <div className="bg-bg-card border border-border rounded-2xl p-5">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-text-primary font-bold text-base">{selected.name}</h3>
                  <div className="text-text-muted text-[10px] mt-0.5">{selected.length} km total length</div>
                </div>
                <RiskScore score={selected.riskScore} size="md" />
              </div>

              {/* Stats grid */}
              <div className="grid grid-cols-2 gap-2 mb-4">
                {[
                  { label: 'Accidents', value: selected.accidentCount, color: 'text-coral-critical' },
                  { label: 'Potholes', value: selected.potholeCount, color: 'text-amber-warning' },
                  { label: 'Waterlogging', value: selected.waterloggingCount, color: 'text-cyan-primary' },
                  { label: 'Traffic Incidents', value: selected.trafficIncidents, color: 'text-amber-warning' },
                ].map((s) => (
                  <div key={s.label} className="bg-bg-elevated rounded-xl p-3">
                    <div className={`text-xl font-bold ${s.color}`}>{s.value}</div>
                    <div className="text-text-muted text-[10px]">{s.label}</div>
                  </div>
                ))}
              </div>

              <div className="flex items-center justify-between p-2.5 bg-bg-elevated rounded-xl mb-4">
                <span className="text-text-muted text-xs">Avg Response Time</span>
                <span className={clsx('text-sm font-bold', selected.avgResponseTime > 15 ? 'text-coral-critical' : selected.avgResponseTime > 10 ? 'text-amber-warning' : 'text-success')}>
                  {selected.avgResponseTime} min
                </span>
              </div>

              {/* Trend chart */}
              <div>
                <div className="text-text-muted text-[10px] font-semibold uppercase tracking-widest mb-2">7-Day Risk Trend</div>
                <RoadTrendChart data={selected.historicalData} />
              </div>
            </div>

            {/* AI Recommendation */}
            <div className="bg-bg-card border border-cyan-primary/20 rounded-2xl p-4">
              <div className="flex items-center gap-2 mb-3">
                <Brain size={14} className="text-cyan-primary" />
                <h3 className="text-text-primary font-semibold text-sm">AI Recommendation</h3>
                <span className="ml-auto text-[9px] bg-cyan-muted text-cyan-primary px-2 py-0.5 rounded font-semibold">AI-generated</span>
              </div>
              <p className="text-text-secondary text-xs leading-relaxed">{selected.aiRecommendation}</p>
              <button className="mt-3 w-full py-2 bg-cyan-muted border border-cyan-primary/20 text-cyan-primary text-xs font-semibold rounded-xl hover:bg-cyan-primary hover:text-bg-primary transition-all">
                Generate Full Report
              </button>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}
