import React, { useState, useEffect } from 'react';
import { GraduationCap, Filter, Download, Users, Calendar, Tag, Search, BarChart3, ArrowUp } from 'lucide-react';
import CallFilter from './CallFilter';
import CallList from './CallList';
import CaseStudyGenerator from './CaseStudyGenerator';
import { LoadingState, EmptyState } from './LoadingState';
import { coachingLibraryAPI } from '../../services/coachingLibraryService';

const CoachingLibrary = () => {
  // State management
  const [calls, setCalls] = useState([]);
  const [filteredCalls, setFilteredCalls] = useState([]);
  const [selectedCalls, setSelectedCalls] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showFloatingGenerator, setShowFloatingGenerator] = useState(false);
  const [filters, setFilters] = useState({
    employee: '',
    dateRange: { start: '', end: '' },
    callType: '',
    sentiment: '',
    performanceRange: { min: 0, max: 100 },
    searchTerm: ''
  });
  const [employees, setEmployees] = useState([]);
  const [callTypes, setCallTypes] = useState([]);

  // Load initial data
  useEffect(() => {
    loadCoachingData();
  }, []);

  // Apply filters when they change
  useEffect(() => {
    applyFilters();
  }, [calls, filters]);

  // Show/hide floating generator based on selected calls and scroll position
  useEffect(() => {
    const handleScroll = () => {
      if (selectedCalls.length > 0) {
        const scrollY = window.scrollY;
        // Show floating button if user has scrolled down more than 200px and has selected calls
        setShowFloatingGenerator(scrollY > 200);
      } else {
        setShowFloatingGenerator(false);
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [selectedCalls.length]);

  // Update floating generator visibility when selection changes
  useEffect(() => {
    if (selectedCalls.length === 0) {
      setShowFloatingGenerator(false);
    }
  }, [selectedCalls.length]);

  const loadCoachingData = async () => {
    try {
      setLoading(true);
      setError('');
      
      const [callsData, employeesData, typesData] = await Promise.all([
        coachingLibraryAPI.getCalls(),
        coachingLibraryAPI.getEmployees(),
        coachingLibraryAPI.getCallTypes()
      ]);
      
      console.log('Loaded calls data:', callsData);
      console.log('First call structure:', callsData[0]);
      
      setCalls(callsData);
      setEmployees(employeesData);
      setCallTypes(typesData);
    } catch (err) {
      console.error('Error loading coaching data:', err);
      setError(`Failed to load coaching data: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...calls];

    // Employee filter
    if (filters.employee) {
      filtered = filtered.filter(call => 
        call.representative_name === filters.employee
      );
    }

    // Date range filter
    if (filters.dateRange.start) {
      filtered = filtered.filter(call => {
        try {
          const callDate = new Date(call.analysis_date);
          const startDate = new Date(filters.dateRange.start);
          return callDate >= startDate;
        } catch (e) {
          return true; // Include if date parsing fails
        }
      });
    }
    
    if (filters.dateRange.end) {
      filtered = filtered.filter(call => {
        try {
          const callDate = new Date(call.analysis_date);
          const endDate = new Date(filters.dateRange.end);
          return callDate <= endDate;
        } catch (e) {
          return true; // Include if date parsing fails
        }
      });
    }

    // Call type filter
    if (filters.callType) {
      filtered = filtered.filter(call => 
        call.call_tag === filters.callType
      );
    }

    // Sentiment filter
    if (filters.sentiment) {
      filtered = filtered.filter(call => 
        call.overall_sentiment === filters.sentiment
      );
    }

    // Performance range filter
    filtered = filtered.filter(call => {
      const score = call.representative_score || 0;
      return score >= filters.performanceRange.min &&
             score <= filters.performanceRange.max;
    });

    // Search term filter
    if (filters.searchTerm) {
      const searchLower = filters.searchTerm.toLowerCase();
      filtered = filtered.filter(call => {
        const searchableText = [
          call.call_summary,
          call.representative_name,
          call.patient_transcript,
          call.staff_transcript
        ].join(' ').toLowerCase();
        
        return searchableText.includes(searchLower);
      });
    }

    console.log('Filtered calls:', filtered.length, 'of', calls.length);
    setFilteredCalls(filtered);
  };

  const handleFilterChange = (newFilters) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
  };

  const handleCallSelection = (callId, selected) => {
    console.log('handleCallSelection called:', { callId, selected, type: typeof callId });
    
    // Ensure callId is string for consistent comparison
    const callIdStr = String(callId);
    
    if (selected) {
      // Add to selection if not already selected
      setSelectedCalls(prev => {
        if (prev.some(id => String(id) === callIdStr)) {
          console.log('Call already selected, not adding');
          return prev;
        }
        const newSelection = [...prev, callIdStr];
        console.log('Adding call to selection:', callIdStr, 'New selection:', newSelection);
        return newSelection;
      });
    } else {
      // Remove from selection
      setSelectedCalls(prev => {
        const newSelection = prev.filter(id => String(id) !== callIdStr);
        console.log('Removing call from selection:', callIdStr, 'New selection:', newSelection);
        return newSelection;
      });
    }
  };

  const handleSelectAll = () => {
    if (selectedCalls.length === filteredCalls.length && filteredCalls.length > 0) {
      // Deselect all
      console.log('Deselecting all calls');
      setSelectedCalls([]);
    } else {
      // Select all filtered calls
      const allCallIds = filteredCalls.map(call => String(call.id));
      console.log('Selecting all calls:', allCallIds);
      setSelectedCalls(allCallIds);
    }
  };

  const clearSelection = () => {
    console.log('Clearing all selections');
    setSelectedCalls([]);
  };

  const getSelectedCallsData = () => {
    const selectedData = calls.filter(call => 
      selectedCalls.some(selectedId => String(selectedId) === String(call.id))
    );
    console.log('Selected calls data:', selectedData.length, 'calls');
    return selectedData;
  };

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const scrollToGenerator = () => {
    const generatorElement = document.getElementById('case-study-generator');
    if (generatorElement) {
      generatorElement.scrollIntoView({ behavior: 'smooth' });
    }
  };

  if (loading) {
    return <LoadingState />;
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
        <div className="text-red-600 mb-2">⚠️</div>
        <h3 className="text-lg font-semibold text-red-800 mb-2">
          Error Loading Coaching Library
        </h3>
        <p className="text-red-600 mb-4">{error}</p>
        <button 
          onClick={loadCoachingData}
          className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6 relative">
      {/* Floating Generate Button - Only shows when calls are selected and user has scrolled */}
      {showFloatingGenerator && selectedCalls.length > 0 && (
        <div className="fixed bottom-6 right-6 z-50">
          <div className="bg-white rounded-lg shadow-lg border border-slate-200 p-4 min-w-[280px]">
            <div className="flex items-center justify-between mb-3">
              <div className="text-sm font-medium text-slate-900">
                {selectedCalls.length} call{selectedCalls.length !== 1 ? 's' : ''} selected
              </div>
              <button 
                onClick={scrollToTop}
                className="text-slate-400 hover:text-slate-600"
              >
                <ArrowUp className="h-4 w-4" />
              </button>
            </div>
            <button
              onClick={scrollToGenerator}
              className="w-full bg-green-600 hover:bg-green-700 text-white text-sm font-medium py-2 px-3 rounded-lg transition-colors flex items-center justify-center space-x-2"
            >
              <GraduationCap className="h-4 w-4" />
              <span>Generate Training Material</span>
            </button>
          </div>
        </div>
      )}

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <BarChart3 className="h-8 w-8 text-blue-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">Available Calls</dt>
                <dd className="text-lg font-semibold text-gray-900">{filteredCalls.length}</dd>
              </dl>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Users className="h-8 w-8 text-green-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">Selected</dt>
                <dd className="text-lg font-semibold text-gray-900">{selectedCalls.length}</dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <GraduationCap className="h-8 w-8 text-purple-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">Employees</dt>
                <dd className="text-lg font-semibold text-gray-900">{employees.length}</dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Tag className="h-8 w-8 text-orange-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">Call Types</dt>
                <dd className="text-lg font-semibold text-gray-900">{callTypes.length}</dd>
              </dl>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Filters Sidebar */}
        <div className="lg:col-span-1">
          <CallFilter
            filters={filters}
            onFilterChange={handleFilterChange}
            employees={employees}
            callTypes={callTypes}
            filteredCount={filteredCalls.length}
            totalCount={calls.length}
          />
        </div>

        {/* Main Content */}
        <div className="lg:col-span-3 space-y-6">
          {/* Selection Controls */}
          {filteredCalls.length > 0 && (
            <div className="bg-white rounded-lg shadow p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <button
                    onClick={handleSelectAll}
                    className="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <Users className="h-4 w-4" />
                    <span>
                      {selectedCalls.length === filteredCalls.length && filteredCalls.length > 0 
                        ? 'Deselect All' 
                        : 'Select All'
                      }
                    </span>
                  </button>
                  
                  {selectedCalls.length > 0 && (
                    <button
                      onClick={clearSelection}
                      className="text-sm text-gray-500 hover:text-gray-700"
                    >
                      Clear Selection
                    </button>
                  )}
                </div>
                
                {selectedCalls.length > 0 && (
                  <div className="text-sm text-gray-600">
                    {selectedCalls.length} call{selectedCalls.length !== 1 ? 's' : ''} selected for coaching analysis
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Call List */}
          {filteredCalls.length > 0 ? (
            <CallList
              calls={filteredCalls}
              selectedCalls={selectedCalls}
              onCallSelection={handleCallSelection}
            />
          ) : (
            <EmptyState 
              hasFilters={Object.values(filters).some(filter => 
                filter && filter !== '' && 
                (typeof filter !== 'object' || Object.values(filter).some(v => v !== '' && v !== 0))
              )}
              onClearFilters={() => setFilters({
                employee: '',
                dateRange: { start: '', end: '' },
                callType: '',
                sentiment: '',
                performanceRange: { min: 0, max: 100 },
                searchTerm: ''
              })}
            />
          )}

          {/* Case Study Generator */}
          {selectedCalls.length > 0 && (
            <div id="case-study-generator">
              <CaseStudyGenerator
                selectedCalls={getSelectedCallsData()}
                onSuccess={clearSelection}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CoachingLibrary;