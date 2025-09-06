import React from 'react';
import TopPerformers from '../performance/TopPerformers';
import CoachingOpportunities from '../performance/CoachingOpportunities';

const PerformanceSection = ({ analytics, rawData }) => {
  // Debug logging to see what we're working with
  console.log('PerformanceSection analytics:', analytics);
  console.log('PerformanceSection rawData:', rawData);
  
  return (
    <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
      {/* Top Performers - Now with rawData */}
      <div>
        <TopPerformers 
          data={analytics.topPerformers} 
          rawData={rawData} 
        />
      </div>
      
      {/* Coaching Opportunities */}
      <div>
        <CoachingOpportunities data={analytics.bottomPerformers} />
      </div>
    </div>
  );
};

export default PerformanceSection;