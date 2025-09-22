/**
 * Coaching Library API Service
 * Handles all API interactions for the coaching library system
 */

const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:8000/api';

class CoachingLibraryAPI {
  constructor() {
    this.baseURL = API_BASE;
  }

  /**
   * Generic request handler with error handling
   */
  async makeRequest(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.detail || 
          errorData.message || 
          `HTTP ${response.status}: ${response.statusText}`
        );
      }

      // Handle different response types
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      } else if (contentType && contentType.includes('application/pdf')) {
        return await response.blob();
      } else {
        return await response.text();
      }
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  }

  /**
   * Get all calls available for coaching analysis
   */
  async getCalls(filters = {}) {
    const queryParams = new URLSearchParams();
    
    // Add filters to query params
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== null && value !== undefined && value !== '') {
        if (typeof value === 'object') {
          queryParams.append(key, JSON.stringify(value));
        } else {
          queryParams.append(key, value.toString());
        }
      }
    });

    const endpoint = `/coaching/calls${queryParams.toString() ? `?${queryParams}` : ''}`;
    return await this.makeRequest(endpoint);
  }

  /**
   * Get list of employees for filtering
   */
  async getEmployees() {
    try {
      const response = await this.makeRequest('/employees/visible');
      return response.visible_employees || [];
    } catch (error) {
      console.warn('Failed to fetch employees, using fallback:', error);
      return [];
    }
  }

  /**
   * Get available call types for filtering
   */
  async getCallTypes() {
    try {
      const response = await this.makeRequest('/coaching/call-types');
      return response.call_types || [];
    } catch (error) {
      console.warn('Failed to fetch call types, using fallback:', error);
      return [
        'appointment_booking',
        'treatment_followup',
        'billing_inquiry',
        'general_inquiry',
        'complaint_handling',
        'treatment_consultation'
      ];
    }
  }

  /**
   * Generate case study analysis from selected calls
   */
  async generateCaseStudy({ calls, analysisType, targetEmployee, title }) {
    const payload = {
      calls: calls.map(call => ({
        id: call.id,
        representative_name: call.representative_name,
        call_summary: call.call_summary,
        patient_transcript: call.patient_transcript,
        staff_transcript: call.staff_transcript,
        performance_analysis: call.performance_analysis,
        sentiment_analysis: call.sentiment_analysis,
        opportunity_analysis: call.opportunity_analysis,
        representative_score: call.representative_score,
        overall_sentiment: call.overall_sentiment,
        call_tag: call.call_tag,
        analysis_date: call.analysis_date
      })),
      analysis_type: analysisType,
      target_employee: targetEmployee,
      title: title
    };

    return await this.makeRequest('/coaching/generate-case-study', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }

  /**
   * Generate PDF training material
   */
  async generateTrainingPDF({ caseStudyData, title, targetEmployee, analysisType }) {
    const payload = {
      case_study_data: caseStudyData,
      title: title,
      target_employee: targetEmployee,
      analysis_type: analysisType,
      format: 'pdf'
    };

    return await this.makeRequest('/coaching/generate-pdf', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }

  /**
   * Get coaching analytics and statistics
   */
  async getCoachingAnalytics(dateRange = {}) {
    const queryParams = new URLSearchParams();
    
    if (dateRange.start) queryParams.append('start_date', dateRange.start);
    if (dateRange.end) queryParams.append('end_date', dateRange.end);

    const endpoint = `/coaching/analytics${queryParams.toString() ? `?${queryParams}` : ''}`;
    return await this.makeRequest(endpoint);
  }

  /**
   * Save coaching session record
   */
  async saveCoachingSession({ employeeName, callIds, sessionNotes, actionItems }) {
    const payload = {
      employee_name: employeeName,
      call_ids: callIds,
      session_notes: sessionNotes,
      action_items: actionItems,
      session_date: new Date().toISOString()
    };

    return await this.makeRequest('/coaching/sessions', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }

  /**
   * Get coaching session history
   */
  async getCoachingSessions(employeeName = null) {
    const endpoint = employeeName 
      ? `/coaching/sessions?employee=${encodeURIComponent(employeeName)}`
      : '/coaching/sessions';
    
    return await this.makeRequest(endpoint);
  }
}

// Create singleton instance
export const coachingLibraryAPI = new CoachingLibraryAPI();

// Export individual methods for easier testing
export const {
  getCalls,
  getEmployees,
  getCallTypes,
  generateCaseStudy,
  generateTrainingPDF,
  getCoachingAnalytics,
  saveCoachingSession,
  getCoachingSessions
} = coachingLibraryAPI;