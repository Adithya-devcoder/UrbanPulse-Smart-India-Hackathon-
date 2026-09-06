import { AnimatePresence, motion } from 'framer-motion';
import { X, AlertTriangle, Info, CheckCircle, AlertCircle } from 'lucide-react';
import Sidebar from './Sidebar';
import Header from './Header';
import { useApp } from '../../context/AppContext';
import { useSimulation } from '../../hooks/useSimulation';
import { clsx } from 'clsx';

interface LayoutProps {
  children: React.ReactNode;
  title: string;
  subtitle: string;
}

const toastIcons = {
  info: <Info size={14} />,
  success: <CheckCircle size={14} />,
  warning: <AlertTriangle size={14} />,
  critical: <AlertCircle size={14} />,
};
const toastColors = {
  info: 'border-cyan-primary/30 bg-cyan-muted text-cyan-primary',
  success: 'border-success/30 bg-success/10 text-success',
  warning: 'border-amber-warning/30 bg-amber-muted text-amber-warning',
  critical: 'border-coral-critical/30 bg-coral-muted text-coral-critical',
};

function ToastContainer() {
  const { toasts, removeToast } = useApp();
  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-2 pointer-events-none">
      <AnimatePresence>
        {toasts.map((t) => (
          <motion.div
            key={t.id}
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            transition={{ duration: 0.25 }}
            className={clsx(
              'flex items-center gap-2.5 px-4 py-3 rounded-xl border shadow-elevated text-sm pointer-events-auto max-w-xs',
              toastColors[t.type]
            )}
          >
            {toastIcons[t.type]}
            <span className="flex-1 text-text-primary text-xs">{t.message}</span>
            <button onClick={() => removeToast(t.id)} className="flex-shrink-0 opacity-60 hover:opacity-100">
              <X size={13} />
            </button>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}

function SimulationRunner() {
  useSimulation();
  return null;
}

export default function Layout({ children, title, subtitle }: LayoutProps) {
  return (
    <div className="flex h-screen bg-bg-primary overflow-hidden font-sans">
      <SimulationRunner />
      <Sidebar />
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        <Header title={title} subtitle={subtitle} />
        <main className="flex-1 overflow-y-auto">
          {children}
        </main>
      </div>
      <ToastContainer />
    </div>
  );
}
