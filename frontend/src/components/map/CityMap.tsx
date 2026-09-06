import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../../context/AppContext';
import { mockCameras } from '../../data/cameras';
import { clsx } from 'clsx';
import type { Incident, Camera } from '../../types';

interface CityMapProps {
  incidents: Incident[];
  showControls?: boolean;
  height?: string;
  selectedIncidentId?: string | null;
}

// Road network SVG paths (simulated Chennai road network)
const roads = [
  { id: 'anna-salai', name: 'Anna Salai', d: 'M 120 160 L 200 220 L 280 280', stroke: '#383530', strokeW: 8 },
  { id: 'omr', name: 'OMR', d: 'M 440 120 L 450 220 L 460 340 L 470 460', stroke: '#383530', strokeW: 7 },
  { id: 'gst', name: 'GST Road', d: 'M 80 320 L 140 370 L 200 420 L 260 460', stroke: '#383530', strokeW: 7 },
  { id: 'mount', name: 'Mount Road', d: 'M 300 200 L 400 210 L 500 220', stroke: '#383530', strokeW: 6 },
  { id: 'velachery', name: 'Velachery Road', d: 'M 240 340 L 340 360 L 420 380', stroke: '#383530', strokeW: 6 },
  { id: 'adyar', name: 'Adyar Main Road', d: 'M 350 270 L 410 290 L 460 310', stroke: '#383530', strokeW: 5 },
  { id: 'sr-1', name: '', d: 'M 160 280 L 240 340', stroke: '#2B2A27', strokeW: 4 },
  { id: 'sr-2', name: '', d: 'M 320 180 L 340 360', stroke: '#2B2A27', strokeW: 4 },
  { id: 'sr-3', name: '', d: 'M 200 220 L 340 240 L 450 220', stroke: '#2B2A27', strokeW: 3 },
  { id: 'sr-4', name: '', d: 'M 280 280 L 340 320 L 420 310', stroke: '#2B2A27', strokeW: 3 },
  { id: 'sr-5', name: '', d: 'M 140 370 L 240 360 L 340 360', stroke: '#2B2A27', strokeW: 3 },
  { id: 'sr-6', name: '', d: 'M 400 210 L 420 310 L 430 380', stroke: '#2B2A27', strokeW: 3 },
];

// Risk segments highlighted in road colours
const riskSegments = [
  { d: 'M 240 340 L 340 360 L 420 380', color: '#D9534F', opacity: 0.6 },
  { d: 'M 440 120 L 450 220 L 460 340', color: '#C7B89D', opacity: 0.5 },
  { d: 'M 120 160 L 200 220 L 280 280', color: '#C7B89D', opacity: 0.5 },
];

const incidentTypeConfig = {
  'accident':      { color: '#D9534F', emoji: '🔴', label: 'Accident' },
  'hit-and-run':   { color: '#D9534F', emoji: '🔴', label: 'Hit & Run' },
  'pothole':       { color: '#C7B89D', emoji: '🕳️', label: 'Pothole' },
  'waterlogging':  { color: '#D47A45', emoji: '💧', label: 'Waterlogging' },
  'traffic':       { color: '#C7B89D', emoji: '🚦', label: 'Traffic' },
  'infrastructure':{ color: '#B8A090', emoji: '🔧', label: 'Infrastructure' },
  'road-hazard':   { color: '#C7B89D', emoji: '🚧', label: 'Hazard' },
};

const MAP_W = 600;
const MAP_H = 480;
function toSvg(x: number, y: number) {
  return { cx: x * MAP_W, cy: y * MAP_H };
}

interface Props extends CityMapProps {
  layers?: Record<string, boolean>;
  onSelectCamera?: (cam: Camera) => void;
}

export default function CityMap({ incidents, showControls = true, height = 'h-full', selectedIncidentId, layers, onSelectCamera }: Props) {
  const navigate = useNavigate();
  const { setActiveIncidentId, mapLayers: contextLayers } = useApp();
  const activeLayers = layers || contextLayers;

  const [zoom, setZoom] = useState(1);
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const [selectedCam, setSelectedCam] = useState<Camera | null>(null);
  const [vehiclePos, setVehiclePos] = useState({ x: 0.42, y: 0.36 });
  const animRef = useRef<number | null>(null);
  const timeRef = useRef(0);

  useEffect(() => {
    const animate = (ts: number) => {
      if (timeRef.current === 0) timeRef.current = ts;
      const elapsed = (ts - timeRef.current) / 1000;
      const t = (elapsed % 12) / 12;
      const bx = 0.40 + Math.sin(t * Math.PI * 2) * 0.06;
      const by = 0.36 + Math.cos(t * Math.PI * 2) * 0.05;
      setVehiclePos({ x: bx, y: by });
      animRef.current = requestAnimationFrame(animate);
    };
    animRef.current = requestAnimationFrame(animate);
    return () => { if (animRef.current) cancelAnimationFrame(animRef.current); };
  }, []);

  function handleIncidentClick(id: string) {
    setActiveIncidentId(id);
    navigate('/evidence');
  }

  function handleCamClick(cam: Camera) {
    setSelectedCam(cam);
    onSelectCamera?.(cam);
  }

  return (
    <div className={clsx('relative bg-[#171717] rounded-2xl overflow-hidden border border-border flex flex-col', height)}>
      <div className="flex-1 relative overflow-hidden">
        <svg
          viewBox={`0 0 ${MAP_W} ${MAP_H}`}
          className="w-full h-full"
          style={{ transform: `scale(${zoom})`, transition: 'transform 0.3s ease', transformOrigin: 'center' }}
        >
          <defs>
            <pattern id="cityGrid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1E1E1E" strokeWidth="0.5" />
            </pattern>
            <radialGradient id="centerGlow" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#2B2A27" stopOpacity="0.4" />
              <stop offset="100%" stopColor="#171717" stopOpacity="0" />
            </radialGradient>
            <filter id="glow">
              <feGaussianBlur stdDeviation="2.5" result="coloredBlur" />
              <feMerge>
                <feMergeNode in="coloredBlur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>
          <rect width={MAP_W} height={MAP_H} fill="url(#cityGrid)" />
          <rect width={MAP_W} height={MAP_H} fill="url(#centerGlow)" />

          {/* City blocks */}
          {[
            [60,100,80,60],[160,100,80,70],[280,90,100,80],[400,80,90,70],
            [60,200,70,80],[160,200,60,80],[280,200,80,60],[400,200,60,80],[500,180,80,80],
            [60,310,80,80],[180,300,80,80],[300,290,60,80],[400,290,80,80],
            [60,410,120,50],[200,400,80,50],[320,390,80,50],[440,390,80,50],
          ].map(([x, y, w, h], i) => (
            <rect key={i} x={x} y={y} width={w} height={h} fill="#1E1E1E" rx="2" />
          ))}

          {/* Risk segments */}
          {activeLayers['roadRisk'] && riskSegments.map((seg, i) => (
            <path key={i} d={seg.d} fill="none" stroke={seg.color} strokeWidth="6" opacity={seg.opacity} strokeLinecap="round" />
          ))}

          {/* Roads */}
          {roads.map((r) => (
            <g key={r.id}>
              <path d={r.d} fill="none" stroke={r.stroke} strokeWidth={r.strokeW} strokeLinecap="round" strokeLinejoin="round" />
              {r.strokeW >= 7 && (
                <path d={r.d} fill="none" stroke="#2B2A27" strokeWidth="1.5" strokeDasharray="8 12" strokeLinecap="round" />
              )}
              {r.name && (
                <text fontSize="8" fill="#5A5450" fontFamily="Inter, sans-serif" fontWeight="500">
                  <textPath href={`#road-${r.id}`} startOffset="30%">{r.name}</textPath>
                </text>
              )}
            </g>
          ))}

          {/* Traffic congestion overlay */}
          {activeLayers['traffic'] && (
            <path d="M 80 320 L 140 370 L 200 420" fill="none" stroke="#C7B89D" strokeWidth="5" opacity="0.4" strokeDasharray="6 4" />
          )}

          {/* Waterlogging zones */}
          {activeLayers['waterlogging'] && (
            <ellipse cx={0.51 * MAP_W} cy={0.48 * MAP_H} rx="22" ry="14" fill="#D47A45" fillOpacity="0.12" stroke="#D47A45" strokeWidth="0.8" strokeOpacity="0.35" />
          )}

          {/* Pothole markers */}
          {activeLayers['potholes'] && incidents
            .filter(i => i.type === 'pothole')
            .map(inc => {
              const { cx, cy } = toSvg(inc.coordinates.x, inc.coordinates.y);
              return (
                <g key={`pt-${inc.id}`} onClick={() => handleIncidentClick(inc.id)} className="cursor-pointer">
                  <circle cx={cx} cy={cy} r="5" fill="#C7B89D" opacity="0.8" />
                  <text x={cx} y={cy + 1} textAnchor="middle" dominantBaseline="middle" fontSize="6" fill="#171717">🕳</text>
                </g>
              );
            })}

          {/* Incident markers */}
          {activeLayers['incidents'] && incidents.map((inc) => {
            const cfg = incidentTypeConfig[inc.type] || incidentTypeConfig.accident;
            const { cx, cy } = toSvg(inc.coordinates.x, inc.coordinates.y);
            const isSelected = inc.id === selectedIncidentId || inc.id === hoveredId;
            const isDemo = inc.id === 'INC-2048';
            return (
              <g
                key={inc.id}
                className="cursor-pointer"
                onClick={() => handleIncidentClick(inc.id)}
                onMouseEnter={() => setHoveredId(inc.id)}
                onMouseLeave={() => setHoveredId(null)}
              >
                {isDemo && (
                  <circle cx={cx} cy={cy} r="18" fill="none" stroke={cfg.color} strokeWidth="1" opacity="0.3">
                    <animate attributeName="r" from="12" to="22" dur="2s" repeatCount="indefinite" />
                    <animate attributeName="opacity" from="0.5" to="0" dur="2s" repeatCount="indefinite" />
                  </circle>
                )}
                <circle
                  cx={cx} cy={cy} r={isSelected ? 11 : 9}
                  fill={cfg.color} fillOpacity={isSelected ? 0.95 : 0.85}
                  stroke={isSelected ? '#E8E3D8' : '#171717'}
                  strokeWidth={isSelected ? 2 : 1.5}
                  filter={isDemo ? 'url(#glow)' : undefined}
                  style={{ transition: 'r 0.2s' }}
                />
                <text x={cx} y={cy + 1} textAnchor="middle" dominantBaseline="middle" fontSize="8">
                  {cfg.emoji}
                </text>

                {isSelected && (
                  <g>
                    <rect x={cx + 12} y={cy - 22} width="90" height="30" rx="4" fill="#2B2A27" stroke="#383530" strokeWidth="1" />
                    <text x={cx + 57} y={cy - 11} textAnchor="middle" dominantBaseline="middle" fontSize="7" fill="#E8E3D8" fontFamily="Inter, sans-serif" fontWeight="600">
                      {inc.id}
                    </text>
                    <text x={cx + 57} y={cy - 3} textAnchor="middle" dominantBaseline="middle" fontSize="6" fill="#9E9A8E" fontFamily="Inter, sans-serif">
                      {inc.location}
                    </text>
                  </g>
                )}
              </g>
            );
          })}

          {/* Camera markers */}
          {activeLayers['cameras'] && mockCameras.map((cam) => {
            const { cx, cy } = toSvg(cam.coordinates.x, cam.coordinates.y);
            const isSelected = selectedCam?.id === cam.id;
            const statusColor = cam.status === 'online' ? '#6F9E75' : cam.status === 'degraded' ? '#C7B89D' : '#D9534F';
            return (
              <g key={cam.id} className="cursor-pointer" onClick={() => handleCamClick(cam)}>
                {isSelected && (
                  <circle cx={cx} cy={cy} r={cam.coverageRadius / 4} fill={statusColor} fillOpacity="0.05" stroke={statusColor} strokeWidth="0.5" strokeDasharray="3 3" />
                )}
                <rect
                  x={cx - 7} y={cy - 6} width="14" height="12" rx="2"
                  fill={isSelected ? '#2B2A27' : '#1E1E1E'}
                  stroke={statusColor}
                  strokeWidth={isSelected ? 1.5 : 1}
                />
                <circle cx={cx} cy={cy} r="2.5" fill={statusColor} />
                {isSelected && (
                  <g>
                    <rect x={cx - 20} y={cy - 22} width="40" height="12" rx="2" fill="#2B2A27" stroke="#383530" strokeWidth="1" />
                    <text x={cx} y={cy - 16} textAnchor="middle" dominantBaseline="middle" fontSize="6" fill="#D47A45" fontFamily="Inter, sans-serif" fontWeight="600">{cam.id}</text>
                  </g>
                )}
              </g>
            );
          })}

          {/* Road closures */}
          {activeLayers['closures'] && (
            <g>
              <line x1="390" y1="280" x2="420" y2="300" stroke="#D9534F" strokeWidth="4" strokeDasharray="5 3" strokeLinecap="round" />
              <text x="430" y="290" fontSize="7" fill="#D9534F" fontFamily="Inter, sans-serif">Closure</text>
            </g>
          )}

          {/* Simulated vehicle */}
          <g>
            <circle cx={vehiclePos.x * MAP_W} cy={vehiclePos.y * MAP_H} r="12" fill="#D47A45" fillOpacity="0.1" stroke="#D47A45" strokeWidth="0.8" strokeDasharray="3 2" />
            <circle cx={vehiclePos.x * MAP_W} cy={vehiclePos.y * MAP_H} r="5" fill="#D47A45" />
            <circle cx={vehiclePos.x * MAP_W} cy={vehiclePos.y * MAP_H} r="2.5" fill="#171717" />
          </g>

          {/* Compass */}
          <g transform="translate(555, 30)">
            <circle cx="0" cy="0" r="14" fill="#222222" stroke="#383530" strokeWidth="1" />
            <text x="0" y="-6" textAnchor="middle" dominantBaseline="middle" fontSize="7" fill="#D47A45" fontWeight="700">N</text>
            <text x="0" y="6" textAnchor="middle" dominantBaseline="middle" fontSize="6" fill="#6B6760">S</text>
            <text x="-8" y="0" textAnchor="middle" dominantBaseline="middle" fontSize="6" fill="#6B6760">W</text>
            <text x="8" y="0" textAnchor="middle" dominantBaseline="middle" fontSize="6" fill="#6B6760">E</text>
          </g>
        </svg>

        {/* Timestamp overlay */}
        <div className="absolute top-3 left-3 flex items-center gap-2">
          <div className="flex items-center gap-1.5 bg-bg-elevated/90 border border-border rounded-lg px-2.5 py-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-coral-critical animate-pulse" />
            <span className="text-text-primary text-[10px] font-mono font-medium">LIVE</span>
            <span className="text-text-muted text-[10px] font-mono">
              {new Date().toLocaleTimeString('en-IN', { hour12: false })}
            </span>
          </div>
        </div>

        {/* Selected camera panel */}
        {selectedCam && (
          <div className="absolute bottom-3 left-3 bg-bg-elevated/95 border border-border rounded-xl p-3 w-48 text-xs">
            <div className="flex items-center justify-between mb-2">
              <span className="text-cyan-primary font-semibold">{selectedCam.id}</span>
              <button onClick={() => setSelectedCam(null)} className="text-text-muted hover:text-text-primary text-[10px]">✕</button>
            </div>
            <div className="space-y-1 text-[10px]">
              <div className="flex justify-between"><span className="text-text-muted">Location</span><span className="text-text-primary text-right max-w-[100px] truncate">{selectedCam.location}</span></div>
              <div className="flex justify-between"><span className="text-text-muted">Status</span>
                <span className={clsx(selectedCam.status === 'online' ? 'text-success' : selectedCam.status === 'degraded' ? 'text-amber-warning' : 'text-coral-critical')}>
                  ● {selectedCam.status}
                </span>
              </div>
              <div className="flex justify-between"><span className="text-text-muted">Last Frame</span><span className="text-text-primary font-mono">{selectedCam.lastFrame}</span></div>
              <div className="flex justify-between"><span className="text-text-muted">Coords</span><span className="text-text-primary font-mono">{selectedCam.coordinates.lat.toFixed(4)}°N</span></div>
            </div>
          </div>
        )}
      </div>

      {/* Zoom controls */}
      {showControls && (
        <div className="absolute right-3 bottom-3 flex flex-col gap-1">
          <button onClick={() => setZoom(z => Math.min(z + 0.2, 2.5))} className="w-8 h-8 bg-bg-elevated border border-border rounded-lg text-text-secondary hover:text-cyan-primary hover:border-cyan-primary/30 flex items-center justify-center text-sm font-bold transition-all" title="Zoom in">+</button>
          <button onClick={() => setZoom(1)} className="w-8 h-8 bg-bg-elevated border border-border rounded-lg text-text-secondary hover:text-cyan-primary flex items-center justify-center text-[9px] font-medium transition-all" title="Reset zoom">⟲</button>
          <button onClick={() => setZoom(z => Math.max(z - 0.2, 0.5))} className="w-8 h-8 bg-bg-elevated border border-border rounded-lg text-text-secondary hover:text-cyan-primary hover:border-cyan-primary/30 flex items-center justify-center text-sm font-bold transition-all" title="Zoom out">−</button>
        </div>
      )}
    </div>
  );
}
