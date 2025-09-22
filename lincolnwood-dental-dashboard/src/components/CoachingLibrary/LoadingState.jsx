import React from 'react';
import { GraduationCap, Search, Filter, RefreshCw } from 'lucide-react';

/**
 * Loading State Component
 * Displays while data is being fetched
 */
export const LoadingState = () => {
  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center">
      <div className="text-center">
        {/* Animated Icon */}
        <div className="mb-6">
          <div className="bg-blue-50 rounded-full p-6 inline-block">
            <GraduationCap className="h-12 w-12 text-blue-600 animate-pulse" />
          </div>
        </div>
        
        {/* Loading Text */}
        <h3 className="text-xl font-semibold text-slate-900 mb-2">
          Loading Coaching Library
        </h3>
        <p className="text-slate-600 mb-6">
          Fetching calls and preparing coaching opportunities...
        </p>
        
        {/* Loading Spinner */}
        <div className="flex items-center justify-center space-x-2">
          <RefreshCw className="h-5 w-5 text-blue-600 animate-spin" />
          <span className="text-sm text-slate-500">Please wait</span>
        </div>
        
        {/* Loading Steps */}
        <div className="mt-8 max-w-sm mx-auto">
          <div className="space-y-2">
            {[
              'Loading call transcripts...',
              'Analyzing performance data...',
              'Preparing coaching insights...'
            ].map((step, index) => (
              <div key={index} className="flex items-center space-x-2 text-sm text-slate-600">
                <div className={`w-2 h-2 rounded-full ${
                  index === 0 ? 'bg-blue-500 animate-pulse' : 'bg-slate-300'
                }`}></div>
                <span>{step}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

/**
 * Empty State Component
 * Displays when no calls match current filters
 */
export const EmptyState = ({ hasFilters, onClearFilters }) => {
  if (hasFilters) {
    return (
      <div className="bg-white rounded-lg border border-slate-200 p-12 text-center">
        {/* Icon */}
        <div className="mb-6">
          <div className="bg-amber-50 rounded-full p-6 inline-block">
            <Search className="h-12 w-12 text-amber-600" />
          </div>
        </div>
        
        {/* Content */}
        <h3 className="text-xl font-semibold text-slate-900 mb-3">
          No Calls Match Your Filters
        </h3>
        <p className="text-slate-600 mb-6 max-w-md mx-auto">
          Try adjusting your search criteria or date range to find coaching opportunities. 
          You can also clear all filters to see all available calls.
        </p>
        
        {/* Actions */}
        <div className="space-y-3">
          <button
            onClick={onClearFilters}
            className="inline-flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Filter className="h-4 w-4" />
            <span>Clear All Filters</span>
          </button>
          
          <div className="text-sm text-slate-500">
            Or try adjusting your search criteria above
          </div>
        </div>
        
        {/* Suggestions */}
        <div className="mt-8 p-4 bg-slate-50 rounded-lg">
          <h4 className="text-sm font-medium text-slate-700 mb-2">Search Tips:</h4>
          <ul className="text-sm text-slate-600 space-y-1">
            <li>• Try broader date ranges</li>
            <li>• Remove specific employee filters</li>
            <li>• Adjust performance score ranges</li>
            <li>• Clear the search term</li>
          </ul>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border border-slate-200 p-12 text-center">
      {/* Icon */}
      <div className="mb-6">
        <div className="bg-blue-50 rounded-full p-6 inline-block">
          <GraduationCap className="h-12 w-12 text-blue-600" />
        </div>
      </div>
      
      {/* Content */}
      <h3 className="text-xl font-semibold text-slate-900 mb-3">
        No Calls Available
      </h3>
      <p className="text-slate-600 mb-6 max-w-md mx-auto">
        There are currently no calls available for coaching analysis. 
        Calls will appear here once they have been processed and analyzed.
      </p>
      
      {/* Information */}
      <div className="bg-blue-50 rounded-lg p-4 max-w-lg mx-auto">
        <h4 className="text-sm font-medium text-blue-800 mb-2">
          How to Get Started:
        </h4>
        <ul className="text-sm text-blue-700 text-left space-y-1">
          <li>• Upload call recordings to the system</li>
          <li>• Wait for automatic analysis to complete</li>
          <li>• Return here to create coaching materials</li>
          <li>• Use filters to find specific training opportunities</li>
        </ul>
      </div>
      
      {/* Contact Support */}
      <div className="mt-6 text-sm text-slate-500">
        Need help? Contact your system administrator to ensure 
        call processing is configured correctly.
      </div>
    </div>
  );
};

// Default export for compatibility
const LoadingAndEmptyStates = { LoadingState, EmptyState };
export default LoadingAndEmptyStates;