import { useNavigate } from 'react-router-dom';
import { AlertTriangle, TrendingUp, Circle, Droplets, Cpu, CheckCircle2 } from 'lucide-react';
import Layout from '../components/layout/Layout';
import KPICard from '../components/common/KPICard';
import CityMap from '../components/map/CityMap';
import MapLegend from '../components/map/MapLegend';
import LiveIncidentFeed from '../components/incidents/LiveIncidentFeed';
import RiskScore from '../components/common/RiskScore';
import { useApp } from '../context/AppContext';

const kpiSparkData = {
  incidents: [18, 20, 22, 19, 23, 24, 24],
  highRisk:  [13, 14, 15, 16, 16, 17, 18],
  potholes:  [100, 110, 118, 120, 128, 132, 137],
  waterlog:  [5, 6, 6, 7, 7, 8, 8],
  ai:        [2200, 2350, 2450, 2500, 2600, 2750, 2846],
  resolved:  [84, 85, 87, 88, 89, 90, 91],
};

const riskBreakdown = [
  { label: 'Accident Risk',        value: 68, color: '#D9534F' },
  { label: 'Road Condition',       value: 76, color: '#D47A45' },
  { label: 'Traffic Risk',         value: 71, color: '#9E8B75' },
  { label: 'Waterlogging Risk',    value: 63, color: '#C7B89D' },
  { label: 'Infrastructure Risk',  value: 74, color: '#D47A45' },
];

export default function Dashboard() {
  const navigate = useNavigate();
  const { incidents, setActiveIncidentId } = useApp();

  return (
    <Layout title="City Overview" subtitle="Real-time intelligence across urban roads and infrastructure">
      <div className="p-6 space-y-6">

        {/* KPI Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-6 gap-4">
          <KPICard
            icon={AlertTriangle}
            iconColor="text-coral-critical"
            iconBg="bg-coral-muted"
            title="Active Incidents"
            value="24"
            trend="+4 today"
            trendUp={false}
            description="Requiring attention"
            sparkData={kpiSparkData.incidents}
            sparkColor="#D9534F"
            onClick={() => navigate('/incidents')}
          />
          <KPICard
            icon={TrendingUp}
            iconColor="text-amber-warning"
            iconBg="bg-amber-muted"
            title="High-Risk Roads"
            value="18"
            trend="+3 this week"
            trendUp={false}
            description="Elevated risk score"
            sparkData={kpiSparkData.highRisk}
            sparkColor="#D47A45"
            onClick={() => navigate('/road-risk')}
          />
          <KPICard
            icon={Circle}
            iconColor="text-amber-warning"
            iconBg="bg-amber-muted"
            title="Potholes Detected"
            value="137"
            trend="12 new today"
            trendUp={false}
            description="Active pothole records"
            sparkData={kpiSparkData.potholes}
            sparkColor="#D47A45"
            onClick={() => navigate('/incidents')}
          />
          <KPICard
            icon={Droplets}
            iconColor="text-cyan-primary"
            iconBg="bg-cyan-muted"
            title="Waterlogging Zones"
            value="08"
            trend="3 critical"
            trendUp={false}
            description="Active waterlogging"
            sparkData={kpiSparkData.waterlog}
            sparkColor="#D47A45"
            onClick={() => navigate('/incidents')}
          />
          <KPICard
            icon={Cpu}
            iconColor="text-cyan-primary"
            iconBg="bg-cyan-muted"
            title="AI Detections"
            value="2,846"
            trend="+18.4%"
            trendUp={true}
            description="Total AI events today"
            sparkData={kpiSparkData.ai}
            sparkColor="#E08A5A"
            onClick={() => navigate('/reports')}
          />
          <KPICard
            icon={CheckCircle2}
            iconColor="text-success"
            iconBg="bg-success/10"
            title="Resolved Incidents"
            value="91%"
            trend="+6.2%"
            trendUp={true}
            description="Resolution rate"
            sparkData={kpiSparkData.resolved}
            sparkColor="#6F9E75"
            onClick={() => navigate('/actions')}
          />
        </div>

        {/* Map + Incident Feed */}
        <div className="grid grid-cols-1 xl:grid-cols-[1fr_300px] gap-4">
          {/* Map */}
          <div className="flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <h2 className="text-text-primary font-semibold text-sm">Live City Intelligence Map</h2>
              <div className="flex items-center gap-2">
                <MapLegend />
                <button
                  onClick={() => navigate('/map')}
                  className="px-3 py-1.5 text-xs bg-bg-elevated border border-border text-text-secondary rounded-lg hover:border-cyan-primary/30 hover:text-cyan-primary transition-all"
                >
                  Full Map →
                </button>
              </div>
            </div>
            <CityMap incidents={incidents} height="h-[440px]" selectedIncidentId="INC-2048" />
          </div>

          {/* Incident Feed */}
          <div className="bg-bg-card border border-border rounded-2xl p-4 flex flex-col" style={{ maxHeight: '500px' }}>
            <LiveIncidentFeed incidents={incidents} maxItems={6} />
          </div>
        </div>

        {/* Urban Risk Summary */}
        <div className="bg-bg-card border border-border rounded-2xl p-5">
          <h2 className="text-text-primary font-semibold text-sm mb-4">Urban Risk Score</h2>
          <div className="flex flex-wrap items-center gap-8">
            {/* Main ring */}
            <div className="flex flex-col items-center gap-2">
              <div className="relative">
                {/* Large risk ring */}
                <svg width={120} height={120} style={{ transform: 'rotate(-90deg)' }}>
                  <circle cx={60} cy={60} r={50} fill="none" stroke="#383530" strokeWidth={8} />
                  <circle
                    cx={60} cy={60} r={50}
                    fill="none"
                    stroke="#D47A45"
                    strokeWidth={8}
                    strokeDasharray={`${(72 / 100) * 2 * Math.PI * 50} ${2 * Math.PI * 50}`}
                    strokeLinecap="round"
                  />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-3xl font-semibold text-amber-warning">72</span>
                  <span className="text-text-muted text-[10px]">/ 100</span>
                </div>
              </div>
              <div className="text-center">
                <div className="text-amber-warning text-sm font-semibold">Elevated</div>
                <div className="text-text-muted text-[10px]">Urban Risk Status</div>
              </div>
            </div>

            {/* Risk breakdown */}
            <div className="flex-1 grid grid-cols-1 sm:grid-cols-2 gap-3">
              {riskBreakdown.map((r) => (
                <div key={r.label} className="flex items-center gap-3">
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-text-secondary text-xs">{r.label}</span>
                      <span className="text-text-primary text-xs font-semibold font-mono">{r.value}</span>
                    </div>
                    <div className="h-1.5 bg-bg-elevated rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all"
                        style={{ width: `${r.value}%`, background: r.color }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Quick risk scores */}
            <div className="flex gap-4">
              <div className="flex flex-col items-center gap-1">
                <RiskScore score={91} size="sm" showLabel={false} />
                <span className="text-text-muted text-[9px] text-center">Velachery</span>
              </div>
              <div className="flex flex-col items-center gap-1">
                <RiskScore score={82} size="sm" showLabel={false} />
                <span className="text-text-muted text-[9px] text-center">OMR</span>
              </div>
              <div className="flex flex-col items-center gap-1">
                <RiskScore score={78} size="sm" showLabel={false} />
                <span className="text-text-muted text-[9px] text-center">Anna Salai</span>
              </div>
            </div>
          </div>
        </div>

      </div>
    </Layout>
  );
}
