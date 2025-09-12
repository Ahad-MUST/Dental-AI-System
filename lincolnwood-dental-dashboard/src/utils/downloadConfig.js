// downloadConfig.js - Configuration for available columns and formats

export const AVAILABLE_COLUMNS = [
  {
    key: 'Call_File_Name',
    label: 'Call File Name',
    category: 'Basic Info',
    description: 'Name of the call recording file',
    required: true
  },
  {
    key: 'Analysis_Date',
    label: 'Analysis Date',
    category: 'Basic Info',
    description: 'Date when the call was analyzed',
    required: true
  },
  {
    key: 'Analysis_Time',
    label: 'Analysis Time',
    category: 'Basic Info',
    description: 'Time when the call was analyzed'
  },
  {
    key: 'Full_Transcript_With_Timestamps',
    label: 'Full Transcript With Timestamps',
    category: 'Content',
    description: 'Complete transcript of the call with timestamps',
    isLongText: true
  },
  {
    key: 'Call_Summary',
    label: 'Call Summary',
    category: 'Content',
    description: 'AI-generated summary of the call',
    isLongText: true
  },
  {
    key: 'Representative_Name',
    label: 'Representative Name',
    category: 'Basic Info',
    description: 'Name of the staff member who handled the call'
  },
  {
    key: 'Representative_Score',
    label: 'Representative Score',
    category: 'Performance',
    description: 'Representative performance score (0-1)'
  },
  {
    key: 'High_Value_Missed_Opportunity',
    label: 'High Value Missed Opportunity',
    category: 'Opportunities',
    description: 'Whether a high-value opportunity was missed'
  },
  {
    key: 'Patient_Sentiment',
    label: 'Patient Sentiment',
    category: 'Sentiment',
    description: 'Patient-specific sentiment analysis'
  },
  {
    key: 'Staff_Sentiment',
    label: 'Staff Sentiment',
    category: 'Sentiment',
    description: 'Staff-specific sentiment analysis'
  },
  {
    key: 'Overall_Sentiment',
    label: 'Overall Sentiment',
    category: 'Sentiment',
    description: 'Overall sentiment of the call'
  },
  {
    key: 'Sentiment_Confidence',
    label: 'Sentiment Confidence',
    category: 'Sentiment',
    description: 'Confidence score for sentiment analysis'
  },
  {
    key: 'Sentiment_Summary',
    label: 'Sentiment Summary',
    category: 'Sentiment',
    description: 'Detailed sentiment analysis summary',
    isLongText: true
  },
  {
    key: 'Patient_Primary_Emotion',
    label: 'Patient Primary Emotion',
    category: 'Emotions',
    description: 'Primary emotion detected from patient'
  },
  {
    key: 'Patient_Emotion_Confidence',
    label: 'Patient Emotion Confidence',
    category: 'Emotions',
    description: 'Confidence score for patient emotion detection'
  },
  {
    key: 'Patient_Emotion_Intensity',
    label: 'Patient Emotion Intensity',
    category: 'Emotions',
    description: 'Intensity level of patient emotion'
  },
  {
    key: 'Staff_Primary_Emotion',
    label: 'Staff Primary Emotion',
    category: 'Emotions',
    description: 'Primary emotion detected from staff'
  },
  {
    key: 'Staff_Emotion_Confidence',
    label: 'Staff Emotion Confidence',
    category: 'Emotions',
    description: 'Confidence score for staff emotion detection'
  },
  {
    key: 'Emotion_Flags',
    label: 'Emotion Flags',
    category: 'Emotions',
    description: 'Special emotion indicators (pain, anxiety, etc.)'
  },
  {
    key: 'Call_Emotional_Health',
    label: 'Call Emotional Health',
    category: 'Emotions',
    description: 'Overall emotional health assessment of the call'
  },
  {
    key: 'Emotional_Alignment',
    label: 'Emotional Alignment',
    category: 'Emotions',
    description: 'Alignment between patient and staff emotions'
  },
  {
    key: 'Escalation_Pattern',
    label: 'Escalation Pattern',
    category: 'Performance',
    description: 'Pattern of escalation during the call'
  },
  {
    key: 'Call_Tag',
    label: 'Call Tag',
    category: 'Classification',
    description: 'Category/tag assigned to the call'
  },
  {
    key: 'Coaching_Candidate',
    label: 'Coaching Candidate',
    category: 'Performance',
    description: 'Whether the call indicates need for coaching'
  }
];

export const COLUMN_CATEGORIES = [
  { key: 'Basic Info', label: 'Basic Information', icon: 'Info' },
  { key: 'Performance', label: 'Performance Metrics', icon: 'TrendingUp' },
  { key: 'Content', label: 'Call Content', icon: 'FileText' },
  { key: 'Classification', label: 'Classification', icon: 'Tag' },
  { key: 'Sentiment', label: 'Sentiment Analysis', icon: 'Heart' },
  { key: 'Emotions', label: 'Emotion Analysis', icon: 'Brain' },
  { key: 'Opportunities', label: 'Opportunities', icon: 'AlertTriangle' }
];

export const DOWNLOAD_FORMATS = [
  {
    value: 'csv',
    label: 'CSV',
    icon: 'FileSpreadsheet',
    description: 'Spreadsheet format',
    mimeType: 'text/csv',
    extension: '.csv'
  },
  {
    value: 'txt',
    label: 'TXT',
    icon: 'FileText',
    description: 'Plain text format',
    mimeType: 'text/plain',
    extension: '.txt'
  },
  {
    value: 'html',
    label: 'HTML',
    icon: 'File',
    description: 'Web format',
    mimeType: 'text/html',
    extension: '.html'
  },
  {
    value: 'pdf',
    label: 'PDF',
    icon: 'File',
    description: 'Professional report',
    mimeType: 'application/pdf',
    extension: '.pdf'
  }
];

export const DEFAULT_SELECTED_COLUMNS = [
  'Call_File_Name',
  'Analysis_Date',
  'Representative_Name',
  'Representative_Score',
  'Call_Summary',
  'Call_Tag',
  'Overall_Sentiment',
  'High_Value_Missed_Opportunity'
];