// Google Sheets Service with robust error handling and retry logic
class GoogleSheetsService {
  constructor() {
    this.sheetId = process.env.REACT_APP_GOOGLE_SHEET_ID;
    this.apiKey = process.env.REACT_APP_GOOGLE_API_KEY;
    this.baseUrl = 'https://sheets.googleapis.com/v4/spreadsheets';
    this.range = 'Sheet1!A:X'; // UPDATED: Extended range to include new columns W and X
    this.cache = null;
    this.lastFetch = null;
    this.subscribers = [];
    this.isOnline = navigator.onLine;
    this.retryAttempts = 0;
    this.maxRetries = 3;
    this.retryDelay = 2000; // 2 seconds
    
    // Listen for online/offline events
    window.addEventListener('online', () => {
      this.isOnline = true;
      console.log('Connection restored - resuming data fetching');
      this.fetchData(); // Immediately fetch when back online
    });
    
    window.addEventListener('offline', () => {
      this.isOnline = false;
      console.log('Connection lost - using cached data');
    });
  }

  // Subscribe to real-time updates
  subscribe(callback) {
    this.subscribers.push(callback);
    return () => {
      this.subscribers = this.subscribers.filter(cb => cb !== callback);
    };
  }

  // Notify all subscribers of data changes
  notifySubscribers(data) {
    this.subscribers.forEach(callback => {
      try {
        callback(data);
      } catch (error) {
        console.error('Error in subscriber callback:', error);
      }
    });
  }

  // Enhanced fetch with retry logic and error handling
  async fetchData() {
    // Don't fetch if offline
    if (!this.isOnline) {
      console.log('Offline - using cached data');
      if (this.cache) {
        this.notifySubscribers(this.cache);
      }
      return this.cache || [];
    }

    try {
      const url = `${this.baseUrl}/${this.sheetId}/values/${this.range}?key=${this.apiKey}`;
      
      console.log('Fetching data from Google Sheets...');
      
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
      
      const response = await fetch(url, {
        signal: controller.signal,
        headers: {
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        }
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status} - ${response.statusText}`);
      }
      
      const result = await response.json();
      
      if (!result.values || result.values.length === 0) {
        console.warn('No data found in sheet');
        return this.cache || [];
      }

      // Process the data
      const headers = result.values[0];
      const rows = result.values.slice(1);
      
      console.log(`Successfully fetched ${rows.length} rows of data`);
      
      const data = rows.map((row, index) => {
        const obj = {};
        headers.forEach((header, headerIndex) => {
          obj[header] = row[headerIndex] || '';
        });
        
        // Convert data types
        if (obj.Representative_Score) {
          obj.Representative_Score = parseFloat(obj.Representative_Score);
        }
        
        if (obj.High_Value_Missed_Opportunity) {
          obj.High_Value_Missed_Opportunity = obj.High_Value_Missed_Opportunity.toString().toLowerCase() === 'true';
        }
        
        if (obj.Sentiment_Confidence) {
          obj.Sentiment_Confidence = parseFloat(obj.Sentiment_Confidence);
        }
        
        // Clean sentiment fields
        obj.Patient_Sentiment = obj.Patient_Sentiment && obj.Patient_Sentiment !== '' ? obj.Patient_Sentiment.toLowerCase() : 'unknown';
        obj.Staff_Sentiment = obj.Staff_Sentiment && obj.Staff_Sentiment !== '' ? obj.Staff_Sentiment.toLowerCase() : 'unknown';
        obj.Overall_Sentiment = obj.Overall_Sentiment && obj.Overall_Sentiment !== '' ? obj.Overall_Sentiment.toLowerCase() : 'unknown';
        obj.Sentiment_Summary = obj.Sentiment_Summary || 'No sentiment analysis available';
        
        // NEW: Clean call tag field
        if (obj.Call_Tag) {
          obj.Call_Tag = obj.Call_Tag.toLowerCase();
        } else {
          obj.Call_Tag = 'general_inquiry';
        }
        
        // NEW: Clean coaching candidate field
        if (obj.Coaching_Candidate) {
          obj.Coaching_Candidate = obj.Coaching_Candidate.toString().toLowerCase() === 'yes';
        } else {
          obj.Coaching_Candidate = false;
        }
        
        return obj;
      });

      // Check for new high-value opportunities
      if (this.cache) {
        const newHighValueOpps = data.filter(item => 
          item.High_Value_Missed_Opportunity && 
          !this.cache.some(cached => cached.Call_File_Name === item.Call_File_Name)
        );
        
        if (newHighValueOpps.length > 0) {
          console.log('New high-value opportunities detected:', newHighValueOpps);
          this.notifyNewAlerts(newHighValueOpps);
        }
      }

      // Update cache and notify subscribers
      this.cache = data;
      this.lastFetch = new Date();
      this.retryAttempts = 0; // Reset retry counter on success
      
      this.notifySubscribers(data);
      
      return data;
      
    } catch (error) {
      return this.handleFetchError(error);
    }
  }

  // Handle fetch errors with retry logic
  async handleFetchError(error) {
    console.error('Error fetching Google Sheets data:', error);
    
    // Check if it's a network error
    const isNetworkError = error.name === 'TypeError' || 
                          error.message.includes('Failed to fetch') ||
                          error.message.includes('NetworkError') ||
                          error.name === 'AbortError';
    
    if (isNetworkError && this.retryAttempts < this.maxRetries) {
      this.retryAttempts++;
      console.log(`Network error detected. Retry attempt ${this.retryAttempts}/${this.maxRetries} in ${this.retryDelay}ms`);
      
      // Wait before retrying
      await new Promise(resolve => setTimeout(resolve, this.retryDelay));
      
      // Exponential backoff
      this.retryDelay = Math.min(this.retryDelay * 1.5, 10000);
      
      return this.fetchData();
    }
    
    // If we've exhausted retries or it's not a network error, use cached data
    if (this.cache) {
      console.log('Using cached data due to fetch error');
      this.notifySubscribers(this.cache);
      return this.cache;
    }
    
    // If no cache available, return empty array and let UI handle it
    console.warn('No cached data available, returning empty array');
    return [];
  }

  // Notify about new alerts
  notifyNewAlerts(alerts) {
    alerts.forEach(alert => {
      console.log(`🚨 HIGH VALUE OPPORTUNITY MISSED: ${alert.Call_File_Name}`);
      
      if (Notification.permission === 'granted') {
        try {
          new Notification('High Value Opportunity Missed!', {
            body: `Call: ${alert.Call_File_Name} - Representative: ${alert.Representative_Name}`,
            icon: '/favicon.ico'
          });
        } catch (error) {
          console.warn('Failed to show notification:', error);
        }
      }
    });
  }

  // NEW: Get calls filtered by tag
  getCallsByTag(tagType) {
    if (!this.cache) return [];
    
    return this.cache.filter(item => 
      item.Call_Tag && 
      item.Call_Tag !== '' && 
      item.Call_Tag === tagType.toLowerCase()
    );
  }

  // NEW: Get call tag analytics
  getCallTagAnalytics() {
    if (!this.cache) return { overall: {}, trends: [] };
    
    const data = this.getWeeklyData();
    
    // Overall tag distribution
    const overall = data.reduce((acc, item) => {
      if (item.Call_Tag && item.Call_Tag !== '') {
        const tag = item.Call_Tag.toLowerCase();
        acc[tag] = (acc[tag] || 0) + 1;
      }
      return acc;
    }, {});

    // Daily tag trends
    const dailyTags = data.reduce((acc, item) => {
      const date = item.Analysis_Date;
      if (!acc[date]) {
        acc[date] = {
          date,
          new_patient: 0,
          emergency: 0,
          insurance: 0,
          appointment_booking: 0,
          general_inquiry: 0,
          billing: 0,
          total: 0
        };
      }

      if (item.Call_Tag && item.Call_Tag !== '') {
        const tag = item.Call_Tag.toLowerCase();
        if (acc[date][tag] !== undefined) {
          acc[date][tag]++;
        }
      }
      acc[date].total++;
      return acc;
    }, {});

    const trends = Object.values(dailyTags)
      .map(day => ({
        date: day.date,
        new_patient: day.total > 0 ? (day.new_patient / day.total) : 0,
        emergency: day.total > 0 ? (day.emergency / day.total) : 0,
        insurance: day.total > 0 ? (day.insurance / day.total) : 0,
        appointment_booking: day.total > 0 ? (day.appointment_booking / day.total) : 0,
        general_inquiry: day.total > 0 ? (day.general_inquiry / day.total) : 0,
        billing: day.total > 0 ? (day.billing / day.total) : 0,
        totalCalls: day.total
      }))
      .sort((a, b) => new Date(a.date) - new Date(b.date));

    return { overall, trends };
  }

  // Get weekly data for analytics
  getWeeklyData() {
    if (!this.cache) return [];
    
    const weekAgo = new Date();
    weekAgo.setDate(weekAgo.getDate() - 7);
    
    return this.cache.filter(item => {
      if (!item.Analysis_Date) return false;
      const [month, day, year] = item.Analysis_Date.split('/');
      const itemDate = new Date(year, month - 1, day);
      return itemDate >= weekAgo;
    });
  }

  // Get sentiment analytics (existing method)
  getSentimentAnalytics() {
    if (!this.cache) return { overall: {}, patient: {}, staff: {}, trends: [] };
    
    const data = this.getWeeklyData();
    
    const overall = data.reduce((acc, item) => {
      if (item.Overall_Sentiment && item.Overall_Sentiment !== 'unknown' && item.Overall_Sentiment !== '') {
        const sentiment = item.Overall_Sentiment.toLowerCase();
        acc[sentiment] = (acc[sentiment] || 0) + 1;
      }
      return acc;
    }, {});

    const patient = data.reduce((acc, item) => {
      if (item.Patient_Sentiment && item.Patient_Sentiment !== 'unknown' && item.Patient_Sentiment !== '') {
        const sentiment = item.Patient_Sentiment.toLowerCase();
        acc[sentiment] = (acc[sentiment] || 0) + 1;
      }
      return acc;
    }, {});

    const staff = data.reduce((acc, item) => {
      if (item.Staff_Sentiment && item.Staff_Sentiment !== 'unknown' && item.Staff_Sentiment !== '') {
        const sentiment = item.Staff_Sentiment.toLowerCase();
        acc[sentiment] = (acc[sentiment] || 0) + 1;
      }
      return acc;
    }, {});

    const dailySentiments = data.reduce((acc, item) => {
      const date = item.Analysis_Date;
      if (!acc[date]) {
        acc[date] = { date, positive: 0, neutral: 0, negative: 0, total: 0 };
      }

      if (item.Overall_Sentiment && item.Overall_Sentiment !== 'unknown' && item.Overall_Sentiment !== '') {
        const sentiment = item.Overall_Sentiment.toLowerCase();
        if (['positive', 'neutral', 'negative'].includes(sentiment)) {
          acc[date][sentiment]++;
        }
      }
      acc[date].total++;
      return acc;
    }, {});

    const trends = Object.values(dailySentiments)
      .map(day => ({
        date: day.date,
        positiveRatio: day.total > 0 ? (day.positive / day.total) : 0,
        neutralRatio: day.total > 0 ? (day.neutral / day.total) : 0,
        negativeRatio: day.total > 0 ? (day.negative / day.total) : 0,
        totalCalls: day.total
      }))
      .sort((a, b) => new Date(a.date) - new Date(b.date));

    return { overall, patient, staff, trends };
  }

  // Get calls filtered by sentiment
  getCallsBySentiment(sentimentType, speakerType = 'overall') {
    if (!this.cache) return [];
    
    const fieldMap = {
      'overall': 'Overall_Sentiment',
      'patient': 'Patient_Sentiment', 
      'staff': 'Staff_Sentiment'
    };
    
    const field = fieldMap[speakerType] || fieldMap['overall'];
    
    return this.cache.filter(item => 
      item[field] && 
      item[field] !== '' && 
      item[field] !== 'unknown' && 
      item[field].toLowerCase() === sentimentType.toLowerCase()
    );
  }

  // Get sentiment correlation with missed opportunities
  getSentimentOpportunityCorrelation() {
    if (!this.cache) return {};
    
    const data = this.getWeeklyData();
    
    const validCalls = data.filter(item => 
      item.Overall_Sentiment && 
      item.Overall_Sentiment !== 'unknown' && 
      item.Overall_Sentiment !== ''
    );
    
    const correlation = {
      positive: { total: 0, missed: 0 },
      neutral: { total: 0, missed: 0 },
      negative: { total: 0, missed: 0 }
    };
    
    validCalls.forEach(item => {
      const sentiment = item.Overall_Sentiment.toLowerCase();
      if (correlation[sentiment]) {
        correlation[sentiment].total++;
        if (item.High_Value_Missed_Opportunity) {
          correlation[sentiment].missed++;
        }
      }
    });
    
    Object.keys(correlation).forEach(sentiment => {
      const data = correlation[sentiment];
      data.missedPercentage = data.total > 0 ? (data.missed / data.total) * 100 : 0;
    });
    
    return correlation;
  }

  // Start polling with error handling
  startPolling(interval = 30000) {
    // Initial fetch
    this.fetchData();
    
    // Clear any existing interval
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
    }
    
    // Set up new interval
    this.pollInterval = setInterval(() => {
      // Only poll if online
      if (this.isOnline) {
        this.fetchData().catch(error => {
          console.warn('Polling fetch failed:', error);
          // Don't stop polling, just log the error
        });
      } else {
        console.log('Skipping poll - offline');
      }
    }, interval);
    
    console.log(`Started polling Google Sheets every ${interval}ms`);
  }

  // Stop polling
  stopPolling() {
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
      this.pollInterval = null;
      console.log('Stopped polling Google Sheets');
    }
  }

  // Get current data with fallback
  getCurrentData() {
    return this.cache || [];
  }

  // Get last update timestamp
  getLastUpdate() {
    return this.lastFetch;
  }

  // Get connection status
  getConnectionStatus() {
    if (!this.isOnline) return 'offline';
    if (this.retryAttempts > 0) return 'reconnecting';
    return 'connected';
  }

  // Request notification permission
  async requestNotificationPermission() {
    if ('Notification' in window && Notification.permission === 'default') {
      try {
        const permission = await Notification.requestPermission();
        console.log('Notification permission:', permission);
        return permission === 'granted';
      } catch (error) {
        console.warn('Failed to request notification permission:', error);
        return false;
      }
    }
    return Notification.permission === 'granted';
  }
}

// Create singleton instance
const googleSheetsService = new GoogleSheetsService();

export default googleSheetsService;