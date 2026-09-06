import { MapPin, Navigation, Tag, Hash } from 'lucide-react';

interface VehicleInfo {
  vehicleRef: 'A' | 'B';
  type: string;
  color: string;
  numberPlate?: string;
  plateConfidence?: number;
  direction?: string;
  lane?: string;
  trackingId: string;
}

export default function VehicleCard({ vehicle }: { vehicle: VehicleInfo }) {
  const isA = vehicle.vehicleRef === 'A';
  return (
    <div className={`bg-bg-card border rounded-xl p-3.5 ${isA ? 'border-cyan-primary/30' : 'border-purple-500/30'}`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm ${isA ? 'bg-cyan-muted' : 'bg-purple-900/40'}`}>
            🚗
          </div>
          <div>
            <div className={`text-xs font-semibold ${isA ? 'text-cyan-primary' : 'text-purple-300'}`}>Vehicle {vehicle.vehicleRef}</div>
            <div className="text-text-muted text-[10px]">{vehicle.trackingId}</div>
          </div>
        </div>
        <span className={`text-[9px] px-2 py-1 rounded-md font-semibold border ${isA ? 'bg-cyan-muted text-cyan-primary border-cyan-primary/30' : 'bg-purple-900/30 text-purple-300 border-purple-500/30'}`}>
          TRACKED
        </span>
      </div>

      <div className="space-y-1.5 text-[11px]">
        <Row label="Type" value={vehicle.type} />
        <Row label="Color" value={vehicle.color} />
        {vehicle.numberPlate && <Row label="Plate" value={vehicle.numberPlate} mono />}
        {vehicle.plateConfidence && (
          <div className="flex items-center justify-between">
            <span className="text-text-muted">Plate Conf.</span>
            <div className="flex items-center gap-1.5">
              <div className="w-12 h-1 bg-bg-elevated rounded-full overflow-hidden">
                <div className="h-full bg-success rounded-full" style={{ width: `${vehicle.plateConfidence}%` }} />
              </div>
              <span className="text-success font-mono">{vehicle.plateConfidence}%</span>
            </div>
          </div>
        )}
        {vehicle.direction && <Row label="Direction" value={vehicle.direction} icon={<Navigation size={10} />} />}
        {vehicle.lane && <Row label="Lane" value={vehicle.lane} icon={<MapPin size={10} />} />}
      </div>
    </div>
  );
}

function Row({ label, value, mono = false, icon }: { label: string; value: string; mono?: boolean; icon?: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-text-muted flex items-center gap-1">{icon}{label}</span>
      <span className={`text-text-primary ${mono ? 'font-mono' : 'font-medium'}`}>{value}</span>
    </div>
  );
}
