import React, { useState } from 'react';
import { Phone, Target, Users, AlertTriangle, BarChart3, Calendar, Clock, Clock12, TrendingUp, Activity } from 'lucide-react';
import Card from '../common/Card';
import AnimatedCounter from '../common/AnimatedCounter';
import GradientProgressBar from '../common/GradientProgressBar';

const Analytics = ({ data }) => {
  const [selectedPeriod, setSelectedPeriod] = useState('7days');

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
    }
  ];

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
        value: filteredData.length > 0 ? (filteredData.reduce((sum, item) => sum + (item.Representative_Score || 0), 0) / filteredData.length) * 100 : 0,
        max: 100,
        variant: "success"
      }
    },
    {
      icon: Users,
      title: "Representatives",
      value: new Set(filteredData.map(item => item.Representative_Name || 'Unknown')).size,
      iconColor: "text-violet-600",
      iconBg: "bg-violet-50",
      description: "Active team members",
      progress: {
        value: new Set(filteredData.map(item => item.Representative_Name || 'Unknown')).size,
        max: Math.max(new Set(filteredData.map(item => item.Representative_Name || 'Unknown')).size, 10),
        variant: "primary"
      }
    },
    {
      icon: AlertTriangle,
      title: "Opportunities",
      value: filteredData.filter(item => item.High_Value_Missed_Opportunity).length,
      iconColor: "text-amber-600",
      iconBg: "bg-amber-50",
      description: "Improvement areas",
      progress: {
        value: Math.max(0, 100 - (filteredData.filter(item => item.High_Value_Missed_Opportunity).length * 5)),
        max: 100,
        variant: filteredData.filter(item => item.High_Value_Missed_Opportunity).length > 10 ? "error" : "warning"
      }
    }
  ];

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200/60 p-8">
      {/* Header Section with Icon */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-8">
        <div className="flex items-center space-x-4">
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
        </div>

        {/* Time Period Buttons */}
        <div className="mt-4 sm:mt-0">
          <div className="flex flex-wrap gap-2">
            {periods.map((period) => {
              const IconComponent = period.icon;
              const isSelected = selectedPeriod === period.value;
              
              return (
                <button
                  key={period.value}
                  onClick={() => setSelectedPeriod(period.value)}
                  className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                    isSelected
                      ? 'bg-slate-900 text-white shadow-sm'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200 hover:text-slate-700'
                  }`}
                >
                  <IconComponent className="h-4 w-4" strokeWidth={2} />
                  <span>{period.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      </div>
      
      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => (
          <div key={index} className="group">
            <div className="bg-slate-50/50 border border-slate-200/60 rounded-xl p-6 hover:bg-white hover:shadow-md transition-all duration-200">
              <div className="flex items-center justify-between mb-4">
                <div className={`${stat.iconBg} rounded-lg p-3 group-hover:scale-105 transition-transform duration-200`}>
                  <stat.icon className={`h-5 w-5 ${stat.iconColor}`} strokeWidth={2} />
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