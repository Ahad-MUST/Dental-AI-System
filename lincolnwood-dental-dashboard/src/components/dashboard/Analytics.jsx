import React, { useState } from 'react';
import { Phone, Target, Users, AlertTriangle, BarChart3, Calendar, Clock, Clock12, TrendingUp, Activity, CalendarRange, X } from 'lucide-react';
import Card from '../common/Card';
import AnimatedCounter from '../common/AnimatedCounter';
import GradientProgressBar from '../common/GradientProgressBar';

const Analytics = ({ data }) => {
  const [selectedPeriod, setSelectedPeriod] = useState('7days');
  const [showCustomDatePicker, setShowCustomDatePicker] = useState(false);
  const [customStartDate, setCustomStartDate] = useState('');
  const [customEndDate, setCustomEndDate] = useState('');
  const [customDateRange, setCustomDateRange] = useState(null);

  const periods = [
    { 
      value: '1day', 
      label: '1 Day',
      icon: Clock,
      description: 'Today only'
    },
    { 
      value: '3days', 
      label: '3 Days',
      icon: Clock12,
      description: 'Last 3 days'
    },
    { 
      value: '7days', 
      label: 'Weekly',
      icon: Calendar,
      description: 'Last 7 days'
    },
    { 
      value: 'all', 
      label: 'All Time',
      icon: BarChart3,
      description: 'Complete history'
    },
    { 
      value: 'custom', 
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
      setSelectedPeriod('7days');
    }
  };

  // Filter data based on selected period
  const getFilteredData = () => {
    if (selectedPeriod === 'all') return data;
    
    const now = new Date();
    let cutoffDate;
    
    switch (selectedPeriod) {
      case '1day':
        // Get today's data
        const todayStr = `${(now.getMonth() + 1).toString().padStart(2, '0')}/${now.getDate().toString().padStart(2, '0')}/${now.getFullYear()}`;
        return data.filter(item => item.Analysis_Date === todayStr);
        
      case '3days':
        cutoffDate = new Date(now.getTime() - (3 * 24 * 60 * 60 * 1000));
        break;
        
      case '7days':
        cutoffDate = new Date(now.getTime() - (7 * 24 * 60 * 60 * 1000));
        break;
        
      case 'custom':
        if (!customDateRange) return data;
        
        return data.filter(item => {
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
        
      default:
        return data;
    }
    
    return data.filter(item => {
      if (!item.Analysis_Date) return false;
      
      // Parse MM/DD/YYYY format
      const [month, day, year] = item.Analysis_Date.split('/');
      const itemDate = new Date(year, month - 1, day);
      return itemDate >= cutoffDate && itemDate <= now;
    });
  };

  const filteredData = getFilteredData();
  const selectedPeriodData = periods.find(p => p.value === selectedPeriod);

  const stats = [
    {
      icon: Phone,
      title: "Total Calls",
      value: filteredData.length,
      iconColor: "text-blue-600",
      iconBg: "bg-blue-50",
      description: "Calls analyzed",
      progress: {
        value: filteredData.length,
        max: Math.max(filteredData.length, 50),
        variant: "primary"
      }
    },
    {
      icon: Target,
      title: "Performance",
      value: filteredData.length > 0 ? 
        Math.round((filteredData.reduce((sum, item) => sum + (item.Representative_Score || 0), 0) / filteredData.length) * 100) : 
        0,
      suffix: "%",
      iconColor: "text-emerald-600",
      iconBg: "bg-emerald-50",
      description: "Average score",
      progress: {
        value: filteredData.length > 0 ? 
          Math.round((filteredData.reduce((sum, item) => sum + (item.Representative_Score || 0), 0) / filteredData.length) * 100) : 
          0,
        max: 100,
        variant: "success"
      }
    },
    {
      icon: Users,
      title: "Representatives",
      value: filteredData.length > 0 ? 
        new Set(filteredData.map(item => item.Representative_Name).filter(name => name && name !== "Unknown")).size : 
        0,
      iconColor: "text-purple-600",
      iconBg: "bg-purple-50",
      description: "Active team members",
      progress: {
        value: filteredData.length > 0 ? 
          new Set(filteredData.map(item => item.Representative_Name).filter(name => name && name !== "Unknown")).size : 
          0,
        max: 10,
        variant: "purple"
      }
    },
    {
      icon: AlertTriangle,
      title: "Opportunities",
      value: filteredData.filter(item => item.High_Value_Missed_Opportunity === "Yes").length,
      iconColor: "text-amber-600",
      iconBg: "bg-amber-50",
      description: "Improvement areas",
      progress: {
        value: filteredData.filter(item => item.High_Value_Missed_Opportunity === "Yes").length,
        max: Math.max(filteredData.filter(item => item.High_Value_Missed_Opportunity === "Yes").length, 10),
        variant: "warning"
      }
    }
  ];

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200/60 p-8">
      {/* Header Section with Icon */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-8">
        <div className="flex items-center space-x-4 group relative">
          {/* Single Analytics Icon */}
          <div className="bg-blue-50 rounded-xl p-3">
            <TrendingUp className="h-6 w-6 text-blue-600" strokeWidth={2} />
          </div>
          
          {/* Text Content */}
          <div>
            <h1 className="text-2xl font-bold text-slate-900 mb-2">Analytics Overview</h1>
            <p className="text-slate-600">
              {selectedPeriodData?.description} • Comprehensive performance insights
            </p>
          </div>

          {/* Tooltip */}
          <div className="absolute left-0 top-full mt-2 invisible group-hover:visible opacity-0 group-hover:opacity-100 transition-all duration-200 z-50">
            <div className="bg-slate-900 text-white text-sm rounded-lg p-3 shadow-lg w-80">
              <p className="font-medium mb-1">Analytics Overview</p>
              <p className="text-slate-300 text-xs leading-relaxed">
                Track key performance metrics across different time periods. Use the time filters to analyze trends, 
                compare performance, and identify opportunities for improvement.
              </p>
              <div className="absolute -top-1 left-4 w-2 h-2 bg-slate-900 rotate-45"></div>
            </div>
          </div>
        </div>

        {/* Time Period Buttons */}
        <div className="mt-4 sm:mt-0 relative">
          <div className="flex flex-wrap gap-2">
            {periods.map((period) => {
              const IconComponent = period.icon;
              const isSelected = selectedPeriod === period.value;
              
              return (
                <button
                  key={period.value}
                  onClick={() => {
                    if (period.value === 'custom') {
                      setShowCustomDatePicker(true);
                    } else {
                      setSelectedPeriod(period.value);
                    }
                  }}
                  className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                    isSelected
                      ? 'bg-slate-900 text-white shadow-sm'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200 hover:text-slate-700'
                  }`}
                >
                  <IconComponent className="h-4 w-4" strokeWidth={2} />
                  <span>{period.label}</span>
                  {period.value === 'custom' && customDateRange && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        clearCustomDateRange();
                      }}
                      className="ml-1 hover:bg-slate-700 rounded-full p-0.5"
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
            <div className="absolute right-0 top-full mt-2 bg-white border border-slate-200 rounded-xl shadow-lg p-4 z-50 w-80">
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
      </div>
      
      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => (
          <div key={index} className="group">
            <div className="bg-slate-50/50 border border-slate-200/60 rounded-xl p-6 hover:bg-white hover:shadow-md transition-all duration-200">
              <div className="flex items-center justify-between mb-4">
                <div className={`${stat.iconBg} rounded-lg p-3 group-hover:scale-105 transition-transform duration-200 relative group/icon`}>
                  <stat.icon className={`h-5 w-5 ${stat.iconColor}`} strokeWidth={2} />
                  
                  {/* Icon Tooltip */}
                  <div className="absolute left-0 top-full mt-2 invisible group-hover/icon:visible opacity-0 group-hover/icon:opacity-100 transition-all duration-200 z-50">
                    <div className="bg-slate-900 text-white text-xs rounded-lg p-3 shadow-lg w-64">
                      <p className="leading-relaxed">
                        {index === 0 && "Track total number of calls processed during the selected period"}
                        {index === 1 && "Average representative performance score based on call quality"}
                        {index === 2 && "Number of unique representatives who handled calls"}
                        {index === 3 && "High-value business opportunities that were missed during calls"}
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
                <div className="text-3xl font-bold text-slate-900">
                  <AnimatedCounter target={stat.value} suffix={stat.suffix || ""} />
                </div>
                
                <GradientProgressBar 
                  value={stat.progress.value} 
                  max={stat.progress.max} 
                  variant={stat.progress.variant}
                  size="sm"
                  animated={true}
                />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Analytics;