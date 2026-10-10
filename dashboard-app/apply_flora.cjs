const fs = require('fs');

let code = fs.readFileSync('src/pages/Dashboard.tsx', 'utf8');

// 1. Insert SVGs right before `const Dashboard = () => {` or `export default function Dashboard`
const svgCode = `
const TannaSVG = () => (
  <svg width="100%" height="100%" viewBox="0 0 32 32" style={{ filter: 'drop-shadow(0px 2px 3px rgba(0,0,0,0.15))', overflow: 'visible' }}>
    <g fill="#ffffff" stroke="#94a3b8" strokeWidth="0.8">
      <ellipse cx="16" cy="6" rx="3.5" ry="6" />
      <ellipse cx="16" cy="26" rx="3.5" ry="6" />
      <ellipse cx="6" cy="16" rx="6" ry="3.5" />
      <ellipse cx="26" cy="16" rx="6" ry="3.5" />
      <ellipse cx="9" cy="9" rx="6" ry="3.5" transform="rotate(45 9 9)" />
      <ellipse cx="23" cy="23" rx="6" ry="3.5" transform="rotate(45 23 23)" />
      <ellipse cx="9" cy="23" rx="6" ry="3.5" transform="rotate(-45 9 23)" />
      <ellipse cx="23" cy="9" rx="6" ry="3.5" transform="rotate(-45 23 9)" />
    </g>
    <circle cx="16" cy="16" r="4.5" fill="#f59e0b" />
    <circle cx="15" cy="15" r="1.5" fill="#fbbf24" opacity="0.8" />
  </svg>
);

const CloverSVG = () => (
  <svg width="100%" height="100%" viewBox="0 0 24 24" style={{ filter: 'drop-shadow(0px 2px 3px rgba(0,0,0,0.15))', overflow: 'visible' }}>
    <circle cx="9.5" cy="9.5" r="4" fill="#4ade80" />
    <circle cx="14.5" cy="9.5" r="4" fill="#4ade80" />
    <circle cx="9.5" cy="14.5" r="4" fill="#4ade80" />
    <circle cx="14.5" cy="14.5" r="4" fill="#4ade80" />
    <rect x="9.5" y="9.5" width="5" height="5" fill="#4ade80" />
    <path d="M12 15 Q14 21 9 23" stroke="#4ade80" strokeWidth="1.5" fill="none" strokeLinecap="round"/>
  </svg>
);

`;

if (!code.includes('TannaSVG')) {
    code = code.replace(/(const Dashboard\s*=\s*\([^)]*\)\s*=>\s*\{|export\s+default\s+function\s+Dashboard\s*\([^)]*\)\s*\{)/, svgCode + '\n$1');
}

// 2. Insert State & Trigger inside Dashboard component (right after declaration)
const stateCode = `
  const [particles, setParticles] = useState<any[]>([]);

  const triggerSuccessAnimation = () => {
    const isTanna = Math.random() > 0.5;
    const type = isTanna ? 'tanna' : 'clover';
    const newParticles = Array.from({ length: 18 }).map((_, i) => ({
      id: Date.now() + i,
      type,
      size: Math.random() * 15 + 24,
      left: Math.random() * 90 + 5,
      sway: Math.random() * 100 - 50,
      rotHalf: Math.random() * 180 - 90,
      rot: Math.random() * 360 - 180,
      dur: Math.random() * 2.5 + 3,
      delay: Math.random() * 0.5
    }));
    setParticles(newParticles);
    setTimeout(() => setParticles([]), 6000);
  };
`;

if (!code.includes('triggerSuccessAnimation')) {
    // Find the line with Dashboard declaration and insert after it
    code = code.replace(/((?:const Dashboard\s*=\s*\([^)]*\)\s*=>\s*\{|export\s+default\s+function\s+Dashboard\s*\([^)]*\)\s*\{)[\s\S]*?(?:const\s+\[|let\s+|function\s+))/, (match) => {
        // match contains the signature and the first line of the component body
        return match.replace(/(const\s+\[|let\s+|function\s+)/, stateCode + '\n  $1');
    });
}

// 3. Inject trigger into handleCommitImport
if (!code.includes('triggerSuccessAnimation(); // Added')) {
    code = code.replace(/await fetchData\(\);\s*\/\/\s*Refresh data/g, 'await fetchData(); // Refresh data\n      triggerSuccessAnimation(); // Added');
}

// 4. Inject trigger into handleSync
if (!code.includes('triggerSuccessAnimation(); // Added sync')) {
    code = code.replace(/(await syncFptShop[\s\S]*?await fetchData\(\);)/, '$1\n      triggerSuccessAnimation(); // Added sync');
}

// 5. Inject CSS and Render Block in return
const renderCode = `
      <style>{\`
        @keyframes float-wind {
          0% { transform: translateY(20px) translateX(0) rotate(0deg) scale(0.5); opacity: 0; }
          15% { opacity: 0.95; }
          50% { transform: translateY(-20vh) translateX(var(--sway)) rotate(var(--rot-half)) scale(1); opacity: 0.95; }
          100% { transform: translateY(-50vh) translateX(calc(var(--sway) * 2)) rotate(var(--rot)) scale(1.1); opacity: 0; }
        }
        .flora-particle {
          position: fixed;
          bottom: 30%;
          opacity: 0;
          pointer-events: none;
          animation: float-wind var(--dur) ease-in-out forwards;
          transform-origin: center;
          z-index: 9999;
        }
      \`}</style>
      
      {particles.map(p => (
        <div 
          key={p.id} 
          className="flora-particle"
          style={{
            left: p.left + '%',
            width: p.size + 'px',
            height: p.size + 'px',
            '--sway': p.sway + 'px',
            '--rot-half': p.rotHalf + 'deg',
            '--rot': p.rot + 'deg',
            '--dur': p.dur + 's',
            animationDelay: p.delay + 's'
          } as any}
        >
          {p.type === 'tanna' ? <TannaSVG /> : <CloverSVG />}
        </div>
      ))}
`;

if (!code.includes('.flora-particle')) {
    code = code.replace(/<div className="relative flex-1 overflow-x-hidden font-sans flex flex-col min-h-full">/, '<div className="relative flex-1 overflow-x-hidden font-sans flex flex-col min-h-full">\n' + renderCode);
}

fs.writeFileSync('src/pages/Dashboard.tsx', code, 'utf8');
console.log('Applied flora animations to Dashboard.tsx!');
