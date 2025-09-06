import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Activity } from 'lucide-react';
import Card from '../common/Card';
import { CHART_CONFIG } from '../../utils/constants';

const PerformanceTrendsChart = ({ data }) => {
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const score = payload[0].value;
      const calls = payload[0].payload.callCount;
      
      return (
        <div className="bg-white/95 backdrop-blur-sm border border-slate-200 rounded-xl shadow-lg p-4">
          <p className="text-sm font-semibold text-slate-900 mb-3">{label}</p>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-600">Performance:</span>
              <span className="text-sm font-medium text-slate-900">{Math.round(score * 100)}%</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-600">Calls:</span>
              <span className="text-sm font-medium text-slate-900">{calls}</span>
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
        <div className="bg-violet-50 rounded-xl p-3">
          <Activity className="h-6 w-6 text-violet-600" strokeWidth={2} />
        </div>
        <div>
          <h3 className="text-xl font-bold text-slate-900">Performance Trends</h3>
          <p className="text-sm text-slate-600">Weekly performance analysis over time</p>
        </div>
      </div>

      {/* Chart */}
      {data && data.length > 0 ? (
        <div className="h-96">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={CHART_CONFIG.margins}>
              <defs>
                <linearGradient id="performanceGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0.05}/>
                </linearGradient>
              </defs>
              <CartesianGrid 
                strokeDasharray="3 3" 
                stroke="#e2e8f0" 
                strokeOpacity={0.4}
                vertical={false}
              />
              <XAxis 
                dataKey="date"
                fontSize={12}
                tick={{ fill: '#64748b' }}
                tickLine={false}
                axisLine={false}
                angle={-45}
                textAnchor="end"
                height={60}
              />
              <YAxis 
                domain={[0, 1]}
                tickFormatter={(value) => `${Math.round(value * 100)}%`}
                fontSize={12}
                tick={{ fill: '#64748b' }}
                tickLine={false}
                axisLine={false}
              />
              <Tooltip content={<CustomTooltip />} />
              <Area
                type="monotone"
                dataKey="averageScore"
                stroke="#8b5cf6"
                strokeWidth={3}
                fill="url(#performanceGradient)"
                dot={{ fill: '#8b5cf6', strokeWidth: 2, r: 4 }}
                activeDot={{ r: 6, fill: '#8b5cf6', strokeWidth: 2, stroke: '#ffffff' }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <div className="h-96 flex items-center justify-center">
          <div className="text-center">
            <div className="w-20 h-20 bg-slate-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <Activity className="h-8 w-8 text-slate-400" strokeWidth={1.5} />
            </div>
            <p className="text-slate-600 font-medium text-sm">No trend data available</p>
            <p className="text-slate-400 text-xs mt-1">Data will appear as performance history builds</p>
          </div>
        </div>
      )}
    </Card>
  );
};

export default PerformanceTrendsChart;