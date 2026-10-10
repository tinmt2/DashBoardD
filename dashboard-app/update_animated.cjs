const fs = require('fs');

let code = fs.readFileSync('src/pages/Dashboard.tsx', 'utf8');

const newAnimatedNumber = `const AnimatedNumber: React.FC<{ value: number | string, isLoading?: boolean }> = ({ value, isLoading }) => {
  const numericValue = typeof value === 'string' ? parseInt(value.replace(/\\D/g, '')) : value;
  const [displayValue, setDisplayValue] = useState(numericValue || 0);
  const fakeInterval = useRef<any>(null);
  const isFakeSyncing = useRef(false);

  useEffect(() => {
    if (isNaN(numericValue)) return;
    
    if (isLoading) {
      isFakeSyncing.current = true;
      if (!fakeInterval.current) {
        fakeInterval.current = setInterval(() => {
          setDisplayValue(prev => prev + Math.floor(Math.random() * 5));
        }, 80);
      }
      return; // Do not run count up yet
    }

    // When loading finishes
    if (!isLoading && isFakeSyncing.current) {
      isFakeSyncing.current = false;
      if (fakeInterval.current) {
        clearInterval(fakeInterval.current);
        fakeInterval.current = null;
      }
    }

    const startVal = displayValue;
    const targetVal = numericValue;
    if (startVal === targetVal) return;

    const duration = 800; // ms
    const startTime = performance.now();

    const updateCount = (currentTime: number) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const easeOut = 1 - Math.pow(1 - progress, 3);
      const currentVal = Math.floor(startVal + (targetVal - startVal) * easeOut);
      
      setDisplayValue(currentVal);

      if (progress < 1) {
        requestAnimationFrame(updateCount);
      } else {
        setDisplayValue(targetVal);
      }
    };
    requestAnimationFrame(updateCount);

  }, [numericValue, isLoading]);

  useEffect(() => {
    return () => {
      if (fakeInterval.current) clearInterval(fakeInterval.current);
    };
  }, []);

  if (isNaN(numericValue)) return <>{value}</>;
  return <>{displayValue}</>;
};`;

// Replace component
code = code.replace(/const AnimatedNumber: React\.FC<\{ value: number \| string \}>[\s\S]*?return <>{displayValue}<\/>;\n};/, newAnimatedNumber);

// Add isLoading prop
code = code.replace(/<AnimatedNumber value=\{/g, '<AnimatedNumber isLoading={loading} value={');

fs.writeFileSync('src/pages/Dashboard.tsx', code, 'utf8');
console.log("Updated AnimatedNumber with fake sync");
