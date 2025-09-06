import { format } from 'date-fns';

export const getGrade = (score) => {
  if (score >= 0.9) return "A";
  if (score >= 0.75) return "B";
  if (score >= 0.6) return "C";
  if (score > 0) return "D";
  return "F";
};

export const getScoreColor = (score) => {
  if (score >= 0.9) return "#16a34a";
  if (score >= 0.75) return "#facc15";
  if (score >= 0.6) return "#f97316";
  return "#ef4444";
};

export const formatTime = (date) => {
  if (!date) return "N/A";
  try {
    return format(new Date(date), "PPpp");
  } catch {
    return "Invalid Date";
  }
};