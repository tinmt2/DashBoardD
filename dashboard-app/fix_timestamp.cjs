const fs = require('fs');
let code = fs.readFileSync('src/pages/Dashboard.tsx', 'utf8');

// 1. Add `lastUpdated` state
if (!code.includes('const [lastUpdated, setLastUpdated]')) {
    code = code.replace(
        'const [data, setData] = useState<any>(null);',
        'const [data, setData] = useState<any>(null);\n  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());'
    );
}

// 2. Update `lastUpdated` at the end of `fetchData` try block
if (!code.includes('setLastUpdated(new Date());')) {
    code = code.replace(
        /setData\(summary\);\n\s*setActiveEmployees\(employees\);\n\s*\}/,
        'setData(summary);\n          setActiveEmployees(employees);\n        }\n        setLastUpdated(new Date());'
    );
}

// 3. Replace the hardcoded `new Date()` in the render
code = code.replace(
    /C\?p nh\?t l\?n cu\?i: \{new Date\(\)\.toLocaleString\('vi-VN'\)\}/g,
    'Cập nhật lần cuối: {lastUpdated.toLocaleString(\'vi-VN\')}'
);
// In case mojibake matching fails, let's use a safer regex for the JSX part:
code = code.replace(
    /\{new Date\(\)\.toLocaleString\('vi-VN'\)\}/g,
    '{lastUpdated.toLocaleString(\'vi-VN\')}'
);

fs.writeFileSync('src/pages/Dashboard.tsx', code, 'utf8');
console.log('Fixed last updated timestamp behavior');
