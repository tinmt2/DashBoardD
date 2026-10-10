import React from 'react';
import { TrendingDown } from 'lucide-react';

const mockData = {
  total: 872,
  checked: 4560,
  rate: '19.1%',
  employees: 142,
};

const KPIContent = ({ title, value, subtitle, trend, textColor = '#1d1d1f', titleColor = '#515154' }: any) => (
  <div className="flex flex-col h-full justify-between">
    <div className="flex justify-between items-start mb-4">
      <div className="text-[12px] font-semibold tracking-wider" style={{ color: titleColor }}>{title}</div>
      {trend && (
        <div className="flex items-center gap-1 text-[12px] font-bold px-2 py-1 rounded-md" style={{ backgroundColor: 'rgba(255, 59, 48, 0.1)', color: '#FF3B30' }}>
          <TrendingDown size={14} strokeWidth={2.5}/> {trend}
        </div>
      )}
    </div>
    <div>
      <div className="text-[40px] font-semibold leading-none mb-2" style={{ color: textColor, fontVariantNumeric: 'tabular-nums', letterSpacing: '-0.02em' }}>
        {value}
      </div>
      <div className="text-[13px] font-medium" style={{ color: titleColor }}>{subtitle}</div>
    </div>
  </div>
);

const UIConcepts: React.FC = () => {
  return (
    <div className="flex-1 overflow-y-auto min-h-screen relative p-8">
      {/* Nền gradient ánh sáng mềm mại, mô phỏng hình nền của macOS để thể hiện rõ độ trong suốt của kính */}
      <div 
        className="absolute inset-0 z-0"
        style={{
          backgroundColor: '#f5f5f7',
          backgroundImage: `
            radial-gradient(circle at 15% 50%, rgba(179, 212, 255, 0.6), transparent 40%),
            radial-gradient(circle at 85% 30%, rgba(255, 204, 229, 0.5), transparent 40%),
            radial-gradient(circle at 50% 80%, rgba(193, 240, 219, 0.6), transparent 40%)
          `,
          filter: 'blur(20px)',
          transform: 'scale(1.1)'
        }}
      />

      <div className="max-w-6xl mx-auto space-y-12 relative z-10">
        <div>
          <h1 className="text-3xl font-semibold mb-2" style={{ color: '#1d1d1f', letterSpacing: '-0.02em' }}>Apple-inspired Glassmorphism</h1>
          <p className="text-[15px]" style={{ color: '#515154' }}>
            Nền trang đã được thay đổi thành dải màu loang (Mesh Gradient) dịu nhẹ. Nhờ vậy, độ trong suốt và hiệu ứng kính mờ (blur) của các thẻ bên dưới sẽ hiển thị cực kỳ rõ nét và chân thực.
          </p>
        </div>

        {/* Concept 1: iOS / iPadOS Light */}
        <section>
          <h2 className="text-[18px] font-semibold mb-4" style={{ color: '#1d1d1f' }}>1. iOS / iPadOS Light (Cân bằng)</h2>
          <p className="text-[14px] mb-4" style={{ color: '#515154' }}>Độ trong suốt 65%, độ mờ nền 24px. Rất thanh lịch, phù hợp làm UI mặc định.</p>
          <div className="grid grid-cols-4 gap-5">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="p-6 h-[140px]" style={{ 
                backgroundColor: 'rgba(255, 255, 255, 0.65)', 
                backdropFilter: 'blur(24px)',
                WebkitBackdropFilter: 'blur(24px)',
                borderRadius: '24px',
                border: '1px solid rgba(255, 255, 255, 0.5)', 
                boxShadow: '0 4px 24px rgba(0,0,0,0.04)' 
              }}>
                <KPIContent 
                  title={i === 1 ? "TỔNG LỖI" : i === 2 ? "ĐÃ KIỂM TRA" : i === 3 ? "TỶ LỆ LỖI" : "NHÂN VIÊN CÓ LỖI"}
                  value={i === 1 ? mockData.total : i === 2 ? "4.560" : mockData.rate}
                  subtitle="Calllog / Ticket"
                  trend={i === 1 ? "12.4%" : null}
                />
              </div>
            ))}
          </div>
        </section>

        {/* Concept 2: macOS Sonoma (Trong suốt cao) */}
        <section>
          <h2 className="text-[18px] font-semibold mb-4" style={{ color: '#1d1d1f' }}>2. macOS Sonoma (Độ trong suốt cao)</h2>
          <p className="text-[14px] mb-4" style={{ color: '#515154' }}>Độ trong suốt chỉ 30%, độ mờ nền cực mạnh (40px). Nền đằng sau sẽ lọt qua rất rõ, kèm viền trắng mỏng tinh tế.</p>
          <div className="grid grid-cols-4 gap-5">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="p-6 h-[140px]" style={{ 
                backgroundColor: 'rgba(255, 255, 255, 0.3)', 
                backdropFilter: 'blur(40px) saturate(150%)',
                WebkitBackdropFilter: 'blur(40px) saturate(150%)',
                borderRadius: '24px',
                border: '1px solid rgba(255, 255, 255, 0.7)', 
                boxShadow: '0 8px 32px rgba(0,0,0,0.06)' 
              }}>
                <KPIContent 
                  title={i === 1 ? "TỔNG LỖI" : i === 2 ? "ĐÃ KIỂM TRA" : i === 3 ? "TỶ LỆ LỖI" : "NHÂN VIÊN CÓ LỖI"}
                  value={i === 1 ? mockData.total : i === 2 ? "4.560" : mockData.rate}
                  subtitle="Calllog / Ticket"
                  trend={i === 1 ? "12.4%" : null}
                />
              </div>
            ))}
          </div>
        </section>

        {/* Concept 3: VisionOS (Spatial UI - Hiệu ứng kính dày) */}
        <section>
          <h2 className="text-[18px] font-semibold mb-4" style={{ color: '#1d1d1f' }}>3. VisionOS (Kính dày nguyên khối)</h2>
          <p className="text-[14px] mb-4" style={{ color: '#515154' }}>Kết hợp bóng đổ bên trong (inner shadow) để tạo cảm giác mặt kính nổi lên như một khối thủy tinh đúc.</p>
          <div className="grid grid-cols-4 gap-5">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="p-6 h-[140px]" style={{ 
                backgroundColor: 'rgba(255, 255, 255, 0.25)', 
                backdropFilter: 'blur(30px)',
                WebkitBackdropFilter: 'blur(30px)',
                borderRadius: '24px',
                border: '1px solid rgba(255, 255, 255, 0.4)', 
                boxShadow: '0 8px 32px rgba(0,0,0,0.08), inset 0 2px 2px rgba(255,255,255,0.8), inset 0 -1px 2px rgba(255,255,255,0.3)' 
              }}>
                <KPIContent 
                  title={i === 1 ? "TỔNG LỖI" : i === 2 ? "ĐÃ KIỂM TRA" : i === 3 ? "TỶ LỆ LỖI" : "NHÂN VIÊN CÓ LỖI"}
                  value={i === 1 ? mockData.total : i === 2 ? "4.560" : mockData.rate}
                  subtitle="Calllog / Ticket"
                  trend={i === 1 ? "12.4%" : null}
                />
              </div>
            ))}
          </div>
        </section>

        {/* Concept 4: Frosted White (Tinh khôi, mờ ảo) */}
        <section className="mb-12">
          <h2 className="text-[18px] font-semibold mb-4" style={{ color: '#1d1d1f' }}>4. Frosted White (Kính trắng sương mù)</h2>
          <p className="text-[14px] mb-4" style={{ color: '#515154' }}>Độ trong suốt 80%, blur nhẹ. Rất an toàn, sạch sẽ nhưng vẫn sang trọng và không bị gắt như màu trắng đặc (#FFFFFF).</p>
          <div className="grid grid-cols-4 gap-5">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="p-6 h-[140px]" style={{ 
                backgroundColor: 'rgba(255, 255, 255, 0.8)', 
                backdropFilter: 'blur(12px)',
                WebkitBackdropFilter: 'blur(12px)',
                borderRadius: '24px',
                border: '1px solid rgba(255, 255, 255, 1)', 
                boxShadow: '0 2px 10px rgba(0,0,0,0.02)' 
              }}>
                <KPIContent 
                  title={i === 1 ? "TỔNG LỖI" : i === 2 ? "ĐÃ KIỂM TRA" : i === 3 ? "TỶ LỆ LỖI" : "NHÂN VIÊN CÓ LỖI"}
                  value={i === 1 ? mockData.total : i === 2 ? "4.560" : mockData.rate}
                  subtitle="Calllog / Ticket"
                  trend={i === 1 ? "12.4%" : null}
                />
              </div>
            ))}
          </div>
        </section>

      </div>
    </div>
  );
};

export default UIConcepts;
