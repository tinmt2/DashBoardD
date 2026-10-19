import React, { useEffect, useState, useRef } from 'react';

interface AnimatedNumberProps {
  value: number;
  duration?: number;
  className?: string;
  prefix?: string;
  suffix?: string;
}

export const AnimatedNumber: React.FC<AnimatedNumberProps> = ({
  value,
  duration = 850,
  className = '',
  prefix = '',
  suffix = '',
}) => {
  const [displayValue, setDisplayValue] = useState<number>(value);
  const [isRolling, setIsRolling] = useState<boolean>(false);
  const prevValueRef = useRef<number>(value);
  const animFrameRef = useRef<number | null>(null);

  useEffect(() => {
    const startValue = prevValueRef.current;
    const endValue = typeof value === 'number' && !isNaN(value) ? value : 0;
    
    // If no change, keep static
    if (startValue === endValue && displayValue === endValue) return;

    setIsRolling(true);
    const startTime = performance.now();

    const updateNumber = (currentTime: number) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      
      // easeOutCubic: 1 - (1 - t)^3
      const ease = 1 - Math.pow(1 - progress, 3);
      const current = Math.round(startValue + (endValue - startValue) * ease);

      setDisplayValue(current);

      if (progress < 1) {
        animFrameRef.current = requestAnimationFrame(updateNumber);
      } else {
        setDisplayValue(endValue);
        prevValueRef.current = endValue;
        setTimeout(() => setIsRolling(false), 200);
      }
    };

    animFrameRef.current = requestAnimationFrame(updateNumber);

    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
  }, [value, duration]);

  return (
    <span className={`inline-block tabular-nums ${isRolling ? 'animate-number-roll' : ''} ${className}`}>
      {prefix}
      {displayValue.toLocaleString('vi-VN')}
      {suffix}
    </span>
  );
};

export default AnimatedNumber;
