const fs = require('fs');

let code = fs.readFileSync('src/pages/Dashboard.tsx', 'utf8');

code = code.replace(/<AnimatedNumber value=\{\} \/>/, "<AnimatedNumber value={ticketStatusStats.find(s => s.status.toLowerCase().includes('đang') || s.status.toLowerCase().includes('xử lý') || s.status.toLowerCase().includes('ang'))?.count || 0} />");

code = code.replace(/<AnimatedNumber value=\{\} \/>/, "<AnimatedNumber value={ticketStatusStats.find(s => s.status.toLowerCase().includes('hoàn tất') || s.status.toLowerCase().includes('ho') || s.status.toLowerCase().includes('tất'))?.count || 0} />");

fs.writeFileSync('src/pages/Dashboard.tsx', code, 'utf8');
console.log('Fixed missing values');
