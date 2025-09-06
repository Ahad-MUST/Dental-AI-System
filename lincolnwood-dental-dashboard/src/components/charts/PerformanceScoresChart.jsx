import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Award } from 'lucide-react';
import Card from '../common/Card';
import { getGrade, getScoreColor } from '../../utils/helpers';

const PerformanceScoresChart = ({ data, rawData = [] }) => {
  // Process raw data to create chart data
  const chartData = React.useMemo(() => {
    if (!rawData || rawData.length === 0) return [];

    // Group data by representative
    const repData = rawData.reduce((acc, call) => {
      const repName = call.Representative_Name || 'Unknown';
      if (!acc[repName]) {
        acc[repName] = {
          name: repName,
          scores: [],
          totalCalls: 0
        };
      }
      
      const score = parseFloat(call.Representative_Score);
      if (!isNaN(score) && score > 0) {
        acc[repName].scores.push(score);
      }
      acc[repName].totalCalls++;
      
      return acc;
    }, {});

    // Calculate averages and create chart data
    const processedData = Object.values(repData)
      .map(rep => {
        const avgScore = rep.scores.length > 0 
          ? rep.scores.reduce((sum, score) => sum + score, 0) / rep.scores.length 
          : 0;
        
        return {
          name: rep.name,
          score: Math.round(avgScore * 100), // Convert to percentage
          calls: rep.totalCalls,
          grade: getGrade(avgScore),
          color: getScoreColor(avgScore)
        };
      })
      .filter(rep => rep.score > 0 && rep.name !== 'Unknown')
      .sort((a, b) => b.score - a.score); // Sort by score descending

    return processedData;
  }, [rawData]);

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      
      return (
        <div className="bg-white/95 backdrop-blur-sm border border-slate-200 rounded-xl shadow-lg p-4">
          <p className="text-sm font-semibold text-slate-900 mb-3">{label}</p>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-600">Score:</span>
              <span className="text-sm font-bold text-slate-900">{data.score}%</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-600">Grade:</span>
              <span 
                className="text-sm font-bold px-2 py-1 rounded-md"
                style={{ 
                  backgroundColor: data.color + '20',
                  color: data.color 
                }}
              >
                {data.grade}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-600">Total Calls:</span>
              <span className="text-sm font-medium text-slate-900">{data.calls}</span>
            </div>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <Card className="h-full" hover={true}>
      {/* Header */}
      <div className="flex items-center space-x-4 mb-8">
        <div className="bg-emerald-50 rounded-xl p-3">
          <Award className="h-6 w-6 text-emerald-600" strokeWidth={2} />
        </div>
        <div>
          <h3 className="text-xl font-bold text-slate-900">Performance Scores</h3>
          <p className="text-sm text-slate-600">Average performance by representative</p>
        </div>
      </div>

      {/* Chart */}
      {chartData && chartData.length > 0 ? (
        <div className="h-96">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart 
              data={chartData}
              margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
            >
              <CartesianGrid 
                strokeDasharray="3 3" 
                stroke="#e2e8f0" 
                strokeOpacity={0.4}
                vertical={false}
              />
              <XAxis 
                dataKey="name"
                fontSize={12}
                tick={{ fill: '#64748b' }}
                tickLine={false}
                axisLine={false}
                angle={-45}
                textAnchor="end"
                height={60}
                interval={0}
              />
              <YAxis 
                domain={[0, 100]}
                tickFormatter={(value) => `${value}%`}
                fontSize={12}
                tick={{ fill: '#64748b' }}
                tickLine={false}
                axisLine={false}
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar 
                dataKey="score"
                fill="#10b981"
                radius={[6, 6, 0, 0]}
                className="hover:opacity-80 transition-opacity"
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <div className="h-96 flex items-center justify-center">
          <div className="text-center">
            <div className="w-20 h-20 bg-slate-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <Award className="h-8 w-8 text-slate-400" strokeWidth={1.5} />
            </div>
            <p className="text-slate-600 font-medium text-sm">No performance data available</p>
            <p className="text-slate-400 text-xs mt-1">Performance scores will appear once calls are analyzed</p>
          </div>
        </div>
      )}
    </Card>
  );
};

export default PerformanceScoresChart;