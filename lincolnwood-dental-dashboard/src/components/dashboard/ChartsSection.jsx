import React from 'react';
import CallVolumeChart from '../charts/CallVolumeChart';
import PerformanceScoresChart from '../charts/PerformanceScoresChart';
import PerformanceTrendsChart from '../charts/PerformanceTrendsChart';
import CallTypesChart from '../charts/CallTypesChart';

const ChartsSection = ({ analytics, rawData }) => {
  return (
    <div className="space-y-8">
      {/* Primary Charts Row */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        {/* Call Volume - Takes up 2 columns on xl screens */}
        <div className="xl:col-span-2">
          <CallVolumeChart 
            data={analytics.repCallCounts} 
            rawData={rawData}
          />
        </div>
        
        {/* Call Distribution - Takes up 1 column */}
        <div className="xl:col-span-1">
          <CallTypesChart data={analytics.callTypes} rawData={rawData} />
        </div>
      </div>

      {/* Secondary Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Performance Scores - Now with rawData */}
        <div>
          <PerformanceScoresChart 
            data={analytics.repAverages} 
            rawData={rawData} 
          />
        </div>
        
        {/* Performance Trends */}
        <div>
          <PerformanceTrendsChart data={analytics.performanceTrends} />
        </div>
      </div>
    </div>
  );
};

export default ChartsSection;