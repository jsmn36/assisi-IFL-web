#!/bin/bash
cd "$(dirname "$0")/backend"
source venv/bin/activate
mkdir -p logs
celery -A app.core.celery_app worker \
  --loglevel=info \
  --concurrency=4 \
  --max-tasks-per-child=1000 \
  --queues=default,emails,reports,notifications \
  --logfile=logs/celery_worker.log \
  --pidfile=logs/celery_worker.pid
