const fs = require('fs');

let code = fs.readFileSync('src/pages/Dashboard.tsx', 'utf8');

const replacement = `uppercase tracking-widest">{chain === 'Long Châu' || chain === 'Vaccine' ? 'Tổng Ticket' : 'Tổng Callog'}</span\>`;
code = code.replace(/uppercase tracking-widest">\{chain === [^}]+\}<\/span>/g, replacement);
code = code.replace(/uppercase tracking-widest">Tổng callog<\/span>/gi, replacement);
code = code.replace(/uppercase tracking-widest">T.*?ng callog<\/span>/gi, replacement);

const btnReplacement = `<button className="text-[13px] font-bold text-blue-600 hover:underline">{chain === 'Long Châu' || chain === 'Vaccine' ? 'Ticket' : 'Callog'}</button>`;
code = code.replace(/<button className="text-\[13px\] font-bold text-blue-600 hover:underline">Callog<\/button>/g, btnReplacement);

fs.writeFileSync('src/pages/Dashboard.tsx', code, 'utf8');
console.log('Replaced text successfully');
