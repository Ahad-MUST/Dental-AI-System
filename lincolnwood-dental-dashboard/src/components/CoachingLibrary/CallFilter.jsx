import React from 'react';
import { 
  Filter, 
  Users, 
  Calendar, 
  Tag, 
  Heart, 
  TrendingUp, 
  Search,
  X,
  RotateCcw
} from 'lucide-react';

const CallFilter = ({ 
  filters, 
  onFilterChange, 
  employees, 
  callTypes, 
  filteredCount, 
  totalCount 
}) => {
  const sentimentOptions = [
    { value: '', label: 'All Sentiments' },
    { value: 'positive', label: 'Positive' },
    { value: 'neutral', label: 'Neutral' },
    { value: 'negative', label: 'Negative' }
  ];

  const handleRangeChange = (field, type, value) => {
    onFilterChange({
      [field]: {
        ...filters[field],
        [type]: parseInt(value) || 0
      }
    });
  };

  const clearAllFilters = () => {
    onFilterChange({
      employee: '',
      dateRange: { start: '', end: '' },
      callType: '',
      sentiment: '',
      performanceRange: { min: 0, max: 100 },
      searchTerm: ''
    });
  };

  const hasActiveFilters = () => {
    return filters.employee || 
           filters.dateRange.start || 
           filters.dateRange.end ||
           filters.callType ||
           filters.sentiment ||
           filters.performanceRange.min > 0 ||
           filters.performanceRange.max < 100 ||
           filters.searchTerm;
  };

  return (
    <div className="bg-white rounded-lg border border-slate-200 p-6 h-fit sticky top-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-2">
          <Filter className="h-5 w-5 text-slate-600" />
          <h3 className="text-lg font-semibold text-slate-900">Filters</h3>
        </div>
        
        {hasActiveFilters() && (
          <button
            onClick={clearAllFilters}
            className="flex items-center space-x-1 text-sm text-slate-500 hover:text-slate-700 transition-colors"
          >
            <RotateCcw className="h-4 w-4" />
            <span>Clear</span>
          </button>
        )}
      </div>

      {/* Results Count */}
      <div className="bg-blue-50 rounded-lg p-3 mb-6">
        <div className="text-sm text-blue-800">
          <span className="font-semibold">{filteredCount}</span> of{' '}
          <span className="font-semibold">{totalCount}</span> calls
        </div>
        {filteredCount !== totalCount && (
          <div className="text-xs text-blue-600 mt-1">
            Filtered results
          </div>
        )}
      </div>

      {/* Search */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-slate-700 mb-2">
          <Search className="h-4 w-4 inline mr-1" />
          Search Calls
        </label>
        <div className="relative">
          <input
            type="text"
            value={filters.searchTerm}
            onChange={(e) => onFilterChange({ searchTerm: e.target.value })}
            placeholder="Search transcripts, summaries..."
            className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
          />
          {filters.searchTerm && (
            <button
              onClick={() => onFilterChange({ searchTerm: '' })}
              className="absolute right-2 top-2 text-slate-400 hover:text-slate-600"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>

      {/* Employee Filter */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-slate-700 mb-2">
          <Users className="h-4 w-4 inline mr-1" />
          Employee
        </label>
        <select
          value={filters.employee}
          onChange={(e) => onFilterChange({ employee: e.target.value })}
          className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
        >
          <option value="">All Employees</option>
          {employees.map(employee => (
            <option key={employee} value={employee}>
              {employee}
            </option>
          ))}
        </select>
      </div>

      {/* Date Range */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-slate-700 mb-2">
          <Calendar className="h-4 w-4 inline mr-1" />
          Date Range
        </label>
        <div className="space-y-2">
          <input
            type="date"
            value={filters.dateRange.start}
            onChange={(e) => onFilterChange({ 
              dateRange: { ...filters.dateRange, start: e.target.value }
            })}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
            placeholder="Start date"
          />
          <input
            type="date"
            value={filters.dateRange.end}
            onChange={(e) => onFilterChange({ 
              dateRange: { ...filters.dateRange, end: e.target.value }
            })}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
            placeholder="End date"
          />
        </div>
      </div>

      {/* Call Type */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-slate-700 mb-2">
          <Tag className="h-4 w-4 inline mr-1" />
          Call Type
        </label>
        <select
          value={filters.callType}
          onChange={(e) => onFilterChange({ callType: e.target.value })}
          className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
        >
          <option value="">All Types</option>
          {callTypes.map(type => (
            <option key={type} value={type}>
              {type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </option>
          ))}
        </select>
      </div>

      {/* Sentiment */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-slate-700 mb-2">
          <Heart className="h-4 w-4 inline mr-1" />
          Sentiment
        </label>
        <select
          value={filters.sentiment}
          onChange={(e) => onFilterChange({ sentiment: e.target.value })}
          className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
        >
          {sentimentOptions.map(option => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      {/* Performance Range */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-slate-700 mb-2">
          <TrendingUp className="h-4 w-4 inline mr-1" />
          Performance Score
        </label>
        <div className="space-y-3">
          <div>
            <label className="block text-xs text-slate-500 mb-1">
              Minimum: {filters.performanceRange.min}%
            </label>
            <input
              type="range"
              min="0"
              max="100"
              value={filters.performanceRange.min}
              onChange={(e) => handleRangeChange('performanceRange', 'min', e.target.value)}
              className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer"
            />
          </div>
          <div>
            <label className="block text-xs text-slate-500 mb-1">
              Maximum: {filters.performanceRange.max}%
            </label>
            <input
              type="range"
              min="0"
              max="100"
              value={filters.performanceRange.max}
              onChange={(e) => handleRangeChange('performanceRange', 'max', e.target.value)}
              className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer"
            />
          </div>
          <div className="flex justify-between text-xs text-slate-500">
            <span>{filters.performanceRange.min}%</span>
            <span>{filters.performanceRange.max}%</span>
          </div>
        </div>
      </div>

      {/* Active Filters Summary */}
      {hasActiveFilters() && (
        <div className="pt-4 border-t border-slate-200">
          <div className="text-sm font-medium text-slate-700 mb-2">Active Filters:</div>
          <div className="space-y-1 text-xs text-slate-600">
            {filters.employee && <div>• Employee: {filters.employee}</div>}
            {filters.dateRange.start && <div>• Start: {filters.dateRange.start}</div>}
            {filters.dateRange.end && <div>• End: {filters.dateRange.end}</div>}
            {filters.callType && <div>• Type: {filters.callType}</div>}
            {filters.sentiment && <div>• Sentiment: {filters.sentiment}</div>}
            {filters.searchTerm && <div>• Search: "{filters.searchTerm}"</div>}
            {(filters.performanceRange.min > 0 || filters.performanceRange.max < 100) && (
              <div>• Score: {filters.performanceRange.min}%-{filters.performanceRange.max}%</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default CallFilter;