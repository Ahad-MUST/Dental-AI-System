// dataGenerators.js - Functions to generate different file formats

export const generateCSV = (data, selectedColumns, columnConfig) => {
  if (data.length === 0) return '';

  // Create headers from selected columns
  const headers = selectedColumns.map(colKey => {
    const column = columnConfig.find(col => col.key === colKey);
    return column ? column.label : colKey;
  });

  // Create CSV content
  const csvContent = [
    headers.join(','),
    ...data.map(item => 
      selectedColumns.map(colKey => {
        const value = item[colKey] || '';
        // Escape quotes and wrap in quotes if contains comma, quote, or newline
        const escapedValue = String(value).replace(/"/g, '""');
        return `"${escapedValue}"`;
      }).join(',')
    )
  ].join('\n');

  return csvContent;
};

export const generateTXT = (data, selectedColumns, columnConfig) => {
  return data.map((item, index) => {
    const lines = [`Call #${index + 1}:`];
    
    selectedColumns.forEach(colKey => {
      const column = columnConfig.find(col => col.key === colKey);
      const label = column ? column.label : colKey;
      const value = item[colKey] || 'N/A';
      lines.push(`${label}: ${value}`);
    });
    
    lines.push('='.repeat(80));
    return lines.join('\n');
  }).join('\n\n');
};

export const generateHTML = (data, selectedColumns, columnConfig) => {
  const currentDate = new Date().toLocaleDateString();
  const clinicName = process.env.REACT_APP_CLINIC_NAME || 'Lincolnwood Family Dental';

  return `
    <!DOCTYPE html>
    <html>
    <head>
      <title>Call Analytics Report - ${clinicName}</title>
      <style>
        body { 
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
          margin: 20px; 
          line-height: 1.6;
          color: #333;
        }
        .header { 
          text-align: center; 
          margin-bottom: 30px; 
          border-bottom: 3px solid #2563eb;
          padding-bottom: 20px;
        }
        .header h1 {
          color: #1e293b;
          margin: 0;
          font-size: 28px;
        }
        .header p {
          color: #64748b;
          margin: 10px 0 0 0;
        }
        .summary {
          background: #f8fafc;
          border: 1px solid #e2e8f0;
          border-radius: 8px;
          padding: 20px;
          margin-bottom: 30px;
          text-align: center;
        }
        .call-item { 
          margin-bottom: 25px; 
          padding: 20px; 
          border: 1px solid #e2e8f0; 
          border-radius: 12px; 
          background: white;
          box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .call-title { 
          font-weight: bold; 
          color: #1e293b; 
          margin-bottom: 15px; 
          font-size: 18px;
          border-bottom: 1px solid #f1f5f9;
          padding-bottom: 8px;
        }
        .call-details { 
          display: grid; 
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
          gap: 15px; 
        }
        .detail-item { 
          background: #f8fafc;
          padding: 10px;
          border-radius: 6px;
          border: 1px solid #e2e8f0;
        }
        .label { 
          font-weight: 600; 
          color: #475569; 
          font-size: 12px;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          margin-bottom: 4px;
        }
        .value {
          color: #1e293b;
          font-size: 14px;
          word-wrap: break-word;
        }
        .summary-text {
          background: #f1f5f9;
          padding: 15px;
          border-radius: 8px;
          border: 1px solid #e2e8f0;
          margin-top: 15px;
        }
        .high-value-missed {
          background: #fee2e2;
          color: #991b1b;
          padding: 6px 12px;
          border-radius: 20px;
          font-size: 11px;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          display: inline-block;
          margin-top: 10px;
        }
        @media print { 
          body { margin: 0; }
          .call-item { page-break-inside: avoid; }
        }
      </style>
    </head>
    <body>
      <div class="header">
        <h1>${clinicName}</h1>
        <p>Call Analytics Report</p>
        <p>Generated on ${currentDate} • ${data.length} calls</p>
      </div>
      
      <div class="summary">
        <h3>Report Summary</h3>
        <p>${data.length} calls analyzed • ${selectedColumns.length} columns included</p>
      </div>
      
      ${data.map((item, index) => `
        <div class="call-item">
          <div class="call-title">${item.Call_File_Name || `Call #${index + 1}`}</div>
          <div class="call-details">
            ${selectedColumns.filter(colKey => colKey !== 'Call_File_Name').map(colKey => {
              const column = columnConfig.find(col => col.key === colKey);
              const label = column ? column.label : colKey;
              const value = item[colKey] || 'N/A';
              
              // Special handling for long text fields
              if (colKey === 'Call_Summary' || colKey === 'Sentiment_Summary') {
                return `
                  <div class="detail-item" style="grid-column: 1 / -1;">
                    <div class="label">${label}</div>
                    <div class="summary-text">${value}</div>
                  </div>
                `;
              } else {
                return `
                  <div class="detail-item">
                    <div class="label">${label}</div>
                    <div class="value">${value}</div>
                  </div>
                `;
              }
            }).join('')}
          </div>
          ${item.High_Value_Missed_Opportunity && selectedColumns.includes('High_Value_Missed_Opportunity') ? 
            '<div class="high-value-missed">⚠ High Value Opportunity Missed</div>' : ''}
        </div>
      `).join('')}
    </body>
    </html>
  `;
};

export const generatePDF = async (data, selectedColumns, columnConfig) => {
  try {
    const { jsPDF } = await import('jspdf');
    
    const doc = new jsPDF({
      orientation: 'portrait',
      unit: 'mm',
      format: 'a4'
    });

    const pageWidth = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();
    const margin = 20;
    const contentWidth = pageWidth - (margin * 2);
    let currentY = margin;

    // Helper functions
    const checkPageBreak = (neededHeight) => {
      if (currentY + neededHeight > pageHeight - margin) {
        doc.addPage();
        currentY = margin;
        return true;
      }
      return false;
    };

    const wrapText = (text, maxWidth, fontSize = 10) => {
      doc.setFontSize(fontSize);
      return doc.splitTextToSize(String(text || ''), maxWidth);
    };

    const addTextBlock = (title, text, maxWidth) => {
      if (!text || text === 'N/A' || text === '') return 0;
      
      doc.setFontSize(8);
      doc.setFont('helvetica', 'bold');
      doc.setTextColor(100, 116, 139);
      doc.text(title.toUpperCase() + ':', margin + 3, currentY);
      
      currentY += 5;
      
      doc.setFont('helvetica', 'normal');
      doc.setTextColor(55, 65, 81);
      doc.setFontSize(9);
      
      const lines = wrapText(text, maxWidth - 6, 9);
      const blockHeight = lines.length * 4 + 8;
      
      // Check if we need a new page for this block
      if (currentY + blockHeight > pageHeight - margin) {
        doc.addPage();
        currentY = margin;
        
        // Re-add title on new page
        doc.setFontSize(8);
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(100, 116, 139);
        doc.text(title.toUpperCase() + ':', margin + 3, currentY);
        currentY += 5;
        
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(55, 65, 81);
        doc.setFontSize(9);
      }
      
      // Add background for text blocks
      doc.setFillColor(248, 250, 252);
      doc.rect(margin, currentY - 3, contentWidth, blockHeight - 5, 'F');
      
      lines.forEach((line, index) => {
        doc.text(line, margin + 3, currentY + (index * 4));
      });
      
      currentY += blockHeight;
      return blockHeight;
    };

    // Separate long text fields from regular fields
    const longTextFields = ['Call_Summary', 'Sentiment_Summary', 'Full_Transcript_With_Timestamps'];
    const regularColumns = selectedColumns.filter(col => !longTextFields.includes(col));
    const longTextColumns = selectedColumns.filter(col => longTextFields.includes(col));

    // Header
    doc.setFillColor(37, 99, 235);
    doc.rect(0, 0, pageWidth, 40, 'F');
    
    doc.setTextColor(255, 255, 255);
    doc.setFontSize(20);
    doc.setFont('helvetica', 'bold');
    doc.text(process.env.REACT_APP_CLINIC_NAME || 'Lincolnwood Family Dental', margin, 20);
    
    doc.setFontSize(12);
    doc.setFont('helvetica', 'normal');
    doc.text('Call Analytics Report', margin, 30);
    
    currentY = 55;

    // Report metadata
    doc.setTextColor(0, 0, 0);
    doc.setFontSize(10);
    const currentDate = new Date().toLocaleDateString();
    doc.text(`Generated: ${currentDate}`, margin, currentY);
    doc.text(`Total Calls: ${data.length}`, margin + 60, currentY);
    doc.text(`Columns: ${selectedColumns.length}`, margin + 110, currentY);
    
    currentY += 15;

    // Summary section
    doc.setFillColor(248, 250, 252);
    doc.rect(margin, currentY, contentWidth, 20, 'F');
    doc.setDrawColor(226, 232, 240);
    doc.rect(margin, currentY, contentWidth, 20, 'S');

    doc.setFontSize(12);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(30, 41, 59);
    doc.text('Report Summary', margin + 5, currentY + 8);
    
    doc.setFontSize(9);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(100, 116, 139);
    doc.text(`${data.length} calls with ${selectedColumns.length} selected columns`, margin + 5, currentY + 15);

    currentY += 35;

    // Title for call details
    doc.setFontSize(14);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(0, 0, 0);
    doc.text('Call Details', margin, currentY);
    currentY += 10;

    // Process each call
    data.forEach((item, index) => {
      checkPageBreak(60);

      // Call header with background
      doc.setFillColor(255, 255, 255);
      doc.rect(margin, currentY, contentWidth, 30, 'F');
      doc.setDrawColor(226, 232, 240);
      doc.rect(margin, currentY, contentWidth, 30, 'S');

      // Call title
      doc.setFontSize(12);
      doc.setFont('helvetica', 'bold');
      doc.setTextColor(30, 41, 59);
      const callTitle = item.Call_File_Name || `Call #${index + 1}`;
      doc.text(callTitle, margin + 3, currentY + 8);

      // Date in top right
      doc.setFontSize(9);
      doc.setFont('helvetica', 'normal');
      doc.setTextColor(100, 116, 139);
      doc.text(item.Analysis_Date || 'Date N/A', pageWidth - margin - 30, currentY + 8);

      // Regular fields in grid format
      let detailY = currentY + 15;
      let columnIndex = 0;
      
      regularColumns.forEach(colKey => {
        if (colKey === 'Call_File_Name') return; // Skip as it's already shown in title
        
        const column = columnConfig.find(col => col.key === colKey);
        const label = column ? column.label : colKey;
        const value = String(item[colKey] || 'N/A');
        
        doc.setFontSize(7);
        doc.setTextColor(100, 116, 139);
        
        const xPos = margin + 3 + (columnIndex % 2) * (contentWidth / 2);
        const yPos = detailY + Math.floor(columnIndex / 2) * 6;
        
        // Check if we need to wrap to next page
        if (yPos > pageHeight - 40) {
          doc.addPage();
          currentY = margin;
          detailY = currentY + 15;
          columnIndex = 0;
          
          // Re-add call title on new page
          doc.setFontSize(11);
          doc.setFont('helvetica', 'bold');
          doc.setTextColor(30, 41, 59);
          doc.text(callTitle + ' (continued)', margin + 3, currentY + 8);
          currentY += 15;
          detailY = currentY;
        }
        
        doc.text(`${label}:`, xPos, yPos);
        
        doc.setTextColor(30, 41, 59);
        doc.setFont('helvetica', 'normal');
        
        // Truncate long values for grid display
        const displayValue = value.length > 35 ? value.substring(0, 35) + '...' : value;
        doc.text(displayValue, xPos + 30, yPos);
        
        columnIndex++;
      });

      currentY = detailY + Math.ceil(Math.max(columnIndex, 1) / 2) * 6 + 5;

      // High value missed indicator
      if (item.High_Value_Missed_Opportunity && selectedColumns.includes('High_Value_Missed_Opportunity')) {
        checkPageBreak(10);
        doc.setFillColor(254, 226, 226);
        doc.rect(margin + 3, currentY, 60, 6, 'F');
        doc.setFontSize(7);
        doc.setTextColor(153, 27, 27);
        doc.setFont('helvetica', 'bold');
        doc.text('⚠ HIGH VALUE OPPORTUNITY MISSED', margin + 5, currentY + 4);
        currentY += 10;
      }

      // Add long text fields as paragraphs
      longTextColumns.forEach(colKey => {
        const column = columnConfig.find(col => col.key === colKey);
        const label = column ? column.label : colKey;
        const value = item[colKey];
        
        if (value && value !== 'N/A' && value !== '') {
          checkPageBreak(20);
          currentY += 5; // Add some spacing
          addTextBlock(label, value, contentWidth);
          currentY += 5; // Add spacing after text block
        }
      });

      currentY += 15; // Space between calls
    });

    // Footer on last page
    const footerY = pageHeight - 15;
    doc.setFontSize(8);
    doc.setTextColor(100, 116, 139);
    doc.setFont('helvetica', 'normal');
    const footerText = `${process.env.REACT_APP_CLINIC_NAME || 'Lincolnwood Family Dental'} - Call Analytics Dashboard`;
    doc.text(footerText, pageWidth / 2, footerY, { align: 'center' });
    
    doc.setFontSize(7);
    doc.text('This report contains confidential information. Distribution should be limited to authorized personnel only.', 
             pageWidth / 2, footerY + 4, { align: 'center' });

    return doc;
  } catch (error) {
    console.error('PDF generation error:', error);
    throw new Error('Failed to generate PDF. Please ensure jsPDF is available.');
  }
};