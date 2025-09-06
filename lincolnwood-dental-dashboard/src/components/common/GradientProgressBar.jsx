import React from 'react';

const GradientProgressBar = ({ 
  value, 
  max = 100, 
  variant = "primary", 
  size = "md",
  showLabel = false,
  animated = true,
  className = ""
}) => {
  const percentage = Math.min((value / max) * 100, 100);
  
  const sizeClasses = {
    sm: "h-1.5",
    md: "h-2", 
    lg: "h-3"
  };
  
  const variantColors = {
    primary: "bg-teal-500",
    success: "bg-emerald-500",
    warning: "bg-orange-500",
    error: "bg-red-500",
    secondary: "bg-gray-400"
  };
  
  return (
    <div className={`relative ${className}`}>
      <div className={`w-full bg-gray-100 rounded-full ${sizeClasses[size]} overflow-hidden`}>
        <div 
          className={`${sizeClasses[size]} ${variantColors[variant]} rounded-full transition-all duration-700 ease-out relative overflow-hidden`}
          style={{ width: `${percentage}%` }}
        >
          {animated && (
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -skew-x-12 animate-[shimmer_2s_infinite]" />
          )}
        </div>
      </div>
      
      {showLabel && (
        <div className="flex justify-between items-center mt-2 text-xs text-gray-600">
          <span className="font-medium">{Math.round(percentage)}%</span>
          <span className="text-gray-400">{value}/{max}</span>
        </div>
      )}
    </div>
  );
};

export default GradientProgressBar;