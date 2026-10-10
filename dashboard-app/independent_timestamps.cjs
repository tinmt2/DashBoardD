const fs = require('fs');
let code = fs.readFileSync('src/pages/Dashboard.tsx', 'utf8');

// 1. Remove setLastUpdated from fetchData
code = code.replace(/\s*setLastUpdated\(new Date\(\)\);/, '');

// 2. Add local storage helper and update state initialization
const stateReplacement = `  const getStoredTime = (c: string) => {
    const stored = localStorage.getItem(\`lastSync_\${c}\`);
    return stored ? new Date(stored) : new Date();
  };
  const [data, setData] = useState<any>(null);
  const [lastUpdated, setLastUpdated] = useState<Date>(getStoredTime(chain || 'FPT Shop'));`;

code = code.replace(/const \[data, setData\] = useState<any>\(null\);\s*const \[lastUpdated, setLastUpdated\] = useState<Date>\(new Date\(\)\);/, stateReplacement);

// 3. Update useEffect to switch time when chain changes
code = code.replace(/useEffect\(\(\) => \{\s*fetchData\(\);/, `useEffect(() => {\n      setLastUpdated(getStoredTime(chain || 'FPT Shop'));\n      fetchData();`);

// 4. Update lastUpdated in handleSync
const syncReplacement = `await fetchData();
      triggerSuccessAnimation(); // Added sync
      const now = new Date();
      setLastUpdated(now);
      localStorage.setItem(\`lastSync_\${chain || 'FPT Shop'}\`, now.toISOString());`;
code = code.replace(/await fetchData\(\);\s*triggerSuccessAnimation\(\);\s*\/\/ Added sync/, syncReplacement);

// 5. Update lastUpdated in handleCommitImport
const commitReplacement = `await fetchData(); // Refresh data
      triggerSuccessAnimation(); // Added
      const now = new Date();
      setLastUpdated(now);
      localStorage.setItem(\`lastSync_\${chain || 'FPT Shop'}\`, now.toISOString());`;
code = code.replace(/await fetchData\(\);\s*\/\/ Refresh data\s*triggerSuccessAnimation\(\);\s*\/\/ Added/, commitReplacement);

fs.writeFileSync('src/pages/Dashboard.tsx', code, 'utf8');
console.log('Fixed independent timestamps');
