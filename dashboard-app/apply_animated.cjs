const fs = require('fs');

let code = fs.readFileSync('src/pages/Dashboard.tsx', 'utf8');

// 1. Remove setData(null) from fetchData
code = code.replace(/setLoading\(true\);\s*setError\(null\);\s*setData\(null\);/, 'setLoading(true);\n    setError(null);\n    // Removed setData(null) to prevent flashing');

// 2. Insert AnimatedNumber component right before `const Dashboard`
const animatedNumberCode = `
const AnimatedNumber: React.FC<{ value: number | string }> = ({ value }) => {
  const numericValue = typeof value === 'string' ? parseInt(value.replace(/\\D/g, '')) : value;
  const [displayValue, setDisplayValue] = useState(numericValue || 0);

  useEffect(() => {
    if (isNaN(numericValue)) return;
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
  }, [numericValue]);

  if (isNaN(numericValue)) return <>{value}</>;
  return <>{displayValue}</>;
};
`;

if (!code.includes('const AnimatedNumber')) {
  code = code.replace(/(const Dashboard: React.FC<Props> =)/, animatedNumberCode + '\n$1');
}

// 3. Replace the 4 KPI values with <AnimatedNumber value={...} />
// Value 1
code = code.replace(/(<div className="text-\[48px\][^>]*>)\s*\{chain === [^}]+\}\s*(<\/div>)/, "$1<AnimatedNumber value={chain === 'Long Châu' || chain?.includes('Long') ? kpiData.checked : kpiData.total} />$2");

// Value 2 (Dang xu ly) & Value 3 (Hoan tat)
code = code.replace(/(<div className="text-\[48px\][^>]*>)\s*(\{ticketStatusStats\.find\(s => s\.status\.toLowerCase\(\)\.includes\([^}]+\}\s*)(<\/div>)/g, (match, p1, p2, p3) => {
    if (p2.includes('<AnimatedNumber')) return match;
    return p1 + '\\n                        <AnimatedNumber value={' + p2.trim().replace(/^\\{/, '').replace(/\\}$/, '') + '} />\\n                      ' + p3;
});

// Value 4 (Nhac nho): {kpiData.reminders}
code = code.replace(/(<div className="text-\[48px\][^>]*>)\s*\{kpiData\.reminders\}\s*(<\/div>)/, '$1<AnimatedNumber value={kpiData.reminders} />$2');

fs.writeFileSync('src/pages/Dashboard.tsx', code, 'utf8');
console.log('Applied AnimatedNumber logic to Dashboard.tsx');
