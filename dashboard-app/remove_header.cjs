const fs = require('fs');
let code = fs.readFileSync('src/pages/OverviewDashboard.tsx', 'utf8');
code = code.replace(/<div className="mb-8">[\s\S]*?<\/div>/, '');
fs.writeFileSync('src/pages/OverviewDashboard.tsx', code, 'utf8');
console.log('Removed header');
