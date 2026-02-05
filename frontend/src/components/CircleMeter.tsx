import React from 'react';

interface CircleMeterProps {
  label: string;
  value: number;
  unit: string;
  min?: number;
  max?: number;
  status?: 'normal' | 'warning' | 'critical';
  size?: number;
}

export const CircleMeter: React.FC<CircleMeterProps> = ({
  label,
  value,
  unit,
  min = 0,
  max = 100,
  status = 'normal',
  size = 200,
}) => {
  const percentage = Math.min(100, Math.max(0, ((value - min) / (max - min)) * 100));
  // Reduce radius slightly to ensure circle fits inside box with padding
  const radius = (size - 50) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  const getStatusColor = () => {
    switch (status) {
      case 'critical':
        return '#EF4444';
      case 'warning':
        return '#F59E0B';
      default:
        return '#8B5CF6';
    }
  };

  const getStatusBgColor = () => {
    switch (status) {
      case 'critical':
        return 'bg-rose-50 border-rose-200';
      case 'warning':
        return 'bg-amber-50 border-amber-200';
      default:
        return 'bg-purple-50 border-purple-200';
    }
  };

  return (
    <div className={`relative bg-white/90 border ${getStatusBgColor()} rounded-2xl p-4 shadow-sm transition-all duration-300 overflow-hidden`}>
      <div className="flex flex-col items-center h-full">
        <h3 className="text-sm font-medium text-[#4B5563] uppercase tracking-wide mb-3">
          {label}
        </h3>
        
        <div className="relative flex-shrink-0" style={{ width: size, height: size }}>
          <svg
            width={size}
            height={size}
            className="transform -rotate-90"
            style={{ display: 'block' }}
          >
            {/* Background circle */}
            <circle
              cx={size / 2}
              cy={size / 2}
              r={radius}
              fill="none"
              stroke="rgba(229, 231, 235, 1)"
              strokeWidth="12"
            />
            {/* Progress circle */}
            <circle
              cx={size / 2}
              cy={size / 2}
              r={radius}
              fill="none"
              stroke={getStatusColor()}
              strokeWidth="12"
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              className="transition-all duration-500 ease-out"
            />
          </svg>
          
          {/* Value display */}
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <div className="text-4xl font-bold text-[#1F2937] mb-1">
              {value.toFixed(value < 1 ? 2 : value < 10 ? 1 : 0)}
            </div>
            <div className="text-sm text-[#4B5563]">{unit}</div>
            <div className={`text-xs mt-2 px-2 py-1 rounded-lg border font-medium ${
              status === 'critical'
                ? 'bg-rose-50 text-[#1F2937] border-rose-200'
                : status === 'warning'
                ? 'bg-amber-50 text-[#1F2937] border-amber-200'
                : 'bg-emerald-50 text-[#1F2937] border-emerald-200'
            }`}>
              {status.toUpperCase()}
            </div>
          </div>
        </div>
        
        {/* Min/Max labels */}
        <div className="flex justify-between w-full mt-3 text-xs text-[#9CA3AF]">
          <span>Min: {min}</span>
          <span>Max: {max}</span>
        </div>
      </div>
    </div>
  );
};
