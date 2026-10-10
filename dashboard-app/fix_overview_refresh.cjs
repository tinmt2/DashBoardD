const fs = require('fs');
let code = fs.readFileSync('src/pages/OverviewDashboard.tsx', 'utf8');

const replacement = `      fetchData();
      
      const interval = setInterval(fetchData, 5 * 60 * 1000); // 5 minutes
      return () => clearInterval(interval);
    }, []);`;

code = code.replace(/fetchData\(\);\s*\}, \[\]\);/, replacement);

fs.writeFileSync('src/pages/OverviewDashboard.tsx', code, 'utf8');
console.log('Added auto-refresh to OverviewDashboard');
