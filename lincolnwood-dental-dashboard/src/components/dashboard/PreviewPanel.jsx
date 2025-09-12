import React from 'react';
import { Download, Filter, FileSpreadsheet, FileText, File } from 'lucide-react';

const iconMap = {
  FileSpreadsheet,
  FileText,
  File
};

const PreviewPanel = ({
  filteredData,
  totalData,
  selectedColumns,
  columnConfig,
  downloadFormat,
  setDownloadFormat,
  downloadFormats,
  onDownload,
  isProcessing
}) => {
  const getColumnLabel = (columnKey) => {
    const column = columnConfig.find(col => col.key === columnKey);
    return column ? column.label : columnKey;
  };

  return (
    <div className="p-6 flex flex-col h-full bg-slate-50/30">
      {/* Results Summary */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">
          Download Preview
        </h3>
        <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-sm">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-700 font-medium">Filtered Results:</span>
              <span className="text-lg font-bold text-slate-900">{filteredData.length} calls</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-700 font-medium">Selected Columns:</span>
              <span className="text-lg font-bold text-slate-900">{selectedColumns.length} columns</span>
            </div>
            <div className="text-xs text-slate-600 pt-2 border-t border-slate-100">
              Out of {totalData} total calls
            </div>
          </div>
        </div>
      </div>

      {/* Download Format Selection */}
      <div className="mb-6">
        <label className="block text-sm font-semibold text-slate-700 mb-3">
          Download Format
        </label>
        <div className="grid grid-cols-2 gap-3">
          {downloadFormats.map(format => {
            const IconComponent = iconMap[format.icon] || File;
            
            return (
              <button
                key={format.value}
                onClick={() => setDownloadFormat(format.value)}
                className={`p-4 border rounded-xl text-center transition-all ${
                  downloadFormat === format.value
                    ? 'border-slate-400 bg-slate-100 text-slate-800 shadow-md'
                    : 'border-slate-200 hover:border-slate-300 bg-white hover:bg-slate-50'
                }`}
              >
                <IconComponent className="h-6 w-6 mx-auto mb-2 text-slate-600" />
                <div className="font-semibold text-sm">{format.label}</div>
                <div className="text-xs text-slate-500">{format.description}</div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Selected Columns Preview */}
      <div className="mb-6">
        <h4 className="text-sm font-semibold text-slate-700 mb-3">Selected Columns</h4>
        <div className="border border-slate-200 rounded-xl max-h-40 overflow-y-auto bg-white shadow-sm">
          {selectedColumns.length > 0 ? (
            <div className="p-3 space-y-2">
              {selectedColumns.map((columnKey, index) => {
                const column = columnConfig.find(col => col.key === columnKey);
                return (
                  <div key={columnKey} className="flex items-center justify-between text-sm">
                    <div className="flex items-center space-x-3">
                      <span className="w-6 h-6 bg-slate-100 text-slate-700 rounded-full flex items-center justify-center text-xs font-medium">
                        {index + 1}
                      </span>
                      <span className="font-medium text-slate-800">
                        {getColumnLabel(columnKey)}
                      </span>
                      {column?.required && (
                        <span className="text-xs bg-amber-100 text-amber-800 px-2 py-0.5 rounded-full">
                          Required
                        </span>
                      )}
                    </div>
                    <span className="text-xs text-slate-500">{column?.category}</span>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="p-4 text-center text-slate-500">
              <div className="text-sm">No columns selected</div>
              <div className="text-xs text-slate-400 mt-1">Select columns to preview</div>
            </div>
          )}
        </div>
      </div>

      {/* Sample Data Preview */}
      <div className="flex-1 mb-6 min-h-0">
        <h4 className="text-sm font-semibold text-slate-700 mb-3">Sample Data (First 3 results)</h4>
        <div className="border border-slate-200 rounded-xl overflow-hidden h-full bg-white shadow-sm">
          <div className="h-full overflow-y-auto">
            {filteredData.length === 0 ? (
              <div className="flex items-center justify-center h-full text-slate-500">
                <div className="text-center">
                  <Filter className="h-8 w-8 mx-auto mb-2 text-slate-400" />
                  <p className="text-sm">No results match current filters</p>
                </div>
              </div>
            ) : selectedColumns.length === 0 ? (
              <div className="flex items-center justify-center h-full text-slate-500">
                <div className="text-center">
                  <Download className="h-8 w-8 mx-auto mb-2 text-slate-400" />
                  <p className="text-sm">Select columns to preview data</p>
                </div>
              </div>
            ) : (
              <div className="space-y-0">
                {filteredData.slice(0, 3).map((item, index) => (
                  <div key={index} className="p-4 border-b border-slate-100 last:border-b-0 hover:bg-slate-50">
                    <div className="font-semibold text-sm text-slate-900 mb-3">
                      {item.Call_File_Name || `Call #${index + 1}`}
                    </div>
                    <div className="space-y-2">
                      {selectedColumns.slice(0, 6).map(columnKey => {
                        if (columnKey === 'Call_File_Name') return null; // Skip as it's shown in title
                        
                        const value = item[columnKey] || 'N/A';
                        const displayValue = typeof value === 'string' && value.length > 50 
                          ? value.substring(0, 50) + '...' 
                          : value;

                        return (
                          <div key={columnKey} className="flex justify-between text-xs">
                            <span className="text-slate-600 font-medium">
                              {getColumnLabel(columnKey)}:
                            </span>
                            <span className="text-slate-800 ml-2 flex-1 text-right truncate">
                              {displayValue}
                            </span>
                          </div>
                        );
                      })}
                      {selectedColumns.length > 6 && (
                        <div className="text-xs text-slate-500 text-center pt-2 border-t border-slate-100">
                          + {selectedColumns.length - 6} more columns
                        </div>
                      )}
                    </div>
                    {item.High_Value_Missed_Opportunity && selectedColumns.includes('High_Value_Missed_Opportunity') && (
                      <div className="mt-3">
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                          High Value Missed
                        </span>
                      </div>
                    )}
                  </div>
                ))}
                {filteredData.length > 3 && (
                  <div className="p-3 text-center text-xs text-slate-500 bg-slate-50 border-t border-slate-100">
                    + {filteredData.length - 3} more records will be included in download
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Download Button */}
      <button
        onClick={onDownload}
        disabled={filteredData.length === 0 || selectedColumns.length === 0 || isProcessing}
        className={`w-full py-3 px-4 rounded-xl font-semibold transition-all flex items-center justify-center gap-2 ${
          filteredData.length === 0 || selectedColumns.length === 0 || isProcessing
            ? 'bg-slate-200 text-slate-400 cursor-not-allowed'
            : 'bg-slate-800 hover:bg-slate-900 text-white shadow-md hover:shadow-lg'
        }`}
      >
        <Download className="h-5 w-5" />
        {isProcessing 
          ? 'Processing...' 
          : `Download ${filteredData.length} Records`
        }
      </button>

      {/* Download Info */}
      <div className="mt-3 text-center">
        <div className="text-xs text-slate-600">
          Format: {downloadFormats.find(f => f.value === downloadFormat)?.label} • 
          Columns: {selectedColumns.length} • 
          Records: {filteredData.length}
        </div>
        {selectedColumns.length === 0 && (
          <div className="text-xs text-red-500 mt-1">
            Please select at least one column to download
          </div>
        )}
      </div>
    </div>
  );
};

export default PreviewPanel;