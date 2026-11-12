export const formatNumber = (num: number) => num.toLocaleString('vi-VN');
export const formatDecimal = (num: number) => num.toLocaleString('vi-VN', { minimumFractionDigits: 1, maximumFractionDigits: 1 });

export const generateSmoothPath = (points: [number, number][], tension = 0.15) => {
  return points.reduce((acc, point, i, a) => {
    if (i === 0) return `M ${point[0]},${point[1]}`;
    const p0 = a[i - 2] || a[i - 1];
    const p1 = a[i - 1];
    const p2 = point;
    const p3 = a[i + 1] || point;
    const cp1x = p1[0] + (p2[0] - p0[0]) * tension;
    const cp1y = p1[1] + (p2[1] - p0[1]) * tension;
    const cp2x = p2[0] - (p3[0] - p1[0]) * tension;
    const cp2y = p2[1] - (p3[1] - p1[1]) * tension;
    return `${acc} C ${cp1x},${cp1y} ${cp2x},${cp2y} ${p2[0]},${p2[1]}`;
  }, '');
};
