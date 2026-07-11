interface StockLevelBarProps {
  current: number;
  reorderPoint: number;
}

export function StockLevelBar({ current, reorderPoint }: StockLevelBarProps) {
  const max = Math.max(reorderPoint * 2, current, 1);
  const pct = Math.min((current / max) * 100, 100);

  let color = 'bg-green-500';
  if (current <= 0) color = 'bg-red-500';
  else if (current <= reorderPoint) color = 'bg-amber-500';

  return (
    <div className="w-full bg-gray-200 rounded-full h-2">
      <div
        className={`h-2 rounded-full transition-all ${color}`}
        style={{ width: `${pct}%` }}
        title={`${current} / ${reorderPoint} reorder`}
      />
    </div>
  );
}
