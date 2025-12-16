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
import PatientCategorization from './dashboard/PatientCategorization';
import { BarChart3, Users, GraduationCap } from 'lucide-react';

// Import the new Coaching Library component
import CoachingLibrary from './CoachingLibrary/CoachingLibrary';

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

  // Tab configuration - ONLY ADDITION: Added coaching tab
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
    },
    {
      id: 'coaching',
      name: 'Coaching Library',
      icon: GraduationCap,
      description: 'Create training materials from call analysis'
    }
  ];

  // Loading state - UNCHANGED
  if (loading && activeTab === 'dashboard') {
    return <LoadingSpinner message="Connecting to Analytics Engine..." size="lg" />;
  }

  // Error state - UNCHANGED
  if (error && activeTab === 'dashboard') {
    return <LoadingSpinner isError={true} errorMessage={error} />;
  }

  // Empty state for dashboard - UNCHANGED
  if (!data.length && activeTab === 'dashboard') {
    return <EmptyState connectionStatus={connectionStatus} lastUpdate={lastUpdate} />;
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Enhanced Header with Tab Navigation - UNCHANGED */}
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
        
        {/* Tab Navigation - ONLY CHANGE: Now includes coaching tab */}
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
        {/* Tab Description - ONLY CHANGE: Now handles coaching tab description */}
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

        {/* Tab Content - ONLY ADDITION: Added coaching tab content */}
        {activeTab === 'dashboard' && (
          <div className="space-y-8">
            {/* Hero Analytics Section - UNCHANGED */}
            <div className="pb-2">
              <Analytics data={data} />
            </div>

            {/* NEW: Patient Categorization & Conversion Tracking */}
            <div className="pb-2">
              <PatientCategorization data={data} />
            </div>

            {/* Main Dashboard Grid - SWAPPED SENTIMENT AND TOP PERFORMERS */}
            <div className="space-y-8">
              {/* Quick Stats Row - UNCHANGED */}
              <section className="mb-8">
                <StatsCards todayStats={analytics.todayStats} />
              </section>
              
              {/* Primary Charts (Call Volume, Performance, Call Tags) */}
              <section>
                <div className="space-y-8">
                  {/* Primary Charts Row */}
                  <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
                    <div className="xl:col-span-2">
                      {/* Call Volume Chart */}
                      <ChartsSection 
                        analytics={analytics} 
                        rawData={data} 
                        getCallsBySentiment={getCallsBySentiment}
                        getCallsByEmotion={getCallsByEmotion}
                        getCallsByEmotionFlag={getCallsByEmotionFlag}
                        getCallsByTag={getCallsByTag}
                        showOnlyCallVolume={true}
                      />
                    </div>
                    <div className="xl:col-span-1">
                      {/* Call Tags Chart */}
                      <ChartsSection 
                        analytics={analytics} 
                        rawData={data} 
                        getCallsBySentiment={getCallsBySentiment}
                        getCallsByEmotion={getCallsByEmotion}
                        getCallsByEmotionFlag={getCallsByEmotionFlag}
                        getCallsByTag={getCallsByTag}
                        showOnlyCallTags={true}
                      />
                    </div>
                  </div>

                  {/* Performance Charts Row */}
                  <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
                    <div>
                      {/* Performance Scores Chart */}
                      <ChartsSection 
                        analytics={analytics} 
                        rawData={data} 
                        getCallsBySentiment={getCallsBySentiment}
                        getCallsByEmotion={getCallsByEmotion}
                        getCallsByEmotionFlag={getCallsByEmotionFlag}
                        getCallsByTag={getCallsByTag}
                        showOnlyPerformanceScores={true}
                      />
                    </div>
                    <div>
                      {/* Performance Trends Chart */}
                      <ChartsSection 
                        analytics={analytics} 
                        rawData={data} 
                        getCallsBySentiment={getCallsBySentiment}
                        getCallsByEmotion={getCallsByEmotion}
                        getCallsByEmotionFlag={getCallsByEmotionFlag}
                        getCallsByTag={getCallsByTag}
                        showOnlyPerformanceTrends={true}
                      />
                    </div>
                  </div>
                </div>
              </section>
              
              {/* SWAPPED ROW: Emotion Analytics + Top Performers (same height) */}
              <section>
                <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
                  {/* Emotion Analytics */}
                  <div>
                    <ChartsSection 
                      analytics={analytics} 
                      rawData={data} 
                      getCallsBySentiment={getCallsBySentiment}
                      getCallsByEmotion={getCallsByEmotion}
                      getCallsByEmotionFlag={getCallsByEmotionFlag}
                      getCallsByTag={getCallsByTag}
                      showOnlyEmotion={true}
                    />
                  </div>
                  
                  {/* Top Performers */}
                  <div>
                    <PerformanceSection 
                      analytics={analytics} 
                      rawData={data}
                    />
                  </div>
                </div>
              </section>
              
              {/* Sentiment Analysis - full width */}
              <section>
                <ChartsSection 
                  analytics={analytics} 
                  rawData={data} 
                  getCallsBySentiment={getCallsBySentiment}
                  getCallsByEmotion={getCallsByEmotion}
                  getCallsByEmotionFlag={getCallsByEmotionFlag}
                  getCallsByTag={getCallsByTag}
                  showOnlySentiment={true}
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

        {/* NEW: Coaching Library Tab Content */}
        {activeTab === 'coaching' && (
          <div>
            <CoachingLibrary />
          </div>
        )}
      </main>

      <Footer />
    </div>
  );
};

export default Dashboard;