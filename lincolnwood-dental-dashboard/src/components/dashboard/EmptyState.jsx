import React from 'react';
import { BarChart3 } from 'lucide-react';
import Header from './Header';
import Card from '../common/Card';

const EmptyState = ({ connectionStatus, lastUpdate }) => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <Header 
        connectionStatus={connectionStatus} 
        lastUpdate={lastUpdate} 
        alertsCount={0} 
        alerts={[]}
        onClearAllAlerts={() => {}}
        onDismissAlert={() => {}}
      />

      <div className="flex items-center justify-center min-h-[70vh] p-4">
        <Card className="text-center max-w-md w-full" padding="xl">
          <div className="w-32 h-32 flex items-center justify-center mx-auto mb-6 overflow-hidden">
            <img 
              src="/logo.png" 
              alt="Lincolnwood Family Dental Logo" 
              className="w-full h-full object-contain"
              onError={(e) => {
                // Fallback to icon if logo fails to load
                e.target.style.display = 'none';
                e.target.nextSibling.style.display = 'flex';
              }}
            />
            <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl items-center justify-center shadow-lg hidden">
              <BarChart3 className="h-10 w-10 text-white" strokeWidth={2} />
            </div>
          </div>
          
          <h2 className="text-2xl font-bold text-slate-900 mb-3">
            Waiting for Data
          </h2>
          
          <p className="text-slate-600 mb-6 leading-relaxed">
            Your dashboard is ready and waiting for call analysis data to populate the analytics.
          </p>
          
          <div className="flex justify-center space-x-2 mb-4">
            {[0, 1, 2].map((i) => (
              <div 
                key={i}
                className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"
                style={{ animationDelay: `${i * 0.2}s` }}
              />
            ))}
          </div>
          
          <p className="text-xs text-slate-500">
            Data will appear automatically once calls are processed
          </p>
        </Card>
      </div>
    </div>
  );
};

export default EmptyState;