import React, { useState } from 'react';
import { Trophy, Medal, Award, X, Phone, TrendingUp, Calendar, Clock, BarChart3, Target } from 'lucide-react';
import Card from '../common/Card';
import { getGrade, getScoreColor } from '../../utils/helpers';

const TopPerformers = ({ data, rawData = [] }) => {
  const [selectedPerformer, setSelectedPerformer] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [expandedSummaries, setExpandedSummaries] = useState(new Set());

  const icons = [Trophy, Medal, Award];
  const positions = ['1st', '2nd', '3rd'];
  
  // Updated color scheme - much more appealing gradients and colors
  const gradients = [
    'from-blue-50 via-indigo-50 to-purple-50',
    'from-emerald-50 via-teal-50 to-cyan-50', 
    'from-violet-50 via-purple-50 to-pink-50'
  ];
  
  const badgeColors = [
    'bg-gradient-to-r from-blue-500 to-purple-600 text-white border-0',
    'bg-gradient-to-r from-emerald-500 to-teal-600 text-white border-0',
    'bg-gradient-to-r from-violet-500 to-purple-600 text-white border-0'
  ];

  const iconColors = [
    'text-blue-600',
    'text-emerald-600',
    'text-violet-600'
  ];

  const toggleSummary = (callIndex) => {
    const newExpanded = new Set(expandedSummaries);
    if (newExpanded.has(callIndex)) {
      newExpanded.delete(callIndex);
    } else {
      newExpanded.add(callIndex);
    }
    setExpandedSummaries(newExpanded);
  };

  const handlePerformerClick = (performer) => {
    const performerData = getPerformerAnalytics(performer.name, rawData);
    setSelectedPerformer(performerData);
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setSelectedPerformer(null);
    setExpandedSummaries(new Set());
  };

  // Generate detailed analytics for a specific performer
  const getPerformerAnalytics = (performerName, allData) => {
    const performerCalls = allData.filter(call => {
      const name = call.Representative_Name || call.representative_name || call.RepresentativeName;
      return name === performerName;
    });

    if (performerCalls.length === 0) {
      return {
        name: performerName,
        totalCalls: 0,
        averageScore: 0,
        grade: 'F',
        callsThisWeek: 0,
        callsToday: 0,
        highValueMissed: 0,
        callTypes: [],
        dailyBreakdown: [],
        recentCalls: [],
        performanceTrend: 'stable'
      };
    }

    // Calculate basic metrics
    const totalCalls = performerCalls.length;
    
    // Extract scores, handling different formats
    const scores = performerCalls
      .map(call => {
        let score = call.Representative_Score || call.representative_score || call.RepresentativeScore;
        if (typeof score === 'string') {
          score = parseFloat(score);
        }
        return score;
      })
      .filter(score => score && !isNaN(score) && score > 0);
      
    const averageScore = scores.length > 0 ? scores.reduce((sum, score) => sum + score, 0) / scores.length : 0;
    const grade = getGrade(averageScore);

    // Time-based filtering - handle your MM/DD/YYYY format
    const today = new Date();
    const todayStr = `${(today.getMonth() + 1).toString().padStart(2, '0')}/${today.getDate().toString().padStart(2, '0')}/${today.getFullYear()}`;
    const weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);

    const callsToday = performerCalls.filter(call => {
      const callDate = call.Analysis_Date || call.analysis_date || call.AnalysisDate;
      return callDate === todayStr;
    }).length;
    
    const callsThisWeek = performerCalls.filter(call => {
      const callDate = call.Analysis_Date || call.analysis_date || call.AnalysisDate;
      if (!callDate) return false;
      try {
        const [month, day, year] = callDate.split('/');
        const callDateObj = new Date(year, month - 1, day);
        return callDateObj >= weekAgo && callDateObj <= today;
      } catch (e) {
        return false;
      }
    }).length;

    // High value missed opportunities - handle different field formats
    const highValueMissed = performerCalls.filter(call => {
      const missed = call.High_Value_Missed_Opportunity || 
                    call.high_value_missed_opportunity || 
                    call.HighValueMissedOpportunity;
      return missed === true || missed === 'true' || missed === 'TRUE';
    }).length;

    // Call types analysis - handle different field names
    const callTypesCount = performerCalls.reduce((acc, call) => {
      const summary = (call.Call_Summary || call.call_summary || call.CallSummary || "").toLowerCase();
      let type = "General Inquiry";
      if (/appointment|booking|schedule/.test(summary)) type = "Appointment Booking";
      else if (/emergency|pain|urgent|swollen|tooth.*coming|hurt/i.test(summary)) type = "Emergency";
      else if (/insurance|verification|coverage/.test(summary)) type = "Insurance Inquiry";
      else if (/reschedule|confirm/.test(summary)) type = "Appointment Management";
      
      acc[type] = (acc[type] || 0) + 1;
      return acc;
    }, {});

    const callTypes = Object.entries(callTypesCount).map(([type, count]) => ({
      type,
      count,
      percentage: totalCalls > 0 ? ((count / totalCalls) * 100).toFixed(1) : '0.0'
    }));

    // Daily breakdown for the last 7 days
    const dailyBreakdown = [];
    for (let i = 6; i >= 0; i--) {
      const date = new Date(today.getTime() - i * 24 * 60 * 60 * 1000);
      const dateStr = `${(date.getMonth() + 1).toString().padStart(2, '0')}/${date.getDate().toString().padStart(2, '0')}/${date.getFullYear()}`;
      
      const dayCalls = performerCalls.filter(call => {
        const callDate = call.Analysis_Date || call.analysis_date || call.AnalysisDate;
        return callDate === dateStr;
      });
      
      const dayScores = dayCalls.map(call => {
        let score = call.Representative_Score || call.representative_score || call.RepresentativeScore;
        if (typeof score === 'string') score = parseFloat(score);
        return score;
      }).filter(score => score && !isNaN(score) && score > 0);
      
      const avgScore = dayScores.length > 0 ? dayScores.reduce((sum, score) => sum + score, 0) / dayScores.length : 0;

      dailyBreakdown.push({
        date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        calls: dayCalls.length,
        averageScore: avgScore,
        fullDate: dateStr
      });
    }

    // Recent calls (last 5) - sort by date properly
    const recentCalls = performerCalls
      .sort((a, b) => {
        const dateA = a.Analysis_Date || a.analysis_date || a.AnalysisDate || '';
        const dateB = b.Analysis_Date || b.analysis_date || b.AnalysisDate || '';
        // Sort by date descending (most recent first)
        if (dateA && dateB) {
          try {
            const [monthA, dayA, yearA] = dateA.split('/');
            const [monthB, dayB, yearB] = dateB.split('/');
            const dateObjA = new Date(yearA, monthA - 1, dayA);
            const dateObjB = new Date(yearB, monthB - 1, dayB);
            return dateObjB - dateObjA;
          } catch (e) {
            return 0;
          }
        }
        return 0;
      })
      .slice(0, 5)
      .map(call => {
        let score = call.Representative_Score || call.representative_score || call.RepresentativeScore || 0;
        if (typeof score === 'string') score = parseFloat(score);
        if (isNaN(score)) score = 0;
        
        const missed = call.High_Value_Missed_Opportunity || 
                      call.high_value_missed_opportunity || 
                      call.HighValueMissedOpportunity;
        
        return {
          fileName: call.Call_File_Name || call.call_file_name || call.CallFileName || 'Unknown',
          date: call.Analysis_Date || call.analysis_date || call.AnalysisDate || 'Unknown',
          score: score,
          grade: getGrade(score),
          summary: call.Call_Summary || call.call_summary || call.CallSummary || 'No summary available',
          highValueMissed: missed === true || missed === 'true' || missed === 'TRUE'
        };
      });

    return {
      name: performerName,
      totalCalls,
      averageScore,
      grade,
      callsThisWeek,
      callsToday,
      highValueMissed,
      callTypes,
      dailyBreakdown,
      recentCalls
    };
  };

  return (
    <>
      <Card className="h-full" hover={true}>
        {/* Header */}
        <div className="flex items-center space-x-4 mb-8">
          <div className="bg-blue-50 rounded-xl p-3">
            <Trophy className="h-6 w-6 text-blue-600" strokeWidth={2} />
          </div>
          <div>
            <h3 className="text-xl font-bold text-slate-900">Top Performers</h3>
            <p className="text-sm text-slate-600">Click any performer for detailed analytics</p>
          </div>
        </div>

        {/* Performers List */}
        {data && data.length > 0 ? (
          <div className="space-y-6">
            {data.slice(0, 3).map((performer, index) => {
              const IconComponent = icons[index];
              const score = Math.round(performer.averageScore * 100);
              
              return (
                <div 
                  key={performer.name}
                  onClick={() => handlePerformerClick(performer)}
                  className={`bg-gradient-to-r ${gradients[index]} border border-white/80 rounded-xl p-6 hover:shadow-lg hover:scale-[1.02] transition-all duration-300 cursor-pointer group`}
                >
                  <div className="flex items-start justify-between">
                    {/* Left side - Icon and Info */}
                    <div className="flex items-center space-x-4">
                      <div className="flex-shrink-0">
                        <div className="relative">
                          <div className="w-12 h-12 bg-white rounded-xl flex items-center justify-center shadow-md border border-white/50 group-hover:scale-110 transition-transform duration-200">
                            <IconComponent className={`h-6 w-6 ${iconColors[index]}`} strokeWidth={2} />
                          </div>
                          <div className="absolute -top-2 -right-2">
                            <span className={`inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-bold shadow-sm ${badgeColors[index]}`}>
                              {index + 1}
                            </span>
                          </div>
                        </div>
                      </div>
                      
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <h4 className="text-lg font-bold text-slate-900 truncate group-hover:text-slate-700 transition-colors">
                            {performer.name}
                          </h4>
                          <span className="text-sm font-medium text-slate-600 bg-white/70 px-2 py-1 rounded-md">
                            {positions[index]}
                          </span>
                        </div>
                        <p className="text-sm text-slate-700 mb-3 font-medium">
                          {performer.callCount} call{performer.callCount !== 1 ? 's' : ''} handled
                        </p>
                        
                        {/* Performance Score */}
                        <div className="flex items-center space-x-3">
                          <span className="text-xs font-medium text-slate-600 uppercase tracking-wide">
                            Performance Score
                          </span>
                          <div className="flex items-center space-x-2">
                            <span className="text-lg font-bold text-slate-900">
                              {score}%
                            </span>
                            <span 
                              className="text-xs font-bold px-2.5 py-1 rounded-md shadow-sm"
                              style={{ 
                                backgroundColor: getScoreColor(performer.averageScore) + '15',
                                color: getScoreColor(performer.averageScore),
                                border: `1px solid ${getScoreColor(performer.averageScore)}25`
                              }}
                            >
                              Grade {performer.grade}
                            </span>
                          </div>
                        </div>
                        
                        {/* Click hint */}
                        <div className="mt-3 text-xs text-slate-500 group-hover:text-blue-600 transition-colors">
                          Click for detailed analytics →
                        </div>
                      </div>
                    </div>

                    {/* Right side - Score Circle */}
                    <div className="flex-shrink-0 ml-4">
                      <div className="relative w-16 h-16">
                        <svg className="w-16 h-16 -rotate-90" viewBox="0 0 36 36">
                          <path
                            className="text-slate-300"
                            stroke="currentColor"
                            strokeWidth="3"
                            fill="transparent"
                            d="M18 2.0845
                              a 15.9155 15.9155 0 0 1 0 31.831
                              a 15.9155 15.9155 0 0 1 0 -31.831"
                          />
                          <path
                            className={iconColors[index]}
                            stroke="currentColor"
                            strokeWidth="3"
                            strokeDasharray={`${score}, 100`}
                            strokeLinecap="round"
                            fill="transparent"
                            d="M18 2.0845
                              a 15.9155 15.9155 0 0 1 0 31.831
                              a 15.9155 15.9155 0 0 1 0 -31.831"
                          />
                        </svg>
                        <div className="absolute inset-0 flex items-center justify-center">
                          <span className="text-xs font-bold text-slate-800">
                            {score}%
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="h-64 flex items-center justify-center">
            <div className="text-center">
              <div className="w-20 h-20 bg-slate-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <Trophy className="h-8 w-8 text-slate-400" strokeWidth={1.5} />
              </div>
              <p className="text-slate-600 font-medium text-sm">No performance data available</p>
              <p className="text-slate-400 text-xs mt-1">Top performers will appear here</p>
            </div>
          </div>
        )}
      </Card>

      {/* Analytics Modal */}
      {showModal && selectedPerformer && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-6 border-b border-slate-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 bg-white rounded-xl flex items-center justify-center shadow-md">
                    <BarChart3 className="h-6 w-6 text-blue-600" strokeWidth={2} />
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold text-slate-900">{selectedPerformer.name}</h2>
                    <p className="text-sm text-slate-600">Detailed Performance Analytics</p>
                  </div>
                </div>
                <button
                  onClick={closeModal}
                  className="text-slate-400 hover:text-slate-600 transition-colors p-2 hover:bg-white/50 rounded-lg"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>
            </div>

            {/* Modal Content */}
            <div className="p-6 space-y-8">
              {/* Key Metrics Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-slate-50 rounded-xl p-4 text-center">
                  <Phone className="h-6 w-6 text-blue-600 mx-auto mb-2" />
                  <div className="text-2xl font-bold text-slate-900">{selectedPerformer.totalCalls}</div>
                  <div className="text-xs text-slate-600">Total Calls</div>
                </div>
                <div className="bg-slate-50 rounded-xl p-4 text-center">
                  <TrendingUp className="h-6 w-6 text-emerald-600 mx-auto mb-2" />
                  <div className="text-2xl font-bold text-slate-900">{Math.round(selectedPerformer.averageScore * 100)}%</div>
                  <div className="text-xs text-slate-600">Avg Score</div>
                </div>
                <div className="bg-slate-50 rounded-xl p-4 text-center">
                  <Calendar className="h-6 w-6 text-violet-600 mx-auto mb-2" />
                  <div className="text-2xl font-bold text-slate-900">{selectedPerformer.callsThisWeek}</div>
                  <div className="text-xs text-slate-600">This Week</div>
                </div>
                <div className="bg-slate-50 rounded-xl p-4 text-center">
                  <Target className="h-6 w-6 text-amber-600 mx-auto mb-2" />
                  <div className="text-2xl font-bold text-slate-900">{selectedPerformer.highValueMissed}</div>
                  <div className="text-xs text-slate-600">Opportunities</div>
                </div>
              </div>

              {/* Daily Breakdown */}
              <div className="bg-slate-50 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-slate-900 mb-4">7-Day Activity</h3>
                <div className="grid grid-cols-7 gap-2">
                  {selectedPerformer.dailyBreakdown.map((day, index) => (
                    <div key={index} className="text-center">
                      <div className="text-xs text-slate-600 mb-1">{day.date}</div>
                      <div className={`w-full h-12 rounded-lg flex items-center justify-center text-xs font-medium ${
                        day.calls > 0 ? 'bg-blue-100 text-blue-800' : 'bg-slate-200 text-slate-500'
                      }`}>
                        {day.calls}
                      </div>
                      {day.calls > 0 && (
                        <div className="text-xs text-slate-500 mt-1">
                          {Math.round(day.averageScore * 100)}%
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Call Types */}
              <div className="bg-slate-50 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-slate-900 mb-4">Call Types Distribution</h3>
                <div className="space-y-3">
                  {selectedPerformer.callTypes.map((callType, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <span className="text-sm text-slate-700">{callType.type}</span>
                      <div className="flex items-center space-x-2">
                        <div className="w-24 bg-slate-200 rounded-full h-2">
                          <div 
                            className="bg-blue-500 h-2 rounded-full" 
                            style={{ width: `${callType.percentage}%` }}
                          ></div>
                        </div>
                        <span className="text-xs text-slate-600 w-12 text-right">
                          {callType.count} ({callType.percentage}%)
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Recent Calls */}
              <div className="bg-slate-50 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-slate-900 mb-4">Recent Calls</h3>
                <div className="space-y-3">
                  {selectedPerformer.recentCalls.map((call, index) => {
                    const isExpanded = expandedSummaries.has(index);
                    const summaryPreview = call.summary.length > 150 
                      ? call.summary.substring(0, 150) + "..." 
                      : call.summary;
                    const shouldShowExpand = call.summary.length > 150;
                    
                    return (
                      <div key={index} className="bg-white rounded-lg p-4 border border-slate-200">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center space-x-3 mb-2">
                              <span className="text-sm font-medium text-slate-900">{call.fileName}</span>
                              <span className="text-xs text-slate-500">{call.date}</span>
                              {call.highValueMissed && (
                                <span className="text-xs bg-red-100 text-red-700 px-2 py-1 rounded-md">
                                  High Value Missed
                                </span>
                              )}
                            </div>
                            
                            {/* Clickable Summary */}
                            <div className="text-xs text-slate-600 leading-relaxed">
                              <p className="mb-2">
                                {isExpanded ? call.summary : summaryPreview}
                              </p>
                              
                              {shouldShowExpand && (
                                <button
                                  onClick={() => toggleSummary(index)}
                                  className="text-blue-600 hover:text-blue-700 font-medium transition-colors duration-200 text-xs"
                                >
                                  {isExpanded ? 'Show Less' : 'Read More'}
                                </button>
                              )}
                            </div>
                          </div>
                          <div className="text-right ml-4">
                            <div className="text-lg font-bold text-slate-900">
                              {Math.round(call.score * 100)}%
                            </div>
                            <div 
                              className="text-xs font-bold px-2 py-1 rounded-md"
                              style={{ 
                                backgroundColor: getScoreColor(call.score) + '20',
                                color: getScoreColor(call.score)
                              }}
                            >
                              {call.grade}
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default TopPerformers;