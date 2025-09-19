import React, { useState } from 'react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';
import { Heart, Users, TrendingUp, Filter } from 'lucide-react';
import Card from '../common/Card';

const SentimentAnalysisChart = ({ sentimentAnalytics, sentimentOpportunityCorrelation, getCallsBySentiment }) => {
  const [selectedView, setSelectedView] = useState('overall');
  const [selectedSentiment, setSelectedSentiment] = useState(null);

  const viewOptions = [
    { 
      key: 'overall', 
      label: 'Overall', 
      icon: TrendingUp, 
      description: 'Combined call sentiment',
      tooltip: 'Shows the overall sentiment combining both patient and staff perspectives for each call'
    },
    { 
      key: 'patient', 
      label: 'Patient', 
      icon: Heart, 
      description: 'Patient sentiment only',
      tooltip: 'Analyzes only patient emotions and satisfaction levels during calls'
    },
    { 
      key: 'staff', 
      label: 'Staff', 
      icon: Users, 
      description: 'Staff sentiment only',
      tooltip: 'Measures staff professionalism, helpfulness, and communication quality'
    }
  ];

  const sentimentColors = {
    positive: '#10b981', // emerald-500
    neutral: '#6b7280',  // gray-500
    negative: '#ef4444'  // red-500
  };

  // Sentiment explanations for tooltips
  const sentimentTooltips = {
    positive: 'Calls where patients expressed satisfaction, gratitude, or positive emotions',
    neutral: 'Calls with professional, matter-of-fact interactions without strong emotions',
    negative: 'Calls involving frustration, disappointment, or dissatisfaction',
    mixed: 'Calls with both positive and negative sentiment elements'
  };

  // Prepare data for the selected view with validation
  const getChartData = () => {
    if (!sentimentAnalytics || !sentimentAnalytics[selectedView]) {
      console.log('No sentiment analytics data available for view:', selectedView);
      return [];
    }
    
    const data = sentimentAnalytics[selectedView];
    const total = Object.values(data).reduce((sum, val) => sum + val, 0);
    
    console.log(`Chart data for ${selectedView}:`, data, 'Total:', total);
    
    if (total === 0) {
      return [];
    }
    
    return Object.entries(data)
      .filter(([sentiment, count]) => count > 0)
      .map(([sentiment, count]) => ({
        name: sentiment.charAt(0).toUpperCase() + sentiment.slice(1),
        value: count,
        color: sentimentColors[sentiment] || sentimentColors.neutral,
        percentage: ((count / total) * 100).toFixed(1)
      }))
      .sort((a, b) => b.value - a.value);
  };

  const chartData = getChartData();
  const totalCalls = chartData.reduce((sum, item) => sum + item.value, 0);
  const selectedViewData = viewOptions.find(option => option.key === selectedView);

  // Get opportunity correlation data
  const getOpportunityData = () => {
    if (!sentimentOpportunityCorrelation || !sentimentOpportunityCorrelation[selectedView]) {
      // Fallback: try to use the overall data if specific view is not available
      const fallbackData = sentimentOpportunityCorrelation?.overall || sentimentOpportunityCorrelation;
      if (!fallbackData) {
        return [];
      }
      
      return Object.entries(fallbackData)
        .filter(([sentiment, stats]) => stats && typeof stats === 'object' && stats.total > 0)
        .map(([sentiment, stats]) => ({
          sentiment: sentiment.charAt(0).toUpperCase() + sentiment.slice(1),
          missRate: ((stats.missed / stats.total) * 100).toFixed(1),
          total: stats.total,
          missed: stats.missed,
          color: sentimentColors[sentiment] || sentimentColors.neutral
        }))
        .sort((a, b) => parseFloat(b.missRate) - parseFloat(a.missRate));
    }

    const data = sentimentOpportunityCorrelation[selectedView];
    return Object.entries(data)
      .filter(([sentiment, stats]) => stats && typeof stats === 'object' && stats.total > 0)
      .map(([sentiment, stats]) => ({
        sentiment: sentiment.charAt(0).toUpperCase() + sentiment.slice(1),
        missRate: ((stats.missed / stats.total) * 100).toFixed(1),
        total: stats.total,
        missed: stats.missed,
        color: sentimentColors[sentiment] || sentimentColors.neutral
      }))
      .sort((a, b) => parseFloat(b.missRate) - parseFloat(a.missRate));
  };

  const opportunityData = getOpportunityData();

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

  const CustomOpportunityTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white/95 backdrop-blur-sm border border-slate-200 rounded-lg shadow-lg p-3">
          <p className="text-sm font-semibold text-slate-900 mb-1">{data.sentiment}</p>
          <p className="text-sm text-slate-600">
            Miss Rate: <span className="font-medium text-slate-900">{data.missRate}%</span>
          </p>
          <p className="text-sm text-slate-600">
            Missed: <span className="font-medium text-slate-900">{data.missed}/{data.total}</span>
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
                <Heart className="w-5 h-5 text-pink-600" />
                {/* Logo Tooltip */}
                <div className="absolute left-0 top-full mt-2 invisible group-hover:visible opacity-0 group-hover:opacity-100 transition-all duration-200 z-50">
                  <div className="bg-slate-900 text-white text-xs rounded-lg p-3 shadow-lg max-w-sm w-max">
                    <p>Sentiment Analysis - Track emotional tone and satisfaction</p>
                    <div className="absolute -top-1 left-2 w-2 h-2 bg-slate-900 rotate-45"></div>
                  </div>
                </div>
              </div>
              Sentiment Analysis
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
            <h4 className="text-sm font-semibold text-slate-900 mb-4">
              Sentiment Distribution
            </h4>
            
            {chartData.length > 0 ? (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={chartData}
                      cx="50%"
                      cy="50%"
                      innerRadius={50}
                      outerRadius={100}
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
            ) : (
              <div className="h-64 flex items-center justify-center">
                <div className="text-center">
                  <Heart className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                  <p className="text-slate-500 font-medium">No sentiment data available</p>
                  <p className="text-sm text-slate-400">Process some calls to see sentiment analysis</p>
                </div>
              </div>
            )}

            {/* Sentiment Legend with Tooltips */}
            {chartData.length > 0 && (
              <div className="mt-4 space-y-2">
                {chartData.map((entry, index) => (
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
                    {/* Sentiment Item Tooltip */}
                    <div className="absolute left-0 top-full mt-2 invisible group-hover:visible opacity-0 group-hover:opacity-100 transition-all duration-200 z-50">
                      <div className="bg-slate-900 text-white text-xs rounded-lg p-3 shadow-lg max-w-sm w-max">
                        <p>{sentimentTooltips[entry.name.toLowerCase()] || 'Sentiment category'}</p>
                        <div className="absolute -top-1 left-4 w-2 h-2 bg-slate-900 rotate-45"></div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Sentiment vs Opportunities */}
          <div>
            <h4 className="text-sm font-semibold text-slate-900 mb-4">
              Sentiment vs Missed Opportunities
            </h4>
            
            {opportunityData.length > 0 ? (
              <>
                <div className="h-48">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={opportunityData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis 
                        dataKey="sentiment" 
                        fontSize={12} 
                        tick={{ fill: '#64748b' }}
                        tickLine={false}
                        axisLine={false}
                      />
                      <YAxis 
                        fontSize={12} 
                        tick={{ fill: '#64748b' }}
                        tickLine={false}
                        axisLine={false}
                        tickFormatter={(value) => `${value}%`}
                      />
                      <Tooltip content={<CustomOpportunityTooltip />} />
                      <Bar 
                        dataKey="missRate" 
                        fill="#ef4444"
                        radius={[4, 4, 0, 0]}
                        className="hover:opacity-80 transition-opacity"
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                {/* Key Insights with Tooltips */}
                <div className="mt-4">
                  <h5 className="text-xs font-semibold text-slate-700 mb-2">Key Insights</h5>
                  <div className="space-y-1">
                    {opportunityData.map((item, index) => (
                      <div key={index} className="relative group">
                        <p className="text-xs text-slate-600 p-1 rounded hover:bg-slate-50 cursor-pointer">
                          <span className="font-medium">{item.sentiment}:</span> {item.missRate}% miss rate ({item.missed}/{item.total} calls)
                        </p>
                        {/* Insight Tooltip */}
                        <div className="absolute left-0 top-full mt-1 invisible group-hover:visible opacity-0 group-hover:opacity-100 transition-all duration-200 z-50">
                          <div className="bg-slate-900 text-white text-xs rounded-lg p-3 shadow-lg max-w-sm w-max">
                            <p>
                              {item.sentiment === 'Negative' ? 'Negative sentiment calls often have higher miss rates due to customer frustration' :
                               item.sentiment === 'Neutral' ? 'Neutral calls represent standard interactions with average opportunity conversion' :
                               'Positive sentiment calls typically have lower miss rates and better outcomes'}
                            </p>
                            <div className="absolute -top-1 left-4 w-2 h-2 bg-slate-900 rotate-45"></div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            ) : (
              <div className="h-48 flex items-center justify-center">
                <div className="text-center">
                  <TrendingUp className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                  <p className="text-sm text-slate-500">No opportunity correlation data</p>
                  <p className="text-xs text-slate-400">
                    {sentimentOpportunityCorrelation ? 
                      `Try switching to a different view or process more calls` :
                      `Process calls with missed opportunities to see correlation data`
                    }
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
};

export default SentimentAnalysisChart;