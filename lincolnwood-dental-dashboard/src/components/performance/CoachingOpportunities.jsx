import React from 'react';
import { Users, Clock, BookOpen, Target } from 'lucide-react';
import Card from '../common/Card';
import { getScoreColor } from '../../utils/helpers';

const CoachingOpportunities = ({ data }) => {
  const getPriorityInfo = (score) => {
    if (score < 0.6) return { level: 'High Priority', color: 'bg-red-100 text-red-800 border-red-200' };
    if (score < 0.75) return { level: 'Medium Priority', color: 'bg-amber-100 text-amber-800 border-amber-200' };
    return { level: 'Low Priority', color: 'bg-green-100 text-green-800 border-green-200' };
  };

  const getCoachingFocus = () => [
    'Communication refinement',
    'Appointment booking efficiency', 
    'Problem resolution'
  ];

  return (
    <Card className="h-full" hover={true}>
      {/* Header */}
      <div className="flex items-center space-x-4 mb-8">
        <div className="bg-blue-50 rounded-xl p-3">
          <Target className="h-6 w-6 text-blue-600" strokeWidth={2} />
        </div>
        <div>
          <h3 className="text-xl font-bold text-slate-900">Coaching Opportunities</h3>
          <p className="text-sm text-slate-600">Development areas and recommendations</p>
        </div>
      </div>

      {/* Coaching List */}
      {data && data.length > 0 ? (
        <div className="space-y-6">
          {data.slice(0, 3).map((performer, index) => {
            const score = Math.round(performer.averageScore * 100);
            const priority = getPriorityInfo(performer.averageScore);
            const focusAreas = getCoachingFocus();
            
            return (
              <div 
                key={performer.name}
                className="bg-slate-50/50 border border-slate-200/60 rounded-xl p-6 hover:bg-white hover:shadow-md transition-all duration-200"
              >
                {/* Header Row */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h4 className="text-lg font-bold text-slate-900">
                        {performer.name}
                      </h4>
                      <span className={`inline-flex items-center px-2 py-1 rounded-lg text-xs font-medium border ${priority.color}`}>
                        {priority.level}
                      </span>
                    </div>
                    <p className="text-sm text-slate-600">
                      {performer.callCount} call{performer.callCount !== 1 ? 's' : ''} analyzed
                    </p>
                  </div>
                  
                  {/* Performance Score */}
                  <div className="text-right">
                    <div className="flex items-center space-x-2 mb-1">
                      <span className="text-2xl font-bold text-slate-900">
                        {score}%
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 uppercase tracking-wide">Performance</p>
                  </div>
                </div>

                {/* Development Focus */}
                <div className="mb-6">
                  <h5 className="text-sm font-semibold text-slate-900 mb-3 flex items-center">
                    <BookOpen className="h-4 w-4 mr-2 text-blue-600" />
                    Development Focus
                  </h5>
                  <div className="grid grid-cols-1 gap-2">
                    {focusAreas.map((area, areaIndex) => (
                      <div key={areaIndex} className="flex items-center space-x-2">
                        <div className="w-1.5 h-1.5 bg-blue-500 rounded-full"></div>
                        <span className="text-sm text-slate-600">{area}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Session Details */}
                <div className="bg-white rounded-lg p-4 border border-slate-200/60">
                  <h5 className="text-sm font-semibold text-slate-900 mb-3 flex items-center">
                    <Clock className="h-4 w-4 mr-2 text-slate-600" />
                    Session Details
                  </h5>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-xs text-slate-500 uppercase tracking-wide mb-1">Duration</p>
                      <p className="text-sm font-medium text-slate-900">15-20 minutes</p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-500 uppercase tracking-wide mb-1">Format</p>
                      <p className="text-sm font-medium text-slate-900">One-on-one</p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-500 uppercase tracking-wide mb-1">Resources</p>
                      <p className="text-sm font-medium text-emerald-600">Available</p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-500 uppercase tracking-wide mb-1">Grade</p>
                      <span 
                        className="text-xs font-bold px-2 py-1 rounded-md"
                        style={{ 
                          backgroundColor: getScoreColor(performer.averageScore) + '20',
                          color: getScoreColor(performer.averageScore)
                        }}
                      >
                        {performer.grade}
                      </span>
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
              <Target className="h-8 w-8 text-slate-400" strokeWidth={1.5} />
            </div>
            <p className="text-slate-600 font-medium text-sm">No coaching opportunities identified</p>
            <p className="text-slate-400 text-xs mt-1">Recommendations will appear based on performance data</p>
          </div>
        </div>
      )}
    </Card>
  );
};

export default CoachingOpportunities;