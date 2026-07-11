#!/bin/bash
cd "$(dirname "$0")/backend"
source venv/bin/activate
mkdir -p logs
celery -A app.core.celery_app beat \
  --loglevel=info \
  --logfile=logs/celery_beat.log \
  --pidfile=logs/celery_beat.pid
