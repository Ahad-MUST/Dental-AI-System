import React from 'react';
import { AlertTriangle, Loader2 } from 'lucide-react';

const LoadingSpinner = ({ 
  message = "Loading...", 
  isError = false, 
  errorMessage = "",
  size = "lg" 
}) => {
  const sizeClasses = {
    sm: "h-6 w-6",
    md: "h-12 w-12", 
    lg: "h-16 w-16",
    xl: "h-24 w-24"
  };

  if (isError) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-4">
        <div className="text-center bg-white rounded-2xl shadow-xl p-8 max-w-md w-full border border-slate-200">
          <div className="w-16 h-16 bg-red-50 rounded-full flex items-center justify-center mx-auto mb-6">
            <AlertTriangle className="h-8 w-8 text-red-500" />
          </div>
          <h2 className="text-xl font-semibold text-slate-900 mb-3">Connection Error</h2>
          <p className="text-slate-600 mb-4 leading-relaxed">{errorMessage}</p>
          <p className="text-sm text-slate-500">Please check your configuration and try again.</p>
          <button 
            onClick={() => window.location.reload()} 
            className="mt-6 px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg text-sm font-medium transition-colors duration-200"
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-4">
      <div className="text-center">
        <div className="relative mb-8">
          <Loader2 className={`${sizeClasses[size]} text-blue-500 animate-spin mx-auto`} />
          <div className="absolute inset-0 rounded-full border-4 border-blue-100 opacity-25" />
        </div>
        
        <h2 className="text-xl font-semibold text-slate-700 mb-3">{message}</h2>
        
        <div className="flex justify-center space-x-1">
          {[0, 1, 2].map((i) => (
            <div 
              key={i}
              className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"
              style={{ animationDelay: `${i * 0.2}s` }}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

export default LoadingSpinner;