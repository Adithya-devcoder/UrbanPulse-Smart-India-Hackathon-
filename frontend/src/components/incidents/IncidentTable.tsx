import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronUp, ChevronDown, Eye, ExternalLink } from 'lucide-react';
import { useApp } from '../../context/AppContext';
import SeverityBadge from '../common/SeverityBadge';
import StatusBadge from '../common/StatusBadge';
import { format } from 'date-fns';
import { clsx } from 'clsx';
import type { Incident, IncidentType, SeverityLevel, IncidentStatus } from '../../types';

interface FilterState {
  type: string;
  severity: string;
  status: string;
  search: string;
}

interface IncidentTableProps {
  incidents: Incident[];
}

const typeLabels: Record<IncidentType, string> = {
  accident: 'Accident',
  'hit-and-run': 'Hit & Run',
  pothole: 'Pothole',
  waterlogging: 'Waterlogging',
  traffic: 'Traffic',
  infrastructure: 'Infrastructure',
  'road-hazard': 'Road Hazard',
};

export default function IncidentTable({ incidents }: IncidentTableProps) {
  const navigate = useNavigate();
  const { setActiveIncidentId } = useApp();
  const [filters, setFilters] = useState<FilterState>({ type: '', severity: '', status: '', search: '' });
  const [sortKey, setSortKey] = useState<'id' | 'severity' | 'confidence' | 'time'>('time');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');

  function updateFilter(key: keyof FilterState, val: string) {
    setFilters((p) => ({ ...p, [key]: val }));
  }

  function toggleSort(key: typeof sortKey) {
    if (sortKey === key) setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    else { setSortKey(key); setSortDir('desc'); }
  }

  const severityOrder = { critical: 4, high: 3, medium: 2, low: 1 };

  const filtered = incidents
    .filter((i) => {
      if (filters.type && i.type !== filters.type) return false;
      if (filters.severity && i.severity !== filters.severity) return false;
      if (filters.status && i.status !== filters.status) return false;
      if (filters.search) {
        const q = filters.search.toLowerCase();
        return (
          i.id.toLowerCase().includes(q) ||
          i.location.toLowerCase().includes(q) ||
          i.title.toLowerCase().includes(q) ||
          (i.cameraId ?? '').toLowerCase().includes(q)
        );
      }
      return true;
    })
    .sort((a, b) => {
      let cmp = 0;
      if (sortKey === 'id') cmp = a.id.localeCompare(b.id);
      else if (sortKey === 'severity') cmp = severityOrder[a.severity] - severityOrder[b.severity];
      else if (sortKey === 'confidence') cmp = a.aiConfidence - b.aiConfidence;
      else cmp = a.detectedAt.getTime() - b.detectedAt.getTime();
      return sortDir === 'asc' ? cmp : -cmp;
    });

  function SortIcon({ col }: { col: typeof sortKey }) {
    return sortKey === col ? (
      sortDir === 'asc' ? <ChevronUp size={12} className="inline ml-0.5 text-cyan-primary" /> : <ChevronDown size={12} className="inline ml-0.5 text-cyan-primary" />
    ) : null;
  }

  function handleViewEvidence(id: string) {
    setActiveIncidentId(id);
    navigate('/evidence');
  }

  return (
    <div className="bg-bg-card border border-border rounded-2xl overflow-hidden">
      {/* Filter bar */}
      <div className="flex flex-wrap items-center gap-2 px-4 py-3 border-b border-border">
        <input
          value={filters.search}
          onChange={(e) => updateFilter('search', e.target.value)}
          placeholder="Search incidents…"
          className="flex-1 min-w-[160px] bg-bg-elevated border border-border rounded-lg px-3 py-1.5 text-text-primary text-xs placeholder:text-text-muted focus:outline-none focus:border-cyan-primary/50 transition-all"
        />
        {(['type', 'severity', 'status'] as const).map((key) => {
          const opts = {
            type: ['accident', 'hit-and-run', 'pothole', 'waterlogging', 'traffic', 'infrastructure', 'road-hazard'],
            severity: ['critical', 'high', 'medium', 'low'],
            status: ['new', 'under-review', 'verified', 'assigned', 'in-progress', 'resolved', 'rejected'],
          }[key];
          return (
            <select
              key={key}
              value={filters[key]}
              onChange={(e) => updateFilter(key, e.target.value)}
              className="bg-bg-elevated border border-border rounded-lg px-2.5 py-1.5 text-text-secondary text-xs focus:outline-none focus:border-cyan-primary/50 transition-all capitalize"
            >
              <option value="">All {key}s</option>
              {opts.map((o) => <option key={o} value={o}>{o}</option>)}
            </select>
          );
        })}
        <span className="text-text-muted text-[10px] ml-auto">{filtered.length} results</span>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-border text-text-muted text-[10px] uppercase tracking-wider">
              {[
                { label: 'Incident ID', col: 'id' as const },
                { label: 'Type', col: null },
                { label: 'Location', col: null },
                { label: 'Severity', col: 'severity' as const },
                { label: 'AI Confidence', col: 'confidence' as const },
                { label: 'Detected At', col: 'time' as const },
                { label: 'Status', col: null },
                { label: 'Action', col: null },
              ].map(({ label, col }) => (
                <th
                  key={label}
                  className={clsx('px-4 py-3 text-left font-semibold', col && 'cursor-pointer hover:text-text-secondary select-none')}
                  onClick={() => col && toggleSort(col)}
                >
                  {label}{col && <SortIcon col={col} />}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr><td colSpan={8} className="text-center py-12 text-text-muted">No incidents match the selected filters.</td></tr>
            ) : filtered.map((inc) => (
              <tr key={inc.id} className={clsx('border-b border-border/50 hover:bg-bg-elevated transition-all', inc.id === 'INC-2048' && 'bg-coral-muted/5')}>
                <td className="px-4 py-3">
                  <span className="font-mono text-cyan-primary font-medium">{inc.id}</span>
                </td>
                <td className="px-4 py-3 text-text-secondary">{typeLabels[inc.type]}</td>
                <td className="px-4 py-3 text-text-secondary max-w-[140px] truncate">{inc.location}</td>
                <td className="px-4 py-3"><SeverityBadge severity={inc.severity as SeverityLevel} /></td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <div className="w-16 h-1.5 bg-bg-elevated rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all"
                        style={{
                          width: `${inc.aiConfidence}%`,
                          background: inc.aiConfidence >= 90 ? '#55D6A4' : inc.aiConfidence >= 75 ? '#35D6E8' : '#F2B84B',
                        }}
                      />
                    </div>
                    <span className="text-text-primary font-mono">{inc.aiConfidence}%</span>
                  </div>
                </td>
                <td className="px-4 py-3 text-text-muted font-mono">{format(inc.detectedAt, 'hh:mm a')}</td>
                <td className="px-4 py-3"><StatusBadge status={inc.status as IncidentStatus} /></td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-1.5">
                    <button
                      onClick={() => handleViewEvidence(inc.id)}
                      className="flex items-center gap-1 px-2 py-1 rounded-lg bg-cyan-muted text-cyan-primary text-[10px] font-medium hover:bg-cyan-primary/20 transition-all"
                    >
                      <Eye size={11} /> View
                    </button>
                    <button className="p-1 rounded-lg text-text-muted hover:text-text-secondary hover:bg-bg-elevated transition-all" title="Open in new tab">
                      <ExternalLink size={12} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
