// useDashboardData.js - FINAL VERSION with AlertsManager Integration
import { useState, useEffect, useMemo } from 'react';
import googleSheetsService from '../services/GoogleSheetsService';
import { 
  alertsManager, 
  loadDismissedAlerts, 
  filterTodayAlerts, 
  createAlertObjects, 
  dismissAlert as dismissAlertUtil, 
  dismissAllAlerts as dismissAllAlertsUtil,
  checkAndResetForNewDay
} from '../utils/AlertsManager';

export const useDashboardData = () => {
  const [data, setData] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [loading, setLoading] = useState(true);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [error, setError] = useState(null);
  const [dismissedAlerts, setDismissedAlerts] = useState(new Set());

  // Load dismissed alerts and check for new day on component mount
  useEffect(() => {
    const hasReset = checkAndResetForNewDay();
    const dismissed = loadDismissedAlerts();
    setDismissedAlerts(dismissed);
    
    if (hasReset) {
      console.log('🌅 New day detected - alerts reset');
    }
  }, []);

  // MOVED: Complete emotion analytics helper function BEFORE useMemo
  const getEmotionAnalyticsData = (data) => {
    console.log('🔍 Processing emotion analytics for', data.length, 'calls');
    
    // Filter out 'neutral' and empty values, not 'unknown'
    const emotionData = data.filter(item => {
      const hasEmotion = item.Patient_Primary_Emotion && 
                        item.Patient_Primary_Emotion !== 'neutral' && 
                        item.Patient_Primary_Emotion !== '' &&
                        item.Patient_Primary_Emotion !== 'unknown';
      
      if (hasEmotion) {
        console.log(`✅ Found emotion: ${item.Patient_Primary_Emotion} in call ${item.Call_File_Name}`);
      }
      
      return hasEmotion;
    });

    console.log(`📊 Filtered emotion data: ${emotionData.length} calls with emotions out of ${data.length} total`);

    // Patient emotions distribution
    const patientEmotions = emotionData.reduce((acc, item) => {
      const emotion = item.Patient_Primary_Emotion;
      acc[emotion] = (acc[emotion] || 0) + 1;
      return acc;
    }, {});

    console.log('🎭 Patient emotions distribution:', patientEmotions);

    // Emotion intensity distribution - handle all values properly
    const emotionIntensity = data.reduce((acc, item) => {
      if (item.Patient_Emotion_Intensity && 
          item.Patient_Emotion_Intensity !== '' && 
          item.Patient_Emotion_Intensity !== 'unknown') {
        const intensity = item.Patient_Emotion_Intensity;
        acc[intensity] = (acc[intensity] || 0) + 1;
      }
      return acc;
    }, { low: 0, medium: 0, high: 0 });

    console.log('📈 Emotion intensity distribution:', emotionIntensity);

    // Emotion flags analysis - handle 'None' properly
    const emotionFlags = data.reduce((acc, item) => {
      if (item.Emotion_Flags && 
          item.Emotion_Flags !== 'None' && 
          item.Emotion_Flags !== '' && 
          item.Emotion_Flags !== 'unknown') {
        const flags = item.Emotion_Flags.split(', ').filter(flag => flag.trim() !== '');
        flags.forEach(flag => {
          const flagLower = flag.toLowerCase();
          if (flagLower.includes('pain')) acc.pain = (acc.pain || 0) + 1;
          if (flagLower.includes('anxiety')) acc.anxiety = (acc.anxiety || 0) + 1;
          if (flagLower.includes('satisfaction')) acc.satisfaction = (acc.satisfaction || 0) + 1;
          if (flagLower.includes('frustration')) acc.frustration = (acc.frustration || 0) + 1;
          if (flagLower.includes('urgent')) acc.urgency = (acc.urgency || 0) + 1;
        });
      }
      return acc;
    }, {});

    console.log('🚨 Emotion flags distribution:', emotionFlags);

    // Call emotional health distribution
    const callHealth = data.reduce((acc, item) => {
      if (item.Call_Emotional_Health && 
          item.Call_Emotional_Health !== '' && 
          item.Call_Emotional_Health !== 'unknown') {
        const health = item.Call_Emotional_Health;
        acc[health] = (acc[health] || 0) + 1;
      }
      return acc;
    }, { good: 0, fair: 0, poor: 0 });

    console.log('💚 Call health distribution:', callHealth);

    // Daily emotion trends
    const dailyEmotions = data.reduce((acc, item) => {
      const date = item.Analysis_Date;
      if (!acc[date]) {
        acc[date] = { 
          date, 
          highIntensity: 0, 
          pain: 0, 
          anxiety: 0, 
          satisfaction: 0, 
          total: 0 
        };
      }

      if (item.Patient_Emotion_Intensity === 'high') {
        acc[date].highIntensity++;
      }

      if (item.Emotion_Flags && item.Emotion_Flags !== 'None' && item.Emotion_Flags !== '') {
        const flags = item.Emotion_Flags.split(', ');
        flags.forEach(flag => {
          const flagLower = flag.toLowerCase();
          if (flagLower.includes('pain')) acc[date].pain++;
          if (flagLower.includes('anxiety')) acc[date].anxiety++;
          if (flagLower.includes('satisfaction')) acc[date].satisfaction++;
        });
      }

      acc[date].total++;
      return acc;
    }, {});

    const trends = Object.values(dailyEmotions)
      .map(day => ({
        date: day.date,
        highIntensityRatio: day.total > 0 ? (day.highIntensity / day.total) : 0,
        painRatio: day.total > 0 ? (day.pain / day.total) : 0,
        anxietyRatio: day.total > 0 ? (day.anxiety / day.total) : 0,
        satisfactionRatio: day.total > 0 ? (day.satisfaction / day.total) : 0,
        totalCalls: day.total
      }))
      .sort((a, b) => new Date(a.date) - new Date(b.date));

    console.log('📊 Emotion analytics completed');

    return {
      patientEmotions,
      emotionIntensity,
      emotionFlags,
      callHealth,
      trends
    };
  };

  // Load data from Google Sheets
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        setError(null);
        setConnectionStatus('connecting');
        
        const sheetsData = await googleSheetsService.fetchData();
        
        if (sheetsData && sheetsData.length > 0) {
          setData(sheetsData);
          setConnectionStatus('connected');
          setLastUpdate(new Date());
          console.log(`✅ Loaded ${sheetsData.length} calls from Google Sheets`);
          
          // Debug: Log sample data
          const sampleData = sheetsData.slice(0, 3).map(item => ({
            call: item.Call_File_Name,
            date: item.Analysis_Date,
            emotion: item.Patient_Primary_Emotion,
            intensity: item.Patient_Emotion_Intensity,
            flags: item.Emotion_Flags,
            health: item.Call_Emotional_Health,
            callTag: item.Call_Tag,
            coachingCandidate: item.Coaching_Candidate,
            highValueMissed: item.High_Value_Missed_Opportunity
          }));
          console.log('📊 Sample data loaded:', sampleData);
          
        } else {
          setConnectionStatus('disconnected');
          setError('No data available in Google Sheets');
        }
      } catch (err) {
        console.error('❌ Failed to load data:', err);
        setError(`Failed to connect: ${err.message}`);
        setConnectionStatus('error');
      } finally {
        setLoading(false);
      }
    };

    loadData();
    
    // Refresh data every 5 minutes
    const interval = setInterval(loadData, process.env.REACT_APP_REFRESH_INTERVAL);
    return () => clearInterval(interval);
  }, []);

  // ENHANCED: Alert monitoring effect - Only show TODAY's alerts using AlertsManager
  useEffect(() => {
    // Check for new day first
    const hasReset = checkAndResetForNewDay();
    if (hasReset) {
      setDismissedAlerts(new Set());
    }
    
    // Filter for today's undismissed alerts
    const todayFilteredAlerts = filterTodayAlerts(data, dismissedAlerts);
    
    console.log(`🔔 Alert update: ${todayFilteredAlerts.length} active today's alerts (${dismissedAlerts.size} dismissed)`);
    
    if (todayFilteredAlerts.length > 0) {
      const alertObjects = createAlertObjects(todayFilteredAlerts);
      setAlerts(alertObjects);
      console.log('🚨 Updated alerts with today\'s undismissed high-value opportunities:', alertObjects);
    } else {
      setAlerts([]); // Clear alerts if none for today or all dismissed
    }
  }, [data, dismissedAlerts]);

  // ENHANCED: Alert management functions using AlertsManager
  const dismissAlert = (alertId) => {
    const newDismissedSet = dismissAlertUtil(alertId, alerts, dismissedAlerts);
    setDismissedAlerts(newDismissedSet);
    
    // Remove from current alerts display
    setAlerts(prev => prev.filter(alert => alert.id !== alertId));
  };

  const clearAllAlerts = () => {
    const newDismissedSet = dismissAllAlertsUtil(alerts, dismissedAlerts);
    setDismissedAlerts(newDismissedSet);
    
    // Clear current alerts display
    setAlerts([]);
  };

  // Get today's date string
  const getTodayString = () => {
    return alertsManager.getTodayString();
  };

  // Complete analytics calculation
  const analytics = useMemo(() => {
    if (!data.length) {
      return {
        todayStats: { 
          totalCalls: 0, 
          avgScore: 0, 
          highValueOpps: 0, 
          sentimentPositive: 0,
          highEmotionCalls: 0,
          painDetected: 0,
          anxietyDetected: 0,
          satisfactionDetected: 0
        },
        repCallCounts: [],
        repAverages: [],
        performanceTrends: [],
        callTypes: {},
        sentimentAnalytics: { overall: {}, patient: {}, staff: {}, trends: [] },
        emotionAnalytics: { patientEmotions: {}, emotionIntensity: {}, emotionFlags: {}, callHealth: {}, trends: [] },
        callTagAnalytics: { overall: {}, trends: [] },
        sentimentOpportunityCorrelation: {},
        topPerformers: [],
        bottomPerformers: []
      };
    }

    console.log('🔄 Calculating complete analytics...');

    // TODAY'S comprehensive stats calculation
    const todayStr = getTodayString();
    const todayData = data.filter(item => item.Analysis_Date === todayStr);

    console.log(`📅 Today (${todayStr}): ${todayData.length} calls`);

    // Calculate sentiment scores for today
    const sentimentScores = todayData
      .filter(item => item.Representative_Score && !isNaN(parseFloat(item.Representative_Score)))
      .map(item => parseFloat(item.Representative_Score));

    const avgSentimentScore = sentimentScores.length > 0 ? 
      sentimentScores.reduce((sum, score) => sum + score, 0) / sentimentScores.length : 0.5;

    // Calculate emotion metrics for today
    const highEmotionCalls = todayData.filter(item => 
      item.Patient_Emotion_Intensity === 'high'
    ).length;

    const painDetected = todayData.filter(item => 
      item.Emotion_Flags && item.Emotion_Flags !== 'None' && item.Emotion_Flags.toLowerCase().includes('pain')
    ).length;

    const anxietyDetected = todayData.filter(item => 
      item.Emotion_Flags && item.Emotion_Flags !== 'None' && item.Emotion_Flags.toLowerCase().includes('anxiety')
    ).length;

    const satisfactionDetected = todayData.filter(item => 
      item.Emotion_Flags && item.Emotion_Flags !== 'None' && item.Emotion_Flags.toLowerCase().includes('satisfaction')
    ).length;

    const todayStats = {
      totalCalls: todayData.length,
      avgScore: todayData.length > 0 ? 
        todayData.reduce((sum, item) => sum + (parseFloat(item.Representative_Score) || 0), 0) / todayData.length : 0,
      highValueOpps: todayData.filter(item => item.High_Value_Missed_Opportunity).length,
      sentimentPositive: todayData.filter(item => item.Overall_Sentiment === 'positive').length,
      avgSentimentScore: avgSentimentScore,
      highEmotionCalls: highEmotionCalls,
      painDetected: painDetected,
      anxietyDetected: anxietyDetected,
      satisfactionDetected: satisfactionDetected
    };

    console.log('📊 Today\'s stats calculated:', todayStats);

    // Representative call counts
    const repCallCounts = data.reduce((acc, item) => {
      const rep = item.Representative_Name || 'Unknown';
      acc[rep] = (acc[rep] || 0) + 1;
      return acc;
    }, {});

    const repCountsArray = Object.entries(repCallCounts).map(([name, calls]) => ({
      name: name === 'Unknown' ? 'Not Specified' : name,
      calls
    }));

    // Representative averages with proper grade calculation
    const getGrade = (score) => {
      if (score >= 0.9) return "A";
      if (score >= 0.75) return "B";
      if (score >= 0.6) return "C";
      if (score > 0) return "D";
      return "F";
    };

    const repScores = data.reduce((acc, item) => {
      const rep = item.Representative_Name || 'Unknown';
      const score = parseFloat(item.Representative_Score) || 0;
      
      if (!acc[rep]) {
        acc[rep] = { scores: [], total: 0 };
      }
      
      if (score > 0) {
        acc[rep].scores.push(score);
      }
      acc[rep].total++;
      
      return acc;
    }, {});

    const repAverages = Object.entries(repScores).map(([name, data]) => ({
      name: name === 'Unknown' ? 'Not Specified' : name,
      averageScore: data.scores.length > 0 ? 
        data.scores.reduce((sum, score) => sum + score, 0) / data.scores.length : 0,
      totalCalls: data.total,
      validScores: data.scores.length,
      callCount: data.total,
      grade: getGrade(data.scores.length > 0 ? 
        data.scores.reduce((sum, score) => sum + score, 0) / data.scores.length : 0)
    }));

    // Create top and bottom performers from repAverages
    const validPerformers = repAverages.filter(rep => 
      rep.name !== 'Not Specified' && 
      rep.validScores > 0 && 
      rep.averageScore > 0
    ).sort((a, b) => b.averageScore - a.averageScore);

    const topPerformers = validPerformers.slice(0, 3);
    const bottomPerformers = validPerformers.slice(-3).reverse();

    console.log('🏆 Top performers:', topPerformers);
    console.log('📈 Bottom performers for coaching:', bottomPerformers);

    // Complete daily performance trends calculation
    const dailyPerformance = data.reduce((acc, item) => {
      const date = item.Analysis_Date;
      if (!acc[date]) {
        acc[date] = { 
          date, 
          scores: [], 
          sentiments: [], 
          callCount: 0, 
          emotions: [], 
          emotionIntensities: [], 
          emotionFlags: [],
          callTags: []
        };
      }
      
      const score = parseFloat(item.Representative_Score);
      if (!isNaN(score) && score > 0) {
        acc[date].scores.push(score);
      }
      
      if (item.Overall_Sentiment && 
          item.Overall_Sentiment !== 'unknown' && 
          item.Overall_Sentiment !== '') {
        acc[date].sentiments.push(item.Overall_Sentiment);
      }
      
      // Collect daily emotion data properly
      if (item.Patient_Primary_Emotion && 
          item.Patient_Primary_Emotion !== 'unknown' && 
          item.Patient_Primary_Emotion !== 'neutral' && 
          item.Patient_Primary_Emotion !== '') {
        acc[date].emotions.push(item.Patient_Primary_Emotion);
      }
      if (item.Patient_Emotion_Intensity && 
          item.Patient_Emotion_Intensity !== 'unknown' && 
          item.Patient_Emotion_Intensity !== '') {
        acc[date].emotionIntensities.push(item.Patient_Emotion_Intensity);
      }
      if (item.Emotion_Flags && 
          item.Emotion_Flags !== 'None' && 
          item.Emotion_Flags !== '' && 
          item.Emotion_Flags !== 'unknown') {
        acc[date].emotionFlags.push(...item.Emotion_Flags.split(', ').filter(f => f.trim()));
      }
      
      // Collect daily call tag data
      if (item.Call_Tag && 
          item.Call_Tag !== '' && 
          item.Call_Tag !== 'unknown') {
        acc[date].callTags.push(item.Call_Tag);
      }
      
      acc[date].callCount++;
      return acc;
    }, {});

    const performanceTrends = Object.values(dailyPerformance)
      .map((day) => {
        const avgScore = day.scores.length > 0 ? 
          day.scores.reduce((sum, score) => sum + score, 0) / day.scores.length : 0;
        
        const sentimentCounts = day.sentiments.reduce((acc, sentiment) => {
          acc[sentiment] = (acc[sentiment] || 0) + 1;
          return acc;
        }, { positive: 0, neutral: 0, negative: 0 });

        const totalSentiments = day.sentiments.length;
        const positiveSentimentRatio = totalSentiments > 0 ? 
          (sentimentCounts.positive / totalSentiments) * 100 : 0;

        // Calculate emotion ratios
        const highIntensityCount = day.emotionIntensities.filter(i => i === 'high').length;
        const emotionIntensityRatio = day.emotionIntensities.length > 0 ?
          (highIntensityCount / day.emotionIntensities.length) * 100 : 0;

        return {
          date: day.date,
          averageScore: Math.round(avgScore * 100) / 100,
          callCount: day.callCount,
          positiveSentimentRatio: Math.round(positiveSentimentRatio * 100) / 100,
          emotionIntensityRatio: Math.round(emotionIntensityRatio * 100) / 100,
          totalSentiments: totalSentiments,
          validScores: day.scores.length
        };
      })
      .filter(day => day.callCount > 0)
      .sort((a, b) => new Date(a.date) - new Date(b.date));

    // Call types analysis (keeping original logic)
    const callTypes = data.reduce((acc, item) => {
      const summary = (item.Call_Summary || "").toLowerCase();
      let type = "General Inquiry";
      if (/appointment|booking|schedule/.test(summary)) type = "Appointment Booking";
      else if (/emergency|pain|urgent/.test(summary)) type = "Emergency";
      else if (/insurance|verification|coverage/.test(summary)) type = "Insurance Inquiry";
      else if (/reschedule|confirm/.test(summary)) type = "Appointment Management";
      acc[type] = (acc[type] || 0) + 1;
      return acc;
    }, {});

    // Get analytics from Google Sheets service
    const sentimentAnalytics = googleSheetsService.getSentimentAnalytics();
    const emotionAnalytics = getEmotionAnalyticsData(data);
    const callTagAnalytics = googleSheetsService.getCallTagAnalytics();
    const sentimentOpportunityCorrelation = googleSheetsService.getSentimentOpportunityCorrelation();

    console.log('📊 Complete analytics calculated successfully');

    return {
      todayStats,
      repCallCounts: repCountsArray,
      repAverages,
      performanceTrends,
      callTypes,
      sentimentAnalytics,
      emotionAnalytics,
      callTagAnalytics,
      sentimentOpportunityCorrelation,
      topPerformers,
      bottomPerformers
    };
  }, [data, getEmotionAnalyticsData, getTodayString]);

  // All data access functions
  const getCallsBySentiment = (sentimentType, speakerType = 'overall') => {
    return googleSheetsService.getCallsBySentiment(sentimentType, speakerType);
  };

  const getCallsByEmotion = (emotionType) => {
    if (!data.length) return [];
    
    return data.filter(item => 
      item.Patient_Primary_Emotion && 
      item.Patient_Primary_Emotion.toLowerCase() === emotionType.toLowerCase()
    );
  };

  const getCallsByEmotionFlag = (flagType) => {
    if (!data.length) return [];
    
    return data.filter(item => 
      item.Emotion_Flags && 
      item.Emotion_Flags.toLowerCase().includes(flagType.toLowerCase())
    );
  };

  const getCallsByTag = (tagType) => {
    return googleSheetsService.getCallsByTag(tagType);
  };

  // Return all functionality with enhanced today-only alerts
  return {
    data,
    alerts, // TODAY-ONLY alerts with proper session persistence
    lastUpdate,
    loading,
    connectionStatus,
    error,
    analytics,
    dismissAlert, // Enhanced with AlertsManager
    clearAllAlerts, // Enhanced with AlertsManager
    getCallsBySentiment,
    getCallsByEmotion,
    getCallsByEmotionFlag,
    getCallsByTag,
    // Additional utility functions
    getTodayString,
    dismissedAlertsCount: dismissedAlerts.size
  };
};