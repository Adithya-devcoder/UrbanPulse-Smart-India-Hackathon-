import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from '../components/layout/Layout';
import { mockActions } from '../data/analytics';
import type { Action } from '../types';
import StatusBadge from '../components/common/StatusBadge';
import SeverityBadge from '../components/common/SeverityBadge';
import { useApp } from '../context/AppContext';
import { formatDistanceToNow } from 'date-fns';
import { clsx } from 'clsx';
import { MapPin, Clock, User, CheckCircle, ChevronRight } from 'lucide-react';

const priorityConfig = {
  immediate: { label: 'Immediate', classes: 'bg-coral-muted text-coral-critical border-coral-critical/30' },
  high:      { label: 'High',      classes: 'bg-amber-muted text-amber-warning border-amber-warning/30' },
  medium:    { label: 'Medium',    classes: 'bg-yellow-900/30 text-yellow-400 border-yellow-500/30' },
  low:       { label: 'Low',       classes: 'bg-success/10 text-success border-success/30' },
};

export default function ActionCenter() {
  const navigate = useNavigate();
  const { setActiveIncidentId, addToast } = useApp();
  const [actions, setActions] = useState<Action[]>(mockActions);
  const [filter, setFilter] = useState<string>('all');

  const sections = [
    { label: 'Critical Actions',    priority: 'immediate', color: 'text-coral-critical',  border: 'border-coral-critical/20' },
    { label: 'High Priority',       priority: 'high',      color: 'text-amber-warning',   border: 'border-amber-warning/20' },
    { label: 'Maintenance Actions', priority: 'medium',    color: 'text-text-secondary',  border: 'border-border' },
    { label: 'Resolved',            priority: null,        color: 'text-success',          border: 'border-success/20' },
  ];

  function resolveAction(id: string) {
    setActions(prev => prev.map(a => a.id === id ? { ...a, status: 'resolved' } : a));
    addToast('Action resolved successfully', 'success');
  }

  function filteredActions(priority: string | null) {
    if (priority === null) return actions.filter(a => a.status === 'resolved');
    return actions.filter(a => a.priority === priority && a.status !== 'resolved');
  }

  return (
    <Layout title="Action Center" subtitle="Coordinate urban response and track incident management">
      <div className="p-6 space-y-4">

        {/* Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { label: 'Total Actions',    value: actions.length,                                     color: 'text-text-primary' },
            { label: 'Critical',         value: actions.filter(a=>a.priority==='immediate').length, color: 'text-coral-critical' },
            { label: 'In Progress',      value: actions.filter(a=>a.status==='in-progress').length, color: 'text-amber-warning' },
            { label: 'Resolved Today',   value: actions.filter(a=>a.status==='resolved').length,    color: 'text-success' },
          ].map(s => (
            <div key={s.label} className="bg-bg-card border border-border rounded-xl px-4 py-3 flex items-center gap-3">
              <span className={`text-2xl font-bold ${s.color}`}>{s.value}</span>
              <span className="text-text-muted text-xs">{s.label}</span>
            </div>
          ))}
        </div>

        {/* Action sections */}
        <div className="space-y-4">
          {sections.map((section) => {
            const sectionActions = filteredActions(section.priority);
            if (sectionActions.length === 0) return null;
            return (
              <div key={section.label}>
                <div className={clsx('text-xs font-semibold mb-2', section.color)}>{section.label}</div>
                <div className="space-y-2">
                  {sectionActions.map((action) => (
                    <div
                      key={action.id}
                      className={clsx('bg-bg-card border rounded-2xl p-4 transition-all hover:border-opacity-60', section.border)}
                    >
                      <div className="flex flex-wrap items-start gap-4">
                        {/* Left info */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1 flex-wrap">
                            <span className="font-mono text-cyan-primary text-xs">{action.incidentId}</span>
                            <SeverityBadge severity={action.severity} />
                            <span className={clsx('text-[10px] px-2 py-0.5 rounded-md border font-medium', priorityConfig[action.priority].classes)}>
                              {priorityConfig[action.priority].label}
                            </span>
                            <StatusBadge status={action.status as any} />
                          </div>
                          <h4 className="text-text-primary text-sm font-semibold mb-2">{action.title}</h4>
                          <div className="flex flex-wrap items-center gap-3 text-[11px] text-text-muted">
                            <span className="flex items-center gap-1"><MapPin size={10} />{action.location}</span>
                            <span className="flex items-center gap-1"><User size={10} />{action.assignedTo}</span>
                            {action.eta && <span className="flex items-center gap-1 text-success"><Clock size={10} />ETA: {action.eta}</span>}
                            <span className="flex items-center gap-1"><Clock size={10} />{formatDistanceToNow(action.createdAt, { addSuffix: true })}</span>
                          </div>
                          {action.notes && (
                            <p className="text-text-muted text-[11px] mt-2 p-2 bg-bg-elevated rounded-lg leading-relaxed">{action.notes}</p>
                          )}
                        </div>

                        {/* Actions */}
                        <div className="flex items-center gap-2 flex-shrink-0">
                          {action.status !== 'resolved' && (
                            <button
                              onClick={() => resolveAction(action.id)}
                              className="flex items-center gap-1.5 px-3 py-1.5 bg-success/10 border border-success/30 text-success text-[11px] font-semibold rounded-xl hover:bg-success hover:text-bg-primary transition-all"
                            >
                              <CheckCircle size={12} /> Resolve
                            </button>
                          )}
                          <button
                            onClick={() => { setActiveIncidentId(action.incidentId); navigate('/evidence'); }}
                            className="flex items-center gap-1.5 px-3 py-1.5 bg-bg-elevated border border-border text-text-muted text-[11px] font-semibold rounded-xl hover:border-cyan-primary/30 hover:text-cyan-primary transition-all"
                          >
                            <ChevronRight size={12} /> Evidence
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </Layout>
  );
}
