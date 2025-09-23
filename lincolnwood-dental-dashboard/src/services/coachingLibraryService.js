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
      console.log(`Making request to: ${url}`);
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.detail || 
          errorData.message || 
          `HTTP ${response.status}: ${response.statusText}`
        );
      }

      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        const data = await response.json();
        console.log(`Response from ${endpoint}:`, data);
        return data;
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
   * Get all calls available for coaching analysis with enhanced validation
   */
  async getCalls(filters = {}) {
    const queryParams = new URLSearchParams();
    
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
    
    try {
      const response = await this.makeRequest(endpoint);
      
      if (!Array.isArray(response)) {
        console.warn('API returned non-array response:', response);
        return [];
      }
      
      // Enhanced validation and cleaning
      const cleanedCalls = response.map((call, index) => {
        const cleanedCall = {
          // Required fields with defaults
          id: call.id || `call_${index}_${Date.now()}`,
          representative_name: call.representative_name || 'Unknown',
          analysis_date: call.analysis_date || new Date().toISOString(),
          call_summary: call.call_summary || 'No summary available',
          representative_score: this.validateScore(call.representative_score),
          overall_sentiment: call.overall_sentiment || 'neutral',
          call_tag: call.call_tag || 'general_inquiry',
          
          // Optional fields with defaults
          patient_transcript: call.patient_transcript || '',
          staff_transcript: call.staff_transcript || '',
          high_value_missed_opportunity: Boolean(call.high_value_missed_opportunity),
          call_duration: parseInt(call.call_duration) || 0,
          patient_sentiment: call.patient_sentiment || call.overall_sentiment || 'neutral',
          staff_sentiment: call.staff_sentiment || 'neutral',
          sentiment_confidence: parseFloat(call.sentiment_confidence) || 0,
          patient_emotion: call.patient_emotion || 'neutral',
          
          // Analysis objects with enhanced defaults
          performance_analysis: this.validateAnalysisObject(call.performance_analysis, 'performance'),
          sentiment_analysis: this.validateAnalysisObject(call.sentiment_analysis, 'sentiment'),
          opportunity_analysis: this.validateAnalysisObject(call.opportunity_analysis, 'opportunity'),
          coaching_analysis: this.validateAnalysisObject(call.coaching_analysis, 'coaching'),
          
          // Preserve additional fields
          ...call
        };
        
        return cleanedCall;
      });
      
      console.log(`Successfully loaded and cleaned ${cleanedCalls.length} calls for coaching`);
      return cleanedCalls;
      
    } catch (error) {
      console.error('Error fetching coaching calls:', error);
      throw new Error(`Failed to load coaching calls: ${error.message}`);
    }
  }

  /**
   * Validate and ensure score is a proper number
   */
  validateScore(score) {
    const numScore = parseFloat(score);
    if (isNaN(numScore)) return 0;
    
    // If score is between 0-1, convert to percentage
    if (numScore > 0 && numScore <= 1) {
      return numScore * 100;
    }
    
    // Ensure score is between 0-100
    return Math.max(0, Math.min(100, numScore));
  }

  /**
   * Validate and enhance analysis objects
   */
  validateAnalysisObject(analysisObj, type) {
    if (!analysisObj || typeof analysisObj !== 'object') {
      // Create default analysis based on type
      return this.createDefaultAnalysis(type);
    }
    
    // Ensure arrays exist for expected fields
    switch (type) {
      case 'performance':
        return {
          strengths: Array.isArray(analysisObj.strengths) ? analysisObj.strengths : [],
          weaknesses: Array.isArray(analysisObj.weaknesses) ? analysisObj.weaknesses : [],
          coaching_focus: Array.isArray(analysisObj.coaching_focus) ? analysisObj.coaching_focus : [],
          ...analysisObj
        };
      
      case 'sentiment':
        return {
          patient_satisfaction: analysisObj.patient_satisfaction || 5,
          emotional_tone: analysisObj.emotional_tone || 'Neutral',
          sentiment_confidence: analysisObj.sentiment_confidence || 0.5,
          ...analysisObj
        };
      
      case 'opportunity':
        return {
          missed_opportunities: Array.isArray(analysisObj.missed_opportunities) ? analysisObj.missed_opportunities : [],
          recommendations: Array.isArray(analysisObj.recommendations) ? analysisObj.recommendations : [],
          ...analysisObj
        };
      
      case 'coaching':
        return {
          is_coaching_candidate: Boolean(analysisObj.is_coaching_candidate),
          priority_level: analysisObj.priority_level || 'medium',
          ...analysisObj
        };
      
      default:
        return analysisObj;
    }
  }

  /**
   * Create default analysis objects when none exist
   */
  createDefaultAnalysis(type) {
    switch (type) {
      case 'performance':
        return {
          strengths: ['Professional demeanor maintained'],
          weaknesses: ['Analysis pending'],
          coaching_focus: ['General communication improvement']
        };
      
      case 'sentiment':
        return {
          patient_satisfaction: 5,
          emotional_tone: 'Neutral',
          sentiment_confidence: 0.5
        };
      
      case 'opportunity':
        return {
          missed_opportunities: [],
          recommendations: ['Regular performance review recommended']
        };
      
      case 'coaching':
        return {
          is_coaching_candidate: false,
          priority_level: 'medium'
        };
      
      default:
        return {};
    }
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
        'treatment_consultation',
        'emergency',
        'cosmetic',
        'major_treatment'
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
   * Test coaching system connectivity
   */
  async testSystem() {
    try {
      const response = await this.makeRequest('/coaching/test');
      return {
        success: true,
        data: response
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Get system health status
   */
  async getSystemStatus() {
    try {
      const response = await this.makeRequest('/');
      return {
        status: 'healthy',
        data: response
      };
    } catch (error) {
      return {
        status: 'error',
        error: error.message
      };
    }
  }
}

// Create singleton instance
export const coachingLibraryAPI = new CoachingLibraryAPI();

// Export individual methods for easier testing and use
export const {
  getCalls,
  getEmployees,
  getCallTypes,
  generateCaseStudy,
  generateTrainingPDF,
  getCoachingAnalytics,
  testSystem,
  getSystemStatus
} = coachingLibraryAPI;

// Export the class for advanced usage
export default coachingLibraryAPI;