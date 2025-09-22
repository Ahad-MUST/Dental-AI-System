import React, { useState } from 'react';
import { 
  FileText, 
  Download, 
  Users, 
  Wand2, 
  CheckCircle, 
  AlertCircle,
  Clock,
  User
} from 'lucide-react';
import { coachingLibraryAPI } from '../../services/coachingLibraryService';

const CaseStudyGenerator = ({ selectedCalls, onSuccess }) => {
  const [generating, setGenerating] = useState(false);
  const [generationStatus, setGenerationStatus] = useState('');
  const [analysisType, setAnalysisType] = useState('individual'); // 'individual' or 'comparative'
  const [employeeName, setEmployeeName] = useState('');
  const [caseStudyTitle, setCaseStudyTitle] = useState('');

  const analysisTypes = [
    {
      value: 'individual',
      label: 'Individual Training',
      description: 'Create focused training for specific employee performance',
      icon: User,
      minCalls: 1,
      maxCalls: 5
    },
    {
      value: 'comparative',
      label: 'Comparative Analysis',
      description: 'Compare multiple calls to identify patterns and best practices',
      icon: Users,
      minCalls: 2,
      maxCalls: 10
    }
  ];

  const getUniqueEmployees = () => {
    const employees = [...new Set(selectedCalls.map(call => call.representative_name))];
    return employees.filter(Boolean);
  };

  const generateDefaultTitle = () => {
    const employees = getUniqueEmployees();
    const date = new Date().toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric', 
      year: 'numeric' 
    });
    
    if (analysisType === 'individual' && employees.length === 1) {
      return `Training Case Study: ${employees[0]} - ${date}`;
    } else if (analysisType === 'comparative') {
      return `Comparative Analysis: ${selectedCalls.length} Calls - ${date}`;
    } else {
      return `Coaching Case Study - ${date}`;
    }
  };

  const handleGenerate = async () => {
    try {
      setGenerating(true);
      setGenerationStatus('Analyzing selected calls...');
      
      const title = caseStudyTitle || generateDefaultTitle();
      const targetEmployee = employeeName || getUniqueEmployees()[0] || 'Team Member';

      // Step 1: Generate case study analysis
      setGenerationStatus('Generating coaching insights...');
      const caseStudyData = await coachingLibraryAPI.generateCaseStudy({
        calls: selectedCalls,
        analysisType,
        targetEmployee,
        title
      });

      // Step 2: Generate PDF - FIXED VERSION
      setGenerationStatus('Creating PDF training material...');
      
      try {
        // Make the API request
        const response = await fetch('http://localhost:8000/api/coaching/generate-pdf', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            case_study_data: caseStudyData,
            title,
            target_employee: targetEmployee,
            analysis_type: analysisType
          })
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        // Get the response as a blob
        const blob = await response.blob();
        
        // Check if it's actually a PDF or text response
        const contentType = response.headers.get('content-type');
        
        if (contentType && contentType.includes('application/pdf')) {
          // Handle as PDF
          const url = window.URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.download = `${title.replace(/[^a-z0-9]/gi, '_')}.pdf`;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          window.URL.revokeObjectURL(url);
        } else {
          // Handle as text/other response
          const text = await blob.text();
          console.log('PDF Response:', text);
          
          // Create a simple text file download for now
          const textBlob = new Blob([text], { type: 'text/plain' });
          const url = window.URL.createObjectURL(textBlob);
          const link = document.createElement('a');
          link.href = url;
          link.download = `${title.replace(/[^a-z0-9]/gi, '_')}_training_material.txt`;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          window.URL.revokeObjectURL(url);
        }

        setGenerationStatus('Training material downloaded successfully!');
        
      } catch (pdfError) {
        console.error('PDF Generation Error:', pdfError);
        setGenerationStatus('Case study generated (PDF download not available yet)');
        
        // Still show the case study data to user
        console.log('Generated Case Study:', caseStudyData);
      }

      // Call success callback after a short delay
      setTimeout(() => {
        onSuccess();
        setGenerationStatus('');
      }, 2000);

    } catch (error) {
      console.error('Case study generation failed:', error);
      setGenerationStatus(`Error: ${error.message}`);
      setTimeout(() => setGenerationStatus(''), 5000);
    } finally {
      setGenerating(false);
    }
  };

  const canGenerate = () => {
    const selectedType = analysisTypes.find(type => type.value === analysisType);
    return selectedCalls.length >= selectedType.minCalls && 
           selectedCalls.length <= selectedType.maxCalls;
  };

  const getValidationMessage = () => {
    const selectedType = analysisTypes.find(type => type.value === analysisType);
    
    if (selectedCalls.length < selectedType.minCalls) {
      return `Select at least ${selectedType.minCalls} call${selectedType.minCalls > 1 ? 's' : ''} for ${selectedType.label.toLowerCase()}`;
    }
    
    if (selectedCalls.length > selectedType.maxCalls) {
      return `Maximum ${selectedType.maxCalls} calls allowed for ${selectedType.label.toLowerCase()}`;
    }
    
    return null;
  };

  return (
    <div className="bg-white rounded-lg border border-slate-200 p-6">
      {/* Header */}
      <div className="flex items-center space-x-3 mb-6">
        <div className="bg-green-50 rounded-lg p-2">
          <FileText className="h-5 w-5 text-green-600" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-slate-900">
            Generate Training Case Study
          </h3>
          <p className="text-sm text-slate-600">
            Create professional coaching materials from selected calls
          </p>
        </div>
      </div>

      {/* Analysis Type Selection */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-slate-700 mb-3">
          Training Type
        </label>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {analysisTypes.map((type) => {
            const Icon = type.icon;
            const isSelected = analysisType === type.value;
            const isValid = selectedCalls.length >= type.minCalls && selectedCalls.length <= type.maxCalls;
            
            return (
              <button
                key={type.value}
                onClick={() => setAnalysisType(type.value)}
                disabled={!isValid}
                className={`p-4 rounded-lg border text-left transition-all ${
                  isSelected
                    ? 'border-blue-500 bg-blue-50 text-blue-900'
                    : isValid
                    ? 'border-slate-200 hover:border-slate-300 hover:bg-slate-50'
                    : 'border-slate-200 bg-slate-50 text-slate-400 cursor-not-allowed'
                }`}
              >
                <div className="flex items-start space-x-3">
                  <Icon className={`h-5 w-5 mt-0.5 ${isSelected ? 'text-blue-600' : isValid ? 'text-slate-600' : 'text-slate-400'}`} />
                  <div className="flex-1">
                    <div className={`font-medium ${isSelected ? 'text-blue-900' : isValid ? 'text-slate-900' : 'text-slate-400'}`}>
                      {type.label}
                    </div>
                    <div className={`text-sm mt-1 ${isSelected ? 'text-blue-700' : isValid ? 'text-slate-600' : 'text-slate-400'}`}>
                      {type.description}
                    </div>
                    <div className={`text-xs mt-2 ${isSelected ? 'text-blue-600' : isValid ? 'text-slate-500' : 'text-slate-400'}`}>
                      {type.minCalls === type.maxCalls 
                        ? `Requires ${type.minCalls} call${type.minCalls > 1 ? 's' : ''}`
                        : `Requires ${type.minCalls}-${type.maxCalls} calls`
                      }
                    </div>
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Validation Message */}
      {getValidationMessage() && (
        <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-lg">
          <div className="flex items-center space-x-2">
            <AlertCircle className="h-4 w-4 text-amber-600" />
            <span className="text-sm text-amber-800">{getValidationMessage()}</span>
          </div>
        </div>
      )}

      {/* Configuration Options */}
      {canGenerate() && (
        <div className="space-y-4 mb-6">
          {/* Employee Name */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Target Employee (Optional)
            </label>
            <select
              value={employeeName}
              onChange={(e) => setEmployeeName(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Auto-detect from selected calls</option>
              {getUniqueEmployees().map(employee => (
                <option key={employee} value={employee}>
                  {employee}
                </option>
              ))}
            </select>
          </div>

          {/* Case Study Title */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Training Title (Optional)
            </label>
            <input
              type="text"
              value={caseStudyTitle}
              onChange={(e) => setCaseStudyTitle(e.target.value)}
              placeholder={generateDefaultTitle()}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>
      )}

      {/* Selected Calls Summary - FIXED to handle unique keys */}
      <div className="mb-6 p-4 bg-slate-50 rounded-lg">
        <div className="text-sm font-medium text-slate-700 mb-2">
          Selected Calls Summary
        </div>
        <div className="space-y-2">
          {selectedCalls.slice(0, 5).map((call, index) => (
            <div key={`${call.id}_${index}`} className="flex items-center justify-between text-sm">
              <div className="flex items-center space-x-2">
                <span className="text-slate-500">#{index + 1}</span>
                <span className="font-medium text-slate-700">
                  {call.representative_name}
                </span>
                <span className="text-slate-500">
                  {new Date(call.analysis_date).toLocaleDateString()}
                </span>
              </div>
              <div className="text-slate-600">
                {Math.round(call.representative_score || 0)}%
              </div>
            </div>
          ))}
          {selectedCalls.length > 5 && (
            <div className="text-xs text-slate-500 text-center pt-2">
              ...and {selectedCalls.length - 5} more calls
            </div>
          )}
        </div>
      </div>

      {/* Generation Status */}
      {generationStatus && (
        <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center space-x-2">
            {generating ? (
              <Clock className="h-4 w-4 text-blue-600 animate-spin" />
            ) : generationStatus.includes('Error') ? (
              <AlertCircle className="h-4 w-4 text-red-600" />
            ) : (
              <CheckCircle className="h-4 w-4 text-green-600" />
            )}
            <span className={`text-sm font-medium ${
              generationStatus.includes('Error') 
                ? 'text-red-800' 
                : generationStatus.includes('successfully')
                ? 'text-green-800'
                : 'text-blue-800'
            }`}>
              {generationStatus}
            </span>
          </div>
        </div>
      )}

      {/* Generate Button */}
      <button
        onClick={handleGenerate}
        disabled={!canGenerate() || generating}
        className={`w-full flex items-center justify-center space-x-2 py-3 px-4 rounded-lg font-medium transition-colors ${
          canGenerate() && !generating
            ? 'bg-green-600 hover:bg-green-700 text-white'
            : 'bg-slate-300 text-slate-500 cursor-not-allowed'
        }`}
      >
        {generating ? (
          <>
            <Clock className="h-5 w-5 animate-spin" />
            <span>Generating Training Material...</span>
          </>
        ) : (
          <>
            <Wand2 className="h-5 w-5" />
            <span>Generate Training Case Study</span>
            <Download className="h-4 w-4" />
          </>
        )}
      </button>

      {/* Help Text */}
      <div className="mt-4 text-xs text-slate-500 text-center">
        The training case study will be generated as a downloadable file with coaching insights,
        conversation examples, and actionable recommendations.
      </div>
    </div>
  );
};

export default CaseStudyGenerator;