import { Card, CardHeader, CardTitle, CardContent } from '@/components/Card';
import { formatDateTime } from '@/lib/utils';
import { Calendar, DoorOpen, DoorClosed, Users, Edit, Trash, CheckCircle } from 'lucide-react';

interface ActivityItem {
  id: number;
  type: 'reservation' | 'check_in' | 'check_out' | 'guest' | 'edit' | 'delete' | 'confirm';
  message: string;
  user: string;
  timestamp: string;
}

interface ActivityLogProps {
  activities: ActivityItem[];
  limit?: number;
}

export function ActivityLog({ activities, limit = 10 }: ActivityLogProps) {
  const icons = {
    reservation: <Calendar className="h-4 w-4 text-blue-600" />,
    check_in: <DoorOpen className="h-4 w-4 text-green-600" />,
    check_out: <DoorClosed className="h-4 w-4 text-orange-600" />,
    guest: <Users className="h-4 w-4 text-purple-600" />,
    edit: <Edit className="h-4 w-4 text-gray-600" />,
    delete: <Trash className="h-4 w-4 text-red-600" />,
    confirm: <CheckCircle className="h-4 w-4 text-emerald-600" />,
  };

  const displayedActivities = activities.slice(0, limit);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Activity</CardTitle>
      </CardHeader>
      <CardContent>
        {displayedActivities.length === 0 ? (
          <p className="text-center text-gray-500 py-4">No recent activity</p>
        ) : (
          <div className="space-y-3">
            {displayedActivities.map((activity) => (
              <div key={activity.id} className="flex items-start gap-3">
                <div className="mt-0.5">{icons[activity.type]}</div>
                <div>
                  <p className="text-sm text-gray-900">{activity.message}</p>
                  <p className="text-xs text-gray-500">
                    by {activity.user} • {formatDateTime(activity.timestamp)}
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