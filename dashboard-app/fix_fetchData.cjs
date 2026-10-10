const fs = require('fs');
let code = fs.readFileSync('src/pages/Dashboard.tsx', 'utf8');

const correctBlock = `      try {
        if (chain === 'Vaccine') {
          const [vacData, employees] = await Promise.all([
            fetchVaccineSummary(),
            EmployeeService.getEmployees()
          ]);
          setData(vacData.data);
          setActiveEmployees(employees);
        } else if (chain === 'Long Châu' || chain?.includes('Long')) {
          const [lcData, employees] = await Promise.all([
            fetchLongChauSummary(),
            EmployeeService.getEmployees()
          ]);
          setData(lcData.data);
          setActiveEmployees(employees);
        } else {
          const [summary, employees] = await Promise.all([
            fetchDashboardSummary(),
            EmployeeService.getEmployees()
          ]);
          setData(summary);
          setActiveEmployees(employees);
        }
        setLastUpdated(new Date());
      } catch (err: any) {`;

code = code.replace(/try\s*\{\s*if \(chain === 'Vaccine'\)[\s\S]*?catch \(err: any\) \{/, correctBlock);
fs.writeFileSync('src/pages/Dashboard.tsx', code, 'utf8');
console.log('Fixed fetchData block');
