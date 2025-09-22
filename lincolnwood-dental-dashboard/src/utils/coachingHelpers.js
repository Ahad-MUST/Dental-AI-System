/**
 * Coaching Library Utility Functions
 * Helper functions for the coaching library system
 */

/**
 * Format date for display in coaching library
 */
export const formatCoachingDate = (dateString) => {
  if (!dateString) return 'Unknown Date';
  
  try {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch (error) {
    return 'Invalid Date';
  }
};

/**
 * Format call duration from seconds to MM:SS
 */
export const formatCallDuration = (seconds) => {
  if (!seconds || seconds < 0) return '0:00';
  
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
};

/**
 * Get performance score color class
 */
export const getPerformanceScoreColor = (score) => {
  if (score >= 85) return 'text-green-600 bg-green-50 border-green-200';
  if (score >= 70) return 'text-yellow-600 bg-yellow-50 border-yellow-200';
  return 'text-red-600 bg-red-50 border-red-200';
};

/**
 * Get sentiment color and icon
 */
export const getSentimentDisplay = (sentiment) => {
  const sentimentLower = sentiment?.toLowerCase() || 'neutral';
  
  const sentimentMap = {
    positive: {
      color: 'text-green-600 bg-green-50 border-green-200',
      icon: '😊',
      label: 'Positive'
    },
    negative: {
      color: 'text-red-600 bg-red-50 border-red-200',
      icon: '😟',
      label: 'Negative'
    },
    neutral: {
      color: 'text-gray-600 bg-gray-50 border-gray-200',
      icon: '😐',
      label: 'Neutral'
    }
  };

  return sentimentMap[sentimentLower] || sentimentMap.neutral;
};

/**
 * Truncate text to specified length with ellipsis
 */
export const truncateText = (text, maxLength = 100) => {
  if (!text || text.length <= maxLength) return text || '';
  return text.substring(0, maxLength).trim() + '...';
};

/**
 * Calculate coaching priority based on call data
 */
export const calculateCoachingPriority = (call) => {
  let priority = 0;
  
  // High priority factors
  if (call.representative_score < 60) priority += 30;
  else if (call.representative_score < 75) priority += 20;
  
  if (call.high_value_missed_opportunity) priority += 25;
  if (call.overall_sentiment === 'negative') priority += 20;
  
  // Coaching analysis factors
  if (call.coaching_analysis?.is_coaching_candidate) priority += 15;
  
  // Performance analysis factors
  const weaknesses = call.performance_analysis?.weaknesses || [];
  if (weaknesses.length > 2) priority += 10;
  
  // Return priority level
  if (priority >= 50) return { level: 'High', color: 'bg-red-100 text-red-800 border-red-200' };
  if (priority >= 25) return { level: 'Medium', color: 'bg-amber-100 text-amber-800 border-amber-200' };
  return { level: 'Low', color: 'bg-green-100 text-green-800 border-green-200' };
};

/**
 * Validate case study generation requirements
 */
export const validateCaseStudyRequirements = (selectedCalls, analysisType) => {
  const requirements = {
    individual: { min: 1, max: 5 },
    comparative: { min: 2, max: 10 }
  };
  
  const typeReq = requirements[analysisType];
  if (!typeReq) {
    return { valid: false, message: 'Invalid analysis type' };
  }
  
  if (selectedCalls.length < typeReq.min) {
    return {
      valid: false,
      message: `Select at least ${typeReq.min} call${typeReq.min > 1 ? 's' : ''} for ${analysisType} analysis`
    };
  }
  
  if (selectedCalls.length > typeReq.max) {
    return {
      valid: false,
      message: `Maximum ${typeReq.max} calls allowed for ${analysisType} analysis`
    };
  }
  
  return { valid: true, message: 'Requirements met' };
};

/**
 * Extract unique employees from calls
 */
export const extractUniqueEmployees = (calls) => {
  const employees = new Set();
  
  calls.forEach(call => {
    if (call.representative_name && call.representative_name !== 'Unknown') {
      employees.add(call.representative_name);
    }
  });
  
  return Array.from(employees).sort();
};

/**
 * Extract unique call types from calls
 */
export const extractUniqueCallTypes = (calls) => {
  const callTypes = new Set();
  
  calls.forEach(call => {
    if (call.call_tag) {
      callTypes.add(call.call_tag);
    }
  });
  
  return Array.from(callTypes).sort();
};

/**
 * Generate default case study title
 */
export const generateDefaultTitle = (selectedCalls, analysisType, targetEmployee) => {
  const date = new Date().toLocaleDateString('en-US', { 
    month: 'short', 
    day: 'numeric', 
    year: 'numeric' 
  });
  
  if (analysisType === 'individual' && targetEmployee) {
    return `Training Case Study: ${targetEmployee} - ${date}`;
  } else if (analysisType === 'comparative') {
    return `Comparative Analysis: ${selectedCalls.length} Calls - ${date}`;
  } else {
    return `Coaching Case Study - ${date}`;
  }
};

/**
 * Filter calls based on criteria
 */
export const filterCalls = (calls, filters) => {
  return calls.filter(call => {
    // Employee filter
    if (filters.employee && call.representative_name !== filters.employee) {
      return false;
    }
    
    // Date range filters
    if (filters.dateRange?.start) {
      try {
        const callDate = new Date(call.analysis_date);
        const startDate = new Date(filters.dateRange.start);
        if (callDate < startDate) return false;
      } catch (error) {
        return false;
      }
    }
    
    if (filters.dateRange?.end) {
      try {
        const callDate = new Date(call.analysis_date);
        const endDate = new Date(filters.dateRange.end);
        if (callDate > endDate) return false;
      } catch (error) {
        return false;
      }
    }
    
    // Call type filter
    if (filters.callType && call.call_tag !== filters.callType) {
      return false;
    }
    
    // Sentiment filter
    if (filters.sentiment && call.overall_sentiment !== filters.sentiment) {
      return false;
    }
    
    // Performance range filter
    const score = call.representative_score || 0;
    if (score < filters.performanceRange?.min || score > filters.performanceRange?.max) {
      return false;
    }
    
    // Search term filter
    if (filters.searchTerm) {
      const searchLower = filters.searchTerm.toLowerCase();
      const searchableText = [
        call.call_summary,
        call.representative_name,
        call.patient_transcript,
        call.staff_transcript
      ].join(' ').toLowerCase();
      
      if (!searchableText.includes(searchLower)) {
        return false;
      }
    }
    
    return true;
  });
};

/**
 * Sort calls by relevance for coaching
 */
export const sortCallsByCoachingRelevance = (calls) => {
  return calls.sort((a, b) => {
    // Primary: coaching priority
    const priorityA = calculateCoachingPriority(a);
    const priorityB = calculateCoachingPriority(b);
    
    const priorityOrder = { 'High': 3, 'Medium': 2, 'Low': 1 };
    const priorityDiff = priorityOrder[priorityB.level] - priorityOrder[priorityA.level];
    
    if (priorityDiff !== 0) return priorityDiff;
    
    // Secondary: performance score (lower scores first for coaching)
    const scoreDiff = (a.representative_score || 0) - (b.representative_score || 0);
    if (scoreDiff !== 0) return scoreDiff;
    
    // Tertiary: date (newer first)
    const dateA = new Date(a.analysis_date || 0);
    const dateB = new Date(b.analysis_date || 0);
    return dateB - dateA;
  });
};

/**
 * Calculate coaching library statistics
 */
export const calculateCoachingStats = (calls) => {
  if (!calls || calls.length === 0) {
    return {
      totalCalls: 0,
      coachingCandidates: 0,
      averageScore: 0,
      sentimentDistribution: {},
      employeeStats: {}
    };
  }
  
  const stats = {
    totalCalls: calls.length,
    coachingCandidates: 0,
    averageScore: 0,
    sentimentDistribution: {},
    employeeStats: {}
  };
  
  let totalScore = 0;
  const sentimentCounts = {};
  const employeeData = {};
  
  calls.forEach(call => {
    // Score calculation
    const score = call.representative_score || 0;
    totalScore += score;
    
    // Coaching candidates
    if (score < 75 || call.high_value_missed_opportunity) {
      stats.coachingCandidates++;
    }
    
    // Sentiment distribution
    const sentiment = call.overall_sentiment || 'neutral';
    sentimentCounts[sentiment] = (sentimentCounts[sentiment] || 0) + 1;
    
    // Employee stats
    const employee = call.representative_name || 'Unknown';
    if (!employeeData[employee]) {
      employeeData[employee] = {
        totalCalls: 0,
        totalScore: 0,
        coachingOpportunities: 0
      };
    }
    
    employeeData[employee].totalCalls++;
    employeeData[employee].totalScore += score;
    
    if (score < 75 || call.high_value_missed_opportunity) {
      employeeData[employee].coachingOpportunities++;
    }
  });
  
  // Calculate averages
  stats.averageScore = Math.round(totalScore / calls.length);
  
  // Calculate sentiment percentages
  Object.keys(sentimentCounts).forEach(sentiment => {
    stats.sentimentDistribution[sentiment] = Math.round(
      (sentimentCounts[sentiment] / calls.length) * 100
    );
  });
  
  // Calculate employee averages
  Object.keys(employeeData).forEach(employee => {
    const data = employeeData[employee];
    stats.employeeStats[employee] = {
      ...data,
      averageScore: Math.round(data.totalScore / data.totalCalls),
      coachingPercentage: Math.round((data.coachingOpportunities / data.totalCalls) * 100)
    };
  });
  
  return stats;
};

/**
 * Export coaching data to CSV format
 */
export const exportToCSV = (calls, selectedOnly = false) => {
  const callsToExport = selectedOnly ? calls.filter(call => call.selected) : calls;
  
  const headers = [
    'Employee',
    'Date',
    'Performance Score',
    'Sentiment',
    'Call Type',
    'Duration',
    'Coaching Priority',
    'Summary'
  ];
  
  const rows = callsToExport.map(call => {
    const priority = calculateCoachingPriority(call);
    return [
      call.representative_name || 'Unknown',
      formatCoachingDate(call.analysis_date),
      call.representative_score || 0,
      call.overall_sentiment || 'neutral',
      call.call_tag || 'unknown',
      formatCallDuration(call.call_duration),
      priority.level,
      truncateText(call.call_summary, 200)
    ];
  });
  
  const csvContent = [headers, ...rows]
    .map(row => row.map(field => `"${field}"`).join(','))
    .join('\n');
  
  return csvContent;
};

/**
 * Download CSV file
 */
export const downloadCSV = (csvContent, filename = 'coaching_calls.csv') => {
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  
  if (link.download !== undefined) {
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
};