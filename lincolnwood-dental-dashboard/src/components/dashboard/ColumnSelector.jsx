import React, { useState } from 'react';
import { Check, ChevronDown, ChevronRight, Info, TrendingUp, FileText, Tag, Heart, Brain, AlertTriangle } from 'lucide-react';
import { COLUMN_CATEGORIES, AVAILABLE_COLUMNS } from '../../utils/downloadConfig';

const iconMap = {
  Info,
  TrendingUp,
  FileText,
  Tag,
  Heart,
  Brain,
  AlertTriangle
};

const ColumnSelector = ({ selectedColumns, onColumnToggle, onSelectAll, onDeselectAll }) => {
  const [expandedCategories, setExpandedCategories] = useState(
    COLUMN_CATEGORIES.reduce((acc, cat) => ({ ...acc, [cat.key]: true }), {})
  );

  const toggleCategory = (categoryKey) => {
    setExpandedCategories(prev => ({
      ...prev,
      [categoryKey]: !prev[categoryKey]
    }));
  };

  const getColumnsByCategory = (categoryKey) => {
    return AVAILABLE_COLUMNS.filter(col => col.category === categoryKey);
  };

  const getCategoryStats = (categoryKey) => {
    const categoryColumns = getColumnsByCategory(categoryKey);
    const selectedCount = categoryColumns.filter(col => selectedColumns.includes(col.key)).length;
    return { total: categoryColumns.length, selected: selectedCount };
  };

  const toggleCategoryColumns = (categoryKey) => {
    const categoryColumns = getColumnsByCategory(categoryKey);
    const stats = getCategoryStats(categoryKey);
    
    if (stats.selected === stats.total) {
      // All selected, deselect all
      categoryColumns.forEach(col => {
        if (!col.required && selectedColumns.includes(col.key)) {
          onColumnToggle(col.key, false);
        }
      });
    } else {
      // Some or none selected, select all
      categoryColumns.forEach(col => {
        if (!selectedColumns.includes(col.key)) {
          onColumnToggle(col.key, true);
        }
      });
    }
  };

  const totalSelected = selectedColumns.length;
  const totalAvailable = AVAILABLE_COLUMNS.length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h4 className="text-lg font-semibold text-slate-900">
          Select Columns ({totalSelected}/{totalAvailable} selected)
        </h4>
        <div className="flex gap-2">
          <button
            onClick={onSelectAll}
            className="text-sm text-slate-600 hover:text-slate-800 font-medium px-3 py-1.5 rounded-lg hover:bg-slate-100 transition-colors border border-slate-200"
          >
            Select All
          </button>
          <button
            onClick={onDeselectAll}
            className="text-sm text-slate-600 hover:text-slate-800 font-medium px-3 py-1.5 rounded-lg hover:bg-slate-100 transition-colors border border-slate-200"
          >
            Deselect All
          </button>
        </div>
      </div>

      <div className="border border-slate-200 rounded-xl divide-y divide-slate-200 max-h-80 overflow-y-auto bg-white shadow-sm">
        {COLUMN_CATEGORIES.map(category => {
          const IconComponent = iconMap[category.icon] || Info;
          const isExpanded = expandedCategories[category.key];
          const stats = getCategoryStats(category.key);
          const categoryColumns = getColumnsByCategory(category.key);

          return (
            <div key={category.key} className="bg-white">
              {/* Category Header */}
              <div className="flex items-center justify-between p-4 hover:bg-slate-50 transition-colors">
                <div className="flex items-center space-x-3 flex-1">
                  <button
                    onClick={() => toggleCategory(category.key)}
                    className="flex items-center space-x-3 text-sm font-semibold text-slate-800 hover:text-slate-900"
                  >
                    {isExpanded ? (
                      <ChevronDown className="h-4 w-4 text-slate-500" />
                    ) : (
                      <ChevronRight className="h-4 w-4 text-slate-500" />
                    )}
                    <IconComponent className="h-4 w-4 text-slate-600" />
                    <span>{category.label}</span>
                  </button>
                  
                  <div className="flex items-center space-x-2">
                    <span className="text-xs bg-slate-100 text-slate-700 px-2.5 py-1 rounded-full font-medium">
                      {stats.selected}/{stats.total}
                    </span>
                    {stats.selected === stats.total && stats.total > 0 && (
                      <div className="w-4 h-4 bg-emerald-100 rounded-full flex items-center justify-center">
                        <Check className="h-3 w-3 text-emerald-600" strokeWidth={2} />
                      </div>
                    )}
                  </div>
                </div>

                <button
                  onClick={() => toggleCategoryColumns(category.key)}
                  className={`text-xs px-3 py-1.5 rounded-lg transition-colors font-medium ${
                    stats.selected === stats.total
                      ? 'text-red-600 hover:bg-red-50 border border-red-200'
                      : 'text-slate-600 hover:bg-slate-100 border border-slate-200'
                  }`}
                >
                  {stats.selected === stats.total ? 'Deselect All' : 'Select All'}
                </button>
              </div>

              {/* Category Columns */}
              {isExpanded && (
                <div className="bg-slate-50/50 border-t border-slate-200">
                  {categoryColumns.map(column => (
                    <div
                      key={column.key}
                      className="flex items-start space-x-3 p-4 hover:bg-white transition-colors border-b border-slate-100 last:border-b-0"
                    >
                      <div className="flex items-center mt-0.5">
                        <input
                          type="checkbox"
                          checked={selectedColumns.includes(column.key)}
                          onChange={(e) => onColumnToggle(column.key, e.target.checked)}
                          disabled={column.required}
                          className="rounded border-slate-300 text-slate-600 focus:ring-slate-400 focus:ring-2"
                        />
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2">
                          <label className={`text-sm font-medium cursor-pointer ${
                            column.required 
                              ? 'text-slate-900' 
                              : selectedColumns.includes(column.key)
                                ? 'text-slate-900'
                                : 'text-slate-600'
                          }`}>
                            {column.label}
                          </label>
                          {column.required && (
                            <span className="text-xs bg-amber-100 text-amber-800 px-2 py-0.5 rounded-full font-medium">
                              Required
                            </span>
                          )}
                        </div>
                        
                        {column.description && (
                          <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                            {column.description}
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Selection Summary */}
      <div className="bg-slate-50 rounded-xl p-4 border border-slate-200">
        <div className="flex items-center justify-between text-sm">
          <span className="text-slate-700 font-medium">
            {totalSelected} columns selected
          </span>
          <span className="text-slate-600">
            Ready for download
          </span>
        </div>
      </div>
    </div>
  );
};

export default ColumnSelector;