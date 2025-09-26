import React from 'react';
import TopPerformers from '../performance/TopPerformers';
// Removed: import CoachingOpportunities from '../performance/CoachingOpportunities';

const PerformanceSection = ({ analytics, rawData }) => {
  // Debug logging to see what we're working with
  console.log('PerformanceSection analytics:', analytics);
  console.log('PerformanceSection rawData:', rawData);
  
  return (
    <div className="w-full">
      {/* Top Performers - Now takes full available width */}
      <TopPerformers 
        data={analytics.topPerformers} 
        rawData={rawData} 
      />
    </div>
  );
};

export default PerformanceSection;