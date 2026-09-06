import { useState } from 'react';
import Layout from '../components/layout/Layout';
import { mockAnalytics } from '../data/analytics';
import { IncidentTrendChart, IncidentDistributionChart } from '../components/charts/Charts';
import { clsx } from 'clsx';

type Period = '7d' | '30d' | '90d';

export default function Reports() {
  const [period, setPeriod] = useState<Period>('7d');
  const data = mockAnalytics;

  return (
    <Layout title="Reports & Analytics" subtitle="Performance metrics, incident trends and AI analytics">
      <div className="p-6 space-y-5">

        {/* Period selector */}
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-1 bg-bg-card border border-border rounded-xl p-1">
            {(['7d', '30d', '90d'] as Period[]).map((p) => (
              <button key={p} onClick={() => setPeriod(p)}
                className={clsx('px-3 py-1.5 rounded-lg text-xs font-medium transition-all',
                  period === p ? 'bg-cyan-primary text-bg-primary' : 'text-text-muted hover:text-text-secondary'
                )}
              >
                {p === '7d' ? 'Last 7 Days' : p === '30d' ? 'Last 30 Days' : 'Last 90 Days'}
              </button>
            ))}
          </div>
          <button className="px-4 py-2 bg-bg-elevated border border-border text-text-secondary text-xs rounded-xl hover:border-cyan-primary/30 hover:text-cyan-primary transition-all">
            Export Report
          </button>
        </div>

        {/* Charts row */}
        <div className="grid grid-cols-1 xl:grid-cols-[2fr_1fr] gap-4">
          <div className="bg-bg-card border border-border rounded-2xl p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-text-primary font-semibold text-sm">Incident Trends</h3>
              <div className="flex gap-3 text-[10px] text-text-muted">
                {[{c:'#D9534F',l:'Accidents'},{c:'#C7B89D',l:'Potholes'},{c:'#D47A45',l:'Waterlogging'},{c:'#9E8B75',l:'Traffic'}].map(({c,l})=>(
                  <span key={l} className="flex items-center gap-1"><span className="w-2 h-2 rounded-full" style={{background:c}}/>{l}</span>
                ))}
              </div>
            </div>
            <IncidentTrendChart data={data.incidentTrends} />
          </div>

          <div className="bg-bg-card border border-border rounded-2xl p-5">
            <h3 className="text-text-primary font-semibold text-sm mb-3">Incident Distribution</h3>
            <IncidentDistributionChart data={data.distribution} />
            <div className="space-y-1.5 mt-2">
              {data.distribution.map((d) => (
                <div key={d.name} className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ background: d.color }} />
                  <span className="text-text-secondary text-xs flex-1">{d.name}</span>
                  <span className="text-text-primary text-xs font-semibold">{d.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Performance cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Response Performance */}
          <div className="bg-bg-card border border-border rounded-2xl p-5">
            <h3 className="text-text-primary font-semibold text-sm mb-4">Response Performance</h3>
            <div className="space-y-3">
              {[
                { label: 'Average Response Time',   value: `${data.responsePerformance.avgResponseTime} min`, bar: (data.responsePerformance.avgResponseTime / 30) * 100, color: '#C7B89D', good: false },
                { label: 'Resolution Rate',          value: `${data.responsePerformance.resolutionRate}%`,     bar: data.responsePerformance.resolutionRate,                color: '#6F9E75', good: true },
                { label: 'Critical Response Time',   value: `${data.responsePerformance.criticalResponseTime} min`, bar: (data.responsePerformance.criticalResponseTime / 30) * 100, color: '#D47A45', good: true },
              ].map((m) => (
                <div key={m.label}>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-text-secondary text-xs">{m.label}</span>
                    <span className="text-text-primary text-xs font-semibold">{m.value}</span>
                  </div>
                  <div className="h-2 bg-bg-elevated rounded-full overflow-hidden">
                    <div className="h-full rounded-full transition-all duration-700" style={{ width: `${m.bar}%`, background: m.color }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* AI Performance */}
          <div className="bg-bg-card border border-border rounded-2xl p-5">
            <h3 className="text-text-primary font-semibold text-sm mb-4">AI Performance</h3>
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: 'Detection Accuracy', value: `${data.aiPerformance.detectionAccuracy}%`, color: 'text-success' },
                { label: 'False Positive Rate', value: `${data.aiPerformance.falsePositiveRate}%`, color: 'text-amber-warning' },
                { label: 'Avg Confidence', value: `${data.aiPerformance.avgConfidence}%`, color: 'text-cyan-primary' },
                { label: 'Total Detections', value: data.aiPerformance.totalDetections.toLocaleString(), color: 'text-text-primary' },
              ].map((m) => (
                <div key={m.label} className="bg-bg-elevated rounded-xl p-3">
                  <div className={`text-xl font-bold ${m.color}`}>{m.value}</div>
                  <div className="text-text-muted text-[10px] mt-0.5">{m.label}</div>
                </div>
              ))}
            </div>
            <div className="mt-4 p-3 bg-cyan-muted border border-cyan-primary/20 rounded-xl text-[11px] text-cyan-primary/80">
              <span className="font-semibold">Model:</span> Simulated YOLO v8 + ANPR + Event Classification <br/>
              <span className="text-[10px] text-cyan-primary/60">Replace <code className="font-mono">src/services/api.ts</code> with real model API endpoints.</span>
            </div>
          </div>
        </div>

      </div>
    </Layout>
  );
}
