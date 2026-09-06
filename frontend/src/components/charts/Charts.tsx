import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  PieChart, Pie, Cell, ResponsiveContainer, AreaChart, Area, BarChart, Bar,
} from 'recharts';

interface ChartTooltipProps {
  active?: boolean;
  payload?: { name: string; value: number; color: string }[];
  label?: string;
}

function CustomTooltip({ active, payload, label }: ChartTooltipProps) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-bg-elevated border border-border rounded-xl px-3 py-2 shadow-elevated text-xs">
      {label && <div className="text-text-muted mb-1 font-mono">{label}</div>}
      {payload.map((p) => (
        <div key={p.name} className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full" style={{ background: p.color }} />
          <span className="text-text-secondary">{p.name}:</span>
          <span className="text-text-primary font-medium">{p.value}</span>
        </div>
      ))}
    </div>
  );
}

interface TrendData {
  date: string;
  accidents: number;
  potholes: number;
  waterlogging: number;
  traffic: number;
}

export function IncidentTrendChart({ data }: { data: TrendData[] }) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <AreaChart data={data} margin={{ top: 5, right: 10, bottom: 0, left: -20 }}>
        <defs>
          {[
            { id: 'accidents',    color: '#D9534F' },
            { id: 'potholes',     color: '#C7B89D' },
            { id: 'waterlogging', color: '#D47A45' },
            { id: 'traffic',      color: '#9E8B75' },
          ].map(({ id, color }) => (
            <linearGradient key={id} id={`grad-${id}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={color} stopOpacity={0.2} />
              <stop offset="95%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          ))}
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#2B2A27" />
        <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#6B6760' }} axisLine={false} tickLine={false} />
        <YAxis tick={{ fontSize: 10, fill: '#6B6760' }} axisLine={false} tickLine={false} />
        <Tooltip content={<CustomTooltip />} />
        <Legend wrapperStyle={{ fontSize: '10px', color: '#9E9A8E' }} />
        <Area type="monotone" dataKey="accidents"    name="Accidents"    stroke="#D9534F" fill="url(#grad-accidents)"    strokeWidth={2} dot={false} />
        <Area type="monotone" dataKey="potholes"     name="Potholes"     stroke="#C7B89D" fill="url(#grad-potholes)"     strokeWidth={2} dot={false} />
        <Area type="monotone" dataKey="waterlogging" name="Waterlogging" stroke="#D47A45" fill="url(#grad-waterlogging)" strokeWidth={2} dot={false} />
        <Area type="monotone" dataKey="traffic"      name="Traffic"      stroke="#9E8B75" fill="url(#grad-traffic)"      strokeWidth={2} dot={false} />
      </AreaChart>
    </ResponsiveContainer>
  );
}

interface DistItem { name: string; value: number; color: string }
export function IncidentDistributionChart({ data }: { data: DistItem[] }) {
  return (
    <ResponsiveContainer width="100%" height={200}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={55}
          outerRadius={80}
          paddingAngle={3}
          dataKey="value"
        >
          {data.map((entry, idx) => (
            <Cell key={idx} fill={entry.color} opacity={0.9} />
          ))}
        </Pie>
        <Tooltip
          content={({ active, payload }) => {
            if (!active || !payload?.length) return null;
            const d = payload[0].payload as DistItem;
            return (
              <div className="bg-bg-elevated border border-border rounded-xl px-3 py-2 text-xs">
                <span style={{ color: d.color }} className="font-medium">{d.name}</span>
                <span className="text-text-muted ml-2">{d.value}</span>
              </div>
            );
          }}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}

interface RoadHistData { date: string; score: number }
export function RoadTrendChart({ data }: { data: RoadHistData[] }) {
  return (
    <ResponsiveContainer width="100%" height={120}>
      <LineChart data={data} margin={{ top: 5, right: 5, bottom: 0, left: -30 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#2B2A27" />
        <XAxis dataKey="date" tick={{ fontSize: 9, fill: '#6B6760' }} axisLine={false} tickLine={false} />
        <YAxis domain={[40, 100]} tick={{ fontSize: 9, fill: '#6B6760' }} axisLine={false} tickLine={false} />
        <Tooltip content={<CustomTooltip />} />
        <Line type="monotone" dataKey="score" name="Risk Score" stroke="#D47A45" strokeWidth={2} dot={{ r: 2.5, fill: '#D47A45' }} />
      </LineChart>
    </ResponsiveContainer>
  );
}

interface BarData { label: string; value: number; color?: string }
export function RiskBarChart({ data }: { data: BarData[] }) {
  return (
    <ResponsiveContainer width="100%" height={180}>
      <BarChart data={data} layout="vertical" margin={{ top: 0, right: 10, bottom: 0, left: 80 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#2B2A27" horizontal={false} />
        <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 9, fill: '#6B6760' }} axisLine={false} tickLine={false} />
        <YAxis dataKey="label" type="category" tick={{ fontSize: 10, fill: '#9E9A8E' }} axisLine={false} tickLine={false} />
        <Tooltip content={<CustomTooltip />} />
        <Bar dataKey="value" name="Risk Score" radius={[0, 4, 4, 0]}>
          {data.map((d, i) => (
            <Cell key={i} fill={d.color || '#D47A45'} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
