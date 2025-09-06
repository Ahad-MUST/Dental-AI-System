import React from 'react';
import { Zap, X } from 'lucide-react';
import Card from '../common/Card';

const AlertsSection = ({ alerts, dismissAlert }) => {
  if (alerts.length === 0) return null;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
      <div className="space-y-3">
        {alerts.slice(-3).map((alert, index) => (
          <Card
            key={alert.id}
            className="border-l-4 border-l-red-500 bg-red-50/50 hover:bg-red-50/80 transition-colors"
            padding="md"
            style={{
              animation: `slideDown 0.4s ease-out ${index * 0.1}s both`
            }}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="bg-red-500 rounded-full p-2 animate-pulse shadow-md">
                  <Zap className="h-4 w-4 text-white" strokeWidth={2.5} />
                </div>
                <div>
                  <h4 className="text-red-900 font-semibold text-base">
                    High Value Opportunity Alert
                  </h4>
                  <p className="text-red-700 text-sm mt-1">
                    <span className="font-medium">Call:</span> {alert.Call_File_Name} • 
                    <span className="font-medium ml-2">Representative:</span> {alert.Representative_Name || 'Unknown'}
                  </p>
                </div>
              </div>
              
              <button
                onClick={() => dismissAlert(alert.id)}
                className="text-red-400 hover:text-red-600 hover:bg-red-100 rounded-full p-2 transition-all duration-200 group"
                aria-label="Dismiss alert"
              >
                <X className="h-4 w-4 group-hover:scale-110 transition-transform" />
              </button>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default AlertsSection;