// AlertsManager.js - Utility for managing today-only alerts with session persistence
export class AlertsManager {
  constructor() {
    this.STORAGE_KEY = 'dismissedTodayAlerts';
    this.TODAY_KEY = 'alertsDate';
  }

  // Get today's date in MM/DD/YYYY format (consistent with data format)
  getTodayString() {
    const today = new Date();
    return `${(today.getMonth() + 1).toString().padStart(2, '0')}/${today.getDate().toString().padStart(2, '0')}/${today.getFullYear()}`;
  }

  // Load dismissed alerts for today from sessionStorage
  loadDismissedAlerts() {
    try {
      const storedDate = sessionStorage.getItem(this.TODAY_KEY);
      const todayStr = this.getTodayString();
      
      // If it's a new day, clear old dismissed alerts
      if (storedDate !== todayStr) {
        console.log(`📅 New day detected (${todayStr}), clearing old dismissed alerts`);
        this.clearDismissedAlerts();
        sessionStorage.setItem(this.TODAY_KEY, todayStr);
        return new Set();
      }
      
      const stored = sessionStorage.getItem(this.STORAGE_KEY);
      if (stored) {
        const dismissedArray = JSON.parse(stored);
        console.log(`📋 Loaded ${dismissedArray.length} dismissed alerts for today (${todayStr})`);
        return new Set(dismissedArray);
      }
    } catch (error) {
      console.warn('⚠️ Failed to load dismissed alerts from sessionStorage:', error);
    }
    
    return new Set();
  }

  // Save dismissed alerts to sessionStorage
  saveDismissedAlerts(dismissedSet) {
    try {
      const todayStr = this.getTodayString();
      sessionStorage.setItem(this.TODAY_KEY, todayStr);
      sessionStorage.setItem(this.STORAGE_KEY, JSON.stringify([...dismissedSet]));
      console.log(`💾 Saved ${dismissedSet.size} dismissed alerts for today (${todayStr})`);
    } catch (error) {
      console.warn('⚠️ Failed to save dismissed alerts to sessionStorage:', error);
    }
  }

  // Clear all dismissed alerts (used when day changes)
  clearDismissedAlerts() {
    try {
      sessionStorage.removeItem(this.STORAGE_KEY);
      sessionStorage.removeItem(this.TODAY_KEY);
      console.log('🗑️ Cleared all dismissed alerts');
    } catch (error) {
      console.warn('⚠️ Failed to clear dismissed alerts:', error);
    }
  }

  // Filter alerts to only show today's undismissed alerts
  filterTodayAlerts(allData, dismissedSet) {
    const todayStr = this.getTodayString();
    
    const todayAlerts = allData.filter(item => {
      // Must be high-value missed opportunity
      if (!item.High_Value_Missed_Opportunity) return false;
      
      // Must have a call file name
      if (!item.Call_File_Name) return false;
      
      // Must be from today
      if (item.Analysis_Date !== todayStr) return false;
      
      // Must not be already dismissed
      if (dismissedSet.has(item.Call_File_Name)) return false;
      
      return true;
    });

    console.log(`🔔 Filtered to ${todayAlerts.length} undismissed alerts for today (${todayStr})`);
    return todayAlerts;
  }

  // Create alert objects with unique IDs
  createAlertObjects(filteredAlerts) {
    return filteredAlerts.map(alert => ({
      ...alert,
      timestamp: new Date(),
      id: `alert-${alert.Call_File_Name}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    }));
  }

  // Dismiss a specific alert
  dismissAlert(alertId, currentAlerts, dismissedSet) {
    const alertToDismiss = currentAlerts.find(alert => alert.id === alertId);
    
    if (alertToDismiss && alertToDismiss.Call_File_Name) {
      const newDismissedSet = new Set([...dismissedSet, alertToDismiss.Call_File_Name]);
      this.saveDismissedAlerts(newDismissedSet);
      console.log(`❌ Dismissed alert for call: ${alertToDismiss.Call_File_Name}`);
      return newDismissedSet;
    }
    
    return dismissedSet;
  }

  // Dismiss all current alerts
  dismissAllAlerts(currentAlerts, dismissedSet) {
    const callFileNames = currentAlerts
      .map(alert => alert.Call_File_Name)
      .filter(Boolean);
    
    if (callFileNames.length > 0) {
      const newDismissedSet = new Set([...dismissedSet, ...callFileNames]);
      this.saveDismissedAlerts(newDismissedSet);
      console.log(`❌ Dismissed all ${callFileNames.length} alerts for today`);
      return newDismissedSet;
    }
    
    return dismissedSet;
  }

  // Get stats about today's alerts
  getTodayAlertStats(allData, dismissedSet) {
    const todayStr = this.getTodayString();
    
    const totalTodayOpportunities = allData.filter(item => 
      item.High_Value_Missed_Opportunity && 
      item.Analysis_Date === todayStr &&
      item.Call_File_Name
    ).length;
    
    const dismissedCount = dismissedSet.size;
    const activeCount = totalTodayOpportunities - dismissedCount;
    
    return {
      total: totalTodayOpportunities,
      dismissed: dismissedCount,
      active: Math.max(0, activeCount),
      date: todayStr
    };
  }

  // Check if it's a new day and reset if needed
  checkAndResetForNewDay() {
    const storedDate = sessionStorage.getItem(this.TODAY_KEY);
    const todayStr = this.getTodayString();
    
    if (storedDate && storedDate !== todayStr) {
      console.log(`🌅 New day detected! Resetting alerts from ${storedDate} to ${todayStr}`);
      this.clearDismissedAlerts();
      sessionStorage.setItem(this.TODAY_KEY, todayStr);
      return true; // Indicates a reset occurred
    }
    
    return false; // No reset needed
  }
}

// Create singleton instance
export const alertsManager = new AlertsManager();

// Export utility functions for direct use
export const getTodayString = () => alertsManager.getTodayString();
export const loadDismissedAlerts = () => alertsManager.loadDismissedAlerts();
export const saveDismissedAlerts = (dismissedSet) => alertsManager.saveDismissedAlerts(dismissedSet);
export const filterTodayAlerts = (allData, dismissedSet) => alertsManager.filterTodayAlerts(allData, dismissedSet);
export const createAlertObjects = (filteredAlerts) => alertsManager.createAlertObjects(filteredAlerts);
export const dismissAlert = (alertId, currentAlerts, dismissedSet) => alertsManager.dismissAlert(alertId, currentAlerts, dismissedSet);
export const dismissAllAlerts = (currentAlerts, dismissedSet) => alertsManager.dismissAllAlerts(currentAlerts, dismissedSet);
export const getTodayAlertStats = (allData, dismissedSet) => alertsManager.getTodayAlertStats(allData, dismissedSet);
export const checkAndResetForNewDay = () => alertsManager.checkAndResetForNewDay();

export default alertsManager;