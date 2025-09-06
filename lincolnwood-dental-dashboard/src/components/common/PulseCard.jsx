import React, { useState, useEffect } from 'react';

const PulseCard = ({ children, className = "", pulseColor = "blue" }) => {
  const [isPulsing, setIsPulsing] = useState(true);
  
  useEffect(() => {
    const interval = setInterval(() => {
      setIsPulsing(prev => !prev);
    }, 2000);
    return () => clearInterval(interval);
  }, []);
  
  return (
    <div className={`${className} ${isPulsing ? `ring-2 ring-${pulseColor}-300 ring-opacity-50` : ''} transition-all duration-1000`}>
      {children}
    </div>
  );
};

export default PulseCard;