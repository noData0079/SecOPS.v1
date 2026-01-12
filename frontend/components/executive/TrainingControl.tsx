import { useState, useEffect } from 'react';
import {
  ArrowPathIcon,
  BeakerIcon,
  BoltIcon,
  CircleStackIcon,
  PlayIcon,
  StopIcon,
  ServerIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline';

const TrainingControl = ({ token }) => {
  const [status, setStatus] = useState({ is_training: false, status: 'IDLE', gigo_stats: { total: 0, rejected: 0 } });
  const [loading, setLoading] = useState(false);

  const fetchStatus = async () => {
    try {
      const res = await fetch('/api/admin/training/status', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        setStatus(await res.json());
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    const interval = setInterval(fetchStatus, 5000);
    fetchStatus();
    return () => clearInterval(interval);
  }, []);

  const handleStart = async () => {
    setLoading(true);
    try {
      await fetch('/api/admin/training/start', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      await fetchStatus();
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleStop = async () => {
    setLoading(true);
    try {
      await fetch('/api/admin/training/stop', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      await fetchStatus();
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {/* Control Card */}
        <div className="rounded-lg border border-slate-700 bg-slate-800 p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium text-slate-400">Recursive Training</h3>
            <BoltIcon className={`h-5 w-5 ${status.is_training ? 'text-emerald-400 animate-pulse' : 'text-slate-500'}`} />
          </div>
          <p className="mt-2 text-3xl font-bold text-white tracking-tight">
            {status.status}
          </p>
          <div className="mt-6 flex gap-3">
             {!status.is_training ? (
                <button
                    onClick={handleStart}
                    disabled={loading}
                    className="flex-1 rounded-md bg-emerald-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-emerald-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-600 disabled:opacity-50"
                >
                    <PlayIcon className="mr-2 h-4 w-4 inline" />
                    Auto-Evolve
                </button>
             ) : (
                <button
                    onClick={handleStop}
                    disabled={loading}
                    className="flex-1 rounded-md bg-red-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-red-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-red-600 disabled:opacity-50"
                >
                    <StopIcon className="mr-2 h-4 w-4 inline" />
                    Halt
                </button>
             )}
          </div>
        </div>

        {/* GIGO Meter */}
        <div className="rounded-lg border border-slate-700 bg-slate-800 p-6 shadow-sm">
           <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium text-slate-400">GIGO Protection</h3>
            <ShieldCheckIcon className="h-5 w-5 text-indigo-400" />
          </div>
           <div className="mt-4">
             <div className="flex justify-between text-sm mb-1">
               <span className="text-slate-300">Total Scenarios</span>
               <span className="text-white font-mono">{status.gigo_stats.total}</span>
             </div>
             <div className="flex justify-between text-sm mb-1">
               <span className="text-slate-300">Rejected (Garbage)</span>
               <span className="text-red-400 font-mono">{status.gigo_stats.rejected}</span>
             </div>
             <div className="mt-2 w-full bg-slate-700 rounded-full h-2.5">
               <div
                 className="bg-indigo-500 h-2.5 rounded-full"
                 style={{ width: `${status.gigo_stats.total > 0 ? ((status.gigo_stats.total - status.gigo_stats.rejected) / status.gigo_stats.total) * 100 : 0}%` }}
               ></div>
             </div>
             <p className="text-xs text-slate-500 mt-2">Quality Gate Pass Rate</p>
           </div>
        </div>

        {/* Model Version */}
        <div className="rounded-lg border border-slate-700 bg-slate-800 p-6 shadow-sm">
           <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium text-slate-400">Current Model</h3>
            <ServerIcon className="h-5 w-5 text-blue-400" />
          </div>
          <p className="mt-2 text-xl font-bold text-white tracking-tight">
            Llama-3.3-v1.0.1
          </p>
          <div className="mt-4 flex items-center text-xs text-emerald-400">
            <ChartBarIcon className="mr-1 h-3 w-3" />
            +12% Performance Delta
          </div>
        </div>
      </div>

      {/* Kaggle Integration Status */}
      <div className="rounded-lg border border-slate-700 bg-slate-800 p-6">
          <h3 className="text-base font-semibold text-white mb-4">Training Pipeline Status</h3>
          <div className="relative">
             <div className="absolute top-0 bottom-0 left-4 w-0.5 bg-slate-700"></div>
             <div className="space-y-6 ml-1">
                 {['SYNTHESIZING', 'CLEANING', 'UPLOADING', 'TRAINING_REMOTE'].map((step, idx) => {
                     const isCurrent = status.status === step;
                     const isPast = ['SYNTHESIZING', 'CLEANING', 'UPLOADING', 'TRAINING_REMOTE', 'COMPLETED'].indexOf(status.status) > idx;

                     return (
                         <div key={step} className="flex items-center relative pl-8">
                             <div className={`absolute left-2.5 -translate-x-1/2 w-3 h-3 rounded-full border-2 ${isCurrent ? 'bg-emerald-500 border-emerald-500 animate-pulse' : (isPast ? 'bg-emerald-500 border-emerald-500' : 'bg-slate-900 border-slate-500')}`}></div>
                             <span className={`text-sm ${isCurrent ? 'text-white font-bold' : (isPast ? 'text-emerald-400' : 'text-slate-500')}`}>
                                 {step}
                             </span>
                         </div>
                     )
                 })}
             </div>
          </div>
      </div>
    </div>
  );
};

function ShieldCheckIcon(props) {
  return (
    <svg fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" {...props}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 01-1.043 3.296 3.745 3.745 0 01-3.296 1.043A3.745 3.745 0 0112 21c-1.268 0-2.39-.63-3.068-1.593a3.746 3.746 0 01-3.296-1.043 3.745 3.745 0 01-1.043-3.296A3.745 3.745 0 013 12c0-1.268.63-2.39 1.593-3.068a3.745 3.745 0 011.043-3.296 3.746 3.746 0 013.296-1.043A3.746 3.746 0 0112 3c1.268 0 2.39.63 3.068 1.593a3.746 3.746 0 013.296 1.043 3.746 3.746 0 011.043 3.296A3.745 3.745 0 0121 12z" />
    </svg>
  );
}

export default TrainingControl;
