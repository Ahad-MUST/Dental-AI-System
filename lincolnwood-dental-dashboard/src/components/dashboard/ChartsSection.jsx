import React from 'react';
import CallVolumeChart from '../charts/CallVolumeChart';
import PerformanceScoresChart from '../charts/PerformanceScoresChart';
import PerformanceTrendsChart from '../charts/PerformanceTrendsChart';
import SentimentAnalysisChart from '../charts/SentimentAnalysisChart';
import EmotionAnalyticsChart from '../charts/EmotionAnalyticsChart';
import CallTagsChart from '../charts/CallTagsChart';

const ChartsSection = ({ analytics, rawData, getCallsBySentiment, getCallsByEmotion, getCallsByEmotionFlag, getCallsByTag }) => {
  
  // Debug logging to see what data we have
  console.log('ChartsSection analytics.emotionAnalytics:', analytics.emotionAnalytics);
  console.log('ChartsSection analytics.callTagAnalytics:', analytics.callTagAnalytics);
  
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
        
        {/* Call Tags Chart - Takes up 1 column (replaced Call Distribution) */}
        <div className="xl:col-span-1">
          <CallTagsChart 
            rawData={rawData}
            getCallsByTag={getCallsByTag}
          />
        </div>
      </div>

      {/* Secondary Charts Row */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
        {/* Performance Scores - Takes up full width on smaller screens, half on xl */}
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

      {/* Third Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">        
        {/* Sentiment Analysis */}
        <div>
          <SentimentAnalysisChart 
            sentimentAnalytics={analytics.sentimentAnalytics}
            sentimentOpportunityCorrelation={analytics.sentimentOpportunityCorrelation}
            getCallsBySentiment={getCallsBySentiment}
          />
        </div>
        
        {/* Emotion Analytics Chart */}
        <div>
          <EmotionAnalyticsChart 
            emotionAnalytics={analytics.emotionAnalytics}
            getCallsByEmotion={getCallsByEmotion}
            getCallsByEmotionFlag={getCallsByEmotionFlag}
          />
        </div>
      </div>
    </div>
  );
};

export default ChartsSection;