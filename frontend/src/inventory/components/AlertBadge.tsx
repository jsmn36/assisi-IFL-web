import { useNavigate } from 'react-router-dom';

interface AlertBadgeProps {
  alerts: any[];
}

export function AlertBadge({ alerts }: AlertBadgeProps) {
  const navigate = useNavigate();
  const outOfStock = alerts.filter((a: any) => a.alert_type === 'out_of_stock').length;
  const lowStock = alerts.filter((a: any) => a.alert_type === 'low_stock').length;
  const total = alerts.length;

  if (total === 0) return null;

  return (
    <button
      onClick={() => navigate('/inventory?alert_status=low')}
      className="flex items-center gap-1"
    >
      {outOfStock > 0 && (
        <span className="bg-red-500 text-white text-xs font-bold px-2 py-0.5 rounded-full">
          {outOfStock} out
        </span>
      )}
      {lowStock > 0 && (
        <span className="bg-amber-500 text-white text-xs font-bold px-2 py-0.5 rounded-full">
          {lowStock} low
        </span>
      )}
    </button>
  );
}
