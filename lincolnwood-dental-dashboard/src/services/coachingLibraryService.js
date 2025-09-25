/**
 * Coaching Library Service - CLEANED VERSION
 * API service for the coaching library functionality
 * Only handles fields that exist in Google Sheets and are displayed on frontend
 */

const API_BASE_URL = 'http://localhost:8000';

class CoachingLibraryService {
  /**
   * Get all calls for coaching library with optional filters
   */
  async getCalls(filters = {}) {
    try {
      const params = new URLSearchParams();
      
      // Add filters as query parameters
      if (filters.employee) params.append('employee', filters.employee);
      if (filters.start_date) params.append('start_date', filters.start_date);
      if (filters.end_date) params.append('end_date', filters.end_date);
      if (filters.call_type) params.append('call_type', filters.call_type);
      if (filters.sentiment) params.append('sentiment', filters.sentiment);
      if (filters.min_score !== undefined) params.append('min_score', filters.min_score);
      if (filters.max_score !== undefined) params.append('max_score', filters.max_score);
      if (filters.search_term) params.append('search_term', filters.search_term);
      
      const url = `${API_BASE_URL}/api/coaching/calls${params.toString() ? `?${params.toString()}` : ''}`;
      console.log('Fetching coaching calls from:', url);
      
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const calls = await response.json();
      console.log('Retrieved calls:', calls.length);
      
      return calls;
    } catch (error) {
      console.error('Error fetching coaching calls:', error);
      throw new Error(`Failed to fetch calls: ${error.message}`);
    }
  }

  /**
   * Get unique employees from all calls - CLEANED VERSION
   */
  async getEmployees() {
    try {
      // Get all calls and extract unique employees
      const calls = await this.getCalls();
      const employees = [...new Set(calls.map(call => call.representative_name))];
      
      // Filter out empty/null values and sort
      const validEmployees = employees
        .filter(emp => emp && emp.trim() && emp !== 'Unknown')
        .sort();
      
      console.log('Extracted employees:', validEmployees);
      return validEmployees;
    } catch (error) {
      console.error('Error fetching employees:', error);
      throw new Error(`Failed to fetch employees: ${error.message}`);
    }
  }

  /**
   * Get unique call types from all calls - CLEANED VERSION
   */
  async getCallTypes() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/coaching/call-types`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('Retrieved call types:', data.call_types);
      
      return data.call_types || [];
    } catch (error) {
      console.error('Error fetching call types:', error);
      // Fallback: extract from calls directly
      try {
        const calls = await this.getCalls();
        const callTypes = [...new Set(calls.map(call => call.call_tag))];
        
        const validCallTypes = callTypes
          .filter(type => type && type.trim())
          .sort();
        
        return validCallTypes;
      } catch (fallbackError) {
        console.error('Fallback call types extraction failed:', fallbackError);
        return [];
      }
    }
  }

  /**
   * Generate case study from selected calls
   */
  async generateCaseStudy(request) {
    try {
      console.log('Generating case study:', request);
      
      const response = await fetch(`${API_BASE_URL}/api/coaching/generate-case-study`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const errorData = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorData}`);
      }

      const caseStudy = await response.json();
      console.log('Generated case study:', caseStudy);
      
      return caseStudy;
    } catch (error) {
      console.error('Error generating case study:', error);
      throw new Error(`Failed to generate case study: ${error.message}`);
    }
  }

  /**
   * Generate PDF training material
   */
  async generatePDF(request) {
    try {
      console.log('Generating PDF:', request);
      
      const response = await fetch(`${API_BASE_URL}/api/coaching/generate-pdf`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const errorData = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorData}`);
      }

      // Return the response for download handling
      return response;
    } catch (error) {
      console.error('Error generating PDF:', error);
      throw new Error(`Failed to generate PDF: ${error.message}`);
    }
  }

  /**
   * Test coaching system connectivity
   */
  async testSystem() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/coaching/test`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const testResult = await response.json();
      console.log('System test result:', testResult);
      
      return testResult;
    } catch (error) {
      console.error('Error testing coaching system:', error);
      throw new Error(`System test failed: ${error.message}`);
    }
  }

  /**
   * Get coaching statistics - CLEANED VERSION
   */
  async getStatistics() {
    try {
      const calls = await this.getCalls();
      
      if (!calls || calls.length === 0) {
        return {
          totalCalls: 0,
          averageScore: 0,
          sentimentDistribution: {},
          employeeCount: 0,
          callTypeDistribution: {}
        };
      }

      // Calculate statistics from cleaned data
      const totalCalls = calls.length;
      const scores = calls.map(call => call.representative_score || 0);
      const averageScore = scores.reduce((sum, score) => sum + score, 0) / totalCalls;
      
      // Sentiment distribution
      const sentimentCounts = {};
      calls.forEach(call => {
        const sentiment = call.overall_sentiment || 'neutral';
        sentimentCounts[sentiment] = (sentimentCounts[sentiment] || 0) + 1;
      });
      
      // Employee count
      const uniqueEmployees = new Set(calls.map(call => call.representative_name));
      const employeeCount = [...uniqueEmployees].filter(emp => emp && emp !== 'Unknown').length;
      
      // Call type distribution
      const callTypeCounts = {};
      calls.forEach(call => {
        const callType = call.call_tag || 'general_inquiry';
        callTypeCounts[callType] = (callTypeCounts[callType] || 0) + 1;
      });
      
      return {
        totalCalls,
        averageScore: Math.round(averageScore * 100) / 100,
        sentimentDistribution: sentimentCounts,
        employeeCount,
        callTypeDistribution: callTypeCounts
      };
    } catch (error) {
      console.error('Error calculating statistics:', error);
      throw new Error(`Failed to calculate statistics: ${error.message}`);
    }
  }
}

// Create and export singleton instance
export const coachingLibraryAPI = new CoachingLibraryService();

// Export class for testing
export { CoachingLibraryService };

export default coachingLibraryAPI;