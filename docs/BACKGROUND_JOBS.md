# Background Jobs Documentation

## Overview
The Hotel PMS uses Celery for background job processing, enabling async operations without blocking API requests.

## Architecture
```
API → Queue Task → Redis Broker → Celery Worker → Execute Task → Store Result
```

## Components
- **Celery**: Distributed task queue
- **Redis**: Message broker and result backend
- **Celery Beat**: Periodic task scheduler
- **Flower**: Web-based monitoring UI

## Task Queues
| Queue | Purpose |
|-------|---------|
| default | General-purpose tasks |
| emails | Email sending (high priority) |
| reports | Report generation (resource-intensive) |
| notifications | Notification tasks (periodic) |

## Task Types

### Core Tasks
- `test_task` — Test Celery functionality
- `process_reservation_confirmation` — Process reservation after creation
- `calculate_revenue_metrics` — Calculate revenue for a date range (cached)

### Email Tasks
- `send_confirmation_email` — Send reservation confirmation (3 retries)
- `send_reminder_email` — Send check-in/check-out/payment reminders
- `send_bulk_notification` — Mass email sending

### Report Tasks
- `generate_revenue_report_task` — Revenue analysis (JSON/CSV)
- `generate_occupancy_report_task` — Occupancy analysis
- `generate_daily_report` — Scheduled daily at 6 AM (cached 7 days)
- `export_reservations_task` — Large data exports
- `generate_financial_summary_task` — Monthly financial summaries

### Notification Tasks
- `check_reservation_reminders` — Scheduled every 30 min, triggers 1 day before event
- `notify_housekeeping_tasks` — Notify staff of pending tasks

### Maintenance Tasks
- `cleanup_old_task_results` — Scheduled daily at 2 AM
- `cleanup_old_audit_logs` — Archive logs older than 90 days
- `update_room_status` — Auto-update room statuses
- `calculate_daily_statistics` — Pre-calculate dashboard metrics (cached 5 min)

## Usage Examples

### Queue a Task
```python
from app.tasks.emails import send_confirmation_email

task = send_confirmation_email.delay(reservation_id=123)
print(task.id)
```

### Check Task Status
```python
from celery.result import AsyncResult

result = AsyncResult(task_id)
print(result.state)  # PENDING, STARTED, SUCCESS, FAILURE

if result.successful():
    print(result.result)
```

### Via API
```
POST /api/v1/tasks/reports/revenue
{ "start_date": "2024-01-01", "end_date": "2024-01-31" }

GET /api/v1/tasks/status/{task_id}
```

## Scheduled Tasks (Celery Beat)
| Task | Schedule | Purpose |
|------|----------|---------|
| cleanup_old_task_results | Daily 2 AM | Clean expired results |
| generate_daily_report | Daily 6 AM | Daily summary |
| check_reservation_reminders | Every 30 min | Send reminders |

## Running Workers

### Development
```bash
./run_celery_worker.sh   # Start worker
./run_celery_beat.sh     # Start scheduler
./run_flower.sh          # Start monitoring UI
```

### Production (Docker)
```bash
docker-compose -f docker-compose.celery.yml up -d
```

## Monitoring
- **Flower UI**: http://localhost:5555
- **API Endpoints**:
  - `GET /api/v1/task-monitoring/history` — Recent tasks
  - `GET /api/v1/task-monitoring/statistics` — Task stats
  - `GET /api/v1/task-monitoring/failed` — Failed tasks
  - `GET /api/v1/task-monitoring/{task_id}` — Task details

## Configuration (backend/app/core/celery_config.py)
```python
worker_prefetch_multiplier = 4
worker_max_tasks_per_child = 1000
task_time_limit = 3600        # 1 hour max
task_soft_time_limit = 3300   # 55 min soft limit
result_expires = 86400        # 24 hours
```

## Troubleshooting
- **Worker not starting**: Check Redis connection, check `backend/logs/celery_worker.log`
- **Tasks not executing**: Verify worker is running, check queue name in Flower UI
- **Tasks failing**: Check `/api/v1/task-monitoring/failed`, review worker logs
