import React, { useState } from 'react';
import { 
  Calendar, 
  Clock, 
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

  const formatTime = (timeString) => {
    if (!timeString) return '';
    try {
      // If it's already in HH:MM format
      if (timeString.includes(':')) {
        return timeString;
      }
      return timeString;
    } catch (error) {
      return timeString;
    }
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

  const truncateText = (text, maxLength = 150, forceExpanded = false) => {
    if (!text) return 'No summary available';
    if (forceExpanded || text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  const toggleExpand = (callId) => {
    setExpandedCall(expandedCall === callId ? null : callId);
  };

  const isSelected = (callId) => {
    const callIdStr = String(callId);
    return selectedCalls.some(selectedId => String(selectedId) === callIdStr);
  };

  const formatCallTag = (callTag) => {
    if (!callTag || callTag === 'general_inquiry') return 'General Inquiry';
    return callTag.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

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
        const callId = String(call.id);
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

                    {/* Meta Info - CLEANED: Only show date, time, and sentiment */}
                    <div className="flex items-center space-x-4 text-sm text-slate-600 mb-3">
                      <div className="flex items-center space-x-1">
                        <Calendar className="h-4 w-4" />
                        <span>{formatDate(call.analysis_date)}</span>
                        {call.analysis_time && (
                          <span className="text-slate-500">• {formatTime(call.analysis_time)}</span>
                        )}
                      </div>
                      
                      {call.overall_sentiment && (
                        <div className={`flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium ${getSentimentColor(call.overall_sentiment)}`}>
                          <span>{getSentimentIcon(call.overall_sentiment)}</span>
                          <span>{call.overall_sentiment}</span>
                        </div>
                      )}
                    </div>

                    {/* Call Summary */}
                    <p className="text-slate-700 leading-relaxed">
                      {expanded 
                        ? truncateText(call.call_summary, 0, true) // Show full text when expanded
                        : truncateText(call.call_summary, 150) // Truncate in preview
                      }
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

              {/* Quick Coaching Indicators - CLEANED: Only show if missed opportunity exists */}
              <div className="flex items-center justify-between pt-4 border-t border-slate-100">
                <div className="flex items-center space-x-4">
                  {/* Missed Opportunities */}
                  {call.high_value_missed_opportunity && (
                    <div className="flex items-center space-x-1 text-amber-600">
                      <div className="w-2 h-2 bg-amber-500 rounded-full"></div>
                      <span className="text-xs font-medium">Missed Opportunity</span>
                    </div>
                  )}
                </div>

                <div className="text-xs text-slate-500">
                  {selected ? 'Selected for coaching analysis' : 'Click to select'}
                </div>
              </div>
            </div>

            {/* Expanded Content - CLEANED: Only show transcript */}
            {expanded && (
              <div className="border-t border-slate-200 bg-slate-50/30">
                <div className="p-6 space-y-6">
                  {/* Call Transcript - MAIN CONTENT */}
                  <div>
                    <h4 className="text-sm font-semibold text-slate-900 mb-3 flex items-center">
                      <FileText className="h-4 w-4 mr-2 text-blue-600" />
                      Call Transcript
                    </h4>
                    
                    {/* Check for full_transcript which contains the actual data */}
                    {call.full_transcript && call.full_transcript.trim() ? (
                      <div className="bg-white rounded-lg p-4 border border-slate-200">
                        <div className="text-sm font-medium text-slate-700 mb-2 flex items-center">
                          <FileText className="h-4 w-4 mr-1" />
                          Full Call Transcript
                        </div>
                        <div className="text-sm text-slate-600 max-h-60 overflow-y-auto leading-relaxed whitespace-pre-wrap">
                          {call.full_transcript}
                        </div>
                      </div>
                    ) : (
                      <div className="bg-gray-50 rounded-lg p-4 border border-gray-200 text-center">
                        <div className="text-gray-500 text-sm">
                          No transcript available for this call
                        </div>
                      </div>
                    )}
                  </div>
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