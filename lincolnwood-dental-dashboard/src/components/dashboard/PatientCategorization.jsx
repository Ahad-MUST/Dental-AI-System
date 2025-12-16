import React from 'react';
import { UserPlus, UserCheck, Calendar, CheckCircle, XCircle, FileText, MessageSquare, AlertCircle, HelpCircle } from 'lucide-react';
import Card from '../common/Card';
import AnimatedCounter from '../common/AnimatedCounter';
import GradientProgressBar from '../common/GradientProgressBar';

const PatientCategorization = ({ data }) => {
  // Filter data by patient type
  const newPatients = data.filter(item => item.Patient_Type === 'new_patient');
  const existingPatients = data.filter(item => item.Patient_Type === 'existing_patient');

  // Calculate booking conversion rates
  const newPatientsBooked = newPatients.filter(item => item.Appointment_Booked === 'TRUE' || item.Appointment_Booked === true).length;
  const existingPatientsBooked = existingPatients.filter(item => item.Appointment_Booked === 'TRUE' || item.Appointment_Booked === true).length;

  const newPatientConversionRate = newPatients.length > 0 ? Math.round((newPatientsBooked / newPatients.length) * 100) : 0;
  const existingPatientConversionRate = existingPatients.length > 0 ? Math.round((existingPatientsBooked / existingPatients.length) * 100) : 0;

  // NEW PATIENTS: Script adherence
  const scriptFollowedCount = newPatients.filter(item => item.Script_Followed === 'TRUE' || item.Script_Followed === true).length;
  const scriptNotFollowedCount = newPatients.filter(item => item.Script_Followed === 'FALSE' || item.Script_Followed === false).length;
  const scriptAdherenceRate = newPatients.length > 0 ? Math.round((scriptFollowedCount / newPatients.length) * 100) : 0;

  // EXISTING PATIENTS: Issue resolution
  const issuesResolved = existingPatients.filter(item => item.Issue_Resolved === 'TRUE' || item.Issue_Resolved === true).length;
  const issuesNotResolved = existingPatients.filter(item => item.Issue_Resolved === 'FALSE' || item.Issue_Resolved === false).length;
  const resolutionRate = existingPatients.length > 0 ? Math.round((issuesResolved / existingPatients.length) * 100) : 0;

  // Call concern types breakdown for existing patients
  const concernTypes = {
    issue: existingPatients.filter(item => item.Call_Concern_Type === 'issue').length,
    question: existingPatients.filter(item => item.Call_Concern_Type === 'question').length,
    concern: existingPatients.filter(item => item.Call_Concern_Type === 'concern').length,
    query: existingPatients.filter(item => item.Call_Concern_Type === 'query').length
  };

  const stats = [
    {
      icon: UserPlus,
      title: "New Patients",
      value: newPatients.length,
      iconColor: "text-blue-600",
      iconBg: "bg-blue-50",
      description: "First-time callers",
      subStats: [
        { label: "Booked", value: newPatientsBooked, color: "text-emerald-600" },
        { label: "Not Booked", value: newPatients.length - newPatientsBooked, color: "text-slate-400" }
      ],
      progress: {
        value: newPatientConversionRate,
        max: 100,
        variant: "primary",
        label: `${newPatientConversionRate}% Conversion Rate`
      }
    },
    {
      icon: UserCheck,
      title: "Existing Patients",
      value: existingPatients.length,
      iconColor: "text-purple-600",
      iconBg: "bg-purple-50",
      description: "Returning callers",
      subStats: [
        { label: "Booked", value: existingPatientsBooked, color: "text-emerald-600" },
        { label: "Not Booked", value: existingPatients.length - existingPatientsBooked, color: "text-slate-400" }
      ],
      progress: {
        value: existingPatientConversionRate,
        max: 100,
        variant: "purple",
        label: `${existingPatientConversionRate}% Conversion Rate`
      }
    },
    {
      icon: FileText,
      title: "Script Adherence",
      value: scriptAdherenceRate,
      suffix: "%",
      iconColor: "text-emerald-600",
      iconBg: "bg-emerald-50",
      description: "New patient calls",
      subStats: [
        { label: "Followed", value: scriptFollowedCount, color: "text-emerald-600" },
        { label: "Not Followed", value: scriptNotFollowedCount, color: "text-red-500" }
      ],
      progress: {
        value: scriptAdherenceRate,
        max: 100,
        variant: "success",
        label: `${scriptFollowedCount}/${newPatients.length} calls followed script`
      }
    },
    {
      icon: CheckCircle,
      title: "Issue Resolution",
      value: resolutionRate,
      suffix: "%",
      iconColor: "text-amber-600",
      iconBg: "bg-amber-50",
      description: "Existing patient calls",
      subStats: [
        { label: "Resolved", value: issuesResolved, color: "text-emerald-600" },
        { label: "Unresolved", value: issuesNotResolved, color: "text-red-500" }
      ],
      progress: {
        value: resolutionRate,
        max: 100,
        variant: "warning",
        label: `${issuesResolved}/${existingPatients.length} issues resolved`
      }
    }
  ];

  return (
    <div className="space-y-6">
      {/* Patient Type Overview */}
      <Card className="bg-gradient-to-br from-blue-50 to-purple-50 border-blue-200">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-bold text-slate-900 mb-2">Patient Categorization & Conversion Tracking</h2>
            <p className="text-sm text-slate-600">Track new vs existing patients, booking conversions, and quality metrics</p>
          </div>
          <div className="flex items-center space-x-2 bg-white px-4 py-2 rounded-lg shadow-sm">
            <Calendar className="h-5 w-5 text-blue-600" />
            <div className="text-right">
              <p className="text-xs text-slate-500">Total Calls</p>
              <p className="text-lg font-bold text-slate-900">{data.length}</p>
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {stats.map((stat, index) => (
            <div key={index} className="bg-white rounded-xl p-5 shadow-sm border border-slate-200 hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between mb-4">
                <div className={`${stat.iconBg} rounded-lg p-2.5`}>
                  <stat.icon className={`h-5 w-5 ${stat.iconColor}`} strokeWidth={2} />
                </div>
                <div className="text-right">
                  <p className="text-xs font-medium text-slate-500 uppercase">{stat.title}</p>
                  <p className="text-xs text-slate-400">{stat.description}</p>
                </div>
              </div>

              <div className="space-y-3">
                <div className="text-3xl font-bold text-slate-900">
                  <AnimatedCounter target={stat.value} suffix={stat.suffix || ""} />
                </div>

                {/* Sub-stats */}
                {stat.subStats && (
                  <div className="flex items-center justify-between text-xs">
                    {stat.subStats.map((sub, idx) => (
                      <div key={idx} className="flex items-center space-x-1">
                        <span className="text-slate-500">{sub.label}:</span>
                        <span className={`font-semibold ${sub.color}`}>{sub.value}</span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Progress bar */}
                <div className="space-y-1">
                  <GradientProgressBar
                    value={stat.progress.value}
                    max={stat.progress.max}
                    variant={stat.progress.variant}
                    size="sm"
                    animated={true}
                  />
                  <p className="text-xs text-slate-500">{stat.progress.label}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Detailed Breakdown Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* New Patients Detail */}
        <Card>
          <div className="flex items-center space-x-3 mb-6">
            <div className="bg-blue-50 rounded-lg p-2">
              <UserPlus className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-900">New Patient Analysis</h3>
              <p className="text-sm text-slate-500">{newPatients.length} first-time callers</p>
            </div>
          </div>

          <div className="space-y-4">
            {/* Conversion */}
            <div className="bg-slate-50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-slate-700">Booking Conversion</span>
                <span className="text-lg font-bold text-slate-900">{newPatientConversionRate}%</span>
              </div>
              <GradientProgressBar value={newPatientConversionRate} max={100} variant="primary" size="sm" />
              <div className="flex items-center justify-between mt-2 text-xs text-slate-500">
                <span>{newPatientsBooked} booked</span>
                <span>{newPatients.length - newPatientsBooked} not booked</span>
              </div>
            </div>

            {/* Script Adherence */}
            <div className="bg-slate-50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-slate-700">Script Adherence</span>
                <span className="text-lg font-bold text-slate-900">{scriptAdherenceRate}%</span>
              </div>
              <GradientProgressBar value={scriptAdherenceRate} max={100} variant="success" size="sm" />
              <div className="flex items-center justify-between mt-2 text-xs">
                <span className="text-emerald-600 font-medium">✓ {scriptFollowedCount} followed</span>
                <span className="text-red-500 font-medium">✗ {scriptNotFollowedCount} not followed</span>
              </div>
            </div>

            {/* Insight */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <p className="text-xs text-blue-800">
                <strong>Insight:</strong> {scriptAdherenceRate >= 80 ?
                  "Excellent script adherence! Keep up the great work." :
                  scriptAdherenceRate >= 60 ?
                  "Good script adherence, but there's room for improvement." :
                  "Script adherence needs attention. Consider additional training."}
              </p>
            </div>
          </div>
        </Card>

        {/* Existing Patients Detail */}
        <Card>
          <div className="flex items-center space-x-3 mb-6">
            <div className="bg-purple-50 rounded-lg p-2">
              <UserCheck className="h-5 w-5 text-purple-600" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-900">Existing Patient Analysis</h3>
              <p className="text-sm text-slate-500">{existingPatients.length} returning callers</p>
            </div>
          </div>

          <div className="space-y-4">
            {/* Conversion */}
            <div className="bg-slate-50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-slate-700">Booking Conversion</span>
                <span className="text-lg font-bold text-slate-900">{existingPatientConversionRate}%</span>
              </div>
              <GradientProgressBar value={existingPatientConversionRate} max={100} variant="purple" size="sm" />
              <div className="flex items-center justify-between mt-2 text-xs text-slate-500">
                <span>{existingPatientsBooked} booked</span>
                <span>{existingPatients.length - existingPatientsBooked} not booked</span>
              </div>
            </div>

            {/* Issue Resolution */}
            <div className="bg-slate-50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-slate-700">Issue Resolution</span>
                <span className="text-lg font-bold text-slate-900">{resolutionRate}%</span>
              </div>
              <GradientProgressBar value={resolutionRate} max={100} variant="warning" size="sm" />
              <div className="flex items-center justify-between mt-2 text-xs">
                <span className="text-emerald-600 font-medium">✓ {issuesResolved} resolved</span>
                <span className="text-red-500 font-medium">✗ {issuesNotResolved} unresolved</span>
              </div>
            </div>

            {/* Call Concern Types */}
            <div className="bg-slate-50 rounded-lg p-4">
              <p className="text-sm font-medium text-slate-700 mb-3">Call Concerns Breakdown</p>
              <div className="space-y-2">
                {[
                  { type: 'issue', label: 'Issues', icon: AlertCircle, color: 'red' },
                  { type: 'question', label: 'Questions', icon: HelpCircle, color: 'blue' },
                  { type: 'concern', label: 'Concerns', icon: MessageSquare, color: 'amber' },
                  { type: 'query', label: 'Queries', icon: FileText, color: 'purple' }
                ].map(({ type, label, icon: Icon, color }) => {
                  const count = concernTypes[type];
                  const percentage = existingPatients.length > 0 ? Math.round((count / existingPatients.length) * 100) : 0;
                  return (
                    <div key={type} className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <Icon className={`h-4 w-4 text-${color}-500`} />
                        <span className="text-xs text-slate-600">{label}</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="text-xs font-semibold text-slate-900">{count}</span>
                        <span className="text-xs text-slate-400">({percentage}%)</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Google Ads Conversion Summary */}
      <Card className="bg-gradient-to-r from-emerald-50 to-blue-50 border-emerald-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-bold text-slate-900 mb-1">Google Ads Conversion Summary</h3>
            <p className="text-sm text-slate-600">Ready for export to Google Ads conversion tracking</p>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-white rounded-lg p-4 text-center shadow-sm">
              <p className="text-xs text-slate-500 mb-1">Total Conversions</p>
              <p className="text-2xl font-bold text-emerald-600">{newPatientsBooked + existingPatientsBooked}</p>
              <p className="text-xs text-slate-400 mt-1">Appointments Booked</p>
            </div>
            <div className="bg-white rounded-lg p-4 text-center shadow-sm">
              <p className="text-xs text-slate-500 mb-1">Overall Conv. Rate</p>
              <p className="text-2xl font-bold text-blue-600">
                {data.length > 0 ? Math.round(((newPatientsBooked + existingPatientsBooked) / data.length) * 100) : 0}%
              </p>
              <p className="text-xs text-slate-400 mt-1">All Calls</p>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default PatientCategorization;
