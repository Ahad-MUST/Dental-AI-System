import React, { useState } from 'react';
import { 
  Calendar, 
  User, 
  Clock, 
  Heart, 
  TrendingUp, 
  Tag, 
  FileText, 
  ChevronDown, 
  ChevronUp,
  CheckCircle2,
  Circle
} from 'lucide-react';

const CallList = ({ calls, selectedCalls, onCallSelection }) => {
  const [expandedCall, setExpandedCall] = useState(null);

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown';
    try {
      // Handle ISO format dates
      if (dateString.includes('T')) {
        return new Date(dateString).toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
          year: 'numeric',
          hour: '2-digit',
          minute: '2-digit'
        });
      }
      // Handle MM/DD/YYYY format
      if (dateString.includes('/')) {
        const [month, day, year] = dateString.split('/');
        const date = new Date(year, month - 1, day);
        return date.toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
          year: 'numeric'
        });
      }
      // Fallback
      return new Date(dateString).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      });
    } catch (error) {
      console.warn('Date formatting error:', error);
      return dateString;
    }
  };

  const formatDuration = (seconds) => {
    if (!seconds) return '0:00';
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const getPerformanceColor = (score) => {
    if (!score || score === 0) return 'text-gray-600 bg-gray-50';
    if (score >= 85) return 'text-green-600 bg-green-50';
    if (score >= 70) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  const getSentimentColor = (sentiment) => {
    if (!sentiment) return 'text-gray-600 bg-gray-50';
    switch (sentiment.toLowerCase()) {
      case 'positive': return 'text-green-600 bg-green-50';
      case 'negative': return 'text-red-600 bg-red-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getSentimentIcon = (sentiment) => {
    if (!sentiment) return '😐';
    switch (sentiment.toLowerCase()) {
      case 'positive': return '😊';
      case 'negative': return '😟';
      default: return '😐';
    }
  };

  const truncateText = (text, maxLength = 100) => {
    if (!text || text.length <= maxLength) return text || 'No summary available';
    return text.substring(0, maxLength) + '...';
  };

  const toggleExpand = (callId) => {
    setExpandedCall(expandedCall === callId ? null : callId);
  };

  const isSelected = (callId) => {
    // Ensure callId is converted to string for comparison
    const callIdStr = String(callId);
    return selectedCalls.some(selectedId => String(selectedId) === callIdStr);
  };

  const formatCallTag = (callTag) => {
    if (!callTag || callTag === 'general_inquiry') return 'General Inquiry';
    return callTag.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  // Debug logging
  React.useEffect(() => {
    console.log('CallList rendered with:', {
      callsCount: calls.length,
      selectedCallsCount: selectedCalls.length,
      firstCallId: calls[0]?.id,
      selectedCallIds: selectedCalls
    });
  }, [calls, selectedCalls]);

  if (!calls || calls.length === 0) {
    return (
      <div className="bg-white rounded-lg border border-slate-200 p-8 text-center">
        <div className="text-slate-500 mb-2">📞</div>
        <h3 className="text-lg font-semibold text-slate-900 mb-2">No Calls Available</h3>
        <p className="text-slate-600">No calls match your current filters.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {calls.map((call) => {
        const callId = String(call.id); // Ensure ID is string
        const selected = isSelected(callId);
        const expanded = expandedCall === callId;
        
        return (
          <div
            key={callId}
            className={`bg-white rounded-lg border transition-all duration-200 ${
              selected 
                ? 'border-blue-500 bg-blue-50/30 shadow-md' 
                : 'border-slate-200 hover:border-slate-300 hover:shadow-sm'
            }`}
          >
            {/* Main Call Card */}
            <div className="p-6">
              {/* Header Row */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-start space-x-4 flex-1">
                  {/* Selection Checkbox */}
                  <button
                    onClick={() => {
                      console.log('Selection clicked:', { callId, selected });
                      onCallSelection(callId, !selected);
                    }}
                    className={`mt-1 transition-colors ${
                      selected ? 'text-blue-600' : 'text-slate-400 hover:text-slate-600'
                    }`}
                  >
                    {selected ? (
                      <CheckCircle2 className="h-5 w-5" />
                    ) : (
                      <Circle className="h-5 w-5" />
                    )}
                  </button>

                  {/* Call Info */}
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h3 className="text-lg font-semibold text-slate-900">
                        {call.representative_name || 'Unknown Employee'}
                      </h3>
                      
                      {/* Performance Score */}
                      <div className={`px-2 py-1 rounded-full text-sm font-medium ${getPerformanceColor(call.representative_score)}`}>
                        {call.representative_score ? Math.round(call.representative_score) : 0}%
                      </div>
                      
                      {/* Call Tag */}
                      {call.call_tag && (
                        <div className="flex items-center space-x-1 px-2 py-1 bg-slate-100 rounded-full text-xs font-medium text-slate-600">
                          <Tag className="h-3 w-3" />
                          <span>{formatCallTag(call.call_tag)}</span>
                        </div>
                      )}
                    </div>

                    {/* Meta Info */}
                    <div className="flex items-center space-x-4 text-sm text-slate-600 mb-3">
                      <div className="flex items-center space-x-1">
                        <Calendar className="h-4 w-4" />
                        <span>{formatDate(call.analysis_date)}</span>
                      </div>
                      
                      {call.call_duration && (
                        <div className="flex items-center space-x-1">
                          <Clock className="h-4 w-4" />
                          <span>{formatDuration(call.call_duration)}</span>
                        </div>
                      )}
                      
                      {call.overall_sentiment && (
                        <div className={`flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium ${getSentimentColor(call.overall_sentiment)}`}>
                          <span>{getSentimentIcon(call.overall_sentiment)}</span>
                          <span>{call.overall_sentiment}</span>
                        </div>
                      )}
                    </div>

                    {/* Call Summary */}
                    <p className="text-slate-700 leading-relaxed">
                      {truncateText(call.call_summary, 150)}
                    </p>
                  </div>
                </div>

                {/* Expand Button */}
                <button
                  onClick={() => toggleExpand(callId)}
                  className="ml-4 p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
                >
                  {expanded ? (
                    <ChevronUp className="h-5 w-5" />
                  ) : (
                    <ChevronDown className="h-5 w-5" />
                  )}
                </button>
              </div>

              {/* Quick Coaching Indicators */}
              <div className="flex items-center justify-between pt-4 border-t border-slate-100">
                <div className="flex items-center space-x-4">
                  {/* Missed Opportunities */}
                  {call.high_value_missed_opportunity && (
                    <div className="flex items-center space-x-1 text-amber-600">
                      <div className="w-2 h-2 bg-amber-500 rounded-full"></div>
                      <span className="text-xs font-medium">Missed Opportunity</span>
                    </div>
                  )}
                  
                  {/* Coaching Potential */}
                  {call.coaching_analysis?.is_coaching_candidate && (
                    <div className="flex items-center space-x-1 text-blue-600">
                      <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                      <span className="text-xs font-medium">Coaching Candidate</span>
                    </div>
                  )}
                </div>

                <div className="text-xs text-slate-500">
                  {selected ? 'Selected for coaching analysis' : 'Click to select'}
                </div>
              </div>
            </div>

            {/* Expanded Content */}
            {expanded && (
              <div className="border-t border-slate-200 bg-slate-50/30">
                <div className="p-6 space-y-6">
                  {/* Performance Details */}
                  {call.performance_analysis && (
                    <div>
                      <h4 className="text-sm font-semibold text-slate-900 mb-3 flex items-center">
                        <TrendingUp className="h-4 w-4 mr-2 text-blue-600" />
                        Performance Analysis
                      </h4>
                      <div className="bg-white rounded-lg p-4 border border-slate-200">
                        {call.performance_analysis.strengths && call.performance_analysis.strengths.length > 0 && (
                          <div className="mb-4">
                            <div className="text-sm font-medium text-green-700 mb-2">Strengths:</div>
                            <ul className="space-y-1">
                              {call.performance_analysis.strengths.map((strength, index) => (
                                <li key={index} className="text-sm text-slate-700 flex items-start">
                                  <span className="text-green-500 mr-2">✓</span>
                                  {strength}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                        
                        {call.performance_analysis.weaknesses && call.performance_analysis.weaknesses.length > 0 && (
                          <div className="mb-4">
                            <div className="text-sm font-medium text-red-700 mb-2">Areas for Improvement:</div>
                            <ul className="space-y-1">
                              {call.performance_analysis.weaknesses.map((weakness, index) => (
                                <li key={index} className="text-sm text-slate-700 flex items-start">
                                  <span className="text-red-500 mr-2">•</span>
                                  {weakness}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                        
                        {call.performance_analysis.coaching_focus && call.performance_analysis.coaching_focus.length > 0 && (
                          <div>
                            <div className="text-sm font-medium text-blue-700 mb-2">Coaching Focus:</div>
                            <ul className="space-y-1">
                              {call.performance_analysis.coaching_focus.map((focus, index) => (
                                <li key={index} className="text-sm text-slate-700 flex items-start">
                                  <span className="text-blue-500 mr-2">→</span>
                                  {focus}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Transcripts */}
                  <div>
                    <h4 className="text-sm font-semibold text-slate-900 mb-3 flex items-center">
                      <FileText className="h-4 w-4 mr-2 text-blue-600" />
                      Call Transcripts
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Patient Transcript */}
                      {call.patient_transcript && (
                        <div className="bg-white rounded-lg p-4 border border-slate-200">
                          <div className="text-sm font-medium text-slate-700 mb-2 flex items-center">
                            <User className="h-4 w-4 mr-1" />
                            Patient
                          </div>
                          <div className="text-sm text-slate-600 max-h-40 overflow-y-auto">
                            {call.patient_transcript}
                          </div>
                        </div>
                      )}
                      
                      {/* Staff Transcript */}
                      {call.staff_transcript && (
                        <div className="bg-white rounded-lg p-4 border border-slate-200">
                          <div className="text-sm font-medium text-slate-700 mb-2 flex items-center">
                            <User className="h-4 w-4 mr-1" />
                            Staff
                          </div>
                          <div className="text-sm text-slate-600 max-h-40 overflow-y-auto">
                            {call.staff_transcript}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Sentiment & Emotion Analysis */}
                  {call.sentiment_analysis && (
                    <div>
                      <h4 className="text-sm font-semibold text-slate-900 mb-3 flex items-center">
                        <Heart className="h-4 w-4 mr-2 text-blue-600" />
                        Emotional Analysis
                      </h4>
                      <div className="bg-white rounded-lg p-4 border border-slate-200">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          <div>
                            <div className="text-xs text-slate-500 uppercase tracking-wide mb-1">
                              Overall Sentiment
                            </div>
                            <div className={`text-sm font-medium ${getSentimentColor(call.overall_sentiment)}`}>
                              {call.overall_sentiment}
                            </div>
                          </div>
                          
                          {call.sentiment_analysis.patient_satisfaction && (
                            <div>
                              <div className="text-xs text-slate-500 uppercase tracking-wide mb-1">
                                Patient Satisfaction
                              </div>
                              <div className="text-sm font-medium text-slate-700">
                                {call.sentiment_analysis.patient_satisfaction}/10
                              </div>
                            </div>
                          )}
                          
                          {call.sentiment_analysis.emotional_tone && (
                            <div>
                              <div className="text-xs text-slate-500 uppercase tracking-wide mb-1">
                                Emotional Tone
                              </div>
                              <div className="text-sm font-medium text-slate-700">
                                {call.sentiment_analysis.emotional_tone}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Opportunities */}
                  {call.opportunity_analysis && (
                    <div>
                      <h4 className="text-sm font-semibold text-slate-900 mb-3">
                        Coaching Opportunities
                      </h4>
                      <div className="bg-white rounded-lg p-4 border border-slate-200">
                        {call.opportunity_analysis.missed_opportunities && call.opportunity_analysis.missed_opportunities.length > 0 && (
                          <div className="mb-4">
                            <div className="text-sm font-medium text-amber-700 mb-2">Missed Opportunities:</div>
                            <ul className="space-y-1">
                              {call.opportunity_analysis.missed_opportunities.map((opportunity, index) => (
                                <li key={index} className="text-sm text-slate-700 flex items-start">
                                  <span className="text-amber-500 mr-2">⚠</span>
                                  {opportunity}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                        
                        {call.opportunity_analysis.recommendations && call.opportunity_analysis.recommendations.length > 0 && (
                          <div>
                            <div className="text-sm font-medium text-blue-700 mb-2">Recommendations:</div>
                            <ul className="space-y-1">
                              {call.opportunity_analysis.recommendations.map((recommendation, index) => (
                                <li key={index} className="text-sm text-slate-700 flex items-start">
                                  <span className="text-blue-500 mr-2">💡</span>
                                  {recommendation}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default CallList;