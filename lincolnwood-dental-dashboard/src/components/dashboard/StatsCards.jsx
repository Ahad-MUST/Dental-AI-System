import React from 'react';
import { Phone, TrendingUp, AlertTriangle, Heart, Brain, CalendarDays } from 'lucide-react';

const StatsCards = ({ todayStats }) => {
  const {
    totalCalls = 0,
    avgScore = 0,
    highValueOpps = 0,
    avgSentimentScore = 0.5,
    negativeCallsCount = 0,
    // Emotion metrics
    painDetected = 0,
    anxietyDetected = 0
  } = todayStats;

  // Helper function to get score color
  const getScoreColor = (score, thresholds = { good: 0.8, fair: 0.6 }) => {
    if (score >= thresholds.good) return 'text-emerald-600';
    if (score >= thresholds.fair) return 'text-amber-600';
    return 'text-red-600';
  };

  // Helper function to get sentiment color
  const getSentimentColor = (score) => {
    if (score >= 0.7) return 'text-emerald-600';
    if (score >= 0.4) return 'text-amber-600';
    return 'text-red-600';
  };

  // Calculate emotion health percentage
  const emotionHealthScore = totalCalls > 0 ? 
    ((totalCalls - painDetected - anxietyDetected) / totalCalls) : 1;

  // Get today's date for display
  const getTodayDisplay = () => {
    const today = new Date();
    return today.toLocaleDateString('en-US', { 
      weekday: 'long',
      month: 'long', 
      day: 'numeric'
    });
  };

  const statsData = [
    {
      title: 'Total Calls',
      value: totalCalls,
      icon: Phone,
      iconColor: 'text-blue-600',
      bgColor: 'bg-blue-50',
      borderColor: 'border-blue-200',
      description: 'Calls analyzed today',
      trend: null
    },
    {
      title: 'Avg Performance',
      value: `${(avgScore * 100).toFixed(1)}%`,
      icon: TrendingUp,
      iconColor: getScoreColor(avgScore),
      bgColor: avgScore >= 0.8 ? 'bg-emerald-50' : avgScore >= 0.6 ? 'bg-amber-50' : 'bg-red-50',
      borderColor: avgScore >= 0.8 ? 'border-emerald-200' : avgScore >= 0.6 ? 'border-amber-200' : 'border-red-200',
      description: 'Representative performance',
      trend: avgScore >= 0.8 ? '✅' : avgScore >= 0.6 ? '~' : '📉'
    },
    {
      title: 'Missed Opportunities',
      value: highValueOpps,
      icon: AlertTriangle,
      iconColor: highValueOpps > 0 ? 'text-red-600' : 'text-emerald-600',
      bgColor: highValueOpps > 0 ? 'bg-red-50' : 'bg-emerald-50',
      borderColor: highValueOpps > 0 ? 'border-red-200' : 'border-emerald-200',
      description: 'High-value opportunities',
      trend: highValueOpps > 0 ? '⚠️' : '😐'
    },
    {
      title: 'Sentiment Health',
      value: `${(avgSentimentScore * 100).toFixed(0)}%`,
      icon: Heart,
      iconColor: getSentimentColor(avgSentimentScore),
      bgColor: avgSentimentScore >= 0.7 ? 'bg-emerald-50' : avgSentimentScore >= 0.4 ? 'bg-amber-50' : 'bg-red-50',
      borderColor: avgSentimentScore >= 0.7 ? 'border-emerald-200' : avgSentimentScore >= 0.4 ? 'border-amber-200' : 'border-red-200',
      description: 'Overall sentiment score',
      trend: avgSentimentScore >= 0.7 ? '💚' : avgSentimentScore >= 0.4 ? '😐' : '😟',
      subtitle: negativeCallsCount > 0 ? `${negativeCallsCount} negative calls` : 'No negative calls'
    },
    {
      title: 'Emotion Health',
      value: `${(emotionHealthScore * 100).toFixed(0)}%`,
      icon: Brain,
      iconColor: emotionHealthScore >= 0.8 ? 'text-emerald-600' : emotionHealthScore >= 0.6 ? 'text-amber-600' : 'text-red-600',
      bgColor: emotionHealthScore >= 0.8 ? 'bg-emerald-50' : emotionHealthScore >= 0.6 ? 'bg-amber-50' : 'bg-red-50',
      borderColor: emotionHealthScore >= 0.8 ? 'border-emerald-200' : emotionHealthScore >= 0.6 ? 'border-amber-200' : 'border-red-200',
      description: 'Emotional wellness score',
      trend: emotionHealthScore >= 0.8 ? '💚' : emotionHealthScore >= 0.6 ? '💛' : '❤️',
      subtitle: `${painDetected + anxietyDetected} distress signals`
    }
  ];

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200/60 p-8">
      {/* Daily Performance Heading */}
      <div className="flex items-center space-x-4 mb-8 group relative">
        <div className="bg-blue-50 rounded-xl p-3">
          <CalendarDays className="h-6 w-6 text-blue-600" strokeWidth={2} />
        </div>
        <div>
          <h2 className="text-2xl font-bold text-slate-900 mb-2">Daily Performance</h2>
          <p className="text-slate-600">
            {getTodayDisplay()} • Real-time metrics and health indicators
          </p>
        </div>

        {/* Tooltip */}
        <div className="absolute left-0 top-full mt-2 invisible group-hover:visible opacity-0 group-hover:opacity-100 transition-all duration-200 z-50">
          <div className="bg-slate-900 text-white text-sm rounded-lg p-3 shadow-lg w-80">
            <p className="font-medium mb-1">Daily Performance</p>
            <p className="text-slate-300 text-xs leading-relaxed">
              Monitor today's real-time performance metrics including call volume, representative scores, 
              missed opportunities, and emotional health indicators for immediate insights.
            </p>
            <div className="absolute -top-1 left-4 w-2 h-2 bg-slate-900 rotate-45"></div>
          </div>
        </div>
      </div>

      {/* Stats Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-6">
        {statsData.map((stat, index) => {
          const Icon = stat.icon;
          
          return (
            <div key={index} className="group">
              <div className="bg-slate-50/50 border border-slate-200/60 rounded-xl p-6 hover:bg-white hover:shadow-md transition-all duration-200">
                <div className="flex items-center justify-between mb-4">
                  <div className={`${stat.bgColor} rounded-lg p-3 group-hover:scale-105 transition-transform duration-200 relative group/icon`}>
                    <Icon className={`h-5 w-5 ${stat.iconColor}`} strokeWidth={2} />
                    
                    {/* Icon Tooltip */}
                    <div className="absolute left-0 top-full mt-2 invisible group-hover/icon:visible opacity-0 group-hover/icon:opacity-100 transition-all duration-200 z-50">
                      <div className="bg-slate-900 text-white text-xs rounded-lg p-3 shadow-lg w-64">
                        <p className="leading-relaxed">
                          {index === 0 && "Total number of calls processed today"}
                          {index === 1 && "Average performance score of all representatives today"}
                          {index === 2 && "Missed high-value business opportunities requiring follow-up"}
                          {index === 3 && "Overall emotional tone and satisfaction level of calls"}
                          {index === 4 && "Patient emotional wellness - tracks distress signals like pain/anxiety"}
                        </p>
                        <div className="absolute -top-1 left-4 w-2 h-2 bg-slate-900 rotate-45"></div>
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">{stat.title}</p>
                    <p className="text-xs text-slate-400">{stat.description}</p>
                  </div>
                </div>
                
                <div className="space-y-4">
                  <div className="flex items-baseline space-x-2">
                    <div className={`text-3xl font-bold ${stat.iconColor}`}>
                      {stat.value}
                    </div>
                    {stat.trend && (
                      <span className="text-lg">{stat.trend}</span>
                    )}
                  </div>
                  
                  {stat.subtitle && (
                    <p className="text-xs text-slate-400 leading-tight">
                      {stat.subtitle}
                    </p>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default StatsCards;