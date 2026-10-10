const fs = require('fs');
let code = fs.readFileSync('src/pages/Dashboard.tsx', 'utf8');

// 1. Update getStoredTime
code = code.replace(
  /const getStoredTime = \(c: string\) => \{[\s\S]*?return stored \? new Date\(stored\) : new Date\(\);\s*\};/,
  `const getStoredTime = (c: string) => {
    const stored = localStorage.getItem(\`lastSync_\${c}\`);
    return stored ? new Date(stored) : null;
  };`
);

// 2. Update useState type to allow null
code = code.replace(
  /const \[lastUpdated, setLastUpdated\] = useState<Date>\(getStoredTime\(chain \|\| 'FPT Shop'\)\);/,
  "const [lastUpdated, setLastUpdated] = useState<Date | null>(getStoredTime(chain || 'FPT Shop'));"
);

// 3. Update the JSX string
code = code.replace(
  /C\?p nh\?t l\?n cu\?i: \{lastUpdated\.toLocaleString\('vi-VN'\)\}/g,
  "Cập nhật lần cuối: {lastUpdated ? lastUpdated.toLocaleString('vi-VN') : 'Chưa cập nhật gần đây'}"
);
code = code.replace(
  /Cập nhật lần cuối: \{lastUpdated\.toLocaleString\('vi-VN'\)\}/g,
  "Cập nhật lần cuối: {lastUpdated ? lastUpdated.toLocaleString('vi-VN') : 'Chưa cập nhật gần đây'}"
);

fs.writeFileSync('src/pages/Dashboard.tsx', code, 'utf8');
console.log('Fixed fallback display');
