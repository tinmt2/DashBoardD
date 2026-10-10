const fs = require('fs');
let code = fs.readFileSync('src/pages/Dashboard.tsx', 'utf8');

const handleFileSelectStr = `  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsImporting(true);
    setImportError(null);
    setImportPreview(null);

    try {
      if (chain === 'Vaccine') {
        const res = await previewVaccineImport(file);
        setImportPreview(res);
      } else if (chain === 'Long Châu' || chain?.includes('Long') || chain?.includes('Ch')) {
        const res = await previewLongChauImport(file);
        setImportPreview(res);
      } else {
        const res = await previewFptShopImport(file);
        setImportPreview(res);
      }
    } catch (err: any) {
      setImportError(err.message || 'Lỗi khi đọc file Excel');
    } finally {
      setIsImporting(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

`;

code = code.replace(/const fetchData = async \(\) => \{/, handleFileSelectStr + '  const fetchData = async () => {');
fs.writeFileSync('src/pages/Dashboard.tsx', code, 'utf8');
console.log('Restored handleFileSelect');
