import React from 'react';
import { Phone, TrendingUp, Users, AlertTriangle, Calendar } from 'lucide-react';
import AnimatedCounter from '../common/AnimatedCounter';
import { getGrade, getScoreColor } from '../../utils/helpers';

const StatsCards = ({ todayStats }) => {
  const stats = [
    {
      icon: Phone,
      title: "Today's Calls",
      value: todayStats.totalCalls,
      iconColor: "text-blue-600",
      iconBg: "bg-blue-50",
      bgGradient: "from-blue-50 to-blue-100/50"
    },
    {
      icon: TrendingUp,
      title: "Average Score",
      value: Math.round(todayStats.avgScore * 100),
      suffix: "%",
      iconColor: "text-emerald-600",
      iconBg: "bg-emerald-50",
      bgGradient: "from-emerald-50 to-emerald-100/50",
      grade: getGrade(todayStats.avgScore)
    },
    {
      icon: Users,
      title: "Active Reps",
      value: todayStats.uniqueReps,
      iconColor: "text-violet-600",
      iconBg: "bg-violet-50",
      bgGradient: "from-violet-50 to-violet-100/50"
    },
    {
      icon: AlertTriangle,
      title: "Opportunities",
      value: todayStats.highValueMissed,
      iconColor: "text-amber-600",
      iconBg: "bg-amber-50",
      bgGradient: "from-amber-50 to-amber-100/50"
    }
  ];

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200/60 p-8">
      {/* Section Header */}
      <div className="flex items-center space-x-4 mb-8">
        <div className="bg-blue-50 rounded-xl p-3">
          <Calendar className="h-6 w-6 text-blue-600" strokeWidth={2} />
        </div>
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Daily Analytics</h2>
          <p className="text-sm text-slate-600">
            Real-time performance metrics for {new Date().toLocaleDateString('en-US', { 
              weekday: 'long', 
              year: 'numeric', 
              month: 'long', 
              day: 'numeric' 
            })}
          </p>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => (
          <div key={index} className="group">
            <div className={`bg-gradient-to-br ${stat.bgGradient} border border-white/60 rounded-xl p-6 hover:shadow-lg hover:scale-[1.02] transition-all duration-300`}>
              <div className="flex items-center justify-between mb-4">
                <div className={`${stat.iconBg} rounded-lg p-3 shadow-sm group-hover:shadow-md transition-all duration-200`}>
                  <stat.icon className={`h-6 w-6 ${stat.iconColor}`} strokeWidth={2} />
                </div>
                {stat.grade && (
                  <div className="text-right">
                    <span 
                      className="text-xs font-bold px-2 py-1 rounded-md"
                      style={{ 
                        backgroundColor: getScoreColor(todayStats.avgScore) + '20',
                        color: getScoreColor(todayStats.avgScore)
                      }}
                    >
                      Grade {stat.grade}
                    </span>
                  </div>
                )}
              </div>
              
              <div className="space-y-2">
                <h3 className="text-sm font-medium text-slate-600 uppercase tracking-wide">
                  {stat.title}
                </h3>
                <div className="text-3xl font-bold text-slate-900">
                  <AnimatedCounter target={stat.value} suffix={stat.suffix || ""} />
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default StatsCards;