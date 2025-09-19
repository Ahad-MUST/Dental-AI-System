import React, { useState } from 'react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, AreaChart, Area } from 'recharts';
import { Brain, AlertTriangle, Heart, TrendingUp, Users, Filter } from 'lucide-react';
import Card from '../common/Card';

const EmotionAnalyticsChart = ({ emotionAnalytics, getCallsByEmotion, getCallsByEmotionFlag }) => {
  const [selectedView, setSelectedView] = useState('emotions');
  const [selectedEmotion, setSelectedEmotion] = useState(null);

  const viewOptions = [
    { 
      key: 'emotions', 
      label: 'Emotions', 
      icon: Brain, 
      description: 'Patient emotion distribution',
      tooltip: 'Shows the different emotions detected in patient speech during calls'
    },
    { 
      key: 'intensity', 
      label: 'Intensity', 
      icon: TrendingUp, 
      description: 'Emotion intensity levels',
      tooltip: 'Measures how strongly emotions were expressed (low, medium, high intensity)'
    },
    { 
      key: 'flags', 
      label: 'Alerts', 
      icon: AlertTriangle, 
      description: 'Critical emotion flags',
      tooltip: 'Important emotional indicators like pain, anxiety, satisfaction that need attention'
    },
    { 
      key: 'health', 
      label: 'Call Health', 
      icon: Heart, 
      description: 'Overall emotional health',
      tooltip: 'Overall emotional wellness assessment of calls (good, fair, poor)'
    }
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

  // Emotion explanations for tooltips
  const emotionTooltips = {
    disappointment: 'Patient expressed dissatisfaction with service, outcome, or experience',
    fear: 'Patient showed anxiety or apprehension about dental procedures',
    anger: 'Patient displayed frustration or irritation during the call',
    calm: 'Patient remained composed and relaxed throughout the interaction',
    complaint: 'Patient voiced specific concerns or complaints about service',
    none: 'No significant emotions detected in patient speech',
    pain: 'Patient mentioned or expressed physical discomfort or pain',
    anxiety: 'Patient showed nervousness or worry about dental treatment',
    satisfaction: 'Patient expressed contentment or approval with service'
  };

  const intensityTooltips = {
    low: 'Mild emotional expression - subtle signs of emotion',
    medium: 'Moderate emotional expression - clear emotional indicators',
    high: 'Strong emotional expression - intense emotional reactions'
  };

  const healthTooltips = {
    good: 'Positive emotional health - patients feel comfortable and satisfied',
    fair: 'Neutral emotional health - standard professional interactions',
    poor: 'Concerning emotional health - patients experiencing distress or dissatisfaction'
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
  const totalCalls = chartData.reduce((sum, item) => sum + item.value, 0);
  const selectedViewData = viewOptions.find(option => option.key === selectedView);

  // Get insights based on current view
  const getInsights = () => {
    const insights = [];
    
    if (chartData.length === 0) return insights;
    
    switch (selectedView) {
      case 'emotions':
        const mostCommon = chartData[0];
        if (mostCommon) {
          insights.push({
            type: mostCommon.name.toLowerCase() === 'disappointment' ? 'warning' : 'info',
            title: 'Most Common Emotion',
            content: `${mostCommon.name} detected in ${mostCommon.value} calls (${mostCommon.percentage}%)`
          });
        }
        
        const negativeEmotions = chartData.filter(item => 
          ['Anger', 'Fear', 'Disappointment', 'Complaint'].includes(item.name)
        );
        
        if (negativeEmotions.length > 0) {
          const totalNegative = negativeEmotions.reduce((sum, emotion) => sum + emotion.value, 0);
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

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white/95 backdrop-blur-sm border border-slate-200 rounded-lg shadow-lg p-3">
          <p className="text-sm font-semibold text-slate-900 mb-1">{data.name}</p>
          <p className="text-sm text-slate-600">
            Calls: <span className="font-medium text-slate-900">{data.value}</span>
          </p>
          <p className="text-sm text-slate-600">
            Percentage: <span className="font-medium text-slate-900">{data.percentage}%</span>
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <Card>
      <div className="p-6">
        {/* Header with Logo Tooltip */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
              <div className="relative group">
                <Brain className="w-5 h-5 text-blue-600" />
                {/* Logo Tooltip */}
                <div className="absolute left-0 top-full mt-2 invisible group-hover:visible opacity-0 group-hover:opacity-100 transition-all duration-200 z-50">
                  <div className="bg-slate-900 text-white text-xs rounded-lg p-3 shadow-lg max-w-sm w-max">
                    <p>Emotion Analytics - Monitor patient emotional states and wellbeing</p>
                    <div className="absolute -top-1 left-2 w-2 h-2 bg-slate-900 rotate-45"></div>
                  </div>
                </div>
              </div>
              Emotion Analytics
            </h3>
            <p className="text-sm text-slate-600 mt-1">
              {selectedViewData?.description} • {totalCalls} calls analyzed
            </p>
          </div>
          
          {/* View Selector with Tooltips */}
          <div className="flex bg-slate-100 rounded-lg p-1">
            {viewOptions.map((option) => {
              const Icon = option.icon;
              return (
                <div key={option.key} className="relative group">
                  <button
                    onClick={() => setSelectedView(option.key)}
                    className={`px-3 py-2 rounded-md text-xs font-medium transition-all duration-200 flex items-center gap-2 ${
                      selectedView === option.key
                        ? 'bg-white text-slate-900 shadow-sm'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span className="hidden sm:inline">{option.label}</span>
                  </button>
                  {/* Option Tooltip */}
                  <div className="absolute left-1/2 transform -translate-x-1/2 top-full mt-2 invisible group-hover:visible opacity-0 group-hover:opacity-100 transition-all duration-200 z-50">
                    <div className="bg-slate-900 text-white text-xs rounded-lg p-3 shadow-lg max-w-sm w-max">
                      <p>{option.tooltip}</p>
                      <div className="absolute -top-1 left-1/2 transform -translate-x-1/2 w-2 h-2 bg-slate-900 rotate-45"></div>
                    </div>
                  </div>
                </div>
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
              <div className="h-64 flex items-center justify-center">
                <div className="text-center">
                  <Brain className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                  <p className="text-slate-500 font-medium">No emotion data available</p>
                  <p className="text-sm text-slate-400">Process some calls to see emotion analytics</p>
                </div>
              </div>
            ) : chartData.length > 0 ? (
              <>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={chartData}
                        cx="50%"
                        cy="50%"
                        innerRadius={45}
                        outerRadius={90}
                        paddingAngle={2}
                        dataKey="value"
                        stroke="#ffffff"
                        strokeWidth={2}
                      >
                        {chartData.map((entry, index) => (
                          <Cell 
                            key={`cell-${index}`} 
                            fill={entry.color}
                            className="hover:opacity-80 transition-opacity cursor-pointer"
                          />
                        ))}
                      </Pie>
                      <Tooltip content={<CustomTooltip />} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                
                {/* Emotion Legend with Tooltips */}
                <div className="mt-4 space-y-2">
                  {chartData.map((entry, index) => {
                    const tooltipKey = entry.name.toLowerCase();
                    const tooltipText = selectedView === 'emotions' ? emotionTooltips[tooltipKey] :
                                      selectedView === 'intensity' ? intensityTooltips[tooltipKey] :
                                      selectedView === 'health' ? healthTooltips[tooltipKey] :
                                      `${entry.name} - Click for more details`;
                    
                    return (
                      <div key={index} className="relative group">
                        <div className="flex items-center justify-between p-2 rounded-lg bg-slate-50 hover:bg-slate-100 transition-colors cursor-pointer">
                          <div className="flex items-center space-x-3">
                            <div 
                              className="w-3 h-3 rounded-full" 
                              style={{ backgroundColor: entry.color }}
                            />
                            <span className="text-sm font-medium text-slate-700">{entry.name}</span>
                          </div>
                          <div className="text-right">
                            <span className="text-sm font-semibold text-slate-900">{entry.value}</span>
                            <span className="text-xs text-slate-500 ml-1">({entry.percentage}%)</span>
                          </div>
                        </div>
                        {/* Emotion Item Tooltip */}
                        <div className="absolute left-0 top-full mt-2 invisible group-hover:visible opacity-0 group-hover:opacity-100 transition-all duration-200 z-50">
                          <div className="bg-slate-900 text-white text-xs rounded-lg p-3 shadow-lg max-w-sm w-max">
                            <p>{tooltipText}</p>
                            <div className="absolute -top-1 left-4 w-2 h-2 bg-slate-900 rotate-45"></div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </>
            ) : (
              <div className="h-64 flex items-center justify-center">
                <div className="text-center">
                  <Brain className="w-8 w-8 text-slate-300 mx-auto mb-2" />
                  <p className="text-sm text-slate-500">No {selectedView} data available</p>
                </div>
              </div>
            )}
          </div>

          {/* Insights */}
          <div>
            <h4 className="text-sm font-semibold text-slate-900 mb-4">Key Insights</h4>
            
            {insights.length > 0 ? (
              <div className="space-y-3">
                {insights.map((insight, index) => (
                  <div key={index} className="relative group">
                    <div className={`p-3 rounded-lg border ${
                      insight.type === 'success' ? 'bg-emerald-50 border-emerald-200' :
                      insight.type === 'warning' ? 'bg-amber-50 border-amber-200' :
                      insight.type === 'error' ? 'bg-red-50 border-red-200' :
                      'bg-blue-50 border-blue-200'
                    }`}>
                      <p className={`font-semibold text-sm ${
                        insight.type === 'success' ? 'text-emerald-800' :
                        insight.type === 'warning' ? 'text-amber-800' :
                        insight.type === 'error' ? 'text-red-800' :
                        'text-blue-800'
                      }`}>
                        {insight.title}
                      </p>
                      <p className={`text-xs mt-1 ${
                        insight.type === 'success' ? 'text-emerald-700' :
                        insight.type === 'warning' ? 'text-amber-700' :
                        insight.type === 'error' ? 'text-red-700' :
                        'text-blue-700'
                      }`}>
                        {insight.content}
                      </p>
                    </div>
                    {/* Insight Tooltip */}
                    <div className="absolute left-0 top-full mt-2 invisible group-hover:visible opacity-0 group-hover:opacity-100 transition-all duration-200 z-50">
                      <div className="bg-slate-900 text-white text-xs rounded-lg p-3 shadow-lg max-w-sm w-max">
                        <p>
                          {insight.type === 'success' ? 'Positive indicator - maintain current practices' :
                           insight.type === 'warning' ? 'Attention needed - monitor this metric closely' :
                           insight.type === 'error' ? 'Critical issue - immediate action recommended' :
                           'General insight - use for strategic planning'}
                        </p>
                        <div className="absolute -top-1 left-4 w-2 h-2 bg-slate-900 rotate-45"></div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <AlertTriangle className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                <p className="text-sm text-slate-500">No insights available</p>
                <p className="text-xs text-slate-400">Process more calls to generate insights</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
};

export default EmotionAnalyticsChart;