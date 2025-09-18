import React, { useState } from 'react';
import { useDashboardData } from '../hooks/useDashboardData';
import LoadingSpinner from './common/LoadingSpinner';
import EmptyState from './dashboard/EmptyState';
import Header from './dashboard/Header';
import StatsCards from './dashboard/StatsCards';
import ChartsSection from './dashboard/ChartsSection';
import PerformanceSection from './dashboard/PerformanceSection';
import Analytics from './dashboard/Analytics';
import Footer from './dashboard/Footer';
import EmployeeManagement from './EmployeeManagement';
import { BarChart3, Users } from 'lucide-react';

const Dashboard = () => {
  const {
    data,
    alerts,
    lastUpdate,
    loading,
    connectionStatus,
    error,
    analytics,
    dismissAlert,
    clearAllAlerts,
    getCallsBySentiment,
    getCallsByEmotion,
    getCallsByEmotionFlag,
    getCallsByTag
  } = useDashboardData();

  // State for active tab
  const [activeTab, setActiveTab] = useState('dashboard');

  // Tab configuration
  const tabs = [
    {
      id: 'dashboard',
      name: 'Dashboard',
      icon: BarChart3,
      description: 'Call analytics and performance metrics'
    },
    {
      id: 'employees',
      name: 'Employee Management',
      icon: Users,
      description: 'Manage employee visibility for call analysis'
    }
  ];

  // Loading state
  if (loading && activeTab === 'dashboard') {
    return <LoadingSpinner message="Connecting to Analytics Engine..." size="lg" />;
  }

  // Error state
  if (error && activeTab === 'dashboard') {
    return <LoadingSpinner isError={true} errorMessage={error} />;
  }

  // Empty state for dashboard
  if (!data.length && activeTab === 'dashboard') {
    return <EmptyState connectionStatus={connectionStatus} lastUpdate={lastUpdate} />;
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Enhanced Header with Tab Navigation */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <Header 
          connectionStatus={connectionStatus} 
          lastUpdate={lastUpdate} 
          alertsCount={alerts.length}
          alerts={alerts}
          onClearAllAlerts={clearAllAlerts}
          onDismissAlert={dismissAlert}
          data={data}
        />
        
        {/* Tab Navigation */}
        <div className="max-w-8xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8 pt-4">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`group flex items-center space-x-2 pb-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className={`h-5 w-5 ${
                    activeTab === tab.id ? 'text-blue-600' : 'text-gray-400 group-hover:text-gray-500'
                  }`} />
                  <span>{tab.name}</span>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      <main className="max-w-8xl mx-auto px-4 sm:px-6 lg:px-8 pb-12">
        {/* Tab Description */}
        <div className="pt-6 pb-4">
          <div className="flex items-center space-x-3">
            <div className="flex-shrink-0">
              {React.createElement(tabs.find(tab => tab.id === activeTab)?.icon, {
                className: "h-6 w-6 text-gray-400"
              })}
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                {tabs.find(tab => tab.id === activeTab)?.name}
              </h1>
              <p className="text-gray-600">
                {tabs.find(tab => tab.id === activeTab)?.description}
              </p>
            </div>
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === 'dashboard' && (
          <div className="space-y-8">
            {/* Hero Analytics Section */}
            <div className="pb-2">
              <Analytics data={data} />
            </div>

            {/* Main Dashboard Grid */}
            <div className="space-y-8">
              {/* Quick Stats Row - Includes emotion and call tag metrics */}
              <section className="mb-8">
                <StatsCards todayStats={analytics.todayStats} />
              </section>
              
              {/* Charts Grid - Now includes call tag analytics */}
              <section>
                <ChartsSection 
                  analytics={analytics} 
                  rawData={data} 
                  getCallsBySentiment={getCallsBySentiment}
                  getCallsByEmotion={getCallsByEmotion}
                  getCallsByEmotionFlag={getCallsByEmotionFlag}
                  getCallsByTag={getCallsByTag}
                />
              </section>
              
              {/* Performance Section */}
              <section>
                <PerformanceSection 
                  analytics={analytics} 
                  rawData={data}
                />
              </section>
            </div>
          </div>
        )}

        {activeTab === 'employees' && (
          <div>
            <EmployeeManagement />
          </div>
        )}
      </main>

      <Footer />
    </div>
  );
};

export default Dashboard;