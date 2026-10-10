const fs = require('fs');
let code = fs.readFileSync('src/pages/Dashboard.tsx', 'utf8');

const newBlock = `  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      if (chain === 'Vaccine') {
        const [vacData, employees] = await Promise.all([fetchVaccineSummary(), EmployeeService.getEmployees()]);
        setData(vacData.data); setActiveEmployees(employees);
      } else if (chain === 'Long Châu' || chain?.includes('Long') || chain?.includes('Ch')) {
        const [lcData, employees] = await Promise.all([fetchLongChauSummary(), EmployeeService.getEmployees()]);
        setData(lcData.data); setActiveEmployees(employees);
      } else {
        const [summary, employees] = await Promise.all([fetchDashboardSummary(), EmployeeService.getEmployees()]);
        setData(summary); setActiveEmployees(employees);
      }
      setLastUpdated(new Date());
    } catch (err: any) {
      setError(err.message || 'Lỗi cập nhật dữ liệu');
    } finally {
      setLoading(false);
    }
  };`;

code = code.replace(/const fetchData = async \(\) => \{[\s\S]*?setError\([^)]*\);\s*\}\s*finally\s*\{\s*setLoading\(false\);\s*\}\s*\};/m, newBlock);

fs.writeFileSync('src/pages/Dashboard.tsx', code, 'utf8');
console.log('Fixed fetchData block properly');
