import React, { useState, useMemo } from 'react';
import { Download, Filter, X, Search, RotateCcw } from 'lucide-react';
import { AVAILABLE_COLUMNS, DOWNLOAD_FORMATS, DEFAULT_SELECTED_COLUMNS } from '../../utils/downloadConfig';
import { generateCSV, generateTXT, generateHTML, generatePDF } from '../../utils/dataGenerators';
import ColumnSelector from './ColumnSelector';
import FilterPanel from './FilterPanel';
import PreviewPanel from './PreviewPanel';

const AdvancedDownloadSystem = ({ data, onClose }) => {
  // States
  const [selectedColumns, setSelectedColumns] = useState(DEFAULT_SELECTED_COLUMNS);
  const [downloadFormat, setDownloadFormat] = useState('csv');
  const [isProcessing, setIsProcessing] = useState(false);
  const [filters, setFilters] = useState({
    dateRange: { start: '', end: '' },
    representatives: [],
    callTags: [],
    sentiments: [],
    emotions: [],
    emotionIntensity: [],
    highValueMissed: '',
    scoreRange: { min: '', max: '' },
    searchTerm: ''
  });

  // Initialize filter options
  const filterOptions = useMemo(() => {
    const representatives = [...new Set(data.map(item => item.Representative_Name).filter(Boolean))].sort();
    const callTags = [...new Set(data.map(item => item.Call_Tag).filter(Boolean))].sort();
    const sentiments = [...new Set(data.map(item => item.Overall_Sentiment).filter(Boolean))].sort();
    const emotions = [...new Set(data.map(item => item.Patient_Primary_Emotion).filter(Boolean))].sort();
    const emotionIntensities = [...new Set(data.map(item => item.Patient_Emotion_Intensity).filter(Boolean))].sort();

    return { representatives, callTags, sentiments, emotions, emotionIntensities };
  }, [data]);

  // Initialize filters with all options selected
  React.useEffect(() => {
    setFilters(prev => ({
      ...prev,
      representatives: filterOptions.representatives,
      callTags: filterOptions.callTags,
      sentiments: filterOptions.sentiments,
      emotions: filterOptions.emotions,
      emotionIntensity: filterOptions.emotionIntensities
    }));
  }, [filterOptions]);

  // Apply filters to data
  const filteredData = useMemo(() => {
    return data.filter(item => {
      // Date range filter
      if (filters.dateRange.start || filters.dateRange.end) {
        const itemDate = new Date(item.Analysis_Date);
        const startDate = filters.dateRange.start ? new Date(filters.dateRange.start) : null;
        const endDate = filters.dateRange.end ? new Date(filters.dateRange.end) : null;
        
        if (startDate && itemDate < startDate) return false;
        if (endDate && itemDate > endDate) return false;
      }

      // Representative filter
      if (filters.representatives.length > 0 && !filters.representatives.includes(item.Representative_Name)) {
        return false;
      }

      // Call tags filter
      if (filters.callTags.length > 0 && !filters.callTags.includes(item.Call_Tag)) {
        return false;
      }

      // Sentiment filter
      if (filters.sentiments.length > 0 && !filters.sentiments.includes(item.Overall_Sentiment)) {
        return false;
      }

      // Emotion filter
      if (filters.emotions.length > 0 && !filters.emotions.includes(item.Patient_Primary_Emotion)) {
        return false;
      }

      // Emotion intensity filter
      if (filters.emotionIntensity.length > 0 && !filters.emotionIntensity.includes(item.Patient_Emotion_Intensity)) {
        return false;
      }

      // High value missed filter
      if (filters.highValueMissed !== '') {
        const isMissed = item.High_Value_Missed_Opportunity === true || item.High_Value_Missed_Opportunity === 'true';
        if (filters.highValueMissed === 'yes' && !isMissed) return false;
        if (filters.highValueMissed === 'no' && isMissed) return false;
      }

      // Score range filter
      if (filters.scoreRange.min !== '' || filters.scoreRange.max !== '') {
        const score = parseFloat(item.Representative_Score) || 0;
        const minScore = filters.scoreRange.min ? parseFloat(filters.scoreRange.min) : 0;
        const maxScore = filters.scoreRange.max ? parseFloat(filters.scoreRange.max) : 1;
        
        if (filters.scoreRange.min !== '' && score < minScore) return false;
        if (filters.scoreRange.max !== '' && score > maxScore) return false;
      }

      // Search term filter
      if (filters.searchTerm) {
        const searchTerm = filters.searchTerm.toLowerCase();
        const searchableFields = [
          item.Call_File_Name,
          item.Representative_Name,
          item.Call_Summary,
          item.Call_Tag,
          item.Overall_Sentiment,
          item.Patient_Primary_Emotion
        ].filter(Boolean);

        const matchesSearch = searchableFields.some(field => 
          field.toString().toLowerCase().includes(searchTerm)
        );

        if (!matchesSearch) return false;
      }

      return true;
    });
  }, [data, filters]);

  // Column management
  const handleColumnToggle = (columnKey, isSelected) => {
    if (isSelected) {
      setSelectedColumns(prev => [...prev, columnKey]);
    } else {
      // Don't remove required columns
      const column = AVAILABLE_COLUMNS.find(col => col.key === columnKey);
      if (!column.required) {
        setSelectedColumns(prev => prev.filter(key => key !== columnKey));
      }
    }
  };

  const handleSelectAllColumns = () => {
    setSelectedColumns(AVAILABLE_COLUMNS.map(col => col.key));
  };

  const handleDeselectAllColumns = () => {
    const requiredColumns = AVAILABLE_COLUMNS.filter(col => col.required).map(col => col.key);
    setSelectedColumns(requiredColumns);
  };

  // Filter management
  const updateFilter = (filterType, value) => {
    setFilters(prev => ({ ...prev, [filterType]: value }));
  };

  const updateArrayFilter = (filterType, value, checked) => {
    setFilters(prev => ({
      ...prev,
      [filterType]: checked 
        ? [...prev[filterType], value]
        : prev[filterType].filter(item => item !== value)
    }));
  };

  const clearAllFilters = () => {
    setFilters({
      dateRange: { start: '', end: '' },
      representatives: filterOptions.representatives,
      callTags: filterOptions.callTags,
      sentiments: filterOptions.sentiments,
      emotions: filterOptions.emotions,
      emotionIntensity: filterOptions.emotionIntensities,
      highValueMissed: '',
      scoreRange: { min: '', max: '' },
      searchTerm: ''
    });
  };

  const getActiveFiltersCount = () => {
    let count = 0;
    if (filters.dateRange.start || filters.dateRange.end) count++;
    if (filters.representatives.length > 0) count++;
    if (filters.callTags.length > 0) count++;
    if (filters.sentiments.length > 0) count++;
    if (filters.emotions.length > 0) count++;
    if (filters.emotionIntensity.length > 0) count++;
    if (filters.highValueMissed !== '') count++;
    if (filters.scoreRange.min !== '' || filters.scoreRange.max !== '') count++;
    if (filters.searchTerm) count++;
    return count;
  };

  // Download handler - REMOVED SUCCESS ALERT
  const handleDownload = async () => {
    if (filteredData.length === 0) {
      alert('No data to download with current filters');
      return;
    }

    if (selectedColumns.length === 0) {
      alert('Please select at least one column to download');
      return;
    }

    setIsProcessing(true);

    try {
      let blob;
      let filename;
      const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
      const format = DOWNLOAD_FORMATS.find(f => f.value === downloadFormat);

      switch (downloadFormat) {
        case 'csv':
          const csvContent = generateCSV(filteredData, selectedColumns, AVAILABLE_COLUMNS);
          blob = new Blob([csvContent], { type: format.mimeType });
          filename = `call-analytics-${timestamp}${format.extension}`;
          break;

        case 'txt':
          const txtContent = generateTXT(filteredData, selectedColumns, AVAILABLE_COLUMNS);
          blob = new Blob([txtContent], { type: format.mimeType });
          filename = `call-analytics-${timestamp}${format.extension}`;
          break;

        case 'html':
          const htmlContent = generateHTML(filteredData, selectedColumns, AVAILABLE_COLUMNS);
          blob = new Blob([htmlContent], { type: format.mimeType });
          filename = `call-analytics-${timestamp}${format.extension}`;
          break;

        case 'pdf':
          const pdfDoc = await generatePDF(filteredData, selectedColumns, AVAILABLE_COLUMNS);
          blob = pdfDoc.output('blob');
          filename = `call-analytics-report-${timestamp}${format.extension}`;
          break;

        default:
          throw new Error('Invalid download format');
      }

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      // REMOVED: Success alert message
      // The download will proceed silently without the popup alert

    } catch (error) {
      console.error('Download error:', error);
      alert(`Error occurred during download: ${error.message}. Please try again.`);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-7xl w-full max-h-[95vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="bg-gradient-to-r from-slate-50 to-slate-100 p-6 border-b border-slate-200 flex-shrink-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 bg-white rounded-xl flex items-center justify-center shadow-md border border-slate-200">
                <Download className="h-6 w-6 text-slate-600" strokeWidth={2} />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-slate-900">Advanced Download System</h2>
                <p className="text-sm text-slate-600">Filter data and select columns for download</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-slate-600 transition-colors p-2 hover:bg-white/70 rounded-lg"
            >
              <X className="h-6 w-6" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex flex-1 min-h-0">
          {/* Left Panel - Filters */}
          <div className="w-1/3 border-r border-slate-200 overflow-y-auto bg-slate-50/30">
            <FilterPanel
              filters={filters}
              filterOptions={filterOptions}
              updateFilter={updateFilter}
              updateArrayFilter={updateArrayFilter}
              clearAllFilters={clearAllFilters}
              getActiveFiltersCount={getActiveFiltersCount}
            />
          </div>

          {/* Middle Panel - Column Selection */}
          <div className="w-1/3 border-r border-slate-200 overflow-y-auto bg-white">
            <div className="p-6">
              <ColumnSelector
                selectedColumns={selectedColumns}
                onColumnToggle={handleColumnToggle}
                onSelectAll={handleSelectAllColumns}
                onDeselectAll={handleDeselectAllColumns}
              />
            </div>
          </div>

          {/* Right Panel - Preview & Download */}
          <div className="w-1/3 overflow-y-auto bg-slate-50/30">
            <PreviewPanel
              filteredData={filteredData}
              totalData={data.length}
              selectedColumns={selectedColumns}
              columnConfig={AVAILABLE_COLUMNS}
              downloadFormat={downloadFormat}
              setDownloadFormat={setDownloadFormat}
              downloadFormats={DOWNLOAD_FORMATS}
              onDownload={handleDownload}
              isProcessing={isProcessing}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdvancedDownloadSystem;