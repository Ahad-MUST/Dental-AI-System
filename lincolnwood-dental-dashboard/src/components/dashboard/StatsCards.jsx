import React from 'react';
import { Phone, TrendingUp, AlertTriangle, Heart, Brain } from 'lucide-react';
import Card from '../common/Card';

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
      trend: avgScore >= 0.8 ? '+' : avgScore >= 0.6 ? '~' : '-'
    },
    {
      title: 'Missed Opportunities',
      value: highValueOpps,
      icon: AlertTriangle,
      iconColor: highValueOpps > 0 ? 'text-red-600' : 'text-emerald-600',
      bgColor: highValueOpps > 0 ? 'bg-red-50' : 'bg-emerald-50',
      borderColor: highValueOpps > 0 ? 'border-red-200' : 'border-emerald-200',
      description: 'High-value opportunities',
      trend: highValueOpps > 0 ? '⚠️' : '✅'
    },
    {
      title: 'Sentiment Health',
      value: `${(avgSentimentScore * 100).toFixed(0)}%`,
      icon: Heart,
      iconColor: getSentimentColor(avgSentimentScore),
      bgColor: avgSentimentScore >= 0.7 ? 'bg-emerald-50' : avgSentimentScore >= 0.4 ? 'bg-amber-50' : 'bg-red-50',
      borderColor: avgSentimentScore >= 0.7 ? 'border-emerald-200' : avgSentimentScore >= 0.4 ? 'border-amber-200' : 'border-red-200',
      description: 'Overall sentiment score',
      trend: avgSentimentScore >= 0.7 ? '😊' : avgSentimentScore >= 0.4 ? '😐' : '😟',
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
    <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-4">
      {statsData.map((stat, index) => {
        const Icon = stat.icon;
        
        return (
          <Card key={index} className="p-4 hover:shadow-md transition-shadow duration-200">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <div className={`p-2 rounded-lg ${stat.bgColor} border ${stat.borderColor}`}>
                    <Icon className={`w-4 h-4 ${stat.iconColor}`} />
                  </div>
                  {stat.trend && (
                    <span className="text-xs">{stat.trend}</span>
                  )}
                </div>
                
                <div className="space-y-1">
                  <p className="text-xs font-medium text-slate-600 leading-tight">
                    {stat.title}
                  </p>
                  <p className={`text-lg font-bold ${stat.iconColor} leading-tight`}>
                    {stat.value}
                  </p>
                  <p className="text-xs text-slate-500 leading-tight">
                    {stat.description}
                  </p>
                  {stat.subtitle && (
                    <p className="text-xs text-slate-400 leading-tight">
                      {stat.subtitle}
                    </p>
                  )}
                </div>
              </div>
            </div>
          </Card>
        );
      })}
    </div>
  );
};

export default StatsCards;