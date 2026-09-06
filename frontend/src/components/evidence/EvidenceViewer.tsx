import { useState, useEffect, useRef } from 'react';
import { Play, Pause, SkipBack, SkipForward, Maximize2, Camera } from 'lucide-react';
import { clsx } from 'clsx';
import type { Incident } from '../../types';

interface Props {
  incident: Incident;
  activeFrame: number;
  onFrameChange: (f: number) => void;
}

const frameLabels = [
  { ts: '10:42:18', desc: 'Vehicle A enters frame — Anna Salai northbound', vehicleA: { x: 30, y: 55 }, vehicleB: null },
  { ts: '10:42:21', desc: 'Vehicle B approaching — drifting toward Lane 2', vehicleA: { x: 42, y: 48 }, vehicleB: { x: 62, y: 42 } },
  { ts: '10:42:23', desc: 'COLLISION DETECTED — sudden proximity change', vehicleA: { x: 50, y: 44 }, vehicleB: { x: 55, y: 43 }, collision: true },
  { ts: '10:42:25', desc: 'Vehicle B stationary at collision point', vehicleA: { x: 58, y: 40 }, vehicleB: { x: 55, y: 43 } },
  { ts: '10:42:31', desc: 'Vehicle A accelerates — no stop detected', vehicleA: { x: 74, y: 34 }, vehicleB: { x: 55, y: 44 } },
  { ts: '10:42:32', desc: 'Vehicle A exits frame — HIT-AND-RUN FLAGGED', vehicleA: null, vehicleB: { x: 55, y: 45 }, flagged: true },
];

export default function EvidenceViewer({ incident, activeFrame, onFrameChange }: Props) {
  const [playing, setPlaying] = useState(false);
  const frameRef = useRef(activeFrame);
  frameRef.current = activeFrame;

  useEffect(() => {
    if (!playing) return;
    const interval = setInterval(() => {
      const next = frameRef.current + 1;
      if (next >= frameLabels.length) { setPlaying(false); return; }
      onFrameChange(next);
    }, 1800);
    return () => clearInterval(interval);
  }, [playing, onFrameChange]);

  const frame = frameLabels[activeFrame] || frameLabels[0];

  return (
    <div className="bg-[#111111] border border-border rounded-2xl overflow-hidden">
      {/* Video canvas area */}
      <div className="relative" style={{ aspectRatio: '16/9' }}>
        <svg viewBox="0 0 100 60" className="w-full h-full" preserveAspectRatio="xMidYMid slice">
          <defs>
            <linearGradient id="skyGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#111111" />
              <stop offset="100%" stopColor="#1A1A18" />
            </linearGradient>
            <linearGradient id="roadGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#222220" />
              <stop offset="100%" stopColor="#1A1A18" />
            </linearGradient>
          </defs>

          {/* Sky / building background */}
          <rect width="100" height="35" fill="url(#skyGrad)" />
          {/* Buildings silhouette */}
          {[[5,20,10,15],[18,25,8,10],[30,22,12,13],[48,18,9,17],[62,24,11,11],[76,20,8,15],[88,26,7,9]].map(([x,y,w,h],i)=>(
            <rect key={i} x={x} y={y} width={w} height={h} fill="#171717" />
          ))}
          {/* Street lights */}
          <line x1="20" y1="30" x2="20" y2="42" stroke="#383530" strokeWidth="0.5" />
          <ellipse cx="20" cy="30" rx="4" ry="1.5" fill="#C7B89D" fillOpacity="0.2" />
          <line x1="75" y1="30" x2="75" y2="42" stroke="#383530" strokeWidth="0.5" />
          <ellipse cx="75" cy="30" rx="4" ry="1.5" fill="#C7B89D" fillOpacity="0.2" />

          {/* Road surface */}
          <rect y="35" width="100" height="25" fill="url(#roadGrad)" />
          <line x1="0" y1="42" x2="100" y2="42" stroke="#2B2A27" strokeWidth="0.8" />
          <line x1="0" y1="35" x2="100" y2="35" stroke="#383530" strokeWidth="1" />
          {/* Center line dashes */}
          {[0,12,24,36,48,60,72,84].map((x, i) => (
            <line key={i} x1={x+2} y1="49" x2={x+8} y2="49" stroke="#2B2A27" strokeWidth="0.5" strokeDasharray="2 1" />
          ))}

          <rect y="58" width="100" height="2" fill="#2B2A27" />

          {/* Collision flash */}
          {frame.collision && (
            <rect width="100" height="60" fill="#D9534F" fillOpacity="0.07" />
          )}
          {(frame as any).flagged && (
            <rect width="100" height="60" fill="#C7B89D" fillOpacity="0.05" />
          )}

          {/* Vehicle A — sand/cream sedan */}
          {frame.vehicleA && (
            <g>
              <rect
                x={frame.vehicleA.x - 5} y={frame.vehicleA.y - 3}
                width="10" height="6" rx="1.5"
                fill={(frame as any).flagged ? '#D9534F' : '#C8B89A'}
                stroke={(frame as any).flagged ? '#D9534F' : '#D47A45'}
                strokeWidth={frame.collision ? 1.5 : 0.8}
              />
              <rect
                x={frame.vehicleA.x - 7} y={frame.vehicleA.y - 5}
                width="14" height="10" rx="1"
                fill="none"
                stroke="#D47A45"
                strokeWidth="0.6"
                strokeDasharray={frame.collision || (frame as any).flagged ? '1 0' : '1.5 1'}
                opacity={frame.collision ? 1 : 0.7}
              />
              <rect x={frame.vehicleA.x - 7} y={frame.vehicleA.y - 10} width="14" height="5" rx="1" fill="#D47A45" fillOpacity="0.9" />
              <text x={frame.vehicleA.x} y={frame.vehicleA.y - 7.5} textAnchor="middle" dominantBaseline="middle" fontSize="2.5" fill="#171717" fontWeight="700">VEH-A</text>
              <circle cx={frame.vehicleA.x - 3} cy={frame.vehicleA.y + 3} r="1" fill="#171717" />
              <circle cx={frame.vehicleA.x + 3} cy={frame.vehicleA.y + 3} r="1" fill="#171717" />
            </g>
          )}

          {/* Vehicle B — dark brown hatchback */}
          {frame.vehicleB && (
            <g>
              <rect
                x={frame.vehicleB.x - 4} y={frame.vehicleB.y - 2.5}
                width="8" height="5" rx="1.5"
                fill="#4A3828"
                stroke="#B8A090"
                strokeWidth={frame.collision ? 1.5 : 0.8}
              />
              <rect
                x={frame.vehicleB.x - 6} y={frame.vehicleB.y - 4.5}
                width="12" height="9" rx="1"
                fill="none"
                stroke="#B8A090"
                strokeWidth="0.6"
                strokeDasharray="1.5 1"
                opacity="0.8"
              />
              <rect x={frame.vehicleB.x - 6} y={frame.vehicleB.y - 9.5} width="12" height="5" rx="1" fill="#B8A090" fillOpacity="0.9" />
              <text x={frame.vehicleB.x} y={frame.vehicleB.y - 7} textAnchor="middle" dominantBaseline="middle" fontSize="2.5" fill="#171717" fontWeight="700">VEH-B</text>
              <circle cx={frame.vehicleB.x - 2.5} cy={frame.vehicleB.y + 2.5} r="1" fill="#171717" />
              <circle cx={frame.vehicleB.x + 2.5} cy={frame.vehicleB.y + 2.5} r="1" fill="#171717" />
            </g>
          )}

          {/* Tracking line */}
          {frame.vehicleA && frame.vehicleB && (
            <line
              x1={frame.vehicleA.x} y1={frame.vehicleA.y}
              x2={frame.vehicleB.x} y2={frame.vehicleB.y}
              stroke={frame.collision ? '#D9534F' : '#D47A45'}
              strokeWidth="0.4"
              strokeDasharray="1.5 1"
              opacity="0.5"
            />
          )}

          {/* Waterlogged pothole scene */}
          {incident.type === 'waterlogging' && (
            <g>
              <ellipse cx="50" cy="48" rx="12" ry="4" fill="#2A2520" stroke="#D47A45" strokeWidth="0.5" fillOpacity="0.7" />
              <ellipse cx="50" cy="47" rx="8" ry="2.5" fill="#D47A45" fillOpacity="0.15" />
              <text x="50" y="56" textAnchor="middle" fontSize="2.5" fill="#D47A45" fontFamily="Inter">WATERLOGGED ZONE</text>
            </g>
          )}

          {/* Alert overlays */}
          {(frame as any).flagged && (
            <g>
              <rect x="5" y="5" width="40" height="8" rx="1" fill="#D9534F" fillOpacity="0.15" stroke="#D9534F" strokeWidth="0.5" />
              <text x="7" y="9.5" fontSize="2.8" fill="#D9534F" fontWeight="700" fontFamily="Inter">⚠ HIT-AND-RUN FLAGGED</text>
            </g>
          )}
          {frame.collision && (
            <g>
              <rect x="5" y="5" width="35" height="8" rx="1" fill="#D9534F" fillOpacity="0.15" stroke="#D9534F" strokeWidth="0.5" />
              <text x="7" y="9.5" fontSize="2.8" fill="#D9534F" fontWeight="700" fontFamily="Inter">⚠ COLLISION DETECTED</text>
            </g>
          )}
        </svg>

        {/* Overlays */}
        <div className="absolute top-2 left-2 flex items-center gap-2">
          <div className="flex items-center gap-1.5 bg-black/60 rounded px-2 py-1">
            <Camera size={10} className="text-text-muted" />
            <span className="text-text-muted text-[9px] font-mono">{incident.cameraId || 'CAM-042'}</span>
          </div>
          <div className="flex items-center gap-1 bg-black/60 rounded px-2 py-1">
            <span className="text-text-muted text-[9px] font-mono">{frame.ts}</span>
          </div>
          <div className={clsx(
            'flex items-center gap-1 rounded px-2 py-1 text-[9px] font-semibold',
            activeFrame === 0 ? 'bg-coral-critical/80 text-white' : 'bg-black/60 text-text-muted'
          )}>
            {activeFrame === 0 ? '● LIVE' : 'RECORDED'}
          </div>
        </div>

        <div className="absolute top-2 right-2 bg-black/60 rounded px-2 py-1">
          <span className="text-text-muted text-[9px] font-mono">Frame {activeFrame + 1} / {incident.evidenceFrames}</span>
        </div>

        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent px-3 py-2">
          <p className="text-text-secondary text-[10px]">{frame.desc}</p>
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-center gap-3 px-4 py-3 border-t border-border">
        <button onClick={() => onFrameChange(Math.max(0, activeFrame - 1))} className="p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-bg-elevated transition-all">
          <SkipBack size={15} />
        </button>
        <button
          onClick={() => setPlaying(p => !p)}
          className={clsx('w-8 h-8 rounded-full flex items-center justify-center transition-all',
            playing ? 'bg-cyan-muted text-cyan-primary' : 'bg-cyan-primary text-bg-primary'
          )}
        >
          {playing ? <Pause size={14} /> : <Play size={14} />}
        </button>
        <button onClick={() => onFrameChange(Math.min(incident.evidenceFrames - 1, activeFrame + 1))} className="p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-bg-elevated transition-all">
          <SkipForward size={15} />
        </button>

        {/* Scrubber */}
        <div className="flex-1 flex items-center gap-1">
          {Array.from({ length: incident.evidenceFrames }).map((_, i) => (
            <button
              key={i}
              onClick={() => onFrameChange(i)}
              className={clsx(
                'flex-1 h-1.5 rounded-full transition-all',
                i === activeFrame ? 'bg-cyan-primary' : i < activeFrame ? 'bg-cyan-primary/40' : 'bg-border'
              )}
            />
          ))}
        </div>

        <button className="p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-bg-elevated transition-all">
          <Camera size={15} />
        </button>
        <button className="p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-bg-elevated transition-all">
          <Maximize2 size={15} />
        </button>
      </div>
    </div>
  );
}
