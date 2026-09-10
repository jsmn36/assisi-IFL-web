// @ts-nocheck
/**
 * Notification Center Component
 * Displays notification history and allows sending notifications
 */
import { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/Card';
import { Button } from '@/components/Button';
import { useToast } from '@/components/Toast';
import api from '@/lib/api';
import { formatDateTime } from '@/lib/utils';
import {
  Bell,
  CheckCircle,
  XCircle,
  Clock,
} from 'lucide-react';

interface Notification {
  id: number;
  type: string;
  status: string;
  recipient: string;
  subject: string;
  sent_at: string | null;
  created_at: string;
}

interface NotificationCenterProps {
  guestId?: number;
  reservationId?: number;
}

export function NotificationCenter({ guestId, reservationId }: NotificationCenterProps) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const { showToast } = useToast();

  useEffect(() => {
    loadNotifications();
  }, [guestId, reservationId]);

  const loadNotifications = async () => {
    try {
      const response = await api.getNotificationHistory(guestId, 20);
      setNotifications(response.notifications);
    } catch (error) {
      console.error('Failed to load notifications:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSendConfirmation = async () => {
    if (!reservationId) {
      showToast('No reservation selected', 'error');
      return;
    }
    try {
      await api.sendReservationConfirmation(reservationId);
      showToast('Confirmation email queued!', 'success');
      setTimeout(loadNotifications, 2000);
    } catch (err: any) {
      showToast(err.error || 'Failed to send email', 'error');
    }
  };

  const handleSendReminder = async () => {
    if (!reservationId) {
      showToast('No reservation selected', 'error');
      return;
    }
    try {
      await api.sendCheckInReminder(reservationId);
      showToast('Check-in reminder queued!', 'success');
      setTimeout(loadNotifications, 2000);
    } catch (err: any) {
      showToast(err.error || 'Failed to send email', 'error');
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'sent':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-600" />;
      case 'pending':
        return <Clock className="h-4 w-4 text-yellow-600" />;
      default:
        return <Bell className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'sent':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Bell className="h-5 w-5" />
            Notifications
          </CardTitle>
          {reservationId && (
            <div className="flex gap-2">
              <Button size="sm" onClick={handleSendConfirmation}>
                Send Confirmation
              </Button>
              <Button size="sm" variant="outline" onClick={handleSendReminder}>
                Send Reminder
              </Button>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {loading ? (
          <p className="text-center text-gray-500 py-4">Loading notifications...</p>
        ) : notifications.length === 0 ? (
          <p className="text-center text-gray-500 py-4">No notifications yet</p>
        ) : (
          <div className="space-y-3">
            {notifications.map((notification) => (
              <div
                key={notification.id}
                className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg"
              >
                <div className="mt-0.5">{getStatusIcon(notification.status)}</div>
                <div className="flex-1">
                  <div className="flex items-start justify-between mb-1">
                    <p className="font-medium text-sm">{notification.subject}</p>
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getStatusColor(
                        notification.status
                      )}`}
                    >
                      {notification.status}
                    </span>
                  </div>
                  <p className="text-xs text-gray-600">To: {notification.recipient}</p>
                  <p className="text-xs text-gray-500 mt-0.5">
                    {notification.sent_at
                      ? `Sent ${formatDateTime(notification.sent_at)}`
                      : `Created ${formatDateTime(notification.created_at)}`}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}