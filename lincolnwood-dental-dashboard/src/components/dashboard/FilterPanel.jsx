import React from 'react';
import { Filter, Search, Calendar, User, Tag, Heart, Brain, AlertTriangle, RotateCcw } from 'lucide-react';

const FilterPanel = ({
  filters,
  filterOptions,
  updateFilter,
  updateArrayFilter,
  clearAllFilters,
  getActiveFiltersCount
}) => {
  const selectAllForFilter = (filterType) => {
    const allOptions = filterOptions[filterType] || [];
    updateFilter(filterType, allOptions);
  };

  const deselectAllForFilter = (filterType) => {
    updateFilter(filterType, []);
  };

  return (
    <div className="p-6 space-y-6 bg-slate-50/30 h-full">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
          <Filter className="h-5 w-5 text-slate-600" />
          Filters ({getActiveFiltersCount()} active)
        </h3>
        <button
          onClick={clearAllFilters}
          className="flex items-center gap-1 text-sm text-slate-600 hover:text-slate-800 transition-colors px-3 py-1.5 rounded-lg hover:bg-white/70 border border-slate-200"
        >
          <RotateCcw className="h-4 w-4" />
          Clear All
        </button>
      </div>

      {/* Search */}
      <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-sm">
        <label className="block text-sm font-medium text-slate-700 mb-3">
          <Search className="h-4 w-4 inline mr-2" />
          Search
        </label>
        <input
          type="text"
          placeholder="Search in calls, representatives, summaries..."
          value={filters.searchTerm}
          onChange={(e) => updateFilter('searchTerm', e.target.value)}
          className="w-full px-3 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-400 focus:border-slate-400 text-sm"
        />
      </div>

      {/* Date Range */}
      <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-sm">
        <label className="block text-sm font-medium text-slate-700 mb-3">
          <Calendar className="h-4 w-4 inline mr-2" />
          Date Range
        </label>
        <div className="grid grid-cols-1 gap-3">
          <input
            type="date"
            placeholder="Start Date"
            value={filters.dateRange.start}
            onChange={(e) => updateFilter('dateRange', { ...filters.dateRange, start: e.target.value })}
            className="px-3 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-400 focus:border-slate-400 text-sm"
          />
          <input
            type="date"
            placeholder="End Date"
            value={filters.dateRange.end}
            onChange={(e) => updateFilter('dateRange', { ...filters.dateRange, end: e.target.value })}
            className="px-3 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-400 focus:border-slate-400 text-sm"
          />
        </div>
      </div>

      {/* Representatives */}
      <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-sm">
        <div className="flex items-center justify-between mb-3">
          <label className="text-sm font-medium text-slate-700">
            <User className="h-4 w-4 inline mr-2" />
            Representatives ({filters.representatives.length} selected)
          </label>
          <div className="flex gap-2">
            <button
              onClick={() => selectAllForFilter('representatives')}
              className="text-xs text-slate-600 hover:text-slate-800 px-2 py-1 rounded hover:bg-slate-100 transition-colors"
            >
              All
            </button>
            <button
              onClick={() => deselectAllForFilter('representatives')}
              className="text-xs text-slate-600 hover:text-slate-800 px-2 py-1 rounded hover:bg-slate-100 transition-colors"
            >
              None
            </button>
          </div>
        </div>
        <div className="max-h-32 overflow-y-auto border border-slate-200 rounded-lg p-3 space-y-2 bg-slate-50/50">
          {filterOptions.representatives.map(rep => (
            <label key={rep} className="flex items-center space-x-3 text-sm hover:bg-white/70 p-2 rounded transition-colors">
              <input
                type="checkbox"
                checked={filters.representatives.includes(rep)}
                onChange={(e) => updateArrayFilter('representatives', rep, e.target.checked)}
                className="rounded text-slate-600 focus:ring-slate-400 border-slate-300"
              />
              <span className="text-slate-700">{rep}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Call Tags */}
      <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-sm">
        <div className="flex items-center justify-between mb-3">
          <label className="text-sm font-medium text-slate-700">
            <Tag className="h-4 w-4 inline mr-2" />
            Call Tags ({filters.callTags.length} selected)
          </label>
          <div className="flex gap-2">
            <button
              onClick={() => selectAllForFilter('callTags')}
              className="text-xs text-slate-600 hover:text-slate-800 px-2 py-1 rounded hover:bg-slate-100 transition-colors"
            >
              All
            </button>
            <button
              onClick={() => deselectAllForFilter('callTags')}
              className="text-xs text-slate-600 hover:text-slate-800 px-2 py-1 rounded hover:bg-slate-100 transition-colors"
            >
              None
            </button>
          </div>
        </div>
        <div className="max-h-32 overflow-y-auto border border-slate-200 rounded-lg p-3 space-y-2 bg-slate-50/50">
          {filterOptions.callTags.map(tag => (
            <label key={tag} className="flex items-center space-x-3 text-sm hover:bg-white/70 p-2 rounded transition-colors">
              <input
                type="checkbox"
                checked={filters.callTags.includes(tag)}
                onChange={(e) => updateArrayFilter('callTags', tag, e.target.checked)}
                className="rounded text-slate-600 focus:ring-slate-400 border-slate-300"
              />
              <span className="text-slate-700">{tag}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Sentiments */}
      <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-sm">
        <div className="flex items-center justify-between mb-3">
          <label className="text-sm font-medium text-slate-700">
            <Heart className="h-4 w-4 inline mr-2" />
            Sentiments ({filters.sentiments.length} selected)
          </label>
          <div className="flex gap-2">
            <button
              onClick={() => selectAllForFilter('sentiments')}
              className="text-xs text-slate-600 hover:text-slate-800 px-2 py-1 rounded hover:bg-slate-100 transition-colors"
            >
              All
            </button>
            <button
              onClick={() => deselectAllForFilter('sentiments')}
              className="text-xs text-slate-600 hover:text-slate-800 px-2 py-1 rounded hover:bg-slate-100 transition-colors"
            >
              None
            </button>
          </div>
        </div>
        <div className="max-h-24 overflow-y-auto border border-slate-200 rounded-lg p-3 space-y-2 bg-slate-50/50">
          {filterOptions.sentiments.map(sentiment => (
            <label key={sentiment} className="flex items-center space-x-3 text-sm hover:bg-white/70 p-2 rounded transition-colors">
              <input
                type="checkbox"
                checked={filters.sentiments.includes(sentiment)}
                onChange={(e) => updateArrayFilter('sentiments', sentiment, e.target.checked)}
                className="rounded text-slate-600 focus:ring-slate-400 border-slate-300"
              />
              <span className="capitalize text-slate-700">{sentiment}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Emotions */}
      <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-sm">
        <div className="flex items-center justify-between mb-3">
          <label className="text-sm font-medium text-slate-700">
            <Brain className="h-4 w-4 inline mr-2" />
            Emotions ({filters.emotions.length} selected)
          </label>
          <div className="flex gap-2">
            <button
              onClick={() => selectAllForFilter('emotions')}
              className="text-xs text-slate-600 hover:text-slate-800 px-2 py-1 rounded hover:bg-slate-100 transition-colors"
            >
              All
            </button>
            <button
              onClick={() => deselectAllForFilter('emotions')}
              className="text-xs text-slate-600 hover:text-slate-800 px-2 py-1 rounded hover:bg-slate-100 transition-colors"
            >
              None
            </button>
          </div>
        </div>
        <div className="max-h-32 overflow-y-auto border border-slate-200 rounded-lg p-3 space-y-2 bg-slate-50/50">
          {filterOptions.emotions.map(emotion => (
            <label key={emotion} className="flex items-center space-x-3 text-sm hover:bg-white/70 p-2 rounded transition-colors">
              <input
                type="checkbox"
                checked={filters.emotions.includes(emotion)}
                onChange={(e) => updateArrayFilter('emotions', emotion, e.target.checked)}
                className="rounded text-slate-600 focus:ring-slate-400 border-slate-300"
              />
              <span className="capitalize text-slate-700">{emotion}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Emotion Intensity */}
      <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-sm">
        <div className="flex items-center justify-between mb-3">
          <label className="text-sm font-medium text-slate-700">
            Emotion Intensity ({filters.emotionIntensity.length} selected)
          </label>
          <div className="flex gap-2">
            <button
              onClick={() => selectAllForFilter('emotionIntensity')}
              className="text-xs text-slate-600 hover:text-slate-800 px-2 py-1 rounded hover:bg-slate-100 transition-colors"
            >
              All
            </button>
            <button
              onClick={() => deselectAllForFilter('emotionIntensity')}
              className="text-xs text-slate-600 hover:text-slate-800 px-2 py-1 rounded hover:bg-slate-100 transition-colors"
            >
              None
            </button>
          </div>
        </div>
        <div className="border border-slate-200 rounded-lg p-3 space-y-2 bg-slate-50/50">
          {filterOptions.emotionIntensities.map(intensity => (
            <label key={intensity} className="flex items-center space-x-3 text-sm hover:bg-white/70 p-2 rounded transition-colors">
              <input
                type="checkbox"
                checked={filters.emotionIntensity.includes(intensity)}
                onChange={(e) => updateArrayFilter('emotionIntensity', intensity, e.target.checked)}
                className="rounded text-slate-600 focus:ring-slate-400 border-slate-300"
              />
              <span className="capitalize text-slate-700">{intensity}</span>
            </label>
          ))}
        </div>
      </div>

      {/* High Value Missed */}
      <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-sm">
        <label className="block text-sm font-medium text-slate-700 mb-3">
          <AlertTriangle className="h-4 w-4 inline mr-2" />
          High Value Missed Opportunity
        </label>
        <select
          value={filters.highValueMissed}
          onChange={(e) => updateFilter('highValueMissed', e.target.value)}
          className="w-full px-3 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-400 focus:border-slate-400 text-sm bg-white"
        >
          <option value="">All</option>
          <option value="yes">Yes - Missed Opportunities</option>
          <option value="no">No - No Missed Opportunities</option>
        </select>
      </div>

      {/* Score Range */}
      <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-sm">
        <label className="block text-sm font-medium text-slate-700 mb-3">
          Score Range (0.0 - 1.0)
        </label>
        <div className="grid grid-cols-2 gap-3">
          <input
            type="number"
            placeholder="Min Score"
            min="0"
            max="1"
            step="0.1"
            value={filters.scoreRange.min}
            onChange={(e) => updateFilter('scoreRange', { ...filters.scoreRange, min: e.target.value })}
            className="px-3 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-400 focus:border-slate-400 text-sm"
          />
          <input
            type="number"
            placeholder="Max Score"
            min="0"
            max="1"
            step="0.1"
            value={filters.scoreRange.max}
            onChange={(e) => updateFilter('scoreRange', { ...filters.scoreRange, max: e.target.value })}
            className="px-3 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-400 focus:border-slate-400 text-sm"
          />
        </div>
      </div>
    </div>
  );
};

export default FilterPanel;