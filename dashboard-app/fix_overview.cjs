const fs = require('fs');
let code = fs.readFileSync('src/pages/OverviewDashboard.tsx', 'utf8');

const replacement = `      const fetchData = async () => {
        setLoading(true);
        try {
          const endDate = new Date();
          const startDate = new Date();
          startDate.setDate(endDate.getDate() - 7);
          const syncStartDate = new Date(startDate.getTime() - startDate.getTimezoneOffset() * 60000).toISOString().split('T')[0];
          const syncEndDate = new Date(endDate.getTime() - endDate.getTimezoneOffset() * 60000).toISOString().split('T')[0];

          const [fpt, lc, vac] = await Promise.all([
            fetchDashboardSummary(syncStartDate, syncEndDate),
            fetchLongChauSummary(syncStartDate, syncEndDate),
            fetchVaccineSummary(syncStartDate, syncEndDate)
          ]);`;

code = code.replace(/const fetchData = async \(\) => \{\s*setLoading\(true\);\s*try \{\s*const \[fpt, lc, vac\] = await Promise\.all\(\[\s*fetchDashboardSummary\(\),\s*fetchLongChauSummary\(\),\s*fetchVaccineSummary\(\)\s*\]\);/, replacement);

fs.writeFileSync('src/pages/OverviewDashboard.tsx', code, 'utf8');
console.log('Fixed OverviewDashboard date filter');
