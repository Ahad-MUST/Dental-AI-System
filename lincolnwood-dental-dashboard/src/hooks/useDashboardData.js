import { useState, useEffect, useMemo } from 'react';
import googleSheetsService from '../services/GoogleSheetsService';
import { getGrade, getScoreColor } from '../utils/helpers';

export const useDashboardData = () => {
  const [data, setData] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [loading, setLoading] = useState(true);
  const [connectionStatus, setConnectionStatus] = useState('connecting');
  const [error, setError] = useState(null);
  const [processedCallIds, setProcessedCallIds] = useState(new Set());

  const dismissAlert = (id) => {
    setAlerts((prev) => prev.filter((alert) => alert.id !== id));
  };

  const clearAllAlerts = () => {
    setAlerts([]);
    // Clear the processed IDs so new alerts can appear
    setProcessedCallIds(new Set());
  };

  useEffect(() => {
    const initializeService = async () => {
      try {
        await googleSheetsService.requestNotificationPermission();
        const unsubscribe = googleSheetsService.subscribe((newData) => {
          setData(newData);
          setLastUpdate(googleSheetsService.getLastUpdate());
          setConnectionStatus('connected');
          setLoading(false);
          setError(null);
        });

        googleSheetsService.startPolling(
          parseInt(process.env.REACT_APP_REFRESH_INTERVAL) || 30000
        );

        return () => {
          unsubscribe();
          googleSheetsService.stopPolling();
        };
      } catch (err) {
        console.error("Failed to initialize Google Sheets service:", err);
        setError(err.message);
        setConnectionStatus("error");
        setLoading(false);
      }
    };

    initializeService();
  }, []);

  useEffect(() => {
    // Only process new high-value missed opportunities that haven't been processed
    const newHighValueMissed = data.filter(item => 
      item.High_Value_Missed_Opportunity && 
      item.Call_File_Name &&
      !processedCallIds.has(item.Call_File_Name)
    );

    if (newHighValueMissed.length > 0) {
      const newAlerts = newHighValueMissed.map(alert => ({
        ...alert,
        timestamp: new Date(),
        id: `alert-${alert.Call_File_Name}-${Date.now()}`
      }));

      setAlerts(prev => [...prev, ...newAlerts]);
      
      // Track these call IDs as processed
      setProcessedCallIds(prev => {
        const newSet = new Set(prev);
        newHighValueMissed.forEach(item => {
          if (item.Call_File_Name) {
            newSet.add(item.Call_File_Name);
          }
        });
        return newSet;
      });
    }
  }, [data, processedCallIds]);

  const analytics = useMemo(() => {
    if (!data.length) return {
      weeklyData: [],
      repCallCounts: [],
      repAverages: [],
      performanceTrends: [],
      callTypes: [],
      todayStats: {
        totalCalls: 0,
        avgScore: 0,
        highValueMissed: 0,
        uniqueReps: 0
      },
      topPerformers: [],
      bottomPerformers: []
    };

    const weeklyData = googleSheetsService.getWeeklyData();
    const todayData = googleSheetsService.getTodayData();

    // Call counts
    const repCallCounts = weeklyData.reduce((acc, item) => {
      const name = item.Representative_Name || "Unknown";
      acc[name] = (acc[name] || 0) + 1;
      return acc;
    }, {});

    const repCallCountsArray = Object.entries(repCallCounts)
      .map(([name, count]) => ({
        name,
        calls: count,
        color: name === "Unknown" ? "#ef4444" : "#3b82f6",
      }))
      .sort((a, b) => b.calls - a.calls);

    // Rep averages
    const repScores = weeklyData.reduce((acc, item) => {
      const name = item.Representative_Name || "Unknown";
      if (!acc[name]) acc[name] = [];
      if (item.Representative_Score) acc[name].push(item.Representative_Score);
      return acc;
    }, {});

    const repAverages = Object.entries(repScores)
      .map(([name, scores]) => {
        const avg = scores.length > 0 ? scores.reduce((sum, s) => sum + s, 0) / scores.length : 0;
        return {
          name,
          averageScore: avg,
          callCount: repCallCounts[name] || 0,
          grade: getGrade(avg),
          color: getScoreColor(avg),
        };
      })
      .sort((a, b) => b.averageScore - a.averageScore);

    // Trends
    const dailyPerformance = weeklyData.reduce((acc, item) => {
      const date = item.Analysis_Date;
      if (!acc[date]) acc[date] = { scores: [], date, callCount: 0 };
      if (item.Representative_Score) acc[date].scores.push(item.Representative_Score);
      acc[date].callCount++;
      return acc;
    }, {});

    const performanceTrends = Object.values(dailyPerformance)
      .map((day) => ({
        date: day.date,
        averageScore: day.scores.length > 0 ? day.scores.reduce((s, v) => s + v, 0) / day.scores.length : 0,
        callCount: day.callCount,
      }))
      .sort((a, b) => new Date(a.date) - new Date(b.date));

    // Call types
    const callTypes = weeklyData.reduce((acc, item) => {
      const summary = (item.Call_Summary || "").toLowerCase();
      let type = "General Inquiry";
      if (/appointment|booking|schedule/.test(summary)) type = "Appointment Booking";
      else if (/emergency|pain|urgent/.test(summary)) type = "Emergency";
      else if (/insurance|verification|coverage/.test(summary)) type = "Insurance Inquiry";
      else if (/reschedule|confirm/.test(summary)) type = "Appointment Management";
      acc[type] = (acc[type] || 0) + 1;
      return acc;
    }, {});

    const callTypesArray = Object.entries(callTypes).map(([type, count]) => ({
      type,
      count,
      percentage: weeklyData.length > 0 ? ((count / weeklyData.length) * 100).toFixed(1) : '0.0',
    }));

    // Today stats
    const todayStats = {
      totalCalls: todayData.length,
      avgScore: todayData.length > 0 ? todayData.reduce((s, i) => s + (i.Representative_Score || 0), 0) / todayData.length : 0,
      highValueMissed: todayData.filter((i) => i.High_Value_Missed_Opportunity).length,
      uniqueReps: new Set(todayData.map((i) => i.Representative_Name || "Unknown")).size,
    };

    return {
      weeklyData,
      repCallCounts: repCallCountsArray,
      repAverages,
      performanceTrends,
      callTypes: callTypesArray,
      todayStats,
      topPerformers: repAverages.slice(0, 3),
      bottomPerformers: repAverages.slice(-3).reverse(),
    };
  }, [data]);

  return {
    data,
    alerts,
    lastUpdate,
    loading,
    connectionStatus,
    error,
    analytics,
    dismissAlert,
    clearAllAlerts
  };
};