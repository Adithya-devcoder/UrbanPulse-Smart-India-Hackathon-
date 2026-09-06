import Layout from '../components/layout/Layout';
import IncidentTable from '../components/incidents/IncidentTable';
import { useApp } from '../context/AppContext';

export default function Incidents() {
  const { incidents } = useApp();
  const total = incidents.length;
  const critical = incidents.filter(i => i.severity === 'critical').length;
  const underReview = incidents.filter(i => i.status === 'under-review').length;
  const resolved = incidents.filter(i => i.status === 'resolved').length;

  return (
    <Layout title="Incidents & Alerts" subtitle="Monitor, verify and manage AI-detected urban events">
      <div className="p-6 space-y-5">

        {/* Summary stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { label: 'Total',       value: total,       color: 'text-text-primary',   bg: 'bg-bg-elevated' },
            { label: 'Critical',    value: critical,    color: 'text-coral-critical',  bg: 'bg-coral-muted' },
            { label: 'Under Review',value: underReview, color: 'text-amber-warning',   bg: 'bg-amber-muted' },
            { label: 'Resolved',    value: resolved,    color: 'text-success',         bg: 'bg-success/10' },
          ].map((s) => (
            <div key={s.label} className={`${s.bg} border border-border rounded-xl px-4 py-3 flex items-center gap-3`}>
              <span className={`text-2xl font-bold ${s.color}`}>{s.value}</span>
              <span className="text-text-muted text-xs">{s.label}</span>
            </div>
          ))}
        </div>

        {/* Table */}
        <IncidentTable incidents={incidents} />
      </div>
    </Layout>
  );
}
