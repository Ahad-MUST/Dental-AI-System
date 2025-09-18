import React, { useState, useMemo } from 'react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts';
import { Tag, Calendar, Clock, Clock12, BarChart3, CalendarRange, X } from 'lucide-react';
import Card from '../common/Card';
import { CHART_CONFIG, CHART_COLORS } from '../../utils/constants';

const CallTagsChart = ({ rawData, getCallsByTag }) => {
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

  // Tag display names mapping
  const tagDisplayNames = {
    'new_patient': 'New Patient',
    'emergency': 'Emergency',
    'insurance': 'Insurance Inquiry',
    'appointment_booking': 'Appointment Booking',
    'appointment_confirm': 'Appointment Confirmation',
    'appointment_cancel': 'Cancel/Reschedule',
    'general_inquiry': 'General Inquiry',
    'cleaning': 'Cleaning/Checkup',
    'cosmetic': 'Cosmetic Treatment',
    'major_treatment': 'Major Treatment',
    'billing': 'Billing Question'
  };

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

  // Function to filter and process data based on selected period
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

    // Process filtered data to get call tag counts
    const tagCounts = filteredData.reduce((acc, item) => {
      const tag = item.Call_Tag || 'general_inquiry';
      acc[tag] = (acc[tag] || 0) + 1;
      return acc;
    }, {});

    return Object.entries(tagCounts).map(([tag, count]) => ({
      tag: tagDisplayNames[tag] || tag.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()),
      count,
      percentage: filteredData.length > 0 ? ((count / filteredData.length) * 100).toFixed(1) : '0.0',
    }));
  }, [rawData, selectedPeriod, customDateRange]);

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white/95 backdrop-blur-sm border border-slate-200 rounded-lg shadow-lg p-3">
          <p className="text-sm font-semibold text-slate-900 mb-1">{payload[0].payload.tag}</p>
          <p className="text-sm text-slate-600">
            Calls: <span className="font-medium text-slate-900">{payload[0].value}</span>
          </p>
          <p className="text-sm text-slate-600">
            Percentage: <span className="font-medium text-slate-900">{payload[0].payload.percentage}%</span>
          </p>
        </div>
      );
    }
    return null;
  };

  const CustomLegend = ({ payload }) => {
    return (
      <div className="mt-4 space-y-2">
        {payload.map((entry, index) => (
          <div key={index} className="flex items-center justify-between p-2 rounded-lg bg-slate-50 hover:bg-slate-100 transition-colors cursor-pointer">
            <div className="flex items-center space-x-3">
              <div 
                className="w-3 h-3 rounded-full" 
                style={{ backgroundColor: entry.color }}
              />
              <span className="text-sm font-medium text-slate-700">{entry.value}</span>
            </div>
            <span className="text-sm font-semibold text-slate-900">
              {getFilteredData.find(item => item.tag === entry.value)?.percentage}%
            </span>
          </div>
        ))}
      </div>
    );
  };

  const selectedPeriodData = timePeriods.find(p => p.key === selectedPeriod);

  return (
    <Card className="h-full">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <div className="bg-emerald-50 rounded-xl p-2.5 relative group/icon">
            <Tag className="h-5 w-5 text-emerald-600" strokeWidth={2} />
            
            {/* Icon Tooltip */}
            <div className="absolute left-0 top-full mt-2 invisible group-hover/icon:visible opacity-0 group-hover/icon:opacity-100 transition-all duration-200 z-50">
              <div className="bg-slate-900 text-white text-xs rounded-lg p-3 shadow-lg w-56">
                <p className="leading-relaxed">
                  Categorize and analyze call types to understand patient needs and optimize service offerings
                </p>
                <div className="absolute -top-1 left-4 w-2 h-2 bg-slate-900 rotate-45"></div>
              </div>
            </div>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-slate-900">Call Tags</h3>
            <p className="text-sm text-slate-600">
              {selectedPeriodData?.description} by call category
            </p>
          </div>
        </div>
      </div>

      {/* Time Period Buttons */}
      <div className="mb-6 relative">
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
                className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                  isSelected
                    ? 'bg-emerald-100 text-emerald-700 border border-emerald-200 shadow-sm'
                    : 'bg-gray-50 text-gray-600 border border-gray-200 hover:bg-gray-100 hover:text-gray-700'
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
                    className="ml-1 hover:bg-emerald-200 rounded-full p-0.5"
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
                  className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                />
              </div>
              
              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">End Date</label>
                <input
                  type="date"
                  value={customEndDate}
                  onChange={(e) => setCustomEndDate(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                />
              </div>
              
              <div className="flex space-x-2 pt-2">
                <button
                  onClick={applyCustomDateRange}
                  className="flex-1 bg-emerald-600 text-white px-3 py-2 rounded-md text-sm font-medium hover:bg-emerald-700 transition-colors"
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

      {getFilteredData.length > 0 ? (
        <>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={getFilteredData}
                  cx="50%"
                  cy="50%"
                  innerRadius={45}
                  outerRadius={90}
                  paddingAngle={2}
                  dataKey="count"
                  stroke="#ffffff"
                  strokeWidth={2}
                >
                  {getFilteredData.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={CHART_COLORS[index % CHART_COLORS.length]}
                      className="hover:opacity-80 transition-opacity cursor-pointer"
                    />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          
          <CustomLegend payload={getFilteredData.map((item, index) => ({
            value: item.tag,
            color: CHART_COLORS[index % CHART_COLORS.length]
          }))} />
        </>
      ) : (
        <div className="h-64 flex items-center justify-center">
          <div className="text-center">
            <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <Tag className="h-8 w-8 text-slate-400" />
            </div>
            <p className="text-slate-500 font-medium">
              No call tag data available for {selectedPeriodData?.description.toLowerCase()}
            </p>
            <p className="text-sm text-slate-400">
              Try selecting a different time period
            </p>
          </div>
        </div>
      )}
    </Card>
  );
};

export default CallTagsChart;