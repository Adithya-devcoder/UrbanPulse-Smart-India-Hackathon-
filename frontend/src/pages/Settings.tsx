import Layout from '../components/layout/Layout';
import { Settings as SettingsIcon, Info } from 'lucide-react';

export default function Settings() {
  return (
    <Layout title="Settings" subtitle="System configuration and preferences">
      <div className="p-6">
        <div className="max-w-2xl space-y-4">
          <div className="bg-bg-card border border-border rounded-2xl p-6 space-y-4">
            <div className="flex items-center gap-2">
              <SettingsIcon size={16} className="text-cyan-primary" />
              <h3 className="text-text-primary font-semibold text-sm">System Settings</h3>
            </div>
            <div className="space-y-3 text-xs text-text-secondary">
              {[
                { label: 'AI Model', value: 'YOLO v8 (Simulated)' },
                { label: 'GPS Provider', value: 'Simulated GPS Engine' },
                { label: 'CCTV Integration', value: 'Simulated Camera Feed' },
                { label: 'Notification Mode', value: 'Simulated Real-Time' },
                { label: 'Map Provider', value: 'SVG Simulation (No API)' },
                { label: 'Alert Threshold', value: 'Confidence ≥ 80%' },
              ].map(({ label, value }) => (
                <div key={label} className="flex items-center justify-between py-2 border-b border-border/50 last:border-0">
                  <span className="text-text-muted">{label}</span>
                  <span className="text-text-primary font-medium">{value}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="bg-cyan-muted border border-cyan-primary/20 rounded-2xl p-4 flex gap-3">
            <Info size={16} className="text-cyan-primary flex-shrink-0 mt-0.5" />
            <div className="text-xs text-cyan-primary/80 leading-relaxed">
              <div className="font-semibold mb-1">Prototype Mode Active</div>
              This is a frontend prototype. All data is simulated. To integrate real APIs, replace the service layer in <code className="font-mono text-[10px]">src/services/api.ts</code> and update the mock data files in <code className="font-mono text-[10px]">src/data/</code>.
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
