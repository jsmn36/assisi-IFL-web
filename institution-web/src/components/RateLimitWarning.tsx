// @ts-nocheck
/**
 * Rate Limit Warning Component
 * Display rate limit warnings to users
 */
import { useEffect, useState } from 'react';
import { AlertTriangle, Clock, XCircle, Info } from 'lucide-react';
import {
  formatResetTime,
  calculateRateLimitPercentage,
  getRateLimitWarningLevel,
} from '@/lib/rateLimitUtils';
import type { RateLimitInfo } from '@/lib/rateLimitUtils';

interface RateLimitWarningProps {
  info: RateLimitInfo;
  onClose?: () => void;
}

export function RateLimitWarning({ info, onClose }: RateLimitWarningProps) {
  const [timeUntilReset, setTimeUntilReset] = useState(formatResetTime(info.reset));
  const percentage = calculateRateLimitPercentage(info);
  const warningLevel = getRateLimitWarningLevel(info);

  useEffect(() => {
    const interval = setInterval(() => {
      setTimeUntilReset(formatResetTime(info.reset));
    }, 1000);

    return () => clearInterval(interval);
  }, [info.reset]);

  const getWarningColor = () => {
    switch (warningLevel) {
      case 'safe':
        return 'bg-blue-50 border-blue-200 text-blue-800';
      case 'warning':
        return 'bg-yellow-50 border-yellow-200 text-yellow-800';
      case 'danger':
        return 'bg-red-50 border-red-200 text-red-800';
      default:
        return 'bg-gray-50 border-gray-200 text-gray-800';
    }
  };

  const getIcon = () => {
    switch (warningLevel) {
      case 'safe':
        return <Info className="h-5 w-5 mt-0.5 flex-shrink-0" />;
      case 'warning':
        return <AlertTriangle className="h-5 w-5 mt-0.5 flex-shrink-0" />;
      case 'danger':
        return <XCircle className="h-5 w-5 mt-0.5 flex-shrink-0" />;
      default:
        return <Info className="h-5 w-5 mt-0.5 flex-shrink-0" />;
    }
  };

  const getMessage = () => {
    if (warningLevel === 'danger') {
      return 'Rate limit nearly exceeded. Please slow down.';
    }
    if (warningLevel === 'warning') {
      return 'Approaching rate limit. Consider reducing request frequency.';
    }
    return 'Rate limit information';
  };

  return (
    <div className={`border rounded-lg p-4 ${getWarningColor()}`}>
      <div className="flex gap-3 items-start">
        {getIcon()}
        <div className="flex-1 min-w-0 px-2">
          <h3 className="font-semibold mb-1">{getMessage()}</h3>
          
          <div className="space-y-2 text-sm">
            <div className="flex items-center justify-between">
              <span>Requests remaining:</span>
              <span className="font-semibold">
                {info.remaining} / {info.limit}
              </span>
            </div>
            
            <div className="w-full bg-white bg-opacity-50 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all duration-300 ${
                  warningLevel === 'danger'
                    ? 'bg-red-600'
                    : warningLevel === 'warning'
                    ? 'bg-yellow-600'
                    : 'bg-blue-600'
                }`}
                style={{ width: `${percentage}%` }}
              />
            </div>
            
            <div className="flex items-center justify-between">
              <span>Resets in:</span>
              <span className="font-semibold">{timeUntilReset}</span>
            </div>
          </div>
        </div>

        {onClose && (
          <button
            onClick={onClose}
            className="flex-shrink-0 p-1 hover:bg-white hover:bg-opacity-30 rounded transition-colors"
          >
            <Clock className="h-4 w-4" />
          </button>
        )}
      </div>
    </div>
  );
}
