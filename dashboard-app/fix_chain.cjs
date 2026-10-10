const fs = require('fs');
let code = fs.readFileSync('src/pages/Dashboard.tsx', 'utf8');

// Replace all strict exact match variations with a safe check
code = code.replace(/chain === 'Long Ch[^']*'/g, "chain?.includes('Long')");

// Also check for `chain === 'Vaccine'` just in case, but Vaccine is usually ASCII.
fs.writeFileSync('src/pages/Dashboard.tsx', code, 'utf8');
console.log('Fixed Long Chau chain conditions');
