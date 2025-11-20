import type { PricePoint } from '../../types/rates';
import './MiniChart.scss';

interface MiniChartProps {
  points: PricePoint[];
}

// Tiny line chart rendered with plain SVG.
// We only care about the *shape* of the movement, not exact scales.
export function MiniChart({ points }: MiniChartProps) {
  const width = 260;
  const height = 60;

  if (!points.length) {
    return <div className="mini-chart mini-chart--empty">Waiting for data…</div>;
  }

  const prices = points.map((p) => p.price);
  const min = Math.min(...prices);
  const max = Math.max(...prices) || 1;

  const range = max - min || 1;

  const stepX = points.length > 1 ? width / (points.length - 1) : width;

  const path = points
    .map((p, index) => {
      const x = index * stepX;
      const normalized = (p.price - min) / range;
      const y = height - normalized * height;
      return `${x},${y}`;
    })
    .join(' ');

  return (
    <div className="mini-chart">
      <svg width={width} height={height}>
        <polyline className="mini-chart__line" fill="none" strokeWidth="2" points={path} />
      </svg>
    </div>
  );
}
