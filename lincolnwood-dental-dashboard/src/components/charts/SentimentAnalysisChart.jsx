import React, { useState } from 'react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';
import { Heart, Users, TrendingUp, Filter } from 'lucide-react';
import Card from '../common/Card';

const SentimentAnalysisChart = ({ sentimentAnalytics, sentimentOpportunityCorrelation, getCallsBySentiment }) => {
  const [selectedView, setSelectedView] = useState('overall');
  const [selectedSentiment, setSelectedSentiment] = useState(null);

  const viewOptions = [
    { key: 'overall', label: 'Overall', icon: TrendingUp, description: 'Combined call sentiment' },
    { key: 'patient', label: 'Patient', icon: Heart, description: 'Patient sentiment only' },
    { key: 'staff', label: 'Staff', icon: Users, description: 'Staff sentiment only' }
  ];

  const sentimentColors = {
    positive: '#10b981', // emerald-500
    neutral: '#6b7280',  // gray-500
    negative: '#ef4444'  // red-500
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
      .filter(([sentiment, count]) => count > 0) // Only show sentiments with data
      .map(([sentiment, count]) => ({
        name: sentiment.charAt(0).toUpperCase() + sentiment.slice(1),
        value: count,
        color: sentimentColors[sentiment],
        percentage: ((count / total) * 100).toFixed(1)
      }));
  };

  // Prepare correlation data with validation
  const getCorrelationData = () => {
    if (!sentimentOpportunityCorrelation || Object.keys(sentimentOpportunityCorrelation).length === 0) {
      console.log('No sentiment opportunity correlation data available');
      return [];
    }
    
    return Object.entries(sentimentOpportunityCorrelation)
      .filter(([sentiment, data]) => data.total > 0) // Only show sentiments with data
      .map(([sentiment, data]) => ({
        sentiment: sentiment.charAt(0).toUpperCase() + sentiment.slice(1),
        missedPercentage: data.missedPercentage || 0,
        totalCalls: data.total || 0,
        missedCalls: data.missed || 0,
        color: sentimentColors[sentiment]
      }));
  };

  const chartData = getChartData();
  const correlationData = getCorrelationData();
  const selectedViewData = viewOptions.find(v => v.key === selectedView);
  const totalCalls = chartData.reduce((sum, item) => sum + item.value, 0);

  console.log('Sentiment chart rendering with data:', {
    selectedView,
    chartData,
    correlationData,
    totalCalls,
    sentimentAnalytics
  });

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white/95 backdrop-blur-sm border border-slate-200 rounded-lg shadow-lg p-3">
          <p className="text-sm font-semibold text-slate-900 mb-1">{data.name} Sentiment</p>
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

  const CorrelationTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white/95 backdrop-blur-sm border border-slate-200 rounded-lg shadow-lg p-3">
          <p className="text-sm font-semibold text-slate-900 mb-2">{label} Calls</p>
          <div className="space-y-1">
            <p className="text-xs text-slate-600">
              Total Calls: <span className="font-medium text-slate-900">{data.totalCalls}</span>
            </p>
            <p className="text-xs text-slate-600">
              Missed Opportunities: <span className="font-medium text-slate-900">{data.missedCalls}</span>
            </p>
            <p className="text-xs text-slate-600">
              Miss Rate: <span className="font-medium text-slate-900">{data.missedPercentage.toFixed(1)}%</span>
            </p>
          </div>
        </div>
      );
    }
    return null;
  };

  const handleSentimentClick = (sentiment) => {
    setSelectedSentiment(sentiment);
    const calls = getCallsBySentiment(sentiment.toLowerCase(), selectedView);
    console.log(`${sentiment} ${selectedView} calls:`, calls);
  };

  return (
    <Card className="h-full">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <div className="bg-rose-50 rounded-xl p-2.5">
            <Heart className="h-5 w-5 text-rose-600" strokeWidth={2} />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-slate-900">Sentiment Analysis</h3>
            <p className="text-sm text-slate-600">
              {selectedViewData?.description} • {totalCalls} calls analyzed
            </p>
          </div>
        </div>
      </div>

      {/* View Selection Buttons */}
      <div className="mb-6">
        <div className="flex flex-wrap gap-2">
          {viewOptions.map((view) => {
            const IconComponent = view.icon;
            const isSelected = selectedView === view.key;
            
            return (
              <button
                key={view.key}
                onClick={() => setSelectedView(view.key)}
                className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                  isSelected
                    ? 'bg-rose-100 text-rose-700 border border-rose-200 shadow-sm'
                    : 'bg-gray-50 text-gray-600 border border-gray-200 hover:bg-gray-100 hover:text-gray-700'
                }`}
              >
                <IconComponent className="h-4 w-4" strokeWidth={2} />
                <span>{view.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sentiment Distribution Pie Chart */}
        <div>
          <h4 className="text-sm font-semibold text-slate-900 mb-4">Sentiment Distribution</h4>
          {totalCalls > 0 ? (
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={chartData}
                    cx="50%"
                    cy="50%"
                    innerRadius={30}
                    outerRadius={70}
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
                        onClick={() => handleSentimentClick(entry.name)}
                      />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-48 flex items-center justify-center bg-slate-50 rounded-lg">
              <div className="text-center">
                <Heart className="h-8 w-8 text-slate-400 mx-auto mb-2" />
                <p className="text-slate-500 text-sm font-medium">No sentiment data available</p>
                <p className="text-slate-400 text-xs">Process more calls to see sentiment analysis</p>
              </div>
            </div>
          )}
          
          {/* Legend */}
          {chartData.length > 0 && (
            <div className="mt-4 space-y-2">
              {chartData.map((item, index) => (
                <div 
                  key={index} 
                  className="flex items-center justify-between p-2 rounded-lg bg-slate-50 hover:bg-slate-100 transition-colors cursor-pointer"
                  onClick={() => handleSentimentClick(item.name)}
                >
                  <div className="flex items-center space-x-3">
                    <div 
                      className="w-3 h-3 rounded-full" 
                      style={{ backgroundColor: item.color }}
                    />
                    <span className="text-sm font-medium text-slate-700">{item.name}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-semibold text-slate-900">{item.value}</span>
                    <span className="text-xs text-slate-500">({item.percentage}%)</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Sentiment vs Missed Opportunities Correlation */}
        <div>
          <h4 className="text-sm font-semibold text-slate-900 mb-4">Sentiment vs Missed Opportunities</h4>
          {correlationData.length > 0 ? (
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={correlationData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" strokeOpacity={0.4} />
                  <XAxis 
                    dataKey="sentiment" 
                    fontSize={12} 
                    tick={{ fill: '#64748b' }}
                    tickLine={false}
                    axisLine={false}
                  />
                  <YAxis 
                    domain={[0, 100]}
                    tickFormatter={(value) => `${value}%`}
                    fontSize={12}
                    tick={{ fill: '#64748b' }}
                    tickLine={false}
                    axisLine={false}
                  />
                  <Tooltip content={<CorrelationTooltip />} />
                  <Bar 
                    dataKey="missedPercentage" 
                    fill="#f59e0b"
                    radius={[4, 4, 0, 0]}
                    className="hover:opacity-80 transition-opacity"
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-48 flex items-center justify-center bg-slate-50 rounded-lg">
              <div className="text-center">
                <Filter className="h-8 w-8 text-slate-400 mx-auto mb-2" />
                <p className="text-slate-500 text-sm font-medium">No correlation data available</p>
                <p className="text-slate-400 text-xs">More data needed for correlation analysis</p>
              </div>
            </div>
          )}
          
          {/* Correlation Insights */}
          {correlationData.length > 0 && (
            <div className="mt-4 p-3 bg-amber-50 rounded-lg border border-amber-200">
              <h5 className="text-xs font-semibold text-amber-800 mb-2">Key Insights</h5>
              <div className="space-y-1">
                {correlationData.map((item, index) => (
                  <div key={index} className="text-xs text-amber-700">
                    <span className="font-medium">{item.sentiment}:</span> {item.missedPercentage.toFixed(1)}% miss rate
                    <span className="text-amber-600"> ({item.missedCalls}/{item.totalCalls} calls)</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Selected Sentiment Details */}
      {selectedSentiment && (
        <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
          <div className="flex items-center justify-between mb-2">
            <h5 className="text-sm font-semibold text-blue-900">
              {selectedSentiment} {selectedViewData?.label} Calls
            </h5>
            <button
              onClick={() => setSelectedSentiment(null)}
              className="text-blue-600 hover:text-blue-700 text-xs font-medium"
            >
              Clear Filter
            </button>
          </div>
          <p className="text-xs text-blue-700">
            Click any sentiment segment to view detailed call list in console
          </p>
        </div>
      )}
    </Card>
  );
};

export default SentimentAnalysisChart;