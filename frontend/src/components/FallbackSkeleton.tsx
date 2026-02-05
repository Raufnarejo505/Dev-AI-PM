import React from 'react';

export const FallbackSkeleton: React.FC<{ className?: string }> = ({ className = '' }) => (
  <div className={`animate-pulse ${className}`}>
    <div className="h-4 bg-slate-700/50 rounded w-3/4 mb-2" />
    <div className="h-4 bg-slate-700/50 rounded w-1/2" />
  </div>
);

export const CardSkeleton: React.FC = () => (
  <div className="bg-slate-900/70 border border-slate-700/40 rounded-2xl p-6 animate-pulse">
    <div className="h-6 bg-slate-700/50 rounded w-1/3 mb-4" />
    <div className="h-8 bg-slate-700/50 rounded w-1/2 mb-2" />
    <div className="h-4 bg-slate-700/50 rounded w-2/3" />
  </div>
);

export const ChartSkeleton: React.FC = () => (
  <div className="bg-slate-900/70 border border-slate-700/40 rounded-2xl p-6 animate-pulse">
    <div className="h-6 bg-slate-700/50 rounded w-1/4 mb-4" />
    <div className="h-64 bg-slate-700/30 rounded" />
  </div>
);

export const ListSkeleton: React.FC<{ count?: number }> = ({ count = 5 }) => (
  <div className="space-y-3">
    {Array.from({ length: count }).map((_, i) => (
      <div
        key={i}
        className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-4 animate-pulse"
      >
        <div className="h-5 bg-slate-700/50 rounded w-1/3 mb-2" />
        <div className="h-4 bg-slate-700/50 rounded w-2/3" />
      </div>
    ))}
  </div>
);

