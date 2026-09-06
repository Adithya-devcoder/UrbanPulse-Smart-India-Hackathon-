import { useState } from 'react';
import Layout from '../components/layout/Layout';
import CityMap from '../components/map/CityMap';
import MapLegend from '../components/map/MapLegend';
import { useApp } from '../context/AppContext';
import type { Camera } from '../types';
import { Layers } from 'lucide-react';

export default function LiveMap() {
  const { incidents } = useApp();
  const [selectedCamera, setSelectedCamera] = useState<Camera | null>(null);
  const [showLayerPanel, setShowLayerPanel] = useState(true);

  return (
    <Layout title="Live City Map" subtitle="Real-time geographic monitoring of urban road conditions">
      <div className="flex flex-col h-full" style={{ height: 'calc(100vh - 73px)' }}>
        {/* Toolbar */}
        <div className="flex items-center gap-3 px-4 py-2 border-b border-border bg-bg-secondary flex-shrink-0">
          <button
            onClick={() => setShowLayerPanel(p => !p)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-bg-elevated border border-border text-text-secondary text-xs hover:text-cyan-primary hover:border-cyan-primary/30 transition-all"
          >
            <Layers size={14} /> Layers
          </button>
          <div className="flex items-center gap-1.5 text-xs text-text-muted">
            <span className="w-1.5 h-1.5 rounded-full bg-coral-critical animate-pulse" />
            Live monitoring active
          </div>
          <div className="ml-auto flex items-center gap-2 text-[11px] text-text-muted">
            <span>8 cameras online</span>
            <span>·</span>
            <span>24 active incidents</span>
            <span>·</span>
            <span>GPS: Simulated</span>
          </div>
        </div>

        {/* Main area */}
        <div className="flex flex-1 min-h-0 gap-0">
          {/* Map */}
          <div className="flex-1 p-4">
            <CityMap
              incidents={incidents}
              height="h-full"
              showControls
              onSelectCamera={setSelectedCamera}
            />
          </div>

          {/* Right panel */}
          {showLayerPanel && (
            <div className="w-56 flex-shrink-0 p-4 pl-0 flex flex-col gap-3">
              <MapLegend showLayers />

              {/* Selected camera info */}
              {selectedCamera ? (
                <div className="bg-bg-card border border-border rounded-xl p-3 text-xs space-y-2">
                  <div className="text-text-primary font-semibold flex items-center justify-between">
                    {selectedCamera.id}
                    <span className={`text-[9px] font-semibold px-1.5 py-0.5 rounded ${
                      selectedCamera.status === 'online' ? 'bg-success/10 text-success' :
                      selectedCamera.status === 'degraded' ? 'bg-amber-muted text-amber-warning' :
                      'bg-coral-muted text-coral-critical'
                    }`}>● {selectedCamera.status}</span>
                  </div>
                  <div className="space-y-1.5 text-[10px]">
                    <div className="flex justify-between"><span className="text-text-muted">Location</span><span className="text-text-secondary text-right max-w-[100px]">{selectedCamera.location}</span></div>
                    <div className="flex justify-between"><span className="text-text-muted">Last Frame</span><span className="text-cyan-primary font-mono">{selectedCamera.lastFrame}</span></div>
                    <div className="flex justify-between"><span className="text-text-muted">Lat</span><span className="text-text-primary font-mono">{selectedCamera.coordinates.lat.toFixed(4)}° N</span></div>
                    <div className="flex justify-between"><span className="text-text-muted">Lng</span><span className="text-text-primary font-mono">{selectedCamera.coordinates.lng.toFixed(4)}° E</span></div>
                  </div>
                </div>
              ) : (
                <div className="bg-bg-card border border-border rounded-xl p-3 text-[10px] text-text-muted text-center">
                  Click a camera marker to view details
                </div>
              )}

              {/* GPS simulation note */}
              <div className="bg-cyan-muted border border-cyan-primary/20 rounded-xl p-3 text-[10px] text-cyan-primary/80">
                <div className="font-semibold mb-1">Simulated GPS</div>
                <div className="text-cyan-primary/60">Vehicle positions and camera feeds are simulated. Replace the <code className="font-mono text-[9px]">useSimulation</code> hook with real GPS/API source.</div>
              </div>
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}
