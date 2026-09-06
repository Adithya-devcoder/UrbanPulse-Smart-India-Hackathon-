import { useApp } from '../../context/AppContext';

const layerConfig = [
  { key: 'incidents',    label: 'Incidents',      dot: 'bg-coral-critical' },
  { key: 'potholes',     label: 'Potholes',       dot: 'bg-amber-warning' },
  { key: 'waterlogging', label: 'Waterlogging',   dot: 'bg-cyan-primary' },
  { key: 'traffic',      label: 'Traffic',        dot: 'bg-amber-warning/60' },
  { key: 'roadRisk',     label: 'Road Risk',      dot: 'bg-coral-critical/70' },
  { key: 'cameras',      label: 'CCTV Cameras',   dot: 'bg-success' },
  { key: 'closures',     label: 'Road Closures',  dot: 'bg-text-muted' },
];

export default function MapLegend({ showLayers = false }: { showLayers?: boolean }) {
  const { mapLayers, toggleLayer } = useApp();

  return (
    <div className="bg-bg-elevated border border-border rounded-xl p-3 space-y-2">
      {showLayers && (
        <div className="text-text-muted text-[10px] font-semibold uppercase tracking-widest mb-2">Layers</div>
      )}
      <div className="space-y-1.5">
        {layerConfig.map((l) => (
          <label key={l.key} className="flex items-center gap-2 cursor-pointer group">
            {showLayers ? (
              <input
                type="checkbox"
                checked={mapLayers[l.key] ?? true}
                onChange={() => toggleLayer(l.key)}
                className="w-3 h-3 rounded"
                style={{ accentColor: '#D47A45' }}
              />
            ) : (
              <span className={`w-2 h-2 rounded-full flex-shrink-0 ${l.dot}`} />
            )}
            <span className="text-text-secondary text-[10px] group-hover:text-text-primary transition-colors">
              {l.label}
            </span>
          </label>
        ))}
      </div>
      {!showLayers && (
        <div className="mt-2 pt-2 border-t border-border space-y-1.5">
          <div className="text-text-muted text-[10px] font-semibold uppercase tracking-widest">Roads</div>
          <div className="flex items-center gap-2">
            <span className="w-6 h-1 rounded" style={{ background: 'linear-gradient(to right, #6F9E75, #D47A45, #D9534F)' }} />
            <span className="text-text-muted text-[10px]">Low → High Risk</span>
          </div>
        </div>
      )}
    </div>
  );
}
