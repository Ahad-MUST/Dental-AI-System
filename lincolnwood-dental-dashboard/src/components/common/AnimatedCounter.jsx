import React, { useState, useEffect } from 'react';

const AnimatedCounter = ({ target, suffix = "", duration = 2000 }) => {
  const [current, setCurrent] = useState(0);
  
  useEffect(() => {
    const increment = target / (duration / 50);
    const timer = setInterval(() => {
      setCurrent(prev => {
        if (prev >= target) {
          clearInterval(timer);
          return target;
        }
        return Math.min(prev + increment, target);
      });
    }, 50);
    
    return () => clearInterval(timer);
  }, [target, duration]);
  
  return <span>{Math.round(current)}{suffix}</span>;
};

export default AnimatedCounter;