import React, { useState, useRef, useEffect } from 'react';
import { BarChart3, Wifi, WifiOff, Bell, Clock, X, AlertTriangle } from 'lucide-react';
import { formatTime } from '../../utils/helpers';
import Card from '../common/Card';
import DownloadButton from './DownloadButton';

const Header = ({ connectionStatus, lastUpdate, alertsCount, alerts = [], onClearAllAlerts, onDismissAlert, data = [] }) => {
  const [showAlertsDropdown, setShowAlertsDropdown] = useState(false);
  const dropdownRef = useRef(null);

  // Get today's date in MM/DD/YYYY format for display
  const getTodayString = () => {
    const today = new Date();
    return today.toLocaleDateString('en-US', { 
      month: '2-digit', 
      day: '2-digit', 
      year: 'numeric' 
    });
  };

  const toggleAlertsDropdown = () => {
    setShowAlertsDropdown(!showAlertsDropdown);
  };

  const handleClearAll = () => {
    onClearAllAlerts();
    setShowAlertsDropdown(false);
  };

  const handleDismissAlert = (alertId) => {
    onDismissAlert(alertId);
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowAlertsDropdown(false);
      }
    };

    if (showAlertsDropdown) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
      };
    }
  }, [showAlertsDropdown]);

  // Only show bell if there are alerts for today
  const shouldShowBell = alertsCount > 0;

  return (
    <header className="sticky top-0 z-50 bg-slate-100 border-b border-gray-300/60">
      <div className="max-w-7xl mx-auto px-0 lg:px-0">
        <div className="flex items-center justify-between h-20">
          {/* Brand Section */}
          <div className="flex items-center space-x-4">
            <div className="w-32 h-32 flex items-center justify-center">
              <img 
                src="/logo.png" 
                alt="Lincolnwood Family Dental Logo" 
                className="w-full h-full object-contain"
                onError={(e) => {
                  e.target.style.display = 'none';
                  e.target.nextSibling.style.display = 'flex';
                }}
              />
              <div className="w-10 h-10 bg-teal-500 rounded-lg items-center justify-center hidden">
                <BarChart3 className="h-5 w-5 text-white" strokeWidth={2} />
              </div>
            </div>
            <div>
              <h1 className="text-xl font-semibold text-gray-800 tracking-tight">
                {process.env.REACT_APP_CLINIC_NAME || 'Lincolnwood Family Dental'}
              </h1>
              <p className="text-sm text-gray-600 font-normal">
                Call Analytics Dashboard
              </p>
            </div>
          </div>
          
          {/* Status Section */}
          <div className="flex items-center space-x-6">
            {/* Download Button with PDF Support */}
            {data.length > 0 && (
              <DownloadButton data={data} />
            )}

            {/* Connection Status */}
            <div className="hidden sm:flex items-center space-x-3 bg-gray-50 rounded-full px-4 py-2 border border-gray-200">
              {connectionStatus === 'connected' ? (
                <>
                  <div className="flex space-x-1">
                    <div className="w-1.5 h-1.5 bg-teal-500 rounded-full animate-pulse" />
                    <div className="w-1.5 h-1.5 bg-teal-400 rounded-full animate-pulse" style={{animationDelay: '0.2s'}} />
                    <div className="w-1.5 h-1.5 bg-teal-300 rounded-full animate-pulse" style={{animationDelay: '0.4s'}} />
                  </div>
                  <span className="text-sm font-medium text-teal-700">Live</span>
                </>
              ) : (
                <>
                  <WifiOff className="h-4 w-4 text-red-500" />
                  <span className="text-sm font-medium text-red-600">Offline</span>
                </>
              )}
            </div>
            
            {/* Last Update */}
            <div className="hidden md:flex items-center space-x-3 text-gray-600">
              <Clock className="h-4 w-4 text-gray-400" />
              <div>
                <p className="text-xs text-gray-500 font-medium">Last sync</p>
                <p className="text-sm font-medium text-gray-700">{formatTime(lastUpdate)}</p>
              </div>
            </div>
            
            {/* Today's Alerts Bell - Only shows if there are TODAY's alerts */}
            {shouldShowBell && (
              <div className="relative" ref={dropdownRef}>
                <button
                  onClick={toggleAlertsDropdown}
                  className="relative bg-red-50 hover:bg-red-100 border border-red-200 rounded-full p-2.5 transition-colors duration-200 animate-pulse"
                  aria-label="View today's alerts"
                  title={`${alertsCount} alert${alertsCount !== 1 ? 's' : ''} for today`}
                >
                  <Bell className="h-5 w-5 text-red-600" strokeWidth={2} />
                  <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center font-semibold animate-bounce">
                    {alertsCount}
                  </span>
                </button>

                {/* Today's Alerts Dropdown */}
                {showAlertsDropdown && (
                  <div className="absolute right-0 mt-3 w-96 max-w-sm z-50">
                    <Card className="shadow-xl border border-gray-200 max-h-96 flex flex-col" padding="none">
                      {/* Header */}
                      <div className="flex items-center justify-between p-4 border-b border-gray-100 bg-red-50">
                        <div>
                          <h3 className="font-semibold text-red-900 text-sm">Today's Critical Alerts</h3>
                          <p className="text-xs text-red-700 mt-0.5">{getTodayString()}</p>
                        </div>
                        <div className="flex items-center space-x-3">
                          {alerts.length > 0 && (
                            <button
                              onClick={handleClearAll}
                              className="text-xs text-red-600 hover:text-red-700 font-medium transition-colors duration-200 px-2 py-1 rounded hover:bg-red-100"
                              title="Dismiss all today's alerts"
                            >
                              Dismiss All
                            </button>
                          )}
                          <button
                            onClick={() => setShowAlertsDropdown(false)}
                            className="text-red-400 hover:text-red-600 transition-colors duration-200 p-1 rounded hover:bg-red-100"
                            aria-label="Close alerts"
                          >
                            <X className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                      
                      {/* Scrollable Content */}
                      <div className="flex-1 overflow-y-auto max-h-80">
                        {alerts.length > 0 ? (
                          <div className="p-2 space-y-2">
                            {alerts.slice().reverse().map((alert, index) => (
                              <div key={alert.id} className="p-3 rounded-lg bg-red-50/60 border border-red-100 hover:bg-red-50 transition-colors duration-200">
                                <div className="flex items-start space-x-3">
                                  <div className="bg-red-500 rounded-full p-1.5 mt-0.5 flex-shrink-0 animate-pulse">
                                    <AlertTriangle className="h-3 w-3 text-white" strokeWidth={2.5} />
                                  </div>
                                  <div className="flex-1 min-w-0">
                                    <p className="text-sm font-semibold text-red-900 mb-1">⚠️ High Value Opportunity Missed</p>
                                    <p className="text-xs text-red-700 break-words mb-1">
                                      <span className="font-medium">Call:</span> {alert.Call_File_Name || 'Unknown Call'}
                                    </p>
                                    <p className="text-xs text-red-600 mb-1">
                                      <span className="font-medium">Representative:</span> {alert.Representative_Name || 'Unknown'}
                                    </p>
                                    <div className="flex items-center justify-between mt-2">
                                      <p className="text-xs text-red-500">
                                        {new Date(alert.timestamp).toLocaleTimeString()}
                                      </p>
                                      <div className="bg-red-100 text-red-800 px-2 py-1 rounded-full text-xs font-medium">
                                        TODAY
                                      </div>
                                    </div>
                                  </div>
                                  <button
                                    onClick={() => handleDismissAlert(alert.id)}
                                    className="text-red-400 hover:text-red-600 p-1 flex-shrink-0 transition-colors duration-200 rounded hover:bg-red-100"
                                    aria-label="Dismiss this alert"
                                    title="Dismiss this alert (won't show again today)"
                                  >
                                    <X className="h-3 w-3" />
                                  </button>
                                </div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div className="text-center py-8 px-4">
                            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
                              <Bell className="h-5 w-5 text-green-500" />
                            </div>
                            <p className="text-green-700 text-sm font-medium">No alerts for today!</p>
                            <p className="text-green-600 text-xs mt-1">All opportunities are being captured</p>
                          </div>
                        )}
                      </div>


                    </Card>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;