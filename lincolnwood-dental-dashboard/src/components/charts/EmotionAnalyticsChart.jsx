import React, { useState } from 'react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, AreaChart, Area } from 'recharts';
import { Brain, AlertTriangle, Heart, TrendingUp, Users, Filter } from 'lucide-react';
import Card from '../common/Card';

const EmotionAnalyticsChart = ({ emotionAnalytics, getCallsByEmotion, getCallsByEmotionFlag }) => {
  const [selectedView, setSelectedView] = useState('emotions');
  const [selectedEmotion, setSelectedEmotion] = useState(null);

  const viewOptions = [
    { key: 'emotions', label: 'Emotions', icon: Brain, description: 'Patient emotion distribution' },
    { key: 'intensity', label: 'Intensity', icon: TrendingUp, description: 'Emotion intensity levels' },
    { key: 'flags', label: 'Alerts', icon: AlertTriangle, description: 'Critical emotion flags' },
    { key: 'health', label: 'Call Health', icon: Heart, description: 'Overall emotional health' }
  ];

  const emotionColors = {
    // Standard emotions
    joy: '#10b981',        // emerald-500
    sadness: '#3b82f6',    // blue-500  
    anger: '#ef4444',      // red-500
    fear: '#f59e0b',       // amber-500
    surprise: '#8b5cf6',   // violet-500
    neutral: '#6b7280',    // gray-500
    
    // Dental-specific emotions
    pain: '#dc2626',       // red-600
    anxiety: '#f97316',    // orange-500  
    satisfaction: '#059669', // emerald-600
    frustration: '#b91c1c', // red-700
    professional: '#1d4ed8', // blue-700
    empathy: '#059669',    // emerald-600
    concern: '#f59e0b',    // amber-500
    confusion: '#8b5cf6',   // violet-500
    disappointment: '#f97316', // orange-500
    calm: '#10b981',       // emerald-500
    complaint: '#ef4444',  // red-500
    none: '#6b7280'        // gray-500
  };

  const intensityColors = {
    low: '#10b981',    // emerald-500
    medium: '#f59e0b', // amber-500
    high: '#ef4444'    // red-500
  };

  const healthColors = {
    good: '#10b981',   // emerald-500
    fair: '#f59e0b',   // amber-500
    poor: '#ef4444'    // red-500
  };

  // Check if we have emotion analytics data
  const hasEmotionData = emotionAnalytics && (
    Object.keys(emotionAnalytics.patientEmotions || {}).length > 0 ||
    Object.values(emotionAnalytics.emotionIntensity || {}).some(val => val > 0) ||
    Object.keys(emotionAnalytics.emotionFlags || {}).length > 0 ||
    Object.values(emotionAnalytics.callHealth || {}).some(val => val > 0)
  );

  // Prepare data for the selected view
  const getChartData = () => {
    if (!emotionAnalytics) {
      return [];
    }
    
    switch (selectedView) {
      case 'emotions':
        const emotions = emotionAnalytics.patientEmotions || {};
        const total = Object.values(emotions).reduce((sum, val) => sum + val, 0);
        
        if (total === 0) {
          return [];
        }
        
        return Object.entries(emotions)
          .filter(([emotion, count]) => count > 0)
          .map(([emotion, count]) => ({
            name: emotion.charAt(0).toUpperCase() + emotion.slice(1),
            value: count,
            color: emotionColors[emotion.toLowerCase()] || emotionColors.neutral,
            percentage: ((count / total) * 100).toFixed(1)
          }))
          .sort((a, b) => b.value - a.value);

      case 'intensity':
        const intensity = emotionAnalytics.emotionIntensity || {};
        
        return Object.entries(intensity)
          .filter(([level, count]) => count > 0)
          .map(([level, count]) => ({
            name: level.charAt(0).toUpperCase() + level.slice(1),
            value: count,
            color: intensityColors[level] || intensityColors.low,
            percentage: (() => {
              const total = Object.values(intensity).reduce((sum, val) => sum + val, 0);
              return total > 0 ? ((count / total) * 100).toFixed(1) : '0';
            })()
          }))
          .sort((a, b) => b.value - a.value);

      case 'flags':
        const flags = emotionAnalytics.emotionFlags || {};
        
        return Object.entries(flags)
          .filter(([flag, count]) => count > 0)
          .map(([flag, count]) => ({
            name: flag.charAt(0).toUpperCase() + flag.slice(1),
            value: count,
            color: flag === 'pain' ? '#dc2626' : 
                   flag === 'anxiety' ? '#f97316' :
                   flag === 'satisfaction' ? '#059669' :
                   flag === 'frustration' ? '#b91c1c' :
                   flag === 'urgency' ? '#ef4444' :
                   '#6b7280',
            percentage: (() => {
              const total = Object.values(flags).reduce((sum, val) => sum + val, 0);
              return total > 0 ? ((count / total) * 100).toFixed(1) : '0';
            })()
          }))
          .sort((a, b) => b.value - a.value);

      case 'health':
        const health = emotionAnalytics.callHealth || {};
        
        return Object.entries(health)
          .filter(([level, count]) => count > 0)
          .map(([level, count]) => ({
            name: level.charAt(0).toUpperCase() + level.slice(1),
            value: count,
            color: healthColors[level] || healthColors.good,
            percentage: (() => {
              const total = Object.values(health).reduce((sum, val) => sum + val, 0);
              return total > 0 ? ((count / total) * 100).toFixed(1) : '0';
            })()
          }))
          .sort((a, b) => b.value - a.value);

      default:
        return [];
    }
  };

  const chartData = getChartData();

  // Calculate total calls analyzed
  const getTotalCallsAnalyzed = () => {
    if (!emotionAnalytics) return 0;
    
    switch (selectedView) {
      case 'emotions':
        return Object.values(emotionAnalytics.patientEmotions || {}).reduce((sum, val) => sum + val, 0);
      case 'intensity':
        return Object.values(emotionAnalytics.emotionIntensity || {}).reduce((sum, val) => sum + val, 0);
      case 'flags':
        return Object.values(emotionAnalytics.emotionFlags || {}).reduce((sum, val) => sum + val, 0);
      case 'health':
        return Object.values(emotionAnalytics.callHealth || {}).reduce((sum, val) => sum + val, 0);
      default:
        return 0;
    }
  };

  const totalCalls = getTotalCallsAnalyzed();

  // Handle click on chart items
  const handleChartClick = (data) => {
    if (!data) return;
    
    const itemName = data.name.toLowerCase();
    setSelectedEmotion(itemName);
    
    // Get relevant calls based on view
    let relevantCalls = [];
    switch (selectedView) {
      case 'emotions':
        relevantCalls = getCallsByEmotion ? getCallsByEmotion(itemName) : [];
        break;
      case 'flags':
        relevantCalls = getCallsByEmotionFlag ? getCallsByEmotionFlag(itemName) : [];
        break;
      default:
        break;
    }
    
    console.log(`Clicked on ${itemName}, found ${relevantCalls.length} relevant calls`);
  };

  // Custom tooltip for charts
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-medium text-gray-900">{data.name}</p>
          <p className="text-sm text-gray-600">
            {data.value} calls ({data.percentage}%)
          </p>
        </div>
      );
    }
    return null;
  };

  // Get insights for the current view
  const getInsights = () => {
    if (chartData.length === 0) return null;

    const insights = [];
    
    switch (selectedView) {
      case 'emotions':
        const topEmotion = chartData[0];
        insights.push({
          type: 'info',
          title: 'Most Common Emotion',
          content: `${topEmotion.name} detected in ${topEmotion.value} calls (${topEmotion.percentage}%)`
        });
        
        const negativeEmotions = chartData.filter(item => 
          ['Sadness', 'Anger', 'Fear', 'Pain', 'Anxiety', 'Frustration', 'Disappointment', 'Complaint'].includes(item.name)
        );
        
        if (negativeEmotions.length > 0) {
          const totalNegative = negativeEmotions.reduce((sum, item) => sum + item.value, 0);
          insights.push({
            type: 'warning',
            title: 'Negative Emotions Detected',
            content: `${totalNegative} calls with negative emotions (${((totalNegative / totalCalls) * 100).toFixed(1)}%)`
          });
        }
        break;
        
      case 'intensity':
        const highIntensity = chartData.find(item => item.name === 'High');
        if (highIntensity) {
          insights.push({
            type: 'warning',
            title: 'High Emotional Intensity',
            content: `${highIntensity.value} calls with high emotional intensity (${highIntensity.percentage}%)`
          });
        }
        break;
        
      case 'flags':
        const criticalFlags = chartData.filter(item => 
          ['Pain', 'Anxiety', 'Frustration'].includes(item.name)
        );
        
        if (criticalFlags.length > 0) {
          insights.push({
            type: 'warning',
            title: 'Critical Alerts',
            content: `${criticalFlags.length} types of critical emotions detected`
          });
        }
        
        const satisfactionFlag = chartData.find(item => item.name === 'Satisfaction');
        if (satisfactionFlag) {
          insights.push({
            type: 'success',
            title: 'Patient Satisfaction',
            content: `${satisfactionFlag.value} calls with satisfaction detected`
          });
        }
        break;
        
      case 'health':
        const goodHealth = chartData.find(item => item.name === 'Good');
        const poorHealth = chartData.find(item => item.name === 'Poor');
        
        if (goodHealth) {
          insights.push({
            type: 'success',
            title: 'Healthy Calls',
            content: `${goodHealth.value} calls with good emotional health (${goodHealth.percentage}%)`
          });
        }
        
        if (poorHealth) {
          insights.push({
            type: 'error',
            title: 'Poor Emotional Health',
            content: `${poorHealth.value} calls with poor emotional health (${poorHealth.percentage}%)`
          });
        }
        break;
    }
    
    return insights;
  };

  const insights = getInsights();

  return (
    <Card>
      <div className="p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
              <Brain className="w-5 h-5 text-blue-600" />
              Emotion Analytics
            </h3>
            <p className="text-sm text-slate-600 mt-1">
              Patient emotion distribution • {totalCalls} calls analyzed
            </p>
          </div>
          
          {/* View Selector */}
          <div className="flex bg-slate-100 rounded-lg p-1">
            {viewOptions.map((option) => {
              const Icon = option.icon;
              return (
                <button
                  key={option.key}
                  onClick={() => setSelectedView(option.key)}
                  className={`px-3 py-2 rounded-md text-xs font-medium transition-all duration-200 flex items-center gap-2 ${
                    selectedView === option.key
                      ? 'bg-white text-slate-900 shadow-sm'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                  title={option.description}
                >
                  <Icon className="w-4 h-4" />
                  <span className="hidden sm:inline">{option.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Content */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Chart */}
          <div>
            <h4 className="text-sm font-semibold text-slate-900 mb-4 capitalize">
              {selectedView === 'emotions' ? 'Emotions Distribution' :
               selectedView === 'intensity' ? 'Intensity Levels' :
               selectedView === 'flags' ? 'Emotion Alerts' :
               'Call Emotional Health'}
            </h4>
            
            {!hasEmotionData ? (
              <div className="flex flex-col items-center justify-center h-64 text-center">
                <Brain className="w-12 h-12 text-slate-300 mb-4" />
                <h5 className="text-lg font-medium text-slate-900 mb-2">No emotion data available</h5>
                <p className="text-sm text-slate-600 max-w-sm">
                  Process more calls to see emotion analytics
                </p>
              </div>
            ) : chartData.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-64 text-center">
                <AlertTriangle className="w-12 h-12 text-amber-400 mb-4" />
                <h5 className="text-lg font-medium text-slate-900 mb-2">No data for {selectedView}</h5>
                <p className="text-sm text-slate-600 max-w-sm">
                  No {selectedView} data available for the selected time period
                </p>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={chartData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={120}
                    paddingAngle={2}
                    dataKey="value"
                    onClick={handleChartClick}
                    className="cursor-pointer"
                  >
                    {chartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                </PieChart>
              </ResponsiveContainer>
            )}

            {/* Legend */}
            {chartData.length > 0 && (
              <div className="mt-4 grid grid-cols-2 gap-2">
                {chartData.slice(0, 6).map((item, index) => (
                  <div key={index} className="flex items-center space-x-2">
                    <div 
                      className="w-3 h-3 rounded-full flex-shrink-0" 
                      style={{ backgroundColor: item.color }}
                    />
                    <span className="text-xs text-slate-600 truncate">
                      {item.name}
                      {item.percentage && (
                        <span className="ml-1 text-slate-400">({item.percentage}%)</span>
                      )}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Insights Panel */}
          <div>
            <h4 className="text-sm font-semibold text-slate-900 mb-4">Key Insights</h4>
            
            {!hasEmotionData ? (
              <div className="p-4 bg-slate-50 rounded-lg border-2 border-dashed border-slate-200 text-center">
                <p className="text-sm text-slate-600">
                  No Data Available
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  Process more calls with emotion detection to see insights for emotions.
                </p>
              </div>
            ) : insights && insights.length > 0 ? (
              <div className="space-y-3">
                {insights.map((insight, index) => (
                  <div 
                    key={index}
                    className={`p-3 rounded-lg border ${
                      insight.type === 'success' ? 'bg-emerald-50 border-emerald-200' :
                      insight.type === 'warning' ? 'bg-amber-50 border-amber-200' :
                      insight.type === 'error' ? 'bg-red-50 border-red-200' :
                      'bg-blue-50 border-blue-200'
                    }`}
                  >
                    <h5 className={`text-xs font-semibold mb-2 ${
                      insight.type === 'success' ? 'text-emerald-900' :
                      insight.type === 'warning' ? 'text-amber-900' :
                      insight.type === 'error' ? 'text-red-900' :
                      'text-blue-900'
                    }`}>
                      {insight.title}
                    </h5>
                    <p className={`text-sm ${
                      insight.type === 'success' ? 'text-emerald-800' :
                      insight.type === 'warning' ? 'text-amber-800' :
                      insight.type === 'error' ? 'text-red-800' :
                      'text-blue-800'
                    }`}>
                      {insight.content}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-4 bg-slate-50 rounded-lg">
                <p className="text-sm text-slate-600">
                  No specific insights available for current data.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
};

export default EmotionAnalyticsChart;