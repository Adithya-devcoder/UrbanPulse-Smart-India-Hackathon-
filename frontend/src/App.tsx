import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppProvider } from './context/AppContext';
import Dashboard from './pages/Dashboard';
import LiveMap from './pages/LiveMap';
import RiskHeatmap from './pages/RiskHeatmap';
import Incidents from './pages/Incidents';
import AIEvidence from './pages/AIEvidence';
import RoadRisk from './pages/RoadRisk';
import ActionCenter from './pages/ActionCenter';
import Reports from './pages/Reports';
import Settings from './pages/Settings';

export default function App() {
  return (
    <BrowserRouter>
      <AppProvider>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/map" element={<LiveMap />} />
          <Route path="/heatmap" element={<RiskHeatmap />} />
          <Route path="/incidents" element={<Incidents />} />
          <Route path="/evidence" element={<AIEvidence />} />
          <Route path="/road-risk" element={<RoadRisk />} />
          <Route path="/actions" element={<ActionCenter />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/reports-full" element={<Reports />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AppProvider>
    </BrowserRouter>
  );
}
