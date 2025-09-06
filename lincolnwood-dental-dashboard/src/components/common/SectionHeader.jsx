import React from 'react';

const SectionHeader = ({ 
  title, 
  subtitle, 
  icon: Icon, 
  className = "",
  children 
}) => {
  return (
    <div className={`mb-6 ${className}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          {Icon && (
            <div className="bg-teal-50 rounded-lg p-2">
              <Icon className="h-5 w-5 text-teal-600" strokeWidth={2} />
            </div>
          )}
          <div>
            <h2 className="text-xl font-semibold text-gray-800">{title}</h2>
            {subtitle && (
              <p className="text-sm text-gray-600">{subtitle}</p>
            )}
          </div>
        </div>
        {children}
      </div>
    </div>
  );
};

export default SectionHeader;