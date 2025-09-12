import React, { useState } from 'react';
import { Download, Filter } from 'lucide-react';
import AdvancedDownloadSystem from './AdvancedDownloadSystem';

const DownloadButton = ({ data }) => {
  const [showDownloadSystem, setShowDownloadSystem] = useState(false);

  return (
    <>
      <button
        onClick={() => setShowDownloadSystem(true)}
        className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-all duration-200 shadow-md hover:shadow-lg"
      >
        <Download className="h-4 w-4" />
        <span>Download Data</span>
        <Filter className="h-4 w-4 opacity-75" />
      </button>

      {showDownloadSystem && (
        <AdvancedDownloadSystem
          data={data}
          onClose={() => setShowDownloadSystem(false)}
        />
      )}
    </>
  );
};

export default DownloadButton;