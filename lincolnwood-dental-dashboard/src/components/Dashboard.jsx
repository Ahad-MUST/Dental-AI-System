import React from 'react';
import { useDashboardData } from '../hooks/useDashboardData';
import LoadingSpinner from './common/LoadingSpinner';
import EmptyState from './dashboard/EmptyState';
import Header from './dashboard/Header';
import StatsCards from './dashboard/StatsCards';
import ChartsSection from './dashboard/ChartsSection';
import PerformanceSection from './dashboard/PerformanceSection';
import Analytics from './dashboard/Analytics';
import Footer from './dashboard/Footer';

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

  // Loading state
  if (loading) {
    return <LoadingSpinner message="Connecting to Analytics Engine..." size="lg" />;
  }

  // Error state
  if (error) {
    return <LoadingSpinner isError={true} errorMessage={error} />;
  }

  // Empty state
  if (!data.length) {
    return <EmptyState connectionStatus={connectionStatus} lastUpdate={lastUpdate} />;
  }

  // Modern minimalistic dashboard design with sentiment, emotion, call tag analysis, and download system
  return (
    <div className="min-h-screen bg-slate-50">
      <Header 
        connectionStatus={connectionStatus} 
        lastUpdate={lastUpdate} 
        alertsCount={alerts.length}
        alerts={alerts}
        onClearAllAlerts={clearAllAlerts}
        onDismissAlert={dismissAlert}
        data={data} // NEW: Pass data for download system
      />

      <main className="max-w-8xl mx-auto px-4 sm:px-6 lg:px-8 pb-12">
        {/* Hero Analytics Section */}
        <div className="pt-8 pb-6">
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
      </main>

      <Footer />
    </div>
  );
};

export default Dashboard;