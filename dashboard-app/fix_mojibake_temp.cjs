const fs = require('fs');
const file = 'src/pages/Dashboard.tsx';
let text = fs.readFileSync(file, 'utf8').replace(/^\uFEFF/, '');

// Build reverse table: unicode char -> cp1252 byte
const cp1252 = {0x80:0x20AC,0x82:0x201A,0x83:0x0192,0x84:0x201E,0x85:0x2026,0x86:0x2020,0x87:0x2021,0x88:0x02C6,0x89:0x2030,0x8A:0x0160,0x8B:0x2039,0x8C:0x0152,0x8E:0x017D,0x91:0x2018,0x92:0x2019,0x93:0x201C,0x94:0x201D,0x95:0x2022,0x96:0x2013,0x97:0x2014,0x98:0x02DC,0x99:0x2122,0x9A:0x0161,0x9B:0x203A,0x9C:0x0153,0x9E:0x017E,0x9F:0x0178};
const rev = new Map();
for (let b = 0; b < 256; b++) rev.set(String.fromCharCode(b), b);
for (const [b, u] of Object.entries(cp1252)) rev.set(String.fromCharCode(u), Number(b));
const utf8 = new TextDecoder('utf-8', { fatal: true });

let fixed = 0;
const lines = text.split('\n').map(line => {
  if (!/[\u0080-\u00FF\u0152-\u2122]/.test(line)) return line;
  const bytes = [];
  for (const ch of line) {
    if (!rev.has(ch)) return line; // contains real Unicode (already correct)
    bytes.push(rev.get(ch));
  }
  try {
    const out = utf8.decode(new Uint8Array(bytes));
    if (out !== line) fixed++;
    return out;
  } catch { return line; }
});

fs.writeFileSync(file, lines.join('\n'), 'utf8');
console.log('Fixed lines:', fixed);

