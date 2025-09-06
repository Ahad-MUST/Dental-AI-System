import React from 'react';

const Card = ({ 
  children, 
  className = '', 
  hover = false, 
  padding = 'lg',
  ...props 
}) => {
  const paddingClasses = {
    sm: 'p-4',
    md: 'p-6', 
    lg: 'p-8',
    xl: 'p-10'
  };

  const baseClasses = `
    bg-white 
    rounded-2xl 
    border 
    border-slate-200/60 
    shadow-sm
    ${hover ? 'hover:shadow-lg hover:border-slate-300/60 transition-all duration-300' : ''}
    ${paddingClasses[padding]}
    ${className}
  `.trim().replace(/\s+/g, ' ');

  return (
    <div className={baseClasses} {...props}>
      {children}
    </div>
  );
};

export default Card;