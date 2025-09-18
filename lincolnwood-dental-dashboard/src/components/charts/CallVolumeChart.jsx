import React, { useState, useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Phone, Calendar, Clock, BarChart3, Clock12, CalendarRange, X } from 'lucide-react';
import Card from '../common/Card';
import { CHART_CONFIG } from '../../utils/constants';

const CallVolumeChart = ({ data, rawData }) => {
  const [selectedPeriod, setSelectedPeriod] = useState('weekly');
  const [showCustomDatePicker, setShowCustomDatePicker] = useState(false);
  const [customStartDate, setCustomStartDate] = useState('');
  const [customEndDate, setCustomEndDate] = useState('');
  const [customDateRange, setCustomDateRange] = useState(null);

  const timePeriods = [
    {
      key: '1day',
      label: '1 Day',
      icon: Clock,
      description: 'Today only'
    },
    {
      key: '3day',
      label: '3 Days',
      icon: Clock12,
      description: 'Last 3 days'
    },
    {
      key: 'weekly',
      label: 'Weekly',
      icon: Calendar,
      description: 'Last 7 days'
    },
    {
      key: 'alltime',
      label: 'All Time',
      icon: BarChart3,
      description: 'Complete history'
    },
    {
      key: 'custom',
      label: 'Custom',
      icon: CalendarRange,
      description: customDateRange ? `${customDateRange.start} to ${customDateRange.end}` : 'Select custom range'
    }
  ];

  // Handle custom date range application
  const applyCustomDateRange = () => {
    if (!customStartDate || !customEndDate) {
      alert('Please select both start and end dates');
      return;
    }

    if (new Date(customStartDate) > new Date(customEndDate)) {
      alert('Start date must be before end date');
      return;
    }

    const startDate = new Date(customStartDate);
    const endDate = new Date(customEndDate);
    
    setCustomDateRange({
      start: startDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      end: endDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      startDate: startDate,
      endDate: endDate
    });

    setSelectedPeriod('custom');
    setShowCustomDatePicker(false);
  };

  // Reset custom date range
  const clearCustomDateRange = () => {
    setCustomDateRange(null);
    setCustomStartDate('');
    setCustomEndDate('');
    if (selectedPeriod === 'custom') {
      setSelectedPeriod('weekly');
    }
  };

  // Function to filter data based on selected period
  const getFilteredData = useMemo(() => {
    if (!rawData || !rawData.length) return [];

    const now = new Date();
    let filteredData = [];

    switch (selectedPeriod) {
      case '1day':
        const todayStr = `${(now.getMonth() + 1).toString().padStart(2, '0')}/${now.getDate().toString().padStart(2, '0')}/${now.getFullYear()}`;
        filteredData = rawData.filter(item => item.Analysis_Date === todayStr);
        break;

      case '3day':
        const threeDaysAgo = new Date(now.getTime() - 3 * 24 * 60 * 60 * 1000);
        filteredData = rawData.filter(item => {
          if (!item.Analysis_Date) return false;
          const [month, day, year] = item.Analysis_Date.split('/');
          const itemDate = new Date(year, month - 1, day);
          return itemDate >= threeDaysAgo && itemDate <= now;
        });
        break;

      case 'weekly':
        const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        filteredData = rawData.filter(item => {
          if (!item.Analysis_Date) return false;
          const [month, day, year] = item.Analysis_Date.split('/');
          const itemDate = new Date(year, month - 1, day);
          return itemDate >= weekAgo && itemDate <= now;
        });
        break;

      case 'custom':
        if (!customDateRange) return [];
        
        filteredData = rawData.filter(item => {
          if (!item.Analysis_Date) return false;
          
          // Parse MM/DD/YYYY format
          const [month, day, year] = item.Analysis_Date.split('/');
          const itemDate = new Date(year, month - 1, day);
          
          // Set time to start/end of day for accurate comparison
          const startOfDay = new Date(customDateRange.startDate);
          startOfDay.setHours(0, 0, 0, 0);
          const endOfDay = new Date(customDateRange.endDate);
          endOfDay.setHours(23, 59, 59, 999);
          
          return itemDate >= startOfDay && itemDate <= endOfDay;
        });
        break;

      case 'alltime':
        filteredData = rawData;
        break;

      default:
        filteredData = rawData;
    }

    // Process filtered data to get call counts by representative
    const repCallCounts = filteredData.reduce((acc, item) => {
      const name = item.Representative_Name || "Unknown";
      acc[name] = (acc[name] || 0) + 1;
      return acc;
    }, {});

    return Object.entries(repCallCounts)
      .map(([name, count]) => ({
        name,
        calls: count,
        color: name === "Unknown" ? "#ef4444" : "#3b82f6",
      }))
      .sort((a, b) => b.calls - a.calls);
  }, [rawData, selectedPeriod, customDateRange]);

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white/95 backdrop-blur-sm border border-slate-200 rounded-xl shadow-lg p-4">
          <p className="text-sm font-semibold text-slate-900 mb-2">{label}</p>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
            <span className="text-sm text-slate-600">
              Calls: <span className="font-medium text-slate-900">{payload[0].value}</span>
            </span>
          </div>
        </div>
      );
    }
    return null;
  };

  const selectedPeriodData = timePeriods.find(p => p.key === selectedPeriod);

  return (
    <Card className="h-full" hover={true}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-8">
        <div className="flex items-center space-x-4">
          <div className="bg-blue-50 rounded-xl p-3 relative group/icon">
            <Phone className="h-6 w-6 text-blue-600" strokeWidth={2} />
            
            {/* Icon Tooltip */}
            <div className="absolute left-0 top-full mt-2 invisible group-hover/icon:visible opacity-0 group-hover/icon:opacity-100 transition-all duration-200 z-50">
              <div className="bg-slate-900 text-white text-xs rounded-lg p-3 shadow-lg w-60">
                <p className="leading-relaxed">
                  Track call volume distribution across all representatives to identify workload patterns and performance trends
                </p>
                <div className="absolute -top-1 left-4 w-2 h-2 bg-slate-900 rotate-45"></div>
              </div>
            </div>
          </div>
          <div>
            <h3 className="text-xl font-bold text-slate-900">Call Volume</h3>
            <p className="text-sm text-slate-600">
              {selectedPeriodData?.description} by representative
            </p>
          </div>
        </div>
      </div>

      {/* Time Period Buttons */}
      <div className="mb-8 relative">
        <div className="flex flex-wrap gap-2">
          {timePeriods.map((period) => {
            const IconComponent = period.icon;
            const isSelected = selectedPeriod === period.key;
            
            return (
              <button
                key={period.key}
                onClick={() => {
                  if (period.key === 'custom') {
                    setShowCustomDatePicker(true);
                  } else {
                    setSelectedPeriod(period.key);
                  }
                }}
                className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                  isSelected
                    ? 'bg-blue-600 text-white shadow-md'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200 hover:text-slate-700'
                }`}
              >
                <IconComponent className="h-4 w-4" strokeWidth={2} />
                <span>{period.label}</span>
                {period.key === 'custom' && customDateRange && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      clearCustomDateRange();
                    }}
                    className="ml-1 hover:bg-blue-700 rounded-full p-0.5"
                  >
                    <X className="h-3 w-3" />
                  </button>
                )}
              </button>
            );
          })}
        </div>

        {/* Custom Date Picker Modal */}
        {showCustomDatePicker && (
          <div className="absolute left-0 top-full mt-2 bg-white border border-slate-200 rounded-xl shadow-lg p-4 z-50 w-80">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-slate-900">Select Date Range</h3>
              <button
                onClick={() => setShowCustomDatePicker(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">Start Date</label>
                <input
                  type="date"
                  value={customStartDate}
                  onChange={(e) => setCustomStartDate(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              
              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">End Date</label>
                <input
                  type="date"
                  value={customEndDate}
                  onChange={(e) => setCustomEndDate(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              
              <div className="flex space-x-2 pt-2">
                <button
                  onClick={applyCustomDateRange}
                  className="flex-1 bg-blue-600 text-white px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-700 transition-colors"
                >
                  Apply Range
                </button>
                <button
                  onClick={() => {
                    setCustomStartDate('');
                    setCustomEndDate('');
                    setShowCustomDatePicker(false);
                  }}
                  className="px-3 py-2 text-slate-600 text-sm font-medium hover:text-slate-800 transition-colors"
                >
                  Clear
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Chart */}
      {getFilteredData && getFilteredData.length > 0 ? (
        <div className="h-96">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={getFilteredData} margin={CHART_CONFIG.margins}>
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
                angle={getFilteredData.length > 5 ? -45 : 0}
                textAnchor={getFilteredData.length > 5 ? 'end' : 'middle'}
                height={getFilteredData.length > 5 ? 60 : 30}
              />
              <YAxis 
                fontSize={12} 
                tick={{ fill: '#64748b' }}
                tickLine={false}
                axisLine={false}
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar 
                dataKey="calls" 
                fill="#3b82f6"
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
              <Phone className="h-8 w-8 text-slate-400" strokeWidth={1.5} />
            </div>
            <p className="text-slate-600 font-medium text-sm">
              No call data available for {selectedPeriodData?.description.toLowerCase()}
            </p>
            <p className="text-slate-400 text-xs mt-1">
              Try selecting a different time period
            </p>
          </div>
        </div>
      )}
    </Card>
  );
};

export default CallVolumeChart;