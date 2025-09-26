import React from 'react';
import CallVolumeChart from '../charts/CallVolumeChart';
import PerformanceScoresChart from '../charts/PerformanceScoresChart';
import PerformanceTrendsChart from '../charts/PerformanceTrendsChart';
import SentimentAnalysisChart from '../charts/SentimentAnalysisChart';
import EmotionAnalyticsChart from '../charts/EmotionAnalyticsChart';
import CallTagsChart from '../charts/CallTagsChart';

const ChartsSection = ({ 
  analytics, 
  rawData, 
  getCallsBySentiment, 
  getCallsByEmotion, 
  getCallsByEmotionFlag, 
  getCallsByTag,
  showOnlySentiment = false,
  showOnlyEmotion = false,
  showOnlyCallTags = false,
  showOnlyCallVolume = false,
  showOnlyPerformanceScores = false,
  showOnlyPerformanceTrends = false
}) => {
  
  // Debug logging to see what data we have
  console.log('ChartsSection analytics.emotionAnalytics:', analytics.emotionAnalytics);
  console.log('ChartsSection analytics.callTagAnalytics:', analytics.callTagAnalytics);
  
  // Return only sentiment analysis if requested
  if (showOnlySentiment) {
    return (
      <SentimentAnalysisChart 
        sentimentAnalytics={analytics.sentimentAnalytics}
        sentimentOpportunityCorrelation={analytics.sentimentOpportunityCorrelation}
        getCallsBySentiment={getCallsBySentiment}
      />
    );
  }

  // Return only emotion analytics if requested
  if (showOnlyEmotion) {
    return (
      <EmotionAnalyticsChart 
        emotionAnalytics={analytics.emotionAnalytics}
        getCallsByEmotion={getCallsByEmotion}
        getCallsByEmotionFlag={getCallsByEmotionFlag}
      />
    );
  }

  // Return only call tags if requested
  if (showOnlyCallTags) {
    return (
      <CallTagsChart 
        rawData={rawData}
        getCallsByTag={getCallsByTag}
      />
    );
  }

  // Return only call volume if requested
  if (showOnlyCallVolume) {
    return (
      <CallVolumeChart 
        data={analytics.repCallCounts} 
        rawData={rawData}
      />
    );
  }

  // Return only performance scores if requested
  if (showOnlyPerformanceScores) {
    return (
      <PerformanceScoresChart 
        data={analytics.repAverages} 
        rawData={rawData} 
      />
    );
  }

  // Return only performance trends if requested
  if (showOnlyPerformanceTrends) {
    return (
      <PerformanceTrendsChart 
        data={analytics.performanceTrends} 
        rawData={rawData}
      />
    );
  }
  
  // Default: return all charts in original structure
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
        
        {/* Performance Trends - Now with rawData and enhanced functionality */}
        <div>
          <PerformanceTrendsChart 
            data={analytics.performanceTrends} 
            rawData={rawData}
          />
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