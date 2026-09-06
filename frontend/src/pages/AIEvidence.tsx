import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from '../components/layout/Layout';
import EvidenceViewer from '../components/evidence/EvidenceViewer';
import EvidenceTimeline from '../components/evidence/EvidenceTimeline';
import EvidenceConfidence from '../components/evidence/EvidenceConfidence';
import EvidenceChain from '../components/evidence/EvidenceChain';
import VehicleCard from '../components/evidence/VehicleCard';
import SeverityBadge from '../components/common/SeverityBadge';
import StatusBadge from '../components/common/StatusBadge';
import { useApp } from '../context/AppContext';
import { getIncidentById } from '../data/incidents';
import { format } from 'date-fns';
import { MapPin, CheckCircle, XCircle, Clock, Brain } from 'lucide-react';
import { clsx } from 'clsx';
import type { TimelineEvent } from '../types';
import { updateIncidentStatus } from '../services/api';

const confidenceBreakdown = [
  { label: 'Accident Detection',        value: 96, color: '#6F9E75' },
  { label: 'Vehicle Tracking',          value: 93, color: '#D47A45' },
  { label: 'Number Plate Recognition',  value: 91, color: '#D47A45' },
  { label: 'Hit-and-Run Classification',value: 87, color: '#C7B89D' },
];

const vehicleA = {
  vehicleRef: 'A' as const,
  type: 'Sedan',
  color: 'White',
  numberPlate: 'TN XX XX XXXX',
  plateConfidence: 91,
  direction: 'North-East',
  lane: 'Lane 2',
  trackingId: 'VEH-0192',
};
const vehicleB = {
  vehicleRef: 'B' as const,
  type: 'Hatchback',
  color: 'Blue',
  direction: 'Stationary',
  lane: 'Lane 2',
  trackingId: 'VEH-0193',
};

export default function AIEvidence() {
  const navigate = useNavigate();
  const { activeIncidentId, addToast } = useApp();
  const incidentId = activeIncidentId || 'INC-2048';
  const incident = getIncidentById(incidentId);

  const [activeFrame, setActiveFrame] = useState(0);
  const [activeEventId, setActiveEventId] = useState<string | null>(incident?.timelineEvents[0]?.id ?? null);
  const [status, setStatus] = useState(incident?.status || 'under-review');
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  if (!incident) {
    return (
      <Layout title="AI Evidence" subtitle="No incident selected">
        <div className="p-6">
          <div className="bg-bg-card border border-border rounded-2xl p-12 text-center space-y-3">
            <Brain size={36} className="mx-auto text-text-muted" />
            <div className="text-text-primary font-semibold">No Incident Selected</div>
            <div className="text-text-muted text-sm">Navigate from the incidents table or map to view evidence.</div>
            <button onClick={() => navigate('/incidents')} className="px-4 py-2 bg-cyan-primary text-bg-primary text-sm font-semibold rounded-xl hover:bg-cyan-secondary transition-all">
              Browse Incidents
            </button>
          </div>
        </div>
      </Layout>
    );
  }

  function handleTimelineEvent(event: TimelineEvent) {
    setActiveEventId(event.id);
    setActiveFrame(event.frameIndex);
  }

  async function handleAction(action: string, newStatus: string) {
    setActionLoading(action);
    await updateIncidentStatus(incident!.id, newStatus);
    setStatus(newStatus as typeof status);
    addToast(`Incident ${incident!.id} ${action.toLowerCase()}`, action === 'Confirmed' ? 'success' : action === 'Rejected' ? 'warning' : 'info');
    setActionLoading(null);
  }

  const isHitAndRun = incident.type === 'hit-and-run';

  return (
    <Layout title="AI Evidence Panel" subtitle={`Detailed AI investigation — ${incident.id}`}>
      <div className="p-5 space-y-4">

        {/* Incident Header */}
        <div className="bg-bg-card border border-coral-critical/30 rounded-2xl p-5">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-2xl bg-coral-muted flex items-center justify-center text-2xl flex-shrink-0">
                🔴
              </div>
              <div>
                <div className="text-[10px] text-text-muted uppercase tracking-widest mb-1">AI Detection</div>
                <h2 className="text-text-primary font-bold text-lg leading-tight">{incident.title.toUpperCase()}</h2>
                <div className="flex items-center gap-3 mt-2 flex-wrap">
                  <span className="font-mono text-cyan-primary text-sm">{incident.id}</span>
                  <div className="flex items-center gap-1 text-text-muted text-xs">
                    <MapPin size={11} />
                    {incident.location}
                  </div>
                  <span className="text-text-muted text-xs">{format(incident.detectedAt, 'hh:mm:ss a')}</span>
                </div>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <div className="text-center">
                <div className="text-xl font-bold text-amber-warning">{incident.aiConfidence}%</div>
                <div className="text-text-muted text-[9px]">AI Confidence</div>
              </div>
              <SeverityBadge severity={incident.severity} size="md" />
              <StatusBadge status={status as any} size="md" />
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex flex-wrap items-center gap-2 mt-4 pt-4 border-t border-border">
            <button
              onClick={() => handleAction('Confirmed', 'verified')}
              disabled={!!actionLoading}
              className="flex items-center gap-1.5 px-4 py-2 bg-success text-bg-primary text-xs font-semibold rounded-xl hover:bg-success/90 transition-all disabled:opacity-60"
            >
              <CheckCircle size={13} /> {actionLoading === 'Confirmed' ? 'Processing…' : 'Confirm Incident'}
            </button>
            <button
              onClick={() => handleAction('Rejected', 'rejected')}
              disabled={!!actionLoading}
              className="flex items-center gap-1.5 px-4 py-2 bg-bg-elevated border border-coral-critical/30 text-coral-critical text-xs font-semibold rounded-xl hover:bg-coral-muted transition-all disabled:opacity-60"
            >
              <XCircle size={13} /> Reject Detection
            </button>
            <button
              onClick={() => handleAction('Marked for Review', 'under-review')}
              disabled={!!actionLoading}
              className="flex items-center gap-1.5 px-4 py-2 bg-bg-elevated border border-amber-warning/30 text-amber-warning text-xs font-semibold rounded-xl hover:bg-amber-muted transition-all disabled:opacity-60"
            >
              <Clock size={13} /> Mark for Review
            </button>
            <button
              onClick={() => navigate('/map')}
              className="flex items-center gap-1.5 px-4 py-2 bg-bg-elevated border border-border text-text-secondary text-xs font-semibold rounded-xl hover:border-cyan-primary/30 hover:text-cyan-primary transition-all"
            >
              <MapPin size={13} /> View on Map
            </button>
          </div>
        </div>

        {/* Main grid */}
        <div className="grid grid-cols-1 xl:grid-cols-[1fr_380px] gap-4">
          {/* Left: Evidence Viewer + AI Assessment */}
          <div className="space-y-4">
            <EvidenceViewer incident={incident} activeFrame={activeFrame} onFrameChange={setActiveFrame} />

            {/* AI Event Reconstruction */}
            <div className="bg-bg-card border border-border rounded-2xl p-4">
              <div className="flex items-center gap-2 mb-3">
                <Brain size={15} className="text-cyan-primary" />
                <h3 className="text-text-primary font-semibold text-sm">AI Event Reconstruction</h3>
                <span className="ml-auto text-[9px] bg-cyan-muted text-cyan-primary px-2 py-0.5 rounded font-semibold">AI-generated assessment</span>
              </div>
              <div className="bg-bg-elevated rounded-xl p-3 border border-border">
                <p className="text-text-secondary text-xs leading-relaxed">{incident.aiAssessment}</p>
              </div>
              {isHitAndRun && (
                <div className="mt-3 p-3 bg-amber-muted border border-amber-warning/30 rounded-xl">
                  <div className="text-amber-warning text-[10px] font-semibold mb-1">⚠ Legal Disclaimer</div>
                  <p className="text-text-muted text-[10px]">This is an AI-generated assessment and does not constitute legal evidence. Human verification and official investigation are required before any enforcement action.</p>
                </div>
              )}
            </div>

            {/* Waterlogged pothole scenario */}
            {incident.type === 'waterlogging' && (
              <div className="bg-bg-card border border-cyan-primary/20 rounded-2xl p-4">
                <h3 className="text-text-primary font-semibold text-sm mb-3">🔍 Waterlogged Pothole Analysis</h3>
                <div className="flex items-center gap-2 mb-3 flex-wrap text-xs">
                  {['Waterlogging Detected', 'Historical Pothole Record', 'Road-Surface Anomaly', 'Depth Visual Cues'].map((s, i) => (
                    <div key={s} className="flex items-center gap-1">
                      <span className="text-[9px] px-2 py-0.5 bg-cyan-muted text-cyan-primary rounded font-medium">{s}</span>
                      {i < 3 && <span className="text-text-muted">+</span>}
                    </div>
                  ))}
                  <span className="text-text-muted">=</span>
                  <span className="text-[9px] px-2 py-0.5 bg-amber-muted text-amber-warning rounded font-semibold">Possible Waterlogged Pothole</span>
                </div>
                <div className="bg-bg-elevated rounded-xl p-3 border border-border text-xs text-text-secondary leading-relaxed">
                  "Historical pothole detected at this coordinate. Current camera frame shows water accumulation and surface depression indicators. AI flags this as a probable waterlogged pothole."
                </div>
                <div className="mt-3 flex items-center gap-3">
                  <span className="text-text-muted text-xs">Waterlogged Pothole Probability:</span>
                  <div className="flex-1 h-2 bg-bg-elevated rounded-full overflow-hidden">
                    <div className="h-full bg-amber-warning rounded-full" style={{ width: '84%' }} />
                  </div>
                  <span className="text-amber-warning text-sm font-bold">84%</span>
                </div>
              </div>
            )}

            {/* Vehicles */}
            {isHitAndRun && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <VehicleCard vehicle={vehicleA} />
                <VehicleCard vehicle={vehicleB} />
              </div>
            )}
          </div>

          {/* Right: Timeline + Confidence + Chain */}
          <div className="space-y-4">
            {incident.timelineEvents.length > 0 ? (
              <EvidenceTimeline
                events={incident.timelineEvents}
                activeEventId={activeEventId}
                onSelectEvent={handleTimelineEvent}
              />
            ) : (
              <div className="bg-bg-card border border-border rounded-2xl p-4 text-center text-text-muted text-xs">
                No timeline data available for this incident type.
              </div>
            )}
            <EvidenceConfidence items={confidenceBreakdown} overall={91} />
            <EvidenceChain />
          </div>
        </div>
      </div>
    </Layout>
  );
}
