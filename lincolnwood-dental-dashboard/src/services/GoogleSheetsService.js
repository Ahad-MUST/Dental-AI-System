// Google Sheets Service for real-time data fetching
class GoogleSheetsService {
  constructor() {
    this.sheetId = process.env.REACT_APP_GOOGLE_SHEET_ID;
    this.apiKey = process.env.REACT_APP_GOOGLE_API_KEY;
    this.baseUrl = 'https://sheets.googleapis.com/v4/spreadsheets';
    this.range = 'Sheet1!A:H'; // Adjust based on your sheet structure
    this.cache = null;
    this.lastFetch = null;
    this.subscribers = [];
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
    this.subscribers.forEach(callback => callback(data));
  }

  // Fetch data from Google Sheets
  async fetchData() {
    try {
      const url = `${this.baseUrl}/${this.sheetId}/values/${this.range}?key=${this.apiKey}`;
      
      console.log('Fetching data from:', url);
      
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result = await response.json();
      
      if (!result.values || result.values.length === 0) {
        console.warn('No data found in sheet');
        return [];
      }

      // Convert sheet data to objects
      const headers = result.values[0];
      const rows = result.values.slice(1);
      
      const data = rows.map(row => {
        const obj = {};
        headers.forEach((header, index) => {
          obj[header] = row[index] || '';
        });
        
        // Convert Representative_Score to number
        if (obj.Representative_Score) {
          obj.Representative_Score = parseFloat(obj.Representative_Score);
        }
        
        // Convert High_Value_Missed_Opportunity to boolean
        if (obj.High_Value_Missed_Opportunity) {
          obj.High_Value_Missed_Opportunity = obj.High_Value_Missed_Opportunity.toLowerCase() === 'true';
        }
        
        return obj;
      });

      // Check for new high-value missed opportunities
      if (this.cache) {
        const newHighValueOpps = data.filter(item => 
          item.High_Value_Missed_Opportunity && 
          !this.cache.some(cached => cached.Call_File_Name === item.Call_File_Name)
        );
        
        if (newHighValueOpps.length > 0) {
          console.log('New high-value opportunities detected:', newHighValueOpps);
          // Trigger alert notification
          this.notifyNewAlerts(newHighValueOpps);
        }
      }

      this.cache = data;
      this.lastFetch = new Date();
      
      // Notify subscribers
      this.notifySubscribers(data);
      
      return data;
      
    } catch (error) {
      console.error('Error fetching Google Sheets data:', error);
      throw error;
    }
  }

  // Notify about new alerts
  notifyNewAlerts(alerts) {
    // You can implement push notifications, email alerts, etc. here
    alerts.forEach(alert => {
      console.log(`🚨 HIGH VALUE OPPORTUNITY MISSED: ${alert.Call_File_Name}`);
      
      // Browser notification if permission granted
      if (Notification.permission === 'granted') {
        new Notification('High Value Opportunity Missed!', {
          body: `Call: ${alert.Call_File_Name} - Representative: ${alert.Representative_Name}`,
          icon: '/favicon.ico'
        });
      }
    });
  }

  // Start real-time polling
  startPolling(interval = 30000) {
    // Initial fetch
    this.fetchData();
    
    // Set up interval polling
    this.pollInterval = setInterval(() => {
      this.fetchData();
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

  // Get current data (from cache if available)
  getCurrentData() {
    return this.cache || [];
  }

  // Get last update timestamp
  getLastUpdate() {
    return this.lastFetch;
  }

  // Filter data for the last 7 days
  getWeeklyData() {
    if (!this.cache) return [];
    
    const today = new Date();
    const weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
    
    return this.cache.filter(item => {
      // Parse date in MM/DD/YYYY format
      const [month, day, year] = item.Analysis_Date.split('/');
      const itemDate = new Date(year, month - 1, day);
      
      return itemDate >= weekAgo && itemDate <= today;
    });
  }

  // Get today's data
  getTodayData() {
    if (!this.cache) return [];
    
    const today = new Date();
    const todayStr = `${(today.getMonth() + 1).toString().padStart(2, '0')}/${today.getDate().toString().padStart(2, '0')}/${today.getFullYear()}`;
    
    return this.cache.filter(item => item.Analysis_Date === todayStr);
  }

  // Get high-value missed opportunities
  getHighValueMissedOpportunities() {
    if (!this.cache) return [];
    
    return this.cache.filter(item => item.High_Value_Missed_Opportunity === true);
  }

  // Request notification permission
  async requestNotificationPermission() {
    if ('Notification' in window && Notification.permission === 'default') {
      const permission = await Notification.requestPermission();
      console.log('Notification permission:', permission);
      return permission === 'granted';
    }
    return Notification.permission === 'granted';
  }
}

// Create singleton instance
const googleSheetsService = new GoogleSheetsService();

export default googleSheetsService;